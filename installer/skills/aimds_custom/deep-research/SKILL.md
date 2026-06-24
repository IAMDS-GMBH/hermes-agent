---
name: deep-research
description: Recherchiert eine konkrete Frage über mehrere Quellen, prüft Behauptungen gegen, und liefert eine knappe, zitierte Synthese. Nutzen, wenn der Nutzer "recherchiere", "finde heraus", Markt-/Wettbewerbs-/Themen-Info verlangt.
---

# Deep Research

## Vorgehen
1. **Scope (max 1 Satz):** Was genau, wofür, welche Tiefe? Bei Unklarheit kurz fragen.
2. **Quellen sammeln:** mind. 2-3 unabhängige Quellen. Erst **AIMDS-AI-KB**
   (`kb_search`) prüfen — gibt es internes Wissen? Dann Web.
3. **Gegenprüfen:** Sagen ≥2 Quellen dasselbe? Datum aktuell? Marketing vs. neutral?
   Bei Widerspruch beide Positionen zeigen.
4. **Synthese:** Befund zuerst, Belege danach. Jede Aussage mit Quelle (Link/Titel).
5. **Confidence:** high / medium / low offen ausweisen. `low` nie still verstecken.

## Verifikation (vor "fertig")
- Jede zentrale Aussage hat eine echte, benannte Quelle (keine erfundenen URLs).
- Offene Lücken explizit nennen ("keine belegbare Aussage zu X gefunden").

## Was NICHT
- Keine halluzinierten Zitate. Keine einzelne Marketing-Quelle als Beleg.
- Keine veralteten Quellen ohne Datums-Hinweis.
