"""Tests for tools/outlook_tool.py."""

from __future__ import annotations

import json

from tools import outlook_tool


def test_outlook_read_calendar_entries_requires_credentials(monkeypatch):
    monkeypatch.setattr(
        outlook_tool,
        "_get_outlook_creds",
        lambda: {"tenant_id": "", "client_id": "", "client_secret": ""},
    )

    payload = json.loads(outlook_tool.outlook_read_calendar_entries())
    assert "error" in payload
    assert "Outlook credentials not configured" in payload["error"]


def test_format_calendar_entry_includes_expected_fields():
    entry = {
        "id": "evt-1",
        "subject": "Team Sync",
        "start": {"dateTime": "2026-06-26T10:00:00", "timeZone": "UTC"},
        "end": {"dateTime": "2026-06-26T10:30:00", "timeZone": "UTC"},
        "isAllDay": False,
        "location": {"displayName": "Room A"},
        "organizer": {
            "emailAddress": {"name": "Alice", "address": "alice@example.com"}
        },
        "webLink": "https://example.com/event",
        "bodyPreview": "Agenda",
    }

    payload = outlook_tool._format_calendar_entry(entry, include_body_preview=True)

    assert payload["id"] == "evt-1"
    assert payload["subject"] == "Team Sync"
    assert payload["start"]["date_time"] == "2026-06-26T10:00:00"
    assert payload["end"]["date_time"] == "2026-06-26T10:30:00"
    assert payload["location"] == "Room A"
    assert payload["organizer"]["email"] == "alice@example.com"
    assert payload["body_preview"] == "Agenda"
