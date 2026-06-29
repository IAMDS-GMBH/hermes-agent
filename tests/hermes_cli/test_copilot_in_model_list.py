"""Tests for GitHub Copilot entries shown in the /model picker."""

import os
from unittest.mock import patch

from hermes_cli.model_switch import list_authenticated_providers


@patch.dict(os.environ, {"GH_TOKEN": "test-key"}, clear=False)
def test_copilot_picker_uses_live_catalog_when_available():
    live_models = ["gpt-5.4", "claude-sonnet-4.6", "gemini-3.1-pro-preview"]

    with patch("agent.models_dev.fetch_models_dev", return_value={}), \
         patch("hermes_cli.models._resolve_copilot_catalog_api_key", return_value="gh-token"), \
         patch("hermes_cli.models._fetch_github_models", return_value=live_models):
        providers = list_authenticated_providers(current_provider="openrouter", max_models=50)

    copilot = next((p for p in providers if p["slug"] == "copilot"), None)

    assert copilot is not None
    assert copilot["models"] == live_models
    assert copilot["total_models"] == len(live_models)


@patch.dict(os.environ, {"GH_TOKEN": "test-key"}, clear=False)
def test_copilot_picker_hidden_for_bootstrap_litellm_mode():
    fake_models_dev = {
        "openai": {"env": ["OPENAI_API_KEY"]},
        "github-copilot": {"env": ["GH_TOKEN"]},
    }
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "GH_TOKEN": "gh-test"}, clear=False), \
         patch("agent.models_dev.fetch_models_dev", return_value=fake_models_dev), \
         patch(
             "hermes_cli.models.cached_provider_model_ids",
             side_effect=lambda provider, **_kwargs: (
                 ["litellm/model-a"] if provider == "openai-api" else ["gpt-5.4"]
             ),
         ):
        providers = list_authenticated_providers(
            current_provider="openai-api",
            current_base_url="https://staging.suite.iamds.com/litellm/v1",
            max_models=50,
        )

    assert any(p.get("slug") == "openai-api" for p in providers)
    assert all(p.get("slug") != "copilot" for p in providers)


@patch.dict(os.environ, {"GH_TOKEN": "test-key"}, clear=False)
def test_copilot_picker_hidden_for_bootstrap_litellm_mode_from_env_base_url():
    fake_models_dev = {
        "openai": {"env": ["OPENAI_API_KEY"]},
        "github-copilot": {"env": ["GH_TOKEN"]},
    }
    with patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": "sk-test",
            "OPENAI_BASE_URL": "https://staging.suite.iamds.com/litellm/v1",
            "GH_TOKEN": "gh-test",
        },
        clear=False,
    ), patch("agent.models_dev.fetch_models_dev", return_value=fake_models_dev), patch(
        "hermes_cli.models.cached_provider_model_ids",
        side_effect=lambda provider, **_kwargs: (
            ["litellm/model-a"] if provider == "openai-api" else ["gpt-5.4"]
        ),
    ):
        providers = list_authenticated_providers(
            current_provider="openai-api",
            current_base_url="",
            max_models=50,
        )

    assert any(p.get("slug") == "openai-api" for p in providers)
    assert all(p.get("slug") != "copilot" for p in providers)
