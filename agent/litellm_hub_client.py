"""Helpers for LiteLLM public hub endpoints (Skill/Agent/Model Hub)."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import httpx

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
        return None, (
            "LiteLLM hub is not configured. "
            "Set skills.litellm_hub.base_url in config.yaml."
        )
    if require_auth and not api_key:
        return None, (
            "This LiteLLM hub endpoint requires authentication. "
            "Set skills.litellm_hub.api_key (or LITELLM_KEY)."
        )

    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    public_endpoint = _HUB_PATH_ALIASES.get(public_path.strip("/"), public_path.strip("/"))
    url = f"{base_url}/public/{public_endpoint}"
    try:
        resp = httpx.get(
            url,
            headers=headers or None,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.HTTPError as exc:
        return None, f"Failed to reach LiteLLM hub at {url}: {exc}"

    if resp.status_code == 401:
        return None, "LiteLLM hub request failed: unauthorized (401). Check API key."
    if resp.status_code == 403:
        return None, "LiteLLM hub request failed: forbidden (403). Check API key scope."
    if resp.status_code != 200:
        return None, f"LiteLLM hub request failed: HTTP {resp.status_code} from {url}."

    try:
        return resp.json(), None
    except ValueError:
        return None, f"LiteLLM hub returned non-JSON response from {url}."
