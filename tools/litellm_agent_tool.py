"""LiteLLM A2A (Agent-to-Agent) tool.

Calls external agents registered on a LiteLLM proxy via the A2A protocol
(``POST <base_url>/a2a/<agent_name>``).  Only agents activated by the user
in the Hub UI are exposed — the tool description lists them dynamically so
the model knows which agents are available without extra discovery calls.

Configuration:
    skills:
      litellm_hub:
        base_url: "https://your-litellm-proxy"
        api_key: "sk-..."
        active_agents:
          - researcher
          - coder

Gated on: LiteLLM base_url configured + at least one active agent.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from tools.registry import registry

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _check_litellm_agent_requirements() -> bool:
    """Gate: LiteLLM base_url set AND at least one active agent."""
    try:
        from agent.litellm_hub_client import get_active_agents, resolve_litellm_hub_settings
        settings = resolve_litellm_hub_settings()
        if not settings.get("base_url"):
            return False
        return len(get_active_agents()) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Schema builder — injects active agent names into description dynamically
# ---------------------------------------------------------------------------

def _build_schema() -> dict[str, Any]:
    try:
        from agent.litellm_hub_client import get_active_agents
        active = get_active_agents()
    except Exception:
        active = []

    agent_list = ", ".join(f"`{a}`" for a in active) if active else "(none activated)"
    return {
        "name": "call_litellm_agent",
        "description": (
            "Call an external AI agent registered on the LiteLLM proxy via the A2A protocol. "
            f"Currently active agents: {agent_list}. "
            "Use this to delegate specialised tasks to remote agents — e.g. a researcher, "
            "a coder, or a domain-specific assistant. Returns the agent's final response."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": (
                        f"Name of the agent to call. Active agents: {agent_list}."
                    ),
                },
                "message": {
                    "type": "string",
                    "description": "The task or question to send to the agent.",
                },
                "context": {
                    "type": "string",
                    "description": "Optional additional context to prepend to the message.",
                    "default": "",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Max seconds to wait for the agent response. Default 120.",
                    "default": 120,
                },
            },
            "required": ["agent_name", "message"],
        },
    }


# ---------------------------------------------------------------------------
# A2A HTTP call
# ---------------------------------------------------------------------------

def _a2a_url(base_url: str, agent_name: str) -> str:
    hub = base_url.rstrip("/")
    if hub.endswith("/litellm"):
        return f"{hub}/a2a/{agent_name}"
    return f"{hub}/litellm/a2a/{agent_name}"


def call_litellm_agent(
    agent_name: str,
    message: str,
    context: str = "",
    timeout: int = 120,
    task_id: str | None = None,
) -> str:
    """Call a LiteLLM-registered agent via A2A and return its response."""
    import httpx

    try:
        from agent.litellm_hub_client import get_active_agents, resolve_litellm_hub_settings
    except ImportError as exc:
        return json.dumps({"error": f"litellm_hub_client not available: {exc}"})

    agent_name = agent_name.strip()
    if not agent_name:
        return json.dumps({"error": "agent_name is required"})

    # Guard: only allow activated agents
    active = get_active_agents()
    if agent_name not in active:
        return json.dumps({
            "error": f"Agent '{agent_name}' is not activated. "
                     f"Active agents: {active}. "
                     "Activate it in the Hub UI first."
        })

    settings = resolve_litellm_hub_settings()
    base_url = settings.get("base_url", "").strip()
    if not base_url:
        return json.dumps({"error": "LiteLLM base_url not configured."})

    api_key = settings.get("api_key", "").strip()
    url = _a2a_url(base_url, agent_name)

    full_message = f"{context.strip()}\n\n{message}".strip() if context.strip() else message

    # A2A uses the OpenAI chat-completions-style request body
    payload = {
        "messages": [{"role": "user", "content": full_message}],
        "stream": False,
    }
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.info("[A2A] Calling agent '%s' at %s", agent_name, url)
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=float(timeout))
    except httpx.TimeoutException:
        return json.dumps({"error": f"Agent '{agent_name}' timed out after {timeout}s."})
    except httpx.HTTPError as exc:
        return json.dumps({"error": f"A2A request failed: {exc}"})

    if resp.status_code == 404:
        return json.dumps({"error": f"Agent '{agent_name}' not found at {url} (404)."})
    if resp.status_code == 401:
        return json.dumps({"error": f"Unauthorized (401) calling agent '{agent_name}'. Check API key."})
    if resp.status_code != 200:
        return json.dumps({"error": f"Agent '{agent_name}' returned HTTP {resp.status_code}: {resp.text[:300]}"})

    try:
        data = resp.json()
    except ValueError:
        return json.dumps({"error": "Agent returned non-JSON response.", "raw": resp.text[:500]})

    # Extract content from OpenAI-style response
    try:
        content = (
            data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
        )
        if not content:
            # Fallback: some A2A impls return {response: ...} or {output: ...}
            content = data.get("response") or data.get("output") or data.get("content") or ""
    except (IndexError, AttributeError, TypeError):
        content = str(data)

    logger.info("[A2A] Agent '%s' responded (%d chars)", agent_name, len(content))
    return json.dumps({
        "agent": agent_name,
        "response": content,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="call_litellm_agent",
    toolset="litellm_agents",
    schema=_build_schema(),
    handler=lambda args, **kw: call_litellm_agent(
        agent_name=str(args.get("agent_name", "")),
        message=str(args.get("message", "")),
        context=str(args.get("context", "")),
        timeout=int(args.get("timeout", 120)),
        task_id=kw.get("task_id"),
    ),
    check_fn=_check_litellm_agent_requirements,
)
