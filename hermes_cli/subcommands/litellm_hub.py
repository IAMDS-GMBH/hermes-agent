"""``hermes litellm-hub`` subcommand parser."""

from __future__ import annotations

from typing import Callable


def build_litellm_hub_parser(subparsers, *, cmd_litellm_hub: Callable) -> None:
    """Attach the ``litellm-hub`` subcommand to ``subparsers``."""
    parser = subparsers.add_parser(
        "litellm-hub",
        help="Discover LiteLLM Agent/Model/Skill Hub entries",
        description=(
            "Query LiteLLM public hub endpoints exposed by your proxy. "
            "Configure skills.litellm_hub.base_url in config.yaml first."
        ),
    )
    subs = parser.add_subparsers(dest="litellm_hub_action")

    agents = subs.add_parser("agents", help="List agents from /litellm/v1/agents")
    agents.add_argument("--limit", type=int, default=50, help="Maximum entries to print")
    agents.add_argument("--json", action="store_true", help="Output JSON")

    models = subs.add_parser("models", help="List public model groups from /public/model_hub")
    models.add_argument("--limit", type=int, default=50, help="Maximum entries to print")
    models.add_argument("--json", action="store_true", help="Output JSON")

    subs.add_parser(
        "models-info",
        help="Show metadata from /public/model_hub/info",
    ).add_argument("--json", action="store_true", help="Output JSON")

    skills = subs.add_parser("skills", help="List public skills from /public/skill_hub")
    skills.add_argument("--limit", type=int, default=50, help="Maximum entries to print")
    skills.add_argument("--json", action="store_true", help="Output JSON")

    subs.add_parser(
        "settings",
        help="Show resolved LiteLLM hub settings (base URL, timeout, auth configured)",
    )

    parser.set_defaults(func=cmd_litellm_hub)
