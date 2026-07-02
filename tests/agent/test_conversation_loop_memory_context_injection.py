from types import SimpleNamespace

from agent.conversation_loop import (
    _inject_first_turn_memory_context_call,
    _resolve_runtime_memory_context_tool_name,
)


def test_resolve_runtime_memory_context_prefers_prefixed_name():
    name = _resolve_runtime_memory_context_tool_name(
        {"read_file", "mcp_remoteMCP_mcp_memory_memory_context"}
    )
    assert name == "mcp_remoteMCP_mcp_memory_memory_context"


def test_injects_memory_context_on_first_turn():
    calls = []

    def _invoke_tool(name, args, task_id, **kwargs):
        calls.append((name, args, task_id, kwargs))
        return '{"ok":true}'

    agent = SimpleNamespace(
        valid_tool_names=["mcp_remoteMCP_mcp_memory_memory_context"],
        _invoke_tool=_invoke_tool,
    )
    messages = [{"role": "user", "content": "Hello"}]

    injected = _inject_first_turn_memory_context_call(
        agent,
        messages,
        current_turn_user_idx=0,
        effective_task_id="task-1",
    )

    assert injected is True
    assert len(calls) == 1
    assert len(messages) == 3
    assert messages[1]["role"] == "assistant"
    assert messages[2]["role"] == "tool"
    assert messages[2]["name"] == "mcp_remoteMCP_mcp_memory_memory_context"


def test_does_not_inject_on_non_first_turn():
    agent = SimpleNamespace(
        valid_tool_names=["mcp_remoteMCP_mcp_memory_memory_context"],
        _invoke_tool=lambda *_args, **_kwargs: '{"ok":true}',
    )
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old reply"},
        {"role": "user", "content": "new"},
    ]

    injected = _inject_first_turn_memory_context_call(
        agent,
        messages,
        current_turn_user_idx=2,
        effective_task_id="task-1",
    )

    assert injected is False
    assert len(messages) == 3
