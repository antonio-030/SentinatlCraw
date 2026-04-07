# Orchestrator — Scan-Koordination

> Koordiniert den gesamten Scan-Ablauf über mehrere Phasen und Sub-Agenten.

## Was macht dieses Modul?

Der Orchestrator-Agent erstellt einen Ausführungsplan mit mindestens zwei Phasen,
delegiert die Ausführung an spezialisierte Sub-Agenten (Recon, Vuln-Scan) und
sammelt die Ergebnisse zu einer Gesamtbewertung. Entspricht FA-01 im Lastenheft.

## Dateien

| Datei | Funktion |
|---|---|
| `agent.py` | Orchestrator-Agent — plant und koordiniert Scans |
| `assessment.py` | Gesamtbewertung aus Einzelergebnissen |
| `multi_phase.py` | Multi-Phasen-Ablaufsteuerung |
| `prompts.py` | LLM-Prompts für den Orchestrator |
| `result_types.py` | Typen für Scan-Phasen und -Ergebnisse |
| `phases/` | Phasen-spezifische Logik |

## Starten

Wird über die API (`POST /api/v1/scans`) oder CLI (`sentinelclaw orchestrate`) aufgerufen.

```bash
python -m src.cli orchestrate --target 10.10.10.1 --profile standard
```

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_MAX_CONCURRENT_SCANS` | Maximale parallele Scans |
| `SENTINEL_LLM_PROVIDER` | LLM-Provider für die Planungsentscheidungen |
| `SENTINEL_OPENSHELL_GATEWAY_NAME` | NemoClaw-Gateway für Agent-Ausführung |

## Dependencies

- `src.agents` (NemoClaw-Runtime, LLM-Provider)
- `src.shared` (Datenbank, Repositories, Scope-Validierung)
