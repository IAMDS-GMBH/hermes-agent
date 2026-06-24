# Agent-Topologie — lokal (Hermes) vs. zentral (LiteLLM A2A)

> Welche "Agenten" laufen auf dem Desktop in Hermes, und welche hosten wir zentral
> hinter dem **LiteLLM A2A Gateway** und bieten sie als Service an. Leitfrage:
> *Braucht die Fähigkeit lokalen Nutzerkontext und Interaktivität — oder ist sie
> eine geteilte, zu governende Org-Fähigkeit?*

## Was "Agent" an welcher Stelle heißt
- **Lokal in Hermes:** der Haupt-Agent, **Skills** (prozedurales Können),
  **delegierte Subagents** (kurzlebig, im Prozess), **Cron-Jobs**. Nutzen LiteLLM
  nur für Inferenz, Tools (MCP) und Memory.
- **Zentral über LiteLLM A2A:** eigenständige Agent-Services, von Hermes übers
  A2A-Protokoll aufgerufen. LiteLLM regelt **Zugriff pro Team/Key, Cost-Tracking,
  Permissions, Iteration-Budgets** — ein Ort für Logik *und* Governance.

## Entscheidungs-Kriterien

**Lokal halten, wenn:**
- braucht **lokalen Kontext** (Dateien, Desktop-Apps, Zwischenablage, OS)
- ist **interaktiv / latenzsensibel** (Teil der User-Schleife)
- ist **generisch und günstig** (zusammenfassen, entwerfen, triagen)
- ist **pro-User / persönlich**

**Zentral als A2A anbieten, wenn:**
- **geteilte Org-Fähigkeit**, die viele Mitarbeiter nutzen (einmal bauen, einmal governen)
- braucht **privilegierten/zentralen Datenzugriff** (DBs, Systeme), den du nicht
  auf jedem Desktop haben willst
- **schwer/teuer/spezialisiert** (lang laufend, großes Modell, GPU)
- braucht **strikte Governance**: Zugriffskontrolle, Audit, Kostenlimit,
  Iteration-Budget — genau die A2A-Gateway-Features
- muss **über alle Oberflächen konsistent** sein (Desktop, Web, andere Clients)
- **deterministisch/compliance-kritisch**

## Konkrete Empfehlung (Start klein, dann wachsen)

> Universelles Prinzip aller Anbieter: **mit dem Einfachsten starten, Komplexität
> nur bei nachgewiesenem Bedarf.** Also: viele leichte lokale Skills, **wenige**
> zentrale A2A-Agents.

### Lokal (Hermes-Skills/Subagents) — der Großteil
| Fähigkeit | Warum lokal |
|---|---|
| meeting-prep | per-User, interaktiv, Kalenderkontext |
| email-triage | per-User, draft-only, Posteingang |
| doc-draft / doc-review | arbeitet an Dateien des Users |
| digest / morning-brief | persönlich, leichtgewichtig |
| deep-research (leicht) | interaktiv, generisch |
| kb-lookup | dünner Wrapper auf KB-MCP, kein eigener Agent nötig |

→ **~6-7 lokale Skills** decken den Office-Alltag ab.

### Zentral (LiteLLM A2A) — gezielt, anfangs 0-2
| Kandidat | Warum zentral |
|---|---|
| **CRM-/Pipeline-Agent** | privilegierter CRM-Zugriff, geteilte Logik, Audit |
| **Daten-/Reporting-Agent** | hängt am Data-Warehouse, schwer, governt |
| **Compliance-/Vertrags-Agent** | muss konsistent & nachvollziehbar sein, Audit-Pflicht |
| **Heavy-Research-Agent** | nur falls er interne, privilegierte Quellen anzapft |

→ **Mit 0-2 starten**, die einen echten "privilegierter Zugriff / Governance /
geteilt"-Grund haben. Nicht auf Vorrat bauen.

## Faustregel
**Per-User-Produktivität → lokal. Org-System-Zugriff + Governance → zentral A2A.**
Oder kürzer: *Lesen/Entwerfen am Desktop, privilegiertes Handeln im Gateway.*

## Warum nicht alles zentral?
- Zentrale A2A-Agents sehen **keinen lokalen Desktop-Kontext** und kosten einen
  Netzwerk-Hop + Latenz.
- Der Desktop-Loop (Plan, Recitation, schnelle Iteration) gehört lokal.
- Zentral lohnt sich dort, wo **Governance und geteilter Zugriff** den Hop wert sind.

## Warum nicht alles lokal?
- Privilegierte Credentials auf 50 Desktops = Angriffsfläche + Wartungshölle.
- Geteilte Logik 50x lokal pflegen = Drift. Zentral = ein Update für alle.
- Kosten/Audit pro Mitarbeiter nur zentral sauber steuerbar (A2A: Permissions,
  Cost-Tracking, Iteration-Budgets).

## Worked Example — Office/Dokumente (Excel/Word/PowerPoint)
**Frage:** Skills, eigener Agent, oder A2A?
**Antwort: lokale Skills mit gebündelten Skripten. NICHT A2A.**

Warum: lokale Dateiarbeit, per-User, generisch-prozedural, kein privilegierter
Zentralzugriff. Ein A2A-Agent kostet einen Netz-Hop und **sieht die lokale Datei
des Users nicht**.

Aufbau eines Office-Skills (= `doc-draft` / `doc-review`):
1. **Prozedurales Wissen** (Hausstil, Aufbau) → `SKILL.md`
2. **Gebündelte Skripte** (`python-pptx`, `openpyxl`, `python-docx`) → lokal via
   Code-Execution, deterministisch, kein Reasoning-Agent nötig
3. **Templates/Brand** → aus KB referenziert

Zentral bleibt es trotzdem: **Verteilung/Update über LiteLLM Skills Gateway / Git**
→ Hausstil firmenweit konsistent. *LiteLLM = Distribution/Governance, Hermes = Ausführung.*

**Anti-Pattern:** NICHT je einen "Excel-/Word-/PPT-Agent" bauen. Ein fähiger Agent
+ wenige hochwertige Doc-Skills schlägt viele dünne Spezial-Agents.

**Ausnahme (dann A2A):** zentraler, governter Report-Generator, der privilegierte
Daten (Warehouse) zieht und ein Standard-Deck/Sheet emittiert — ein Daten-Agent,
der zufällig Office ausgibt, kein generisches Office-Können.

## Offene Punkte
- ⚠ A2A-Agents brauchen ein **Agent Card** (Capability-Beschreibung) — wer baut/pflegt die?
- ⚠ Kann Hermes **als A2A-Client** out-of-the-box A2A-Agents aufrufen, oder via
  MCP-Bridge? (Hermes spricht nativ MCP; A2A-Aufruf ggf. über einen MCP-Wrapper —
  vor Pilot verifizieren.)
- ⚠ Identitäts-Durchreichung: User-Key pro A2A-Call, damit Permissions & Audit greifen.
