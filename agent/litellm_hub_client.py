"""Helpers for LiteLLM public hub endpoints (Skill/Agent/Model Hub)."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_HUB_PATH_ALIASES = {
    "agents": "agent_hub",
    "skills": "skill_hub",
}


def resolve_litellm_hub_settings() -> Dict[str, Any]:
    """Resolve LiteLLM hub settings from config.yaml with env fallback.

    Resolution order for base_url:
    1. skills.litellm_hub.base_url (explicit hub override)
    2. LITELLM_PROXY_URL env var
    3. OPENAI_BASE_URL env var
    4. First provider entry with a base_url (the model provider is usually LiteLLM)
    """
    from hermes_cli.config import load_config

    cfg = load_config() or {}
    skills_cfg = cfg.get("skills", {}) if isinstance(cfg, dict) else {}
    hub_cfg = skills_cfg.get("litellm_hub", {}) if isinstance(skills_cfg, dict) else {}

    base_url = str(
        hub_cfg.get("base_url")
        or os.getenv("LITELLM_PROXY_URL")
        or os.getenv("OPENAI_BASE_URL")
        or _first_provider_base_url(cfg)
        or ""
    ).strip().rstrip("/")
    if base_url.endswith("/v1"):
        base_url = base_url[:-3]
    api_key = str(
        hub_cfg.get("api_key")
        or os.getenv("LITELLM_KEY")
        or os.getenv("OPENAI_API_KEY")
        or _first_provider_api_key(cfg)
        or ""
    ).strip()
    timeout_raw = hub_cfg.get("timeout", 20)
    try:
        timeout = max(1, int(timeout_raw))
    except (TypeError, ValueError):
        timeout = 20

    return {
        "base_url": base_url,
        "api_key": api_key,
        "timeout": timeout,
    }


def _first_provider_base_url(cfg: Dict[str, Any]) -> str:
    """Return the base_url of the first configured provider entry, if any."""
    providers = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    if not isinstance(providers, dict):
        return ""
    for entry in providers.values():
        if not isinstance(entry, dict):
            continue
        for key in ("base_url", "url", "api"):
            val = entry.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().rstrip("/")
    return ""


def _first_provider_api_key(cfg: Dict[str, Any]) -> str:
    """Return the api_key of the first configured provider entry, if any."""
    providers = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    if not isinstance(providers, dict):
        return ""
    for entry in providers.values():
        if not isinstance(entry, dict):
            continue
        val = entry.get("api_key")
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


def fetch_litellm_hub_json(
    public_path: str,
    *,
    require_auth: bool,
    settings: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[Any], Optional[str]]:
    """Fetch JSON from ``/public/<public_path>`` on a LiteLLM proxy."""
    settings = settings or resolve_litellm_hub_settings()
    base_url = str(settings.get("base_url", "")).strip().rstrip("/")
    api_key = str(settings.get("api_key", "")).strip()
    timeout = settings.get("timeout", 20)

    if not base_url:
        logger.warning("[LiteLLMHub] base_url is not configured")
        return None, (
            "LiteLLM hub is not configured. "
            "Set skills.litellm_hub.base_url in config.yaml."
        )
    if require_auth and not api_key:
        logger.warning("[LiteLLMHub] api_key is required but not configured")
        return None, (
            "This LiteLLM hub endpoint requires authentication. "
            "Set skills.litellm_hub.api_key (or LITELLM_KEY)."
        )

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    public_endpoint = _HUB_PATH_ALIASES.get(public_path.strip("/"), public_path.strip("/"))
    # Strip trailing /litellm if present to avoid double path segment
    hub_base = base_url.rstrip("/")
    if hub_base.endswith("/litellm"):
        url = f"{hub_base}/public/{public_endpoint}"
    else:
        url = f"{hub_base}/litellm/public/{public_endpoint}"
    logger.info("[LiteLLMHub] Fetching %s (auth=%s)", url, bool(api_key))
    try:
        resp = httpx.get(
            url,
            headers=headers or None,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.HTTPError as exc:
        logger.error("[LiteLLMHub] Request failed for %s: %s", url, exc)
        return None, f"Failed to reach LiteLLM hub at {url}: {exc}"

    logger.info("[LiteLLMHub] Response from %s: HTTP %s", url, resp.status_code)
    if resp.status_code == 401:
        return None, f"LiteLLM hub request failed: unauthorized (401) at {url}. Check API key."
    if resp.status_code == 403:
        return None, f"LiteLLM hub request failed: forbidden (403) at {url}. Check API key scope."
    if resp.status_code != 200:
        return None, f"LiteLLM hub request failed: HTTP {resp.status_code} from {url}."

    try:
        data = resp.json()
        logger.info("[LiteLLMHub] Successfully parsed JSON from %s", url)
        return data, None
    except ValueError:
        logger.error("[LiteLLMHub] Non-JSON response from %s: %.200s", url, resp.text)
        return None, f"LiteLLM hub returned non-JSON response from {url}."


def fetch_litellm_agents(
    settings: Optional[Dict[str, Any]] = None,
) -> Tuple[Optional[list], Optional[str]]:
    """Fetch agents from the LiteLLM ``/v1/agents`` endpoint.

    Returns (agents_list, error_message).  The agents list items contain at
    minimum ``agent_id`` / ``agent_name`` fields as returned by LiteLLM.
    """
    settings = settings or resolve_litellm_hub_settings()
    base_url = str(settings.get("base_url", "")).strip().rstrip("/")
    api_key = str(settings.get("api_key", "")).strip()
    timeout = settings.get("timeout", 20)

    if not base_url:
        return None, (
            "LiteLLM base_url is not configured. "
            "Set skills.litellm_hub.base_url in config.yaml."
        )

    # Normalise: strip /litellm suffix (handled below), strip /v1 suffix
    hub_base = base_url.rstrip("/")
    if hub_base.endswith("/v1"):
        hub_base = hub_base[:-3]
    if hub_base.endswith("/litellm"):
        url = f"{hub_base}/v1/agents"
    else:
        url = f"{hub_base}/litellm/v1/agents"

    headers: Dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info("[LiteLLMHub] Fetching agents from %s", url)
    try:
        resp = httpx.get(url, headers=headers or None, timeout=timeout, follow_redirects=True)
    except httpx.HTTPError as exc:
        logger.error("[LiteLLMHub] Agents request failed for %s: %s", url, exc)
        return None, f"Failed to reach LiteLLM agents endpoint at {url}: {exc}"

    if resp.status_code == 401:
        return None, f"Unauthorized (401) at {url}. Check API key."
    if resp.status_code == 403:
        return None, f"Forbidden (403) at {url}. Check API key scope."
    if resp.status_code != 200:
        return None, f"LiteLLM agents request failed: HTTP {resp.status_code} from {url}."

    try:
        data = resp.json()
    except ValueError:
        return None, f"LiteLLM agents endpoint returned non-JSON from {url}."

    # LiteLLM may return {"data": [...]} (OpenAI list format) or a plain list
    if isinstance(data, list):
        agents = data
    elif isinstance(data, dict):
        agents = data.get("data") or data.get("agents") or []
    else:
        agents = []

    return agents, None


def get_active_agents() -> list[str]:
    """Return the list of agent names the user has activated via the Hub UI."""
    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        hub_cfg = cfg.get("skills", {}).get("litellm_hub", {})
        active = hub_cfg.get("active_agents", [])
        return [str(a) for a in active if a]
    except Exception:
        return []


def set_active_agents(agent_names: list[str]) -> None:
    """Persist the list of active agent names to config.yaml."""
    from hermes_cli.config import load_config, save_config
    cfg = load_config() or {}
    skills = cfg.setdefault("skills", {})
    hub = skills.setdefault("litellm_hub", {})
    hub["active_agents"] = sorted(set(agent_names))
    save_config(cfg)

