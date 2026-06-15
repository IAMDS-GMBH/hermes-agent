---
sidebar_position: 12
title: "Bootstrap Installer Architecture"
description: "Technical design of the cross-platform bootstrap installer and credential threading"
---

# Bootstrap Installer Architecture

This document describes the bootstrap installer internals used to unify macOS and Windows installation flows.

## Goals

- One guided UX for credentials collection
- Cross-platform script execution (`install.sh` / `install.ps1`)
- Backward-compatible script behavior without bootstrap input
- Safe credential handling from UI to local config files

## High-level flow

```text
React credentials form
  -> Tauri command (start_bootstrap)
  -> Rust args struct (StartBootstrapArgs + CredentialsData)
  -> subprocess env vars (HERMES_BOOTSTRAP_*)
  -> platform install script (install.sh/install.ps1)
  -> config.yaml + .env updates
```

## Components

### Frontend (React)

- Route sequence: welcome -> credentials -> progress -> success/failure
- Credentials form validates required fields before install starts
- Credentials payload is stored in state and passed into bootstrap start command

Primary files:

- `apps/bootstrap-installer/src/routes/credentials.tsx`
- `apps/bootstrap-installer/src/store.ts`
- `apps/bootstrap-installer/src/app.tsx`

### Backend (Tauri/Rust)

- `CredentialsData` carries bootstrap credential payload
- `StartBootstrapArgs` includes optional credentials block
- Script runner maps credential fields into subprocess env vars

Primary files:

- `apps/bootstrap-installer/src-tauri/src/bootstrap.rs`
- `apps/bootstrap-installer/src-tauri/src/powershell.rs`

### Install scripts

- `scripts/install.sh` uses `apply_bootstrap_credentials()`
- `scripts/install.ps1` uses `Apply-BootstrapCredentials`
- Both scripts no-op if required bootstrap values are absent

## Credential transport contract

Required keys:

- `HERMES_BOOTSTRAP_API_KEY`
- `HERMES_BOOTSTRAP_BASE_URL`
- `HERMES_BOOTSTRAP_MODEL`

Optional keys:

- `HERMES_BOOTSTRAP_MEMORY_API_URL`
- `HERMES_BOOTSTRAP_EMAIL`
- `HERMES_BOOTSTRAP_EMAIL_PASSWORD`
- `HERMES_BOOTSTRAP_IMAP_SERVER`
- `HERMES_BOOTSTRAP_SMTP_SERVER`

Reference:

- [/reference/bootstrap-installer-environment-variables](/reference/bootstrap-installer-environment-variables)

## Config write behavior

### config.yaml

- Updates model default and base URL
- Appends `mcp_servers` memory block when memory URL is provided

### .env

- Writes/updates `OPENAI_API_KEY`
- Appends optional email gateway variables
- Applies restricted permissions in script flow (`chmod 600` on supported platforms)

## Security and hardening expectations

- No plaintext secret logging to console output
- Secrets written to `.env`, not printed
- URL and replacement escaping in shell/PowerShell substitutions
- PowerShell replacement path avoids injection-prone patterns
- Execution remains idempotent under repeat runs

## Backward compatibility

If bootstrap env vars are not present, scripts return early and continue with standard interactive/default install behavior.

This preserves compatibility for existing non-bootstrap install paths.

## Validation coverage

Implemented tests cover:

- End-to-end credentials threading
- Script substitution behavior
- Security checks and edge cases
- YAML structure validity
- Backward compatibility guard behavior

See test suites:

- `tests/test_bootstrap_credentials_e2e.py`
- `tests/test_bootstrap_phase5_hardening.py`
