# Tool-Risk-Registry & Freigabe-Regeln

> Welche Tool-Aktionen ohne Freigabe laufen dürfen und welche nicht. Prinzip:
> **gezielt gaten, nicht pauschal** — sonst Approval-Fatigue (der Nutzer klickt
> blind "OK"). Nur das Konsequenzreiche wird gegated.

## Risk-Rating
| Stufe | Kriterium | Verhalten |
|---|---|---|
| 🟢 **low** | nur lesen, reversibel, keine Außenwirkung | autonom |
| 🟡 **medium** | schreibt lokal/intern, reversibel | autonom, im Ergebnis vermerken |
| 🔴 **high** | Außenwirkung, irreversibel, Geld | **immer Freigabe vor Ausführung** |

## Konkrete Einstufung
| Aktion / Tool | Stufe | Regel |
|---|---|---|
| KB lesen (`kb_search`, `kb_get_topic`) | 🟢 | autonom |
| Web-Recherche / Seite lesen | 🟢 | autonom |
| User-Memory lesen (MCP) | 🟢 | autonom |
| Kalender lesen | 🟢 | autonom |
| Mail lesen / clustern | 🟢 | autonom |
| Datei lokal erstellen/bearbeiten (Entwurf) | 🟡 | autonom |
| User-Memory schreiben (MCP) | 🟡 | autonom, ggf. `write_approval` |
| **Mail senden** | 🔴 | **immer Freigabe** |
| **Termin anlegen/ändern/absagen** | 🔴 | **Freigabe** |
| **Datei/Datensatz löschen** | 🔴 | **Freigabe** |
| **Extern teilen / veröffentlichen** | 🔴 | **Freigabe** |
| **Geld bewegen / Bestellung / Transaktion** | 🔴 | **niemals autonom — Nutzer macht es selbst** |

## Umsetzung in Hermes
- **Default-Haltung:** neue Rollouts laufen **draft-only / read-only**. Schreib-
  und Sende-Rechte werden bewusst freigeschaltet, wenn Vertrauen da ist.
- **`write_approval`** für Memory und Skills auf `true` (Enterprise).
- **Event-Hooks** für High-Risk-Tools: Logging/Alert/Freigabe-Gate.
- **Prompt-Injection-Scan**: Hermes scannt Context-Files und Memory automatisch.
  Zusätzlich: Inhalte aus Mails/Web nie als Anweisung behandeln (in SOUL/AGENTS verankert).
- **Angriffsfläche klein:** ungenutzte MCP-Connectoren deaktivieren.
- Optional zentral in LiteLLM: **Guardrails/Policies** als zweite Screening-Schicht
  (Input + Output).

## Anti-Pattern (vermeiden)
- Pauschale "alles freigeben"-Gewohnheit (Approval-Fatigue).
- Autonomer Mailversand "weil's bequem ist".
- High-Frequency-Goal-Loop mit schreibenden Tools ohne Gate.
