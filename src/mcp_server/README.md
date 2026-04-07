# MCP-Server — Tool-Abstraktion für KI-Agenten

> Exponiert Pentest-Tools (nmap, nuclei) als MCP-Tools mit Scope-Validierung.

## Was macht dieses Modul?

Der MCP-Server stellt die Brücke zwischen KI-Agent und Pentest-Werkzeugen dar.
Jeder Tool-Aufruf wird gegen den Pentest-Scope validiert und in der Audit-Log
protokolliert. Die Tools laufen isoliert in der Sandbox — nie auf dem Host.

## Dateien

| Datei | Funktion |
|---|---|
| `server.py` | MCP-Server-Setup mit FastMCP |
| `audit.py` | Audit-Logging für Tool-Aufrufe |
| `tools/port_scan.py` | Port-Scan via nmap |
| `tools/vuln_scan.py` | Schwachstellen-Scan via nuclei |
| `tools/exec_command.py` | Allgemeine Befehlsausführung (Allowlist) |
| `tools/parse_output.py` | Tool-Ausgabe-Parsing |
| `tools/input_validation.py` | Eingabevalidierung für alle Tools |

## Starten

```bash
python -m src.mcp_server
```

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_MCP_HOST` | Host-Adresse (Standard: localhost) |
| `SENTINEL_MCP_PORT` | Port (Standard: 8080) |
| `SENTINEL_SANDBOX_IMAGE` | Docker-Image für die Sandbox |
| `SENTINEL_SANDBOX_TIMEOUT` | Timeout pro Tool-Aufruf in Sekunden |

## Dependencies

- `fastmcp` (MCP-Protokoll-Implementierung)
- `src.sandbox` (Docker-Container-Ausführung)
- `src.shared` (Scope-Validierung, Konfiguration)
