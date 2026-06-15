---
sidebar_position: 3
title: "Bootstrap Installer Environment Variables"
description: "Environment variable contract used by bootstrap installer credential threading"
---

# Bootstrap Installer Environment Variables

These variables are passed by the bootstrap installer process to install scripts.

They are install-time transport variables, not long-term user config variables.

## Required variables

| Variable | Meaning | Destination |
|---|---|---|
| `HERMES_BOOTSTRAP_API_KEY` | Primary API key entered in credentials form | Written to `.env` as `OPENAI_API_KEY` |
| `HERMES_BOOTSTRAP_BASE_URL` | OpenAI-compatible provider base URL | `config.yaml` model base_url |
| `HERMES_BOOTSTRAP_MODEL` | Default model name | `config.yaml` model default |

## Optional variables

| Variable | Meaning | Destination |
|---|---|---|
| `HERMES_BOOTSTRAP_MEMORY_API_URL` | Memory server URL | `config.yaml` `mcp_servers.memory.url` |
| `HERMES_BOOTSTRAP_EMAIL` | Email address for email gateway | `.env` as `EMAIL_ADDRESS` |
| `HERMES_BOOTSTRAP_EMAIL_PASSWORD` | Email password/app password | `.env` as `EMAIL_PASSWORD` |
| `HERMES_BOOTSTRAP_IMAP_SERVER` | IMAP host | `.env` as `IMAP_SERVER` |
| `HERMES_BOOTSTRAP_SMTP_SERVER` | SMTP host | `.env` as `SMTP_SERVER` |

## Source and sink

Source side:

- Bootstrap UI form (React)
- Tauri command arguments (Rust)

Sink side:

- `scripts/install.sh`
- `scripts/install.ps1`

## Behavior notes

- If required bootstrap API key is missing/empty, scripts skip bootstrap credential application.
- Optional values are only written when provided.
- Script behavior remains backward-compatible for non-bootstrap installs.

## Security notes

- These transport vars should not be printed in logs.
- Final secrets live in `.env`; handle and share with care.
- Use `hermes doctor` and `hermes config check` for diagnostics rather than printing secret files.

## Related references

- Main env var catalog: [/reference/environment-variables](/reference/environment-variables)
- Bootstrap quickstart: [/getting-started/bootstrap-installer-quickstart](/getting-started/bootstrap-installer-quickstart)
- Bootstrap architecture: [/developer-guide/bootstrap-installer-architecture](/developer-guide/bootstrap-installer-architecture)
