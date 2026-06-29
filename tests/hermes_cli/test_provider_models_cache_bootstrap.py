import json

from hermes_cli import models as models_mod


def test_load_provider_models_cache_accepts_nested_bootstrap_shape(tmp_path, monkeypatch):
    cache_path = tmp_path / "provider_models_cache.json"
    cache_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openai-api": {
                        "fp": "pinned",
                        "at": 9_999_999_999.0,
                        "models": ["litellm/model-a", "litellm/model-b"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(models_mod, "_provider_models_cache_path", lambda: cache_path)

    loaded = models_mod._load_provider_models_cache()

    assert "openai-api" in loaded
    assert loaded["openai-api"]["models"] == ["litellm/model-a", "litellm/model-b"]


def test_cached_provider_model_ids_honors_pinned_entries(monkeypatch):
    monkeypatch.setattr(
        models_mod,
        "_load_provider_models_cache",
        lambda: {"openai-api": {"fp": "pinned", "at": 0.0, "models": ["litellm/model-a"]}},
    )
    monkeypatch.setattr(models_mod, "_credential_fingerprint", lambda _provider: "different-fp")
    monkeypatch.setattr(
        models_mod,
        "provider_model_ids",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("live fetch must not run")),
    )

    assert models_mod.cached_provider_model_ids("openai-api") == ["litellm/model-a"]
