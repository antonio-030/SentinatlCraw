# Runbook: Setup und Installation

- **Autor:** Jaciel Antonio Acea Ruiz
- **Datum:** 2026-04-04
- **Status:** Aktuell

---

## Systemvoraussetzungen

### Hardware

| Ressource | Minimum | Empfohlen |
|---|---|---|
| RAM | 4 GB | 8 GB |
| CPU | 2 Kerne | 4 Kerne |
| Festplatte | 5 GB frei | 10 GB frei |
| Netzwerk | Internetzugang fuer Scan-Ziele | Stabile Verbindung |

### Software

| Software | Version | Pruefbefehl |
|---|---|---|
| Python | 3.12+ | `python3 --version` |
| Docker Desktop | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ (in Docker Desktop enthalten) | `docker compose version` |
| Git | 2.30+ | `git --version` |
| Claude Code CLI | Aktuell | `claude --version` |

### Claude Code CLI einrichten

Die Claude Code CLI muss installiert und mit einem aktiven Abo authentifiziert sein:

```bash
# Claude Code CLI installieren (falls noch nicht vorhanden)
npm install -g @anthropic-ai/claude-code

# Authentifizierung pruefen
claude --version
```

Falls `claude` nicht gefunden wird, muss die CLI zuerst installiert und das Abo eingerichtet werden. Details unter: https://docs.anthropic.com/en/docs/claude-code

---

## Installation Schritt fuer Schritt

### 1. Repository klonen

```bash
git clone https://github.com/jacea-dev/sentinelclaw.git
cd sentinelclaw
```

### 2. Virtuelle Umgebung erstellen

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Unter Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Abhaengigkeiten installieren

```bash
pip install -e ".[dev]"
```

Dieser Befehl installiert alle Abhaengigkeiten aus `pyproject.toml`:

- `fastmcp>=2.0.0` -- MCP-Server-Framework
- `anthropic>=0.40.0` -- Anthropic API Client
- `pydantic>=2.0.0` -- Datenvalidierung
- `pydantic-settings>=2.0.0` -- Konfiguration aus Umgebungsvariablen
- `python-dotenv>=1.0.0` -- .env-Datei laden
- `structlog>=24.0.0` -- Strukturiertes Logging
- `aiosqlite>=0.20.0` -- Async SQLite
- `docker>=7.0.0` -- Docker API Client

Sowie die Dev-Abhaengigkeiten: `pytest`, `pytest-asyncio`, `ruff`, `black`.

### 4. Umgebungsvariablen konfigurieren

```bash
cp .env.example .env
```

Die `.env`-Datei oeffnen und mindestens folgende Werte anpassen:

```bash
# LLM-Provider (Standard: Claude Code CLI ueber Abo)
SENTINEL_LLM_PROVIDER=claude-abo

# Erlaubte Scan-Ziele (PFLICHT: nur autorisierte Ziele eintragen)
SENTINEL_ALLOWED_TARGETS=scanme.nmap.org
```

Fuer weitere Konfigurationsoptionen siehe die Kommentare in `.env.example`.

### 5. Docker-Sandbox bauen

Sicherstellen, dass Docker Desktop laeuft:

```bash
docker info
```

Sandbox-Image bauen:

```bash
docker compose build sandbox
```

Dieser Schritt erstellt ein Docker-Image auf Basis von Ubuntu 22.04 mit nmap und nuclei. Das Image ist ca. 300 MB gross.

### 6. Sandbox-Container starten

```bash
docker compose up -d sandbox
```

Pruefen, ob der Container laeuft:

```bash
docker ps --filter name=sentinelclaw-sandbox
```

Erwartete Ausgabe: Container `sentinelclaw-sandbox` mit Status `Up` und `(healthy)`.

### 7. Sandbox-Funktionalitaet testen

```bash
# nmap im Container pruefen
docker exec sentinelclaw-sandbox nmap --version

# nuclei im Container pruefen
docker exec sentinelclaw-sandbox nuclei --version
```

Beide Befehle sollten die jeweilige Versionsnummer ausgeben.

---

## Verifizierung mit verify_m1.py

