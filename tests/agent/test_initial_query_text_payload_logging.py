from agent.conversation_loop import _collect_initial_query_text_segments


def test_collect_initial_query_text_segments_includes_location_type_and_lengths():
    api_messages = [
        {"role": "system", "content": "sys"},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "input_text", "input_text": "from-part"},
            ],
        },
        {
            "role": "assistant",
            "content": "tool step",
            "reasoning_content": "why",
            "tool_calls": [
                {
                    "function": {
                        "name": "search_docs",
                        "arguments": '{"query":"abc"}',
                    }
                }
            ],
        },
    ]

    payload = _collect_initial_query_text_segments(api_messages)

    assert payload["segment_count"] == 7
    assert payload["omitted_segment_count"] == 0
    assert payload["total_chars"] == (
        len("sys")
        + len("hello")
        + len("from-part")
        + len("tool step")
        + len("why")
        + len("search_docs")
        + len('{"query":"abc"}')
    )
    assert payload["segments"][0] == {
        "location": "api_messages[0].content",
        "type": "system_content",
        "chars": 3,
    }
    assert any(
        seg["location"] == "api_messages[1].content[0].text"
        and seg["type"] == "user_text_text"
        and seg["chars"] == len("hello")
        for seg in payload["segments"]
    )
    assert any(
        seg["location"] == "api_messages[2].tool_calls[0].function.arguments"
        and seg["type"] == "assistant_tool_call_arguments"
        and seg["chars"] == len('{"query":"abc"}')
        for seg in payload["segments"]
    )


def test_collect_initial_query_text_segments_applies_truncation_limit():
    api_messages = [{"role": "user", "content": f"msg-{idx}"} for idx in range(5)]

    payload = _collect_initial_query_text_segments(api_messages, max_segments=3)

    assert payload["segment_count"] == 5
    assert payload["reported_segment_count"] == 3
    assert payload["omitted_segment_count"] == 2
    assert len(payload["segments"]) == 3
