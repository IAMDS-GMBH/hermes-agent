"""Outlook / Microsoft Graph inbox read tool.

Lets the agent fetch and summarize emails from the user's Outlook inbox
on demand, using the same delegated token cache as the Outlook gateway
adapter (``~/.hermes/outlook_token.json``).

Credentials are resolved (in order):
  1. ``platforms.outlook.extra`` in ``config.yaml``
  2. ``OUTLOOK_TENANT_ID`` / ``OUTLOOK_CLIENT_ID`` / ``OUTLOOK_CLIENT_SECRET``
     environment variables

Authentication flow:
  - If a valid token/refresh exists in the cache, emails are fetched silently.
  - If no token cache exists, the tool returns a device-code auth prompt
    (URL + code) immediately — the agent surfaces these to the user in chat.
    The user opens the URL, enters the code, and then calls the tool again.
    On the second call the token is cached and emails are returned.

The tool is gated on ``OUTLOOK_TENANT_ID`` and ``OUTLOOK_CLIENT_ID`` being
available — the same minimum requirement as the delegated gateway adapter.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any

from tools.registry import registry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Credential helpers (mirrors adapter.py logic, no coupling)
# ---------------------------------------------------------------------------

def _outlook_creds_from_config() -> dict[str, str]:
    """Return Outlook credentials from config.yaml platforms.outlook.extra."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config()
        extra = (
            cfg.get("platforms", {})
               .get("outlook", {})
               .get("extra", {})
        ) or {}
        return {
            "tenant_id": str(extra.get("tenant_id") or "").strip(),
            "client_id": str(extra.get("client_id") or "").strip(),
            "client_secret": str(extra.get("client_secret") or "").strip(),
        }
    except Exception:
        return {"tenant_id": "", "client_id": "", "client_secret": ""}


def _get_outlook_creds() -> dict[str, str]:
    cfg = _outlook_creds_from_config()
    return {
        "tenant_id": cfg["tenant_id"] or os.getenv("OUTLOOK_TENANT_ID", ""),
        "client_id": cfg["client_id"] or os.getenv("OUTLOOK_CLIENT_ID", ""),
        "client_secret": cfg["client_secret"] or os.getenv("OUTLOOK_CLIENT_SECRET", ""),
    }


def _check_outlook_tool_requirements() -> bool:
    creds = _get_outlook_creds()
    return bool(creds["tenant_id"] and creds["client_id"])


def _has_valid_token_cache() -> bool:
    """Return True if a usable token/refresh already exists on disk."""
    try:
        from hermes_constants import get_hermes_home
        cache_path = get_hermes_home() / "outlook_token.json"
        if not cache_path.exists():
            return False
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        # A refresh token is enough — it will silently renew the access token
        if data.get("refresh_token"):
            return True
        # Or an unexpired access token
        expires_at = float(data.get("expires_at", 0))
        return expires_at > time.time() + 120
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Async: initiate device code (no polling — returns prompt immediately)
# ---------------------------------------------------------------------------

async def _start_device_code_async() -> dict[str, Any]:
    """Request a device code from Microsoft and return the auth prompt info."""
    import httpx
    from tools.microsoft_graph_auth import (
        GraphDelegatedCredentials,
        DEFAULT_GRAPH_AUTHORITY_URL,
        DEFAULT_DELEGATED_SCOPE,
    )
    creds_raw = _get_outlook_creds()
    creds = GraphDelegatedCredentials(
        tenant_id=creds_raw["tenant_id"],
        client_id=creds_raw["client_id"],
        client_secret=creds_raw["client_secret"] or None,
    )
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            creds.device_code_url,
            data={"client_id": creds.client_id, "scope": DEFAULT_DELEGATED_SCOPE},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Device code request failed: {resp.text}")
        payload = resp.json()

    expires_in = int(payload.get("expires_in", 900))
    return {
        "device_code": payload["device_code"],
        "user_code": payload["user_code"],
        "verification_uri": payload["verification_uri"],
        "expires_in_seconds": expires_in,
        "poll_interval": int(payload.get("interval", 5)),
    }


