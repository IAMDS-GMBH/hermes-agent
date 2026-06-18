import argparse
from argparse import Namespace
from unittest.mock import patch

from hermes_cli.litellm_hub import litellm_hub_command
from hermes_cli.subcommands.litellm_hub import build_litellm_hub_parser


def test_litellm_hub_agents_json(capsys):
    with patch(
        "hermes_cli.litellm_hub.fetch_litellm_hub_json",
        return_value=([{"name": "hello-world-agent", "description": "demo"}], None),
    ):
        code = litellm_hub_command(
            Namespace(litellm_hub_action="agents", json=True, limit=10)
        )

    out = capsys.readouterr().out
    assert code == 0
    assert "hello-world-agent" in out


def test_litellm_hub_skills_text(capsys):
    with patch(
        "hermes_cli.litellm_hub.fetch_litellm_hub_json",
        return_value=(
            [{"name": "grill-me", "description": "Interview skill", "domain": "Productivity"}],
            None,
        ),
    ):
        code = litellm_hub_command(
            Namespace(litellm_hub_action="skills", json=False, limit=10)
        )

    out = capsys.readouterr().out
    assert code == 0
    assert "grill-me" in out
    assert "LiteLLM Skill Hub" in out


def test_litellm_hub_reports_fetch_errors(capsys):
    with patch(
        "hermes_cli.litellm_hub.fetch_litellm_hub_json",
        return_value=(None, "failed"),
    ):
        code = litellm_hub_command(
            Namespace(litellm_hub_action="models", json=False, limit=10)
        )

    out = capsys.readouterr().out
    assert code == 1
    assert "Error: failed" in out


def test_litellm_hub_parser_builds_subcommands():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    build_litellm_hub_parser(subparsers, cmd_litellm_hub=lambda args: 0)

    args = parser.parse_args(["litellm-hub", "skills", "--json", "--limit", "5"])
    assert args.command == "litellm-hub"
    assert args.litellm_hub_action == "skills"
    assert args.json is True
    assert args.limit == 5

