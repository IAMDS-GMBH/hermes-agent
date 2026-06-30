---
name: auto-load-memory-context
description: "This skill ensures that memory_context is loaded automatically at the start of each session."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, context, session-start, workflow]
---

# Auto Load Memory Context Skill

This skill ensures that `memory_context` is loaded automatically at the start of each session.

## Actions

- **load_memory_context**: This action will be called at the beginning of each session to load the memory context.

## Usage

To use this skill, simply include it in your Hermes configuration and ensure it is enabled.

## Example

```yaml
skills:
  - name: auto-load-memory-context
    actions:
      - load_memory_context
```
