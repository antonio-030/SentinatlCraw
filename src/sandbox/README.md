# Sandbox — Docker-Container-Ausführung

> Führt Pentest-Tools sicher in gehärteten Docker-Containern aus.

## Was macht dieses Modul?

Der Sandbox-Executor kapselt alle Tool-Ausführungen in Docker-Containern.
Kein Befehl läuft direkt auf dem Host. Container werden mit minimalen
Rechten gestartet (CAP_DROP ALL, read-only FS, PID-Limits, Netzwerk-Whitelist).

## Dateien

| Datei | Funktion |
|---|---|
| `executor.py` | Docker-Container-Verwaltung und Befehlsausführung |

## Starten

Wird nicht eigenständig gestartet. Wird vom MCP-Server importiert.

## Sicherheitsmerkmale

- `--cap-drop=ALL` + nur `NET_RAW` (für nmap)
- Read-only Dateisystem (tmpfs für /tmp)
- PID-Limit (Standard: 256)
- Memory-Limit (Standard: 2 GB)
- CPU-Limit (Standard: 2.0 Cores)
- Allowlist für erlaubte Binaries
- Timeout für jeden Befehl
- Kill-Switch-Integration

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_SANDBOX_IMAGE` | Docker-Image (Standard: sentinelclaw/sandbox) |
| `SENTINEL_SANDBOX_TIMEOUT` | Timeout pro Befehl in Sekunden |
| `SENTINEL_SANDBOX_MEMORY_LIMIT` | Memory-Limit pro Container |
| `SENTINEL_SANDBOX_CPU_LIMIT` | CPU-Limit pro Container |
| `SENTINEL_SANDBOX_PID_LIMIT` | Maximale Anzahl Prozesse |

## Dependencies

- `docker` (Docker SDK für Python)
- `src.shared` (Kill-Switch, Konfiguration, Konstanten)
