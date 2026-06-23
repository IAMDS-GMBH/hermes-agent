"""Microsoft Graph app-only and delegated authentication helpers."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

DEFAULT_GRAPH_SCOPE = "https://graph.microsoft.com/.default"
DEFAULT_DELEGATED_SCOPE = "Mail.Read Mail.Send offline_access"
DEFAULT_GRAPH_AUTHORITY_URL = "https://login.microsoftonline.com"
DEFAULT_TOKEN_SKEW_SECONDS = 120


class MicrosoftGraphAuthError(RuntimeError):
    """Base class for Microsoft Graph auth failures."""


class MicrosoftGraphConfigError(MicrosoftGraphAuthError):
    """Raised when Graph credentials are missing or invalid."""


class MicrosoftGraphTokenError(MicrosoftGraphAuthError):
    """Raised when token acquisition fails."""


@dataclass(frozen=True)
class GraphCredentials:
    """Normalized Microsoft Graph app-only credentials."""

    tenant_id: str
    client_id: str
    client_secret: str
    scope: str = DEFAULT_GRAPH_SCOPE
    authority_url: str = DEFAULT_GRAPH_AUTHORITY_URL

    @property
    def token_url(self) -> str:
        base = self.authority_url.rstrip("/")
        tenant = self.tenant_id.strip().strip("/")
        return f"{base}/{tenant}/oauth2/v2.0/token"

    @classmethod
    def from_env(
        cls,
        environ: dict[str, str] | None = None,
        *,
        required: bool = True,
    ) -> "GraphCredentials | None":
        env = environ if environ is not None else os.environ
        tenant_id = (env.get("MSGRAPH_TENANT_ID") or "").strip()
        client_id = (env.get("MSGRAPH_CLIENT_ID") or "").strip()
        client_secret = (env.get("MSGRAPH_CLIENT_SECRET") or "").strip()
        scope = (env.get("MSGRAPH_SCOPE") or DEFAULT_GRAPH_SCOPE).strip()
        authority_url = (
            env.get("MSGRAPH_AUTHORITY_URL") or DEFAULT_GRAPH_AUTHORITY_URL
        ).strip()

        missing = [
            name
            for name, value in (
                ("MSGRAPH_TENANT_ID", tenant_id),
                ("MSGRAPH_CLIENT_ID", client_id),
                ("MSGRAPH_CLIENT_SECRET", client_secret),
            )
            if not value
        ]
        if missing:
            if not required:
                return None
            raise MicrosoftGraphConfigError(
                f"Missing Microsoft Graph configuration: {', '.join(missing)}"
            )

        return cls(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            authority_url=authority_url,
        )


@dataclass
class CachedAccessToken:
    """Cached app-only Graph access token."""

    access_token: str
    expires_at: float
    token_type: str = "Bearer"

    def is_expired(self, *, skew_seconds: int = DEFAULT_TOKEN_SKEW_SECONDS) -> bool:
        return self.expires_at <= (time.time() + max(0, int(skew_seconds)))

    @property
    def expires_in_seconds(self) -> int:
        return max(0, int(self.expires_at - time.time()))


class MicrosoftGraphTokenProvider:
    """Acquire and cache Microsoft Graph app-only access tokens."""

    def __init__(
        self,
        credentials: GraphCredentials,
        *,
        timeout: float = 20.0,
        skew_seconds: int = DEFAULT_TOKEN_SKEW_SECONDS,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.credentials = credentials
        self.timeout = timeout
        self.skew_seconds = max(0, int(skew_seconds))
        self._transport = transport
        self._cached_token: CachedAccessToken | None = None
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(
        cls,
        environ: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> "MicrosoftGraphTokenProvider":
        credentials = GraphCredentials.from_env(environ)
        return cls(credentials, **kwargs)

    def clear_cache(self) -> None:
        self._cached_token = None

    def inspect_token_health(self) -> dict[str, Any]:
        cached = self._cached_token
        return {
            "configured": True,
            "tenant_id": self.credentials.tenant_id,
            "client_id": self.credentials.client_id,
            "scope": self.credentials.scope,
            "authority_url": self.credentials.authority_url,
            "token_url": self.credentials.token_url,
            "cached": bool(cached),
            "expires_in_seconds": cached.expires_in_seconds if cached else None,
            "is_expired": cached.is_expired(skew_seconds=0) if cached else None,
            "refresh_skew_seconds": self.skew_seconds,
        }

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        cached = self._cached_token
        if not force_refresh and cached and not cached.is_expired(
            skew_seconds=self.skew_seconds
        ):
            return cached.access_token

        async with self._lock:
            cached = self._cached_token
            if not force_refresh and cached and not cached.is_expired(
                skew_seconds=self.skew_seconds
            ):
                return cached.access_token

            token = await self._fetch_access_token()
            self._cached_token = token
            return token.access_token

    async def _fetch_access_token(self) -> CachedAccessToken:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.credentials.client_id,
            "client_secret": self.credentials.client_secret,
            "scope": self.credentials.scope,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            transport=self._transport,
        ) as client:
            response = await client.post(
                self.credentials.token_url,
                data=data,
                headers=headers,
            )

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise MicrosoftGraphTokenError(
                "Microsoft Graph token request failed with HTTP "
                f"{response.status_code}: {detail}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise MicrosoftGraphTokenError(
                "Microsoft Graph token response was not valid JSON."
            ) from exc

        access_token = str(payload.get("access_token") or "").strip()
        token_type = str(payload.get("token_type") or "Bearer").strip() or "Bearer"
        expires_in = payload.get("expires_in")

        if not access_token:
            raise MicrosoftGraphTokenError(
                "Microsoft Graph token response did not include access_token."
            )

        try:
            expires_in_seconds = int(expires_in)
        except (TypeError, ValueError) as exc:
            raise MicrosoftGraphTokenError(
                "Microsoft Graph token response did not include a valid expires_in."
            ) from exc

        return CachedAccessToken(
            access_token=access_token,
            token_type=token_type,
            expires_at=time.time() + max(0, expires_in_seconds),
        )


# ---------------------------------------------------------------------------
# Delegated auth — Device Code Flow
# ---------------------------------------------------------------------------

_TOKEN_CACHE_FILENAME = "outlook_token.json"


@dataclass(frozen=True)
class GraphDelegatedCredentials:
    """Credentials for delegated (on-behalf-of-user) Microsoft Graph auth."""

    tenant_id: str
    client_id: str
    client_secret: str | None = None  # None = public client
    scope: str = DEFAULT_DELEGATED_SCOPE
    authority_url: str = DEFAULT_GRAPH_AUTHORITY_URL

    @property
    def device_code_url(self) -> str:
        base = self.authority_url.rstrip("/")
        return f"{base}/{self.tenant_id.strip()}/oauth2/v2.0/devicecode"

    @property
    def token_url(self) -> str:
        base = self.authority_url.rstrip("/")
        return f"{base}/{self.tenant_id.strip()}/oauth2/v2.0/token"


class GraphDeviceCodeProvider:
    """Delegated Graph token provider using the OAuth 2.0 Device Code flow.

    On first use it prints a URL + one-time code to the gateway log so the
    user can authenticate in a browser.  The resulting refresh token is
    persisted to ``~/.hermes/outlook_token.json`` and silently renewed on
    subsequent gateway starts.

    Optionally accepts a ``device_code_callback`` for integration with UI
    (e.g., desktop app modal). The callback is called with device code info
    and can be async or sync.

    Usage::

        creds = GraphDelegatedCredentials(tenant_id=..., client_id=...)
        provider = GraphDeviceCodeProvider(creds)
        token = await provider.get_access_token()

    With callback (e.g., desktop app)::

        async def on_device_code(verification_uri, user_code, expires_in):
            # Send to desktop UI, show modal, etc.
            await notify_desktop(verification_uri, user_code, expires_in)

        provider = GraphDeviceCodeProvider(creds, device_code_callback=on_device_code)
        token = await provider.get_access_token()
    """

    def __init__(
        self,
        credentials: GraphDelegatedCredentials,
        *,
        timeout: float = 20.0,
        skew_seconds: int = DEFAULT_TOKEN_SKEW_SECONDS,
        token_cache_path: Path | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
        device_code_callback: callable | None = None,
    ) -> None:
        self.credentials = credentials
        self.timeout = timeout
        self.skew_seconds = max(0, int(skew_seconds))
        self._transport = transport
        self._token_cache_path: Path = (
            token_cache_path
            if token_cache_path is not None
            else get_hermes_home() / _TOKEN_CACHE_FILENAME
        )
        self._cached_token: CachedAccessToken | None = None
        self._refresh_token: str | None = None
        self._lock = asyncio.Lock()
        self._device_code_callback = device_code_callback
        self._load_token_cache()

    # ------------------------------------------------------------------
    # Public interface (same as MicrosoftGraphTokenProvider)
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        self._cached_token = None
        self._refresh_token = None

    async def get_access_token(self, *, force_refresh: bool = False) -> str:
        cached = self._cached_token
        if not force_refresh and cached and not cached.is_expired(
            skew_seconds=self.skew_seconds
        ):
            return cached.access_token

        async with self._lock:
            cached = self._cached_token
            if not force_refresh and cached and not cached.is_expired(
                skew_seconds=self.skew_seconds
            ):
                return cached.access_token

            if self._refresh_token:
                try:
                    token, refresh = await self._refresh_access_token(self._refresh_token)
                    self._cached_token = token
                    self._refresh_token = refresh
                    self._save_token_cache()
                    return token.access_token
                except MicrosoftGraphTokenError as exc:
                    logger.warning("[Outlook] Refresh token invalid, re-authenticating: %s", exc)
                    self._refresh_token = None

            # No valid refresh token — run device code flow
            token, refresh = await self._device_code_flow()
            self._cached_token = token
            self._refresh_token = refresh
            self._save_token_cache()
            return token.access_token

    # ------------------------------------------------------------------
    # Device code flow
    # ------------------------------------------------------------------

    async def _device_code_flow(self) -> tuple[CachedAccessToken, str]:
        """Run the interactive device code flow and return (access_token, refresh_token)."""
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            transport=self._transport,
        ) as client:
            data: dict[str, str] = {
                "client_id": self.credentials.client_id,
                "scope": self.credentials.scope,
            }
            resp = await client.post(self.credentials.device_code_url, data=data)
            if resp.status_code >= 400:
                raise MicrosoftGraphTokenError(
                    f"Device code request failed: {_extract_error_detail(resp)}"
                )
            payload = resp.json()

        device_code = payload["device_code"]
        user_code = payload["user_code"]
        verification_uri = payload["verification_uri"]
        expires_in = int(payload.get("expires_in", 900))
        interval = int(payload.get("interval", 5))
        deadline = time.time() + expires_in

        # Notify via callback if provided (e.g., for desktop app modal)
        if self._device_code_callback:
            try:
                await self._device_code_callback(
                    verification_uri=verification_uri,
                    user_code=user_code,
                    expires_in=expires_in,
                )
            except Exception as exc:
                logger.warning("[Outlook] Device code callback failed: %s", exc)

        # Show authentication prompt in logs / stdout (fallback if no callback)
        msg = (
            f"\n"
            f"  ┌─────────────────────────────────────────────────────┐\n"
            f"  │  📧 Outlook Authentication Required                  │\n"
            f"  │                                                      │\n"
            f"  │  1. Open:  {verification_uri:<41}│\n"
            f"  │  2. Enter: {user_code:<41}│\n"
            f"  │  (expires in {expires_in // 60} minutes)                          │\n"
            f"  └─────────────────────────────────────────────────────┘\n"
        )
        print(msg, flush=True)
        logger.info("[Outlook] Device code auth required — open %s and enter %s", verification_uri, user_code)

        # Poll for token
        token_data: dict[str, str] = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": self.credentials.client_id,
            "device_code": device_code,
        }
        if self.credentials.client_secret:
            token_data["client_secret"] = self.credentials.client_secret

        while time.time() < deadline:
            await asyncio.sleep(interval)
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                transport=self._transport,
            ) as client:
                resp = await client.post(self.credentials.token_url, data=token_data)
                result = resp.json()

            error = result.get("error")
            if error == "authorization_pending":
                continue
            if error == "slow_down":
                interval = min(interval + 5, 30)
                continue
            if error:
                raise MicrosoftGraphTokenError(
                    f"Device code flow failed: {result.get('error_description', error)}"
                )

            # Success
            access_token = result.get("access_token", "").strip()
            refresh_token = result.get("refresh_token", "").strip()
            if not access_token or not refresh_token:
                raise MicrosoftGraphTokenError("Device code flow: missing access_token or refresh_token.")

            expires_in_tok = int(result.get("expires_in", 3600))
            logger.info("[Outlook] Device code auth successful.")
            print("  ✓ Outlook authentication successful.", flush=True)
            return (
                CachedAccessToken(
                    access_token=access_token,
                    token_type=result.get("token_type", "Bearer"),
                    expires_at=time.time() + max(0, expires_in_tok),
                ),
                refresh_token,
            )

        raise MicrosoftGraphTokenError("Device code flow: authentication timed out.")

    async def _refresh_access_token(self, refresh_token: str) -> tuple[CachedAccessToken, str]:
        data: dict[str, str] = {
            "grant_type": "refresh_token",
            "client_id": self.credentials.client_id,
            "refresh_token": refresh_token,
            "scope": self.credentials.scope,
        }
        if self.credentials.client_secret:
            data["client_secret"] = self.credentials.client_secret

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            transport=self._transport,
        ) as client:
            resp = await client.post(self.credentials.token_url, data=data)
            result = resp.json()

        if resp.status_code >= 400 or result.get("error"):
            raise MicrosoftGraphTokenError(
                f"Token refresh failed: {result.get('error_description', result.get('error', 'unknown'))}"
            )

        access_token = result.get("access_token", "").strip()
        new_refresh = result.get("refresh_token", refresh_token).strip()
        expires_in = int(result.get("expires_in", 3600))

        return (
            CachedAccessToken(
                access_token=access_token,
                token_type=result.get("token_type", "Bearer"),
                expires_at=time.time() + max(0, expires_in),
            ),
            new_refresh,
        )

    # ------------------------------------------------------------------
    # Token cache (disk persistence)
    # ------------------------------------------------------------------

    def _load_token_cache(self) -> None:
        # Check for refresh token from environment first (user provided)
        env_refresh = os.getenv("OUTLOOK_REFRESH_TOKEN", "").strip()
        if env_refresh:
            self._refresh_token = env_refresh
            return
        
        try:
            if not self._token_cache_path.exists():
                return
            data = json.loads(self._token_cache_path.read_text(encoding="utf-8"))
            self._refresh_token = data.get("refresh_token") or None
            access_token = data.get("access_token", "")
            expires_at = float(data.get("expires_at", 0))
            token_type = data.get("token_type", "Bearer")
            if access_token and expires_at > time.time() + self.skew_seconds:
                self._cached_token = CachedAccessToken(
                    access_token=access_token,
                    token_type=token_type,
                    expires_at=expires_at,
                )
        except Exception as exc:
            logger.debug("[Outlook] Could not load token cache: %s", exc)

    def _save_token_cache(self) -> None:
        try:
            data: dict[str, Any] = {}
            if self._refresh_token:
                data["refresh_token"] = self._refresh_token
            if self._cached_token:
                data["access_token"] = self._cached_token.access_token
                data["expires_at"] = self._cached_token.expires_at
                data["token_type"] = self._cached_token.token_type
            self._token_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._token_cache_path.write_text(
                json.dumps(data, indent=2), encoding="utf-8"
            )
            # Restrict permissions — contains a refresh token
            try:
                self._token_cache_path.chmod(0o600)
            except Exception:
                pass
        except Exception as exc:
            logger.warning("[Outlook] Could not save token cache: %s", exc)


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        text = response.text.strip()
        return text or "unknown error"

    if isinstance(payload, dict):
        if isinstance(payload.get("error_description"), str):
            return payload["error_description"]
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            code = error.get("code")
            if message and code:
                return f"{code}: {message}"
            if message:
                return str(message)
            if code:
                return str(code)
        if isinstance(error, str):
            return error
    return str(payload)