# ---------------------------------------------------------------------------
# Async: poll for token after user has authenticated
# ---------------------------------------------------------------------------

async def _poll_device_code_async(device_code: str) -> bool:
    """Poll once for a token. Saves cache on success. Returns True if authed."""
    import httpx
    from tools.microsoft_graph_auth import (
        GraphDelegatedCredentials,
        MicrosoftGraphAuthError,
    )
    from hermes_constants import get_hermes_home

    creds_raw = _get_outlook_creds()
    creds = GraphDelegatedCredentials(
        tenant_id=creds_raw["tenant_id"],
        client_id=creds_raw["client_id"],
        client_secret=creds_raw["client_secret"] or None,
    )
    token_data: dict[str, str] = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": creds.client_id,
        "device_code": device_code,
    }
    if creds.client_secret:
        token_data["client_secret"] = creds.client_secret

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(creds.token_url, data=token_data)
        result = resp.json()

    error = result.get("error")
    if error in ("authorization_pending", "slow_down"):
        return False
    if error:
        raise RuntimeError(f"Token poll failed: {result.get('error_description', error)}")

    access_token = result.get("access_token", "").strip()
    refresh_token = result.get("refresh_token", "").strip()
    if not access_token or not refresh_token:
        raise RuntimeError("Missing access_token or refresh_token in response.")

    expires_in = int(result.get("expires_in", 3600))
    cache_path = get_hermes_home() / "outlook_token.json"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": time.time() + max(0, expires_in),
            "token_type": result.get("token_type", "Bearer"),
        }, indent=2),
        encoding="utf-8",
    )
    try:
        cache_path.chmod(0o600)
    except Exception:
        pass
    return True


# ---------------------------------------------------------------------------
# Core async fetch logic
# ---------------------------------------------------------------------------

async def _fetch_emails_async(
    count: int,
    folder: str,
    unread_only: bool,
    include_body: bool,
) -> list[dict[str, Any]]:
    from tools.microsoft_graph_auth import (
        GraphDelegatedCredentials,
        GraphDeviceCodeProvider,
    )
    from tools.microsoft_graph_client import MicrosoftGraphClient

    creds_raw = _get_outlook_creds()
    creds = GraphDelegatedCredentials(
        tenant_id=creds_raw["tenant_id"],
        client_id=creds_raw["client_id"],
        client_secret=creds_raw["client_secret"] or None,
    )
    provider = GraphDeviceCodeProvider(creds)
    client = MicrosoftGraphClient(provider, user_agent="Hermes-Outlook/1.0")

    select_fields = ["id", "subject", "receivedDateTime", "isRead",
                     "from", "toRecipients", "hasAttachments", "importance"]
    if include_body:
        select_fields.append("bodyPreview")

    params: dict[str, Any] = {
        "$top": min(max(1, count), 50),
        "$orderby": "receivedDateTime desc",
        "$select": ",".join(select_fields),
    }
    if unread_only:
        params["$filter"] = "isRead eq false"

    folder_map = {
        "inbox": "inbox",
        "sent": "sentitems",
        "drafts": "drafts",
        "deleted": "deleteditems",
        "archive": "archive",
    }
    graph_folder = folder_map.get(folder.lower(), "inbox")
    path = f"/me/mailFolders/{graph_folder}/messages"

    resp = await client.get_json(path, params=params)
    return resp.get("value", [])


def _format_email(msg: dict[str, Any], include_body: bool) -> dict[str, Any]:
    sender = msg.get("from", {}).get("emailAddress", {})
    return {
        "id": msg.get("id", ""),
        "subject": msg.get("subject") or "(no subject)",
        "from": f"{sender.get('name', '')} <{sender.get('address', '')}>".strip(),
        "received": msg.get("receivedDateTime", ""),
        "is_read": msg.get("isRead", True),
        "has_attachments": msg.get("hasAttachments", False),
        "importance": msg.get("importance", "normal"),
        **({"body_preview": msg.get("bodyPreview", "")} if include_body else {}),
    }


