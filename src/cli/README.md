# CLI — Kommandozeilen-Interface

> Kommandozeilen-Werkzeug für Scans, Findings, Reports und Systemverwaltung.

## Was macht dieses Modul?

Das CLI bietet direkten Zugriff auf alle SentinelClaw-Funktionen ohne Web-UI.
Es unterstützt Recon-Scans, orchestrierte Multi-Phasen-Scans, Finding-Abfragen,
Scan-Vergleiche, Report-Generierung und den Notfall-Kill-Switch.

## Befehle

| Befehl | Funktion |
|---|---|
| `scan` | Einfachen Recon-Scan durchführen |
| `orchestrate` | Orchestrierten Multi-Phasen-Scan starten |
| `profiles` | Verfügbare Scan-Profile anzeigen |
| `status` | Systemstatus und laufende Scans |
| `history` | Vergangene Scans auflisten |
| `findings` | Findings filtern und anzeigen |
| `compare` | Zwei Scans vergleichen (Delta) |
| `report` | Report generieren (Executive, Technical, Compliance) |
| `export` | Findings exportieren (CSV, JSONL, SARIF) |
| `kill` | NOTAUS — alle laufenden Scans sofort stoppen |

## Starten

```bash
python -m src.cli scan --target 10.10.10.1 --ports 1-1000
python -m src.cli orchestrate --target 10.10.10.1 --profile standard
python -m src.cli findings --severity critical --output json
python -m src.cli report --scan-id <UUID> --type technical
python -m src.cli export --scan-id <UUID> --format sarif
```

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_DB_PATH` | Pfad zur SQLite-Datenbank |
| `SENTINEL_LOG_LEVEL` | Log-Level für CLI-Ausgabe |

## Dependencies

- `argparse` (Standardbibliothek)
- `src.orchestrator` (Scan-Ausführung)
- `src.shared` (Datenbank, Konfiguration, Formatierung)
