"""CLI handlers for ``hermes litellm-hub``."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from agent.litellm_hub_client import fetch_litellm_hub_json, resolve_litellm_hub_settings


def _iter_items(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "skills", "agents", "models", "groups"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _limit(items: Iterable[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return list(items)
    out: List[Dict[str, Any]] = []
    for item in items:
        out.append(item)
        if len(out) >= limit:
            break
    return out


def _print_json(data: Any) -> int:
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def _print_skills(items: List[Dict[str, Any]]) -> int:
    if not items:
        print("No LiteLLM Skill Hub entries found.")
        return 0
    print("LiteLLM Skill Hub")
    for item in items:
        name = str(item.get("name", "")).strip() or "<unnamed>"
        desc = str(item.get("description", "")).strip()
        domain = str(item.get("domain", "")).strip()
        namespace = str(item.get("namespace", "")).strip()
        extra = " · ".join([part for part in (domain, namespace) if part])
        if extra:
            print(f"- {name} ({extra})")
        else:
            print(f"- {name}")
        if desc:
            print(f"  {desc}")
    return 0


def _print_agents(items: List[Dict[str, Any]]) -> int:
    if not items:
        print("No LiteLLM Agent Hub entries found.")
        return 0
    print("LiteLLM Agent Hub")
    for item in items:
        name = str(item.get("name") or item.get("agent_name") or item.get("id") or "<unnamed>").strip()
        description = str(item.get("description", "")).strip()
        url = str(item.get("url", "")).strip()
        version = str(item.get("version", "")).strip()
        tail = " · ".join([part for part in (version, url) if part])
        print(f"- {name}" + (f" ({tail})" if tail else ""))
        if description:
            print(f"  {description}")
    return 0


def _print_models(items: List[Dict[str, Any]]) -> int:
    if not items:
        print("No LiteLLM Model Hub entries found.")
        return 0
    print("LiteLLM Model Hub")
    for item in items:
        group_name = str(item.get("name") or item.get("group_name") or item.get("group") or "<group>").strip()
        models = item.get("models")
        if isinstance(models, list):
            print(f"- {group_name}: {len(models)} model(s)")
        else:
            print(f"- {group_name}")
    return 0


def litellm_hub_command(args: Any) -> int:
    action = getattr(args, "litellm_hub_action", None) or "agents"
    as_json = bool(getattr(args, "json", False))
    limit = int(getattr(args, "limit", 50) or 50)

    if action == "settings":
        return _print_json(resolve_litellm_hub_settings())

    if action == "skills":
        payload, err = fetch_litellm_hub_json("skill_hub", require_auth=False)
        if err:
            print(f"Error: {err}")
            return 1
        items = _limit(_iter_items(payload), limit)
        return _print_json(items if as_json else {"items": items}) if as_json else _print_skills(items)

    if action == "models":
        payload, err = fetch_litellm_hub_json("model_hub", require_auth=True)
        if err:
            print(f"Error: {err}")
            return 1
        items = _limit(_iter_items(payload), limit)
        return _print_json(items if as_json else {"items": items}) if as_json else _print_models(items)

    if action == "models-info":
        payload, err = fetch_litellm_hub_json("model_hub/info", require_auth=True)
        if err:
            print(f"Error: {err}")
            return 1
        return _print_json(payload)

    # Default: agents
    payload, err = fetch_litellm_hub_json("agent_hub", require_auth=True)
    if err:
        print(f"Error: {err}")
        return 1
    items = _limit(_iter_items(payload), limit)
    return _print_json(items if as_json else {"items": items}) if as_json else _print_agents(items)

