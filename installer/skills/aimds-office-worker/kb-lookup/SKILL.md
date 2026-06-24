---
name: kb-lookup
description: Beantwortet Fragen zu Firmenwissen (Policies, Prozesse, Templates, interne Fakten) aus dem AIMDS-AI-KB und zitiert die Quelle. Nutzen für "wie ist unser Prozess für…", "wo finde ich…", "was ist unsere Policy zu…".
---

# KB Lookup

## Vorgehen
1. **Frage präzisieren** (1 Satz).
2. **KB abfragen:** `kb_search` für die Suche, `kb_get_topic` für den vollen Artikel,
   `kb_get_related` für Verwandtes.
3. **Antworten mit Zitat:** Aussage + Quelle (Titel/Topic). Wenn die KB nichts hat,
   das **klar sagen** — nicht raten.

## Verifikation
- Antwort stammt aus der KB, nicht aus dem Modellgedächtnis.
- Quelle ist benannt und existiert wirklich.

## Was NICHT
- Firmenwissen nie aus dem Gedächtnis "erinnern" — immer KB prüfen.
- Keine veralteten Stände zitieren, wenn ein neuerer Topic existiert.
