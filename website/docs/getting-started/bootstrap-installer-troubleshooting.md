---
sidebar_position: 4
title: "Bootstrap Installer Troubleshooting"
description: "Fix common bootstrap installer issues on macOS and Windows"
---

# Bootstrap Installer Troubleshooting

This page covers the most common bootstrap installer issues and how to fix them quickly.

## 1) Installer fails before setup starts

### Symptoms

- Bootstrap UI closes early
- Installation never reaches dependency/setup stages

### Checks

- Confirm internet access
- Confirm disk space is available
- Retry install with a clean terminal session

### Fix

- Re-run installer
- If the issue persists, run CLI install fallback:

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

or on Windows:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

## 2) Missing API key or provider errors after successful install

### Symptoms

- `hermes doctor` reports missing key
- First chat fails with authentication errors

### Checks

- Open `~/.hermes/.env`
- Verify `OPENAI_API_KEY` is present and non-empty

### Fix

- Set key with CLI:

```bash
hermes config set OPENAI_API_KEY <your_key>
```

- Re-check provider config:

```bash
hermes model
```

## 3) Model not found or invalid endpoint

### Symptoms

- 404 or model-not-found errors
- connection failures to base URL

### Checks

- Confirm model name exists for your provider
- Confirm base URL is OpenAI-compatible
- Confirm no trailing whitespace in credentials form fields

### Fix

```bash
hermes model
```

Then update model/base URL and retry.

## 4) Memory server block not applied

### Symptoms

- Memory endpoint expected but not present in config

### Checks

- Verify Memory API URL was entered in bootstrap form
- Open `~/.hermes/config.yaml` and inspect `mcp_servers`

### Fix

- Add/repair manually in `config.yaml`
- Or re-run bootstrap with Memory API URL set

## 5) Email gateway values missing

### Symptoms

- Email platform not authenticating
- Missing `EMAIL_*` values in `.env`

### Checks

- Confirm Email section was enabled in bootstrap form
- Confirm all 4 fields were filled when enabled

### Fix

- Set values directly:

```bash
hermes config set EMAIL_ADDRESS <email>
hermes config set EMAIL_PASSWORD <password>
hermes config set IMAP_SERVER <imap_host>
hermes config set SMTP_SERVER <smtp_host>
```

## 6) `hermes` command not found after install

### Fix

Reload shell profile and verify path:

```bash
source ~/.bashrc
# or
source ~/.zshrc
which hermes
```

If still missing, use the installation guide:

- [/getting-started/installation](/getting-started/installation)

## 7) Windows-specific issues

### Common fixes

- Re-open PowerShell as normal user (not stale elevated shell)
- Re-run installer and allow completion of bundled Git Bash step
- Verify Hermes doctor output:

```powershell
hermes doctor
```

More details:

- [/user-guide/windows-native](/user-guide/windows-native)

## Diagnostics checklist

Run these commands and keep output for bug reports:

```bash
hermes doctor
hermes config check
hermes model
```

Include:

- OS and version
- Installer platform and version
- Whether this is first install or migration
- Relevant output snippets (without secrets)

## Security note

Do not share full `.env` contents in issue reports.

- Redact API keys and passwords
- Redact bearer tokens
