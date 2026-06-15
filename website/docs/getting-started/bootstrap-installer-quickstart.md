---
sidebar_position: 3
title: "Bootstrap Installer Quickstart"
description: "Set up Hermes with the cross-platform bootstrap installer in one guided flow"
---

# Bootstrap Installer Quickstart

The bootstrap installer is the guided install path for Hermes on macOS and Windows. It collects your model credentials in a form, runs the platform installer, and writes a ready-to-use config.

## Who should use this

- You want the fastest path to a working Hermes setup
- You do not want to manually edit config files during install
- You want one installer flow for macOS and Windows

## What it configures

During install, the bootstrap flow can pre-populate:

- Default model name
- Model base URL
- API key (stored in `.env`)
- Optional memory server URL
- Optional email gateway settings (address, password, IMAP, SMTP)

## Before you start

Choose your provider and collect these values:

- API key
- Base URL (OpenAI-compatible endpoint)
- Model name

Optional values:

- Memory API URL
- Email gateway settings

Provider setup links:

- OpenAI: <https://platform.openai.com/api-keys>
- Anthropic: <https://console.anthropic.com/settings/keys>
- OpenRouter: <https://openrouter.ai/keys>
- Nous Portal: <https://portal.nousresearch.com>
- Full provider catalog: [/integrations/providers](/integrations/providers)

## Install flow

1. Launch the Hermes bootstrap installer.
2. Fill the Credentials screen:
   - Required: API Key, Base URL, Model Name
   - Optional: Memory API URL
   - Optional Email section: Email Address, Email Password, IMAP, SMTP
3. Start installation.
4. Wait for stage completion.
5. Open Hermes and verify with a test prompt.

## What gets written

- `~/.hermes/config.yaml` (or profile-specific `HERMES_HOME`)
- `~/.hermes/.env`

Credential mapping:

- `OPENAI_API_KEY` goes to `.env`
- Model default and base URL go to `config.yaml`
- Optional memory server block is added to `config.yaml`
- Optional email values are appended to `.env`

## Verify after install

Run:

```bash
hermes doctor
hermes model
hermes -q "hello"
```

Expected result:

- Provider resolves without missing-key errors
- Model calls succeed
- Session starts normally

## Next steps

- Configure tools: [/user-guide/features/tools](/user-guide/features/tools)
- Configure gateway: [/user-guide/messaging](/user-guide/messaging)
- Reference vars: [/reference/bootstrap-installer-environment-variables](/reference/bootstrap-installer-environment-variables)
- Troubleshoot: [Bootstrap Installer Troubleshooting](./bootstrap-installer-troubleshooting.md)
