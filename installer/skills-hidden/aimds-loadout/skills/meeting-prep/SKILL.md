---
name: meeting-prep
description: Erstellt ein kompaktes Briefing zu einem anstehenden Termin aus Kalender, relevanten Dokumenten und aktueller Web-/Firmeninfo. Nutzen vor Meetings, Kundenterminen, Calls.
---

# Meeting Prep

## Vorgehen
1. **Termin holen:** aus dem Kalender (Titel, Zeit, Teilnehmer, Beschreibung).
2. **Kontext sammeln:** relevante Mails/Dokumente; bei Personen/Firmen kurz
   recherchieren (`deep-research`-Logik); Firmeninternes via **KB** (`kb_search`).
3. **Briefing bauen** (kurz, scanbar):
   - Wer/Was/Wann + Ziel des Termins
   - 3-5 Talking Points
   - mögliche Fragen/Einwände + Antworten
   - offene Punkte / was der Nutzer mitbringen muss

## Verifikation
- Teilnehmer & Zeit stimmen mit dem Kalender überein.
- Keine erfundenen Fakten über Personen/Firmen — nur Belegtes.

## Was NICHT
- Keine privaten/sensiblen Daten über Teilnehmer aus unsicheren Quellen.
```yaml
# Beispiel: als Cron-Blueprint nutzbar
metadata:
  hermes:
    blueprint:
      name: meeting-prep
      fields: [vorlaufzeit]
      default_schedule: "0 7 * * 1-5"
```