def _run_async(coro: Any, timeout: float = 120) -> Any:
    """Run a coroutine safely regardless of whether a loop is already running."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result(timeout=timeout)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Tool handler
# ---------------------------------------------------------------------------

def outlook_read_emails(
    count: int = 10,
    folder: str = "inbox",
    unread_only: bool = False,
    include_body: bool = True,
    device_code: str = "",
    task_id: str | None = None,
) -> str:
    """Fetch recent emails, or handle device-code auth if no token exists."""

    # Step 1 — if caller is providing a device_code to poll (user just authed)
    if device_code:
        try:
            authed = _run_async(_poll_device_code_async(device_code), timeout=30)
        except Exception as exc:
            return json.dumps({"error": f"Token poll failed: {exc}"})
        if not authed:
            return json.dumps({
                "status": "pending",
                "message": "Authentication still pending. Please complete sign-in at the URL provided, then try again.",
            })
        # Fall through — now fetch emails with the fresh token

    # Step 2 — if no token cached, initiate device code and return prompt
    if not _has_valid_token_cache():
        try:
            info = _run_async(_start_device_code_async(), timeout=30)
        except Exception as exc:
            return json.dumps({"error": f"Could not start device code flow: {exc}"})
        return json.dumps({
            "status": "auth_required",
            "message": (
                "Outlook authentication required. "
                f"Open {info['verification_uri']} and enter the code: {info['user_code']}. "
                f"The code expires in {info['expires_in_seconds'] // 60} minutes. "
                "Once you have signed in, call this tool again with the device_code parameter "
                f"set to: {info['device_code']}"
            ),
            "verification_uri": info["verification_uri"],
            "user_code": info["user_code"],
            "device_code": info["device_code"],
            "expires_in_seconds": info["expires_in_seconds"],
        })

    # Step 3 — fetch emails normally
    try:
        raw_emails = _run_async(
            _fetch_emails_async(count, folder, unread_only, include_body), timeout=120
        )
    except Exception as exc:
        return json.dumps({"error": str(exc)})

    emails = [_format_email(m, include_body) for m in raw_emails]
    return json.dumps({
        "folder": folder,
        "count": len(emails),
        "unread_only": unread_only,
        "emails": emails,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="outlook_read_emails",
    toolset="outlook",
    schema={
        "name": "outlook_read_emails",
        "description": (
            "Read emails from the Microsoft Outlook / Microsoft 365 mailbox. "
            "Use this to fetch recent emails, get a briefing, check unread messages, "
            "or search the inbox. Returns subject, sender, date, and optional body preview."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Number of emails to fetch (1-50). Default 10.",
                    "default": 10,
                },
                "folder": {
                    "type": "string",
                    "description": "Folder to read: inbox, sent, drafts, deleted, archive. Default inbox.",
                    "default": "inbox",
                    "enum": ["inbox", "sent", "drafts", "deleted", "archive"],
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "If true, return only unread messages.",
                    "default": False,
                },
                "include_body": {
                    "type": "boolean",
                    "description": "Include body preview (~255 chars) in results.",
                    "default": True,
                },
                "device_code": {
                    "type": "string",
                    "description": (
                        "Only set this after an auth_required response. "
                        "Pass back the device_code value from that response "
                        "after the user has completed sign-in at the verification URL."
                    ),
                    "default": "",
                },
            },
            "required": [],
        },
    },
    handler=lambda args, **kw: outlook_read_emails(
        count=int(args.get("count", 10)),
        folder=str(args.get("folder", "inbox")),
        unread_only=bool(args.get("unread_only", False)),
        include_body=bool(args.get("include_body", True)),
        device_code=str(args.get("device_code", "")),
        task_id=kw.get("task_id"),
    ),
    check_fn=_check_outlook_tool_requirements,
    requires_env=["OUTLOOK_TENANT_ID", "OUTLOOK_CLIENT_ID"],
)
