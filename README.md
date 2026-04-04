# SentinelClaw

Self-hosted, KI-gestuetzte Security Assessment Platform (Penetrationstest-Tool), angetrieben von NVIDIA NemoClaw als Agent-Runtime und Claude als LLM-Backend. Der PoC laeuft vollstaendig lokal mit Python 3.12+, FastMCP, Docker und SQLite.

---

## Features (PoC-Scope)

- **Orchestrator-Agent (FA-01)** -- Plant und koordiniert mehrphasige Scans (Recon, Vuln, Full). Delegiert Aufgaben an Sub-Agenten und erstellt eine Executive Summary mit Empfehlungen.
- **Recon-Agent (FA-02)** -- Fuehrt autonome Reconnaissance durch: Host Discovery, Port-Scan mit Service-Erkennung und Vulnerability-Scan. Analysiert Ergebnisse und fasst Risiken zusammen.
- **MCP-Server mit 4 Tools (FA-03)** -- Exponiert `port_scan`, `vuln_scan`, `exec_command` und `parse_output` als MCP-Tools via FastMCP. Jeder Aufruf wird gegen den Scope validiert und im Audit-Log protokolliert.
- **Claude via NemoClaw-Runtime (FA-04)** -- Nutzt die Claude Code CLI im Agent-Modus (Abo, kein API-Key noetig). Claude plant autonom, fuehrt nmap/nuclei ueber `docker exec` in der Sandbox aus und analysiert die Ergebnisse.
- **Sandbox-Isolation (FA-05)** -- Gehaerteter Docker-Container (cap_drop ALL, read-only FS, non-root User, PID-Limit) fuer die Ausfuehrung von Scan-Tools. Kein direkter Host-Zugriff.

---

## Voraussetzungen

| Komponente | Version | Hinweis |
|---|---|---|
| Python | 3.12+ | Mit `venv`-Unterstuetzung |
| Docker Desktop | 20.10+ | Muss laufen bevor Scans gestartet werden |
| Claude Code CLI | Aktuell | Installiert und authentifiziert (Abo erforderlich) |
| Git | 2.30+ | Fuer Repository-Klonen |

---

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/jacea-dev/sentinelclaw.git
cd sentinelclaw

# 2. Virtuelle Umgebung erstellen und aktivieren
python3 -m venv .venv && source .venv/bin/activate

# 3. Abhaengigkeiten installieren (inkl. Dev-Tools)
pip install -e ".[dev]"

# 4. Umgebungsvariablen konfigurieren
cp .env.example .env
# .env anpassen: SENTINEL_ALLOWED_TARGETS setzen

# 5. Sandbox-Container bauen und starten
docker compose build sandbox
docker compose up -d sandbox

# 6. Ersten Scan ausfuehren
python -m src.cli orchestrate --target scanme.nmap.org --ports 22,80,443 --yes
```

Nach dem Scan werden die Ergebnisse direkt im Terminal ausgegeben. Audit-Logs und Scan-Daten werden in `data/sentinelclaw.db` (SQLite) gespeichert.

---

## Architektur

```
                         +------------------+
                         |       CLI        |
                         | (scan/orchestrate)|
                         +--------+---------+
                                  |
                                  v
                      +-----------+-----------+
                      |   Orchestrator-Agent  |
                      |       (FA-01)         |
                      +-----------+-----------+
                                  |
                                  v
                      +-----------+-----------+
                      | NemoClaw Runtime      |
                      | (Claude CLI Agent)    |
                      +-----------+-----------+
                                  |
                          +-------+-------+
                          |               |
                          v               v
                   +------+------+  +-----+-------+
                   | Recon-Agent |  | MCP-Server   |
                   |   (FA-02)   |  | (4 Tools)    |
                   +------+------+  +-----+--------+
                          |               |
                          v               v
                    +-----+-----+   +-----+--------+
                    |   Bash    |   | Scope-       |
                    |   Tool    |   | Validator    |
                    +-----+-----+   +--------------+
                          |
                          v
                  +-------+--------+
                  |  docker exec   |
                  +-------+--------+
                          |
                          v
              +-----------+-----------+
              |   Sandbox-Container   |
              |  (nmap, nuclei)       |
              |  cap_drop=ALL         |
              |  read_only=true       |
              |  user=scanner         |
              +-----------------------+