Das Verifizierungs-Script prueft alle Komponenten automatisch:

```bash
python scripts/verify_m1.py
```

### Erwartete Ausgabe (alle Checks bestanden)

```
============================================================
  SentinelClaw — Meilenstein 1 Verifizierung
============================================================

  OK Konfiguration — Provider=claude-abo
  OK Logging — Structlog + Secret-Masking
  OK Datenbank — SQLite CRUD + Audit-Log OK
  OK NemoClaw-Runtime — Initialisiert mit ClaudeAboProvider
  OK Claude LLM — ClaudeAboProvider (Provider=claude-abo)
  OK Docker + Sandbox — Docker 27.x, Nmap 7.80

------------------------------------------------------------
  MEILENSTEIN 1 BESTANDEN (6/6 Checks)
------------------------------------------------------------
```

### Was wird geprueft

| Check | Beschreibung |
|---|---|
| Konfiguration | `.env` wird geladen, Pydantic validiert alle Werte |
| Logging | Structlog initialisiert, Secret-Masking aktiv |
| Datenbank | SQLite-Datenbank wird erstellt, CRUD-Operationen funktionieren, Audit-Log schreibbar |
| NemoClaw-Runtime | Runtime-Klasse kann mit dem konfigurierten Provider instanziiert werden |
| Claude LLM | LLM-Provider ist erreichbar und antwortet |
| Docker + Sandbox | Docker-Daemon laeuft, Sandbox-Image existiert, nmap im Container ausfuehrbar |

---

## Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'src'`

**Ursache:** Das Paket wurde nicht im editable-Modus installiert.

**Loesung:**
```bash
pip install -e ".[dev]"
```

### Problem: `RuntimeError: Sandbox-Container 'sentinelclaw-sandbox' nicht gefunden`

**Ursache:** Der Sandbox-Container laeuft nicht.

**Loesung:**
```bash
docker compose up -d sandbox
docker ps --filter name=sentinelclaw-sandbox
```

### Problem: `docker.errors.DockerException: Error while fetching server API version`

**Ursache:** Docker Desktop ist nicht gestartet.

**Loesung:** Docker Desktop oeffnen und warten bis der Daemon bereit ist. Dann erneut versuchen:
```bash
docker info
```

### Problem: `Claude CLI nicht gefunden`

**Ursache:** Die Claude Code CLI ist nicht installiert oder nicht im PATH.

**Loesung:**
```bash
npm install -g @anthropic-ai/claude-code
which claude
```

Falls `which claude` keinen Pfad zurueckgibt, muss der npm-Bin-Ordner zum PATH hinzugefuegt werden.

### Problem: `Sandbox-Image baut nicht (nuclei Download schlaegt fehl)`

**Ursache:** Netzwerkproblem oder falsche Architektur (arm64 vs. amd64).

**Loesung:** Die Architektur im `docker/sandbox/Dockerfile` pruefen. Fuer Intel/AMD-Systeme muss `linux_arm64` durch `linux_amd64` ersetzt werden:
```dockerfile
ARG NUCLEI_VERSION=3.3.7
RUN wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_amd64.zip" ...
```

### Problem: `Scope-Verletzung: Ziel 'x.x.x.x' ist nicht in der Whitelist`

**Ursache:** Das Scan-Ziel ist nicht in `SENTINEL_ALLOWED_TARGETS` eingetragen.

**Loesung:** In der `.env`-Datei das Ziel hinzufuegen:
```bash
SENTINEL_ALLOWED_TARGETS=10.10.10.0/24,scanme.nmap.org
```

### Problem: Unit-Tests schlagen fehl

**Loesung:**
```bash
# Sicherstellen dass Dev-Abhaengigkeiten installiert sind
pip install -e ".[dev]"

# Tests ausfuehren
python -m pytest tests/unit/ -v
```

### Problem: `SENTINEL_LLM_PROVIDER` Validierungsfehler

**Ursache:** Ungueltiger Provider-Wert in `.env`.

**Loesung:** Nur diese Werte sind erlaubt: `claude-abo`, `claude`, `azure`, `ollama`.
