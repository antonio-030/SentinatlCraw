# Changelog

Alle relevanten Aenderungen an SentinelClaw werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
und dieses Projekt haelt sich an [Semantic Versioning](https://semver.org/lang/de/).

## [0.1.0] - 2026-04-04

Erster Proof-of-Concept (Meilensteine M1--M4 abgeschlossen).

### Hinzugefuegt

- **Orchestrator-Agent (FA-01)** -- Mehrphasige Scan-Koordination mit Scan-Plan-Erstellung, Delegation an Sub-Agenten und Executive Summary. Unterstuetzt die Scan-Typen `recon`, `vuln` und `full` ueber den CLI-Befehl `orchestrate`.
- **Recon-Agent (FA-02)** -- Autonome Reconnaissance mit Host Discovery (nmap -sn), Port-Scan mit Service-Erkennung (nmap -sV -sC) und Vulnerability-Scan (nuclei). Analysiert Ergebnisse und erstellt eine strukturierte Zusammenfassung mit Risikobewertung.
- **MCP-Server mit 4 Tools (FA-03)** -- FastMCP-Server mit den Tools `port_scan` (nmap), `vuln_scan` (nuclei), `exec_command` (freie Sandbox-Befehlsausfuehrung) und `parse_output` (Parsing von nmap-XML, nuclei-JSONL, Plaintext). Jeder Tool-Aufruf wird validiert und geloggt.
- **Claude via NemoClaw-Runtime (FA-04)** -- Integration der Claude Code CLI im Agent-Modus als NemoClaw-kompatible Runtime. Claude plant autonom, fuehrt Scan-Befehle ueber `docker exec` in der Sandbox aus und analysiert die Ergebnisse. Laeuft ueber das Claude-Code-Abo ohne separaten API-Key.
- **Sandbox-Isolation (FA-05)** -- Gehaerteter Docker-Container auf Basis von Ubuntu 22.04 mit nmap 7.80 und nuclei 3.3.7. Sicherheitsmassnahmen: `cap_drop ALL`, `NET_RAW` fuer SYN-Scans, Read-only Filesystem, Non-root User (`scanner`), PID-Limit, separate Docker-Netzwerke.
- **Scope-Validator mit 7 Checks** -- Validiert jeden Tool-Aufruf gegen den definierten Pentest-Scope: Target-Whitelist, Target-Blacklist, Verbotene IP-Ranges, Port-Bereich, Zeitfenster, Eskalationsstufe und Tool-Allowlist. Blockiert den gesamten Aufruf wenn auch nur ein Check fehlschlaegt.
- **Kill-Switch** -- Singleton mit Thread-sicherem Event-Flag fuer sofortiges, irreversibles Abschalten aller Operationen. Stoppt den Sandbox-Container ueber die Docker-API und protokolliert die Aktivierung im Audit-Log.
- **SQLite-Datenbank und Audit-Logging** -- Schema mit 5 Tabellen (scan_jobs, findings, scan_results, audit_logs, agent_logs). WAL-Modus fuer concurrent Reads, Foreign Keys aktiviert. Audit-Logs sind unveraenderbar (kein UPDATE, kein DELETE). Repository-Pattern fuer spaetere Migration zu PostgreSQL.
- **CLI mit scan- und orchestrate-Befehlen** -- Kommandozeilen-Interface mit argparse. `scan` fuer einzelne Recon-Scans, `orchestrate` fuer koordinierte Mehrphasen-Scans. Unterstuetzt Ausgabeformate Markdown und JSON, Eskalationsstufen 0--2 und automatische Disclaimer-Bestaetigung (`--yes`).

### Sicherheit

- Input-Validierung fuer alle MCP-Tool-Parameter: Target-Format (IP, CIDR, Domain), Port-Ranges (1--65535), nmap-Flag-Allowlist, nuclei-Template-Allowlist. Shell-Metazeichen werden blockiert.
- Binary-Allowlist im Sandbox-Executor: Nur `nmap` und `nuclei` duerfen ausgefuehrt werden. Alle anderen Binaries werden mit `PermissionError` abgelehnt.
- Secret-Masking im Logging: API-Keys, Passwoerter und Private Keys werden automatisch aus Log-Ausgaben entfernt (Regex-basiert ueber `structlog`).
- Docker-Compose mit Netzwerk-Isolation: `sentinel-internal` (kein Internet) fuer MCP-Sandbox-Kommunikation, `sentinel-scanning` fuer Zugriff auf Scan-Ziele.
- Parametrisierte Befehlsausfuehrung: Kein `shell=True`, keine String-Konkatenation. Befehle werden als Liste an die Docker-API uebergeben.