```

**Datenfluss:** CLI nimmt Ziel und Parameter entgegen. Der Orchestrator erstellt einen Scan-Plan und delegiert an den Recon-Agent. Dieser nutzt die NemoClaw-Runtime (Claude CLI im Agent-Modus), die ueber Bash-Tool `docker exec` Befehle im gehaerteten Sandbox-Container ausfuehrt. Alle Aufrufe werden durch den Scope-Validator und den Kill-Switch abgesichert. Ergebnisse werden in SQLite persistiert und im Audit-Log protokolliert.

---

## Projektstruktur

```
src/
|-- cli.py                          # CLI-Einstiegspunkt (scan + orchestrate)
|-- __init__.py
|
|-- agents/
|   |-- __init__.py
|   |-- nemoclaw_runtime.py         # NemoClaw Agent-Runtime (Claude CLI)
|   |-- llm_provider.py             # LLM-Provider-Abstraktion
|   |-- token_tracker.py            # Token-Budget-Tracking
|   |-- tool_bridge.py              # Tool-Bridge fuer Agent-Runtime
|   |-- recon/
|   |   |-- __init__.py
|   |   |-- agent.py                # Recon-Agent (FA-02)
|   |   |-- prompts.py              # System-Prompts fuer Recon
|   |   |-- result_types.py         # Typisierte Recon-Ergebnisse
|
|-- orchestrator/
|   |-- __init__.py
|   |-- agent.py                    # Orchestrator-Agent (FA-01)
|   |-- prompts.py                  # System-Prompts fuer Orchestrator
|   |-- result_types.py             # Typisierte Orchestrator-Ergebnisse
|
|-- mcp_server/
|   |-- __init__.py
|   |-- __main__.py                 # MCP-Server Startpunkt
|   |-- server.py                   # FastMCP Server mit 4 Tools
|   |-- audit.py                    # Audit-Logging fuer MCP-Aufrufe
|   |-- tools/
|   |   |-- __init__.py
|   |   |-- port_scan.py            # Tool: nmap Port-Scan
|   |   |-- vuln_scan.py            # Tool: nuclei Vulnerability-Scan
|   |   |-- exec_command.py         # Tool: Freie Befehlsausfuehrung
|   |   |-- parse_output.py         # Tool: Output-Parsing
|   |   |-- input_validation.py     # Input-Validierung fuer alle Tools
|
|-- sandbox/
|   |-- __init__.py
|   |-- executor.py                 # Docker-Sandbox-Executor
|
|-- shared/
|   |-- __init__.py
|   |-- config.py                   # Zentrale Konfiguration (Pydantic)
|   |-- database.py                 # SQLite-Datenbankmanager
|   |-- repositories.py             # Repository-Pattern (CRUD)
|   |-- scope_validator.py          # Scope-Validator (7 Checks)
|   |-- kill_switch.py              # Kill-Switch (Singleton)
|   |-- logging_setup.py            # Structlog + Secret-Masking
|   |-- sanitizer.py                # Input-Sanitizer
|   |-- formatters.py               # Ausgabe-Formatierung
|   |-- constants/
|   |   |-- __init__.py
|   |   |-- defaults.py             # Zentrale Default-Werte
|   |-- types/
|   |   |-- __init__.py
|   |   |-- models.py               # Datenmodelle (ScanJob, Finding, etc.)
|   |   |-- scope.py                # PentestScope + ValidationResult
|   |   |-- agent_runtime.py        # Agent-Runtime Interfaces
|   |-- utils/
|       |-- __init__.py
```

---

## Konfiguration

Alle Einstellungen werden ueber Umgebungsvariablen mit dem Praefix `SENTINEL_` gesteuert. Die Datei `.env.example` enthaelt alle verfuegbaren Variablen mit Erklaerungen.

| Variable | Default | Beschreibung |
|---|---|---|
| `SENTINEL_LLM_PROVIDER` | `claude-abo` | LLM-Provider: `claude-abo`, `claude`, `azure`, `ollama` |
| `SENTINEL_ALLOWED_TARGETS` | *(leer)* | Komma-separierte Scan-Ziele (IP, CIDR, Domain) |
| `SENTINEL_SANDBOX_TIMEOUT` | `300` | Max. Tool-Laufzeit in Sekunden |
| `SENTINEL_LLM_MAX_TOKENS_PER_SCAN` | `50000` | Token-Budget pro Scan |
| `SENTINEL_LLM_MONTHLY_TOKEN_LIMIT` | `1000000` | Monatliches Token-Limit |
| `SENTINEL_LOG_LEVEL` | `INFO` | Log-Verbosity: DEBUG, INFO, WARNING, ERROR |
| `SENTINEL_MCP_PORT` | `8080` | MCP-Server Port |
| `SENTINEL_SANDBOX_IMAGE` | `sentinelclaw/sandbox:latest` | Docker-Image fuer Sandbox |
| `SENTINEL_SANDBOX_MEMORY_LIMIT` | `2g` | RAM-Limit fuer Sandbox-Container |
| `SENTINEL_SANDBOX_CPU_LIMIT` | `2.0` | CPU-Limit fuer Sandbox-Container |
| `SENTINEL_SANDBOX_PID_LIMIT` | `100` | Max. Prozesse im Container |
| `SENTINEL_DB_PATH` | `data/sentinelclaw.db` | Pfad zur SQLite-Datenbank |

---

## Sicherheit

SentinelClaw implementiert mehrere Sicherheitsebenen, die nicht umgangen werden koennen:

### Scope-Validator (7 Checks)

Jeder Tool-Aufruf durchlaeuft 7 unabhaengige Pruefungen. Wenn auch nur eine fehlschlaegt, wird der gesamte Aufruf blockiert:

1. **Target in Scope** -- Ist das Ziel in der Whitelist (`targets_include`)?
2. **Target nicht ausgeschlossen** -- Ist das Ziel nicht in der Blacklist (`targets_exclude`)?
3. **Target nicht verboten** -- Liegt das Ziel nicht in verbotenen IP-Ranges (Loopback, Multicast)?
4. **Port im Scope** -- Ist der Port im erlaubten Bereich?
5. **Zeitfenster** -- Liegt die aktuelle Zeit innerhalb des erlaubten Scan-Fensters?
6. **Eskalationsstufe** -- Ist das Tool innerhalb der erlaubten Stufe (0=Passiv bis 4=Post-Exploitation)?
7. **Tool erlaubt** -- Ist das Tool in der expliziten Allowlist (falls gesetzt)?

### Kill-Switch

Sofortiges, irreversibles Abschalten aller Operationen bei Sicherheitsverstossen:

- Singleton-Pattern mit Thread-sicherem Event-Flag
- Stoppt den Sandbox-Container ueber die Docker-API (`container.kill()`)
- Einmal aktiviert, kann er in der laufenden Sitzung nicht zurueckgesetzt werden
- Audit-Log-Eintrag bei jeder Aktivierung

### Sandbox-Isolation

- `cap_drop: ALL` + nur `NET_RAW` fuer nmap SYN-Scans
- Read-only Filesystem (`read_only: true`)
- Non-root User (`scanner`)
- PID-Limit (Default: 100 Prozesse)
- Separate Netzwerke: `sentinel-internal` (kein Internet) + `sentinel-scanning` (nur Scan-Ziele)
- Binary-Allowlist: Nur `nmap` und `nuclei` duerfen ausgefuehrt werden

---

## Tests

```bash
# Unit-Tests ausfuehren
python -m pytest tests/unit/ -v

# Alle Tests (inkl. Integration und E2E)
python -m pytest tests/ -v

# Mit Coverage
python -m pytest tests/unit/ -v --cov=src
```

Die Tests pruefen unter anderem:
- Scope-Validator (alle 7 Checks)
- Input-Validierung (Target, Ports, nmap-Flags)
- Datenbank-Operationen (CRUD, Audit-Logs)
- Konfigurationsvalidierung

---

## Lizenz

Proprietary -- Alle Rechte vorbehalten.

---

## Autor

**Jaciel Antonio Acea Ruiz**
