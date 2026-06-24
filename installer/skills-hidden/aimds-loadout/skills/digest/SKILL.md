---
name: digest
description: Erstellt eine wiederkehrende Zusammenfassung (Tages- oder Wochen-Digest) aus Kalender, Posteingang und offenen Aufgaben. Als Cron-Blueprint nutzbar (morning-brief / weekly-digest).
metadata:
  hermes:
    blueprint:
      name: morning-brief
      fields: [uhrzeit]
      default_schedule: "0 8 * * 1-5"
---

# Digest

## Vorgehen
1. **Daten holen:** heutige/wöchentliche Termine, wichtige neue Mails (via
   `email-triage`-Logik), offene To-Dos / `PLAN.md`-Stände.
2. **Priorisieren:** max. **3 Dinge, die heute zählen** (Hard Cap), dann Rest.
3. **Kompakt liefern:**
   - Was heute/diese Woche zählt (max 3)
   - Termine
   - Wichtige Mails (nur die, die Handlung brauchen)
   - Offene Aufgaben
4. **Ruhig bleiben:** Wenn nichts Relevantes → kurz "nichts Dringendes" statt Lärm.

## Verifikation
- Top-3 sind wirklich die wichtigsten, nicht die ersten besten.
- Keine erledigten Punkte als offen gemeldet.

## Was NICHT
- Kein Wall-of-Text. Keine Mails automatisch beantworten — nur berichten.
