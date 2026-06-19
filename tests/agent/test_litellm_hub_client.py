from unittest.mock import MagicMock, patch

from agent.litellm_hub_client import fetch_litellm_hub_json


def _mock_response(payload):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


def test_fetch_litellm_hub_aliases_legacy_paths_and_strips_v1_suffix():
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        return _mock_response([{"id": "agent-1"}])

    settings = {
        "base_url": "http://localhost:4000/litellm/v1",
        "api_key": "",
        "timeout": 20,
    }

    with patch("httpx.get", side_effect=fake_get):
        payload, error = fetch_litellm_hub_json("agents", require_auth=False, settings=settings)

    assert error is None
    assert payload == [{"id": "agent-1"}]
    assert captured["url"] == "http://localhost:4000/litellm/public/agent_hub"


def test_fetch_litellm_hub_uses_skill_hub_path_directly():
    captured = {}

    def fake_get(url, **kwargs):
        captured["url"] = url
        return _mock_response([{"id": "skill-1"}])

    settings = {
        "base_url": "http://localhost:4000/litellm",
        "api_key": "",
        "timeout": 20,
    }

    with patch("httpx.get", side_effect=fake_get):
        payload, error = fetch_litellm_hub_json("skill_hub", require_auth=False, settings=settings)

    assert error is None
    assert payload == [{"id": "skill-1"}]
    assert captured["url"] == "http://localhost:4000/litellm/public/skill_hub"
