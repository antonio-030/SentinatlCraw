# Watchdog — Überwachungsservice

> Unabhängiger Überwachungsprozess der bei Anomalien den Kill-Switch auslöst.

## Was macht dieses Modul?

Der Watchdog läuft als eigenständiger Prozess und prüft alle 10 Sekunden:
Scan-Timeouts, Sandbox-Container-Gesundheit, API-Health-Checks und
Kill-Switch-Vervollständigung. Bei Anomalien wird automatisch Kill-Pfad 2 ausgelöst.

## Dateien

| Datei | Funktion |
|---|---|
| `service.py` | Watchdog-Hauptlogik mit Prüfzyklen |
| `scope_checks.py` | Scope-Überwachung während laufender Scans |
| `__main__.py` | Einstiegspunkt für `python -m src.watchdog` |

## Starten

```bash
python -m src.watchdog
```

In Production wird der Watchdog als eigener Container gestartet (siehe `docker-compose.prod.yml`).

## Prüfungen

| Prüfung | Aktion bei Fehler |
|---|---|
| Scan-Timeout überschritten | Scan abbrechen, Kill-Switch |
| Sandbox-Container gestoppt | Warnung loggen, Neustart versuchen |
| API-Health-Check fehlgeschlagen (3x) | Kill-Pfad 2 auslösen |
| Kill-Switch unvollständig | Vervollständigung erzwingen |

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_DB_PATH` | Pfad zur SQLite-Datenbank |
| `SENTINEL_MAX_SCAN_DURATION` | Maximale Scan-Dauer in Sekunden |

## Dependencies

- `docker` (Docker SDK — Container-Überwachung)
- `src.shared` (Kill-Switch, Datenbank, Repositories)
