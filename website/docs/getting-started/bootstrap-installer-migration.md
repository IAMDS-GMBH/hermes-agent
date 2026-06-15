---
sidebar_position: 5
title: "Migrating from Legacy Installers"
description: "Move from standalone shell/PowerShell installer flows to the unified bootstrap installer"
---

# Migrating from Legacy Installers

Hermes now uses a unified bootstrap installer flow for credential collection and setup. This page explains how to migrate from older standalone workflows safely.

## What changed

Legacy install paths used separate script-first flows:

- macOS/Linux: `install.sh`
- Windows: `install.ps1`

The bootstrap installer now orchestrates both and passes credentials via environment variables during install.

## What remains compatible

- Existing script installs still work
- Interactive mode remains available when no bootstrap env vars are set
- Existing `~/.hermes` config/env files are respected

## Safe migration steps

1. Back up current config:

```bash
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak
cp ~/.hermes/.env ~/.hermes/.env.bak
```

2. Run bootstrap installer.
3. Enter credentials in the form.
4. Complete install.
5. Validate:

```bash
hermes doctor
hermes -q "migration check"
```

## Merge behavior

During bootstrap-backed install:

- `.env` is appended (not fully overwritten)
- `config.yaml` model fields are updated from form input
- Optional memory block is added when memory URL exists

## When to re-run bootstrap

Re-run when you need to:

- Switch provider endpoint and model together
- Re-seed clean credentials on a new machine
- Add memory/email settings during install flow

## Rollback plan

If something looks wrong after migration:

1. Restore backups:

```bash
mv ~/.hermes/config.yaml.bak ~/.hermes/config.yaml
mv ~/.hermes/.env.bak ~/.hermes/.env
```

2. Run:

```bash
hermes doctor
```

3. Re-run bootstrap only after confirming backup restore works.

## Related docs

- Quickstart: [Bootstrap Installer Quickstart](./bootstrap-installer-quickstart.md)
- Troubleshooting: [Bootstrap Installer Troubleshooting](./bootstrap-installer-troubleshooting.md)
- Architecture: [/developer-guide/bootstrap-installer-architecture](/developer-guide/bootstrap-installer-architecture)
