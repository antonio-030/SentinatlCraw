# SentinelClaw — Claude Code Regeln

> AI-gestützte Security Assessment Platform — Proof of Concept
> Autor: Jaciel Antonio Acea Ruiz | Status: Entwicklung | Klassifizierung: Vertraulich

## Weiterführende Dokumente

| Dokument | Inhalt |
|---|---|
| [docs/SECURITY_POLICY.md](docs/SECURITY_POLICY.md) | Sicherheitsrichtlinien, Verschlüsselung, DSGVO, OWASP, API-Auth |
| [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Code-Konventionen, Benennungsregeln, Error Handling |
| [docs/FRONTEND_RULES.md](docs/FRONTEND_RULES.md) | React/TS Stack, Components, Accessibility, Frontend-Security |
| [docs/DOCKER_RULES.md](docs/DOCKER_RULES.md) | Container-Standards, Compose, Sandbox-Härtung |
| [docs/DOCUMENTATION_RULES.md](docs/DOCUMENTATION_RULES.md) | ADR-Format, API-Doku, Runbooks, CHANGELOG |
| [docs/RBAC_MODEL.md](docs/RBAC_MODEL.md) | Rollenmodell, Berechtigungsmatrix, Session-Management |
| [docs/COMPLIANCE_MATRIX.md](docs/COMPLIANCE_MATRIX.md) | DSGVO, BSI Grundschutz, ISO 27001 Mapping |
| [docs/OPERATIONS.md](docs/OPERATIONS.md) | Monitoring, Backup, Kosten, Legal, Responsible Disclosure |
| [docs/PENTEST_FRAMEWORK.md](docs/PENTEST_FRAMEWORK.md) | Rules of Engagement, Autorisierung, Tool-Klassifizierung, Legal |
| [docs/AGENT_SAFETY.md](docs/AGENT_SAFETY.md) | Scope Lock, Eskalationskontrolle, Daten-Sanitizing |
| [docs/KILL_SWITCH.md](docs/KILL_SWITCH.md) | 4 Kill-Pfade, Watchdog, Verifizierung — 100% Stopp-Garantie |
| [docs/ABLAUF.md](docs/ABLAUF.md) | Kompletter Ablauf: Installation → Setup → Scan → Report |
| [docs/UI_DESIGN_PLAN.md](docs/UI_DESIGN_PLAN.md) | Design-System, 10 Seiten, Komponenten, Farben, Typografie |
| [docs/AGENT_CHAT_DESIGN.md](docs/AGENT_CHAT_DESIGN.md) | Chat-UI, Interaktionsmodi, Approval-Flow, Multi-Agent, WebSocket |
| [docs/architecture/ADR-001](docs/architecture/ADR-001-nemoclaw-als-agent-runtime.md) | NemoClaw als Agent-Runtime |
| [docs/architecture/ADR-002](docs/architecture/ADR-002-datenbank-persistierung.md) | PostgreSQL als Datenbank |
| [docs/architecture/ADR-003](docs/architecture/ADR-003-llm-provider-strategie.md) | LLM-Provider: Azure OpenAI, Claude, Ollama |

---

## Sprache & Kommunikation

- **Code**: Englisch (Variablen, Funktionen, Klassen, Dateinamen)
- **Kommentare im Code**: Deutsch
- **Dokumentation**: Deutsch (docs/, README, CHANGELOG)
- **Git-Commits**: Deutsch, imperativ ("Füge Recon-Agent hinzu", nicht "Added recon agent")
- **PR-Beschreibungen**: Deutsch

---

## Konfigurierbarkeit — Goldene Regel

> **ALLES wird über die Web-UI konfiguriert. NICHTS ist hardcoded.**

Jeder Wert der das Verhalten des Systems beeinflusst — Tool-Stufen, Eskalationslimits, Timeouts, Whitelists, Provider-Auswahl, Token-Budgets, Rollen, Berechtigungen — wird in der Datenbank gespeichert und ist über die UI änderbar.

**Ausnahmen (wirklich hardcoded, aus Sicherheitsgründen):**
- Die verbotene Aktionsliste (DoS, Ransomware, Massen-Exfiltration) — NIEMALS änderbar
- Der Kill-Switch-Mechanismus — darf nicht deaktiviert werden
- Audit-Log Unveränderbarkeit — kein DELETE, auch nicht durch SYSTEM_ADMIN

Alles andere: **Konfiguration → Datenbank → UI-änderbar → Audit-geloggt**.

---

## Code-Konventionen

### Allgemein
- **Maximale Dateigröße**: 300 Zeilen pro Datei — wird eine Datei größer, muss refactored werden
- **Lesbarer Code**: Kein "cleverer" Code. Kollegen müssen alles auf Anhieb verstehen können
- **Selbstdokumentierender Code**: Variablennamen erklären den Zweck (`scanResult`, nicht `res` oder `x`)
- **Keine Abkürzungen**: `targetAddress` statt `tgtAddr`, `vulnerabilityReport` statt `vulnRpt`
- **Funktionslänge**: Max. 50 Zeilen pro Funktion — sonst aufteilen
- **Verschachtelungstiefe**: Max. 3 Ebenen — bei mehr: Early Returns oder Hilfsfunktionen nutzen

### TypeScript / JavaScript (Frontend & MCP-Server)
- **Strict Mode**: `"strict": true` in tsconfig.json — immer
- **Typen**: Explizite Typen, kein `any` — niemals
- **Imports**: Named Imports bevorzugen, keine Wildcard-Imports (`import * as`)
- **Async/Await**: Statt `.then().catch()` Chains
- **Error Handling**: Typisierte Errors, kein generisches `catch(e)`
- **Enums**: `const enum` oder Union Types statt normaler Enums

### Python (MCP-Server / Tools)
- **Version**: Python 3.12+
- **Type Hints**: Pflicht für alle Funktionen und Parameter
- **Docstrings**: Google-Style, auf Deutsch
- **Formatter**: Black (Zeilenlänge 100)
- **Linter**: Ruff
- **Imports**: Absolute Imports, sortiert via isort

### Namenskonventionen
| Element | Konvention | Beispiel |
|---|---|---|
| Dateien | kebab-case | `recon-agent.ts` |
| Klassen | PascalCase | `ReconAgent` |
| Funktionen | camelCase (TS) / snake_case (Python) | `runPortScan()` / `run_port_scan()` |
| Konstanten | UPPER_SNAKE_CASE | `MAX_SCAN_TIMEOUT` |
| Typen/Interfaces | PascalCase mit Präfix | `ScanResult`, `AgentConfig` |
| Umgebungsvariablen | UPPER_SNAKE_CASE mit Prefix | `SENTINEL_API_KEY` |
| CSS-Klassen | kebab-case (BEM wenn nötig) | `scan-result__header` |

---

## Architektur-Regeln

### Schichtenmodell
```
[Web-UI / CLI] → [Orchestrator-Agent] → [Sub-Agenten] → [MCP-Server] → [Sandbox-Container]
```

- **Kein Layer-Skipping**: UI spricht NIE direkt mit MCP-Server oder Tools
- **Dependency Direction**: Immer von oben nach unten, nie umgekehrt
- **Shared Code**: Nur über `src/shared/` — keine relativen Imports über Modulgrenzen

### Modulgrenzen
- Jedes Modul (`orchestrator`, `agents/*`, `mcp-server`, `sandbox`) ist eigenständig
- Kommunikation zwischen Modulen NUR über definierte Interfaces in `src/shared/types/`
- Keine zirkulären Abhängigkeiten — wird im CI geprüft

### Konfiguration
- Alle Konfigurationswerte über Umgebungsvariablen oder Config-Dateien in `configs/`
- KEINE hardcodierten Werte im Code (Ports, URLs, Timeouts, Limits)
- Defaults immer in einer zentralen `src/shared/constants/defaults.ts`

---

## Sicherheitsregeln (KRITISCH)

> SentinelClaw ist ein Security-Tool. Der Code selbst MUSS vorbildlich sicher sein.

### Secrets & Credentials
- **NIEMALS** API-Keys, Passwörter oder Tokens im Code oder in Konfigurationsdateien
- Alle Secrets über Umgebungsvariablen (`SENTINEL_*` Prefix)
- `.env` Dateien sind in `.gitignore` — ausnahmslos
- `.env.example` mit Platzhaltern wird committed

### Input Validation
- **Jede externe Eingabe** wird validiert — keine Ausnahme
- Scan-Ziele: Validierung gegen IP-Regex und Domain-Format
- Tool-Parameter: Schema-Validierung via Zod (TS) oder Pydantic (Python)
- SQL Injection, XSS, Command Injection: Selbst wenn "intern" — immer sanitizen

### Sandbox & Isolation
- Tool-Ausführung NUR im Docker-Container — nie auf dem Host
- Container haben KEINEN Zugriff auf Host-Filesystem (außer definierte Volumes)
- Netzwerk-Whitelist: Container erreichen NUR freigegebene Ziele
- Container laufen als non-root User
- Timeouts für JEDEN Tool-Aufruf — keine endlos laufenden Prozesse

### Command Execution
- **KEIN** direktes `exec()` oder `subprocess.run()` mit User-Input
- Alle Commands über parametrisierte MCP-Tool-Aufrufe
- Shell-Injection verhindern: Keine String-Konkatenation für Commands
- Allowlist für erlaubte Binaries: `nmap`, `nuclei` — sonst nichts

### Logging & Audit
- Alle Tool-Aufrufe werden geloggt (Zeitstempel, Tool, Parameter, Ergebnis)
- Keine Secrets in Logs — PII und Credentials werden maskiert
- Log-Level: DEBUG, INFO, WARN, ERROR — konfigurierbar
- Logs bleiben lokal — kein externer Log-Service im PoC

### Dependency Security
- Keine Packages mit bekannten CVEs — `npm audit` / `pip audit` im CI
- Minimale Dependencies: Nur was wirklich gebraucht wird
- Lock-Files (`package-lock.json`, `poetry.lock`) werden committed
- Regelmäßiger Dependency-Review

---

## Docker-Regeln

### Images
- Offizielle Basis-Images verwenden (z.B. `python:3.12-slim`, `node:20-alpine`)
- Multi-Stage Builds für Production-Images
- Keine `latest` Tags — immer versioniert pinnen
- Image-Größe minimieren: nur benötigte Packages installieren

### Dockerfiles
- Ein `Dockerfile` pro Service in `docker/<service>/`
- `.dockerignore` für jedes Image — kein `node_modules`, kein `.git`
- `HEALTHCHECK` für jeden Service
- Non-root `USER` Directive — immer

### Compose
- `docker-compose.yml` im Projektroot
- Netzwerk-Isolation: Eigenes Bridge-Network für SentinelClaw
- Resource Limits (CPU, Memory) für jeden Container
- Restart Policy: `unless-stopped` für Services

### Sandbox-Container spezifisch
- `--cap-drop=ALL` + nur benötigte Capabilities (`NET_RAW` für nmap)
- Read-only Filesystem wo möglich
- Keine privilegierten Container — niemals
- Netzwerk-Policy: Nur Whitelist-Ziele erreichbar

---

## Frontend-Regeln (zukünftige Web-UI)

> Im PoC gibt es keine UI. Diese Regeln gelten für die spätere Produktentwicklung.

### Tech Stack
- **Framework**: React 18+ mit TypeScript
- **State Management**: Zustand oder React Query — kein Redux
- **Styling**: Tailwind CSS — kein CSS-in-JS
- **Components**: Funktionale Components mit Hooks — keine Class Components
- **Build**: Vite

### Component-Regeln
- Eine Component pro Datei
- Max. 200 Zeilen pro Component — sonst aufteilen
- Props immer als Interface typisiert
- Keine Business-Logik in Components — auslagern in Hooks oder Services
- Barrel Exports (`index.ts`) pro Feature-Ordner

### Accessibility
- Semantische HTML-Elemente (`<nav>`, `<main>`, `<button>`)
- ARIA-Labels wo nötig
- Keyboard-Navigation für alle interaktiven Elemente
- Farbkontrast: WCAG 2.1 AA Minimum

### Browser-Kompatibilität
- Aktuelle Version + 1 zurück: Chrome, Firefox, Edge, Safari
- Kein Internet Explorer Support

---

## Dokumentations-Regeln

### Code-Dokumentation
- **Deutsche Kommentare** im Code — erklären das WARUM, nicht das WAS
- JSDoc/Docstrings für alle öffentlichen Funktionen
- Komplexe Algorithmen: Block-Kommentar mit Erklärung VOR der Implementierung
- TODO-Kommentare: Immer mit Ticket-Referenz (`// TODO(SC-42): ...`)

### Projekt-Dokumentation (in `docs/`)
- `docs/architecture/` — Architektur-Entscheidungen (ADRs)
- `docs/api/` — API-Dokumentation für MCP-Server
- `docs/runbooks/` — Betriebsanleitungen (Setup, Deployment, Troubleshooting)
- Jedes Dokument hat Header: Titel, Autor, Datum, Status

### ADR-Format (Architecture Decision Records)
```markdown
# ADR-001: [Titel der Entscheidung]
- **Status**: Akzeptiert | Abgelehnt | Ersetzt
- **Datum**: YYYY-MM-DD
- **Kontext**: Warum stand diese Entscheidung an?
- **Entscheidung**: Was wurde entschieden?
- **Alternativen**: Was wurde verworfen und warum?
- **Konsequenzen**: Was folgt daraus?
```

### README-Struktur
Jedes Modul hat eine eigene `README.md` mit:
1. Was macht dieses Modul?
2. Wie wird es gestartet?
3. Welche Umgebungsvariablen braucht es?
4. Welche Dependencies hat es?

### CHANGELOG
- Format: [Keep a Changelog](https://keepachangelog.com/de/)
- Kategorien: Hinzugefügt, Geändert, Behoben, Entfernt, Sicherheit
- Jeder Eintrag mit Datum und Versionsnummer

---

## Git-Regeln

### Branching
- `main` — stabiler Stand, immer deploybar
- `develop` — Integrationsbranch
- `feature/SC-XX-beschreibung` — Feature-Branches
- `fix/SC-XX-beschreibung` — Bugfix-Branches
- `chore/beschreibung` — Maintenance

### Commits
- Deutsche Commit-Messages im Imperativ
- Format: `[Bereich] Kurzbeschreibung` (max. 72 Zeichen)
- Beispiel: `[MCP-Server] Füge port_scan Tool hinzu`
- Body optional für Details — Warum, nicht Was
- Ein Commit = eine logische Änderung

### Pull Requests
- Jeder PR braucht mindestens eine Beschreibung
- PR-Template wird genutzt (`.github/PULL_REQUEST_TEMPLATE.md`)
- Kein Force-Push auf `main` oder `develop`

---

## Testing-Regeln

### Allgemein
- Kein Code ohne Tests in Production-Modulen
- Test-Dateien neben dem Code: `scan-runner.ts` → `scan-runner.test.ts`
- Oder zentral in `tests/` mit gleicher Ordnerstruktur

### Testarten
| Art | Wo | Was |
|---|---|---|
| Unit Tests | `tests/unit/` | Einzelne Funktionen, isoliert |
| Integration Tests | `tests/integration/` | Modul-Zusammenspiel, MCP-Calls |
| E2E Tests | `tests/e2e/` | Kompletter Scan-Durchlauf |

### Namenskonvention
- Testdateien: `*.test.ts` / `*_test.py`
- Describe-Blöcke: Deutsch, beschreiben das Feature
- Test-Cases: `sollte [erwartetes Verhalten] wenn [Bedingung]`

---

## CI/CD-Regeln (vorbereitet für spätere Pipeline)

- Lint + Type-Check bei jedem Push
- Tests bei jedem PR
- Security Audit (`npm audit`, `pip audit`) wöchentlich
- Docker Image Build + Scan bei Release
- Keine Deployments ohne grüne Pipeline

---

## Implementierungsregeln (KRITISCH)

> **Keine halben Sachen. Keine Platzhalter. Kein Fake-Code.**

### Wenn Code geschrieben wird, dann richtig:
- **Keine Platzhalter-Funktionen** — kein `// TODO: implementieren`, kein `return null`, kein `throw new Error("not implemented")`
- **Keine Mock-Daten als Ersatz für echte Logik** — wenn eine Funktion geschrieben wird, funktioniert sie
- **Keine leeren Interfaces oder Stub-Klassen** — jedes Interface hat eine echte Implementierung
- **Jede Funktion ist vollständig** — Validierung, Error-Handling, Logging, Return-Wert
- **API-Endpoints sind komplett** — Request-Validierung, Business-Logik, Response-Format, Error-Responses
- **Frontend-Components sind komplett** — State, Events, Loading-States, Error-States, Edge-Cases
- **Lieber WENIGER bauen, aber das dann RICHTIG** — ein funktionierender Endpoint ist besser als 10 Stubs

### Full-Stack Qualität:
- **Frontend**: React + TypeScript, echte Components mit State, echte API-Anbindung, echte Fehlerbehandlung
- **Backend API**: REST-Endpoints mit Validierung (Zod), Auth-Middleware, typisierte Responses
- **MCP-Server**: Echte Tool-Implementierungen die echte Commands ausführen
- **Datenbank**: Echte Queries, echte Migrationen, echte Transaktionen
- **Docker**: Funktionierende Dockerfiles, getestete Compose-Konfiguration
- **Tests**: Echte Tests die echte Logik testen, nicht `expect(true).toBe(true)`

### Was NICHT akzeptiert wird:
```typescript
// VERBOTEN — Platzhalter
async function runScan(target: string): Promise<ScanResult> {
  // TODO: Scan-Logik implementieren
  return {} as ScanResult;
}

// VERBOTEN — Fake-Daten
function getFindings(): Finding[] {
  return [{ id: "1", title: "Test Finding" }]; // Hardcoded Fake
}

// VERBOTEN — Leere Fehlerbehandlung
try { await doSomething(); } catch {}
```

---

## Verbotene Praktiken (Absolute No-Gos)

1. **Kein `any` in TypeScript** — typisiere es oder lass es
2. **Keine Secrets im Code** — auch nicht "nur für Tests"
3. **Kein `eval()` oder `exec()` mit dynamischem Input**
4. **Keine `console.log` in Production** — nutze den Logger
5. **Keine auskommentierte Code-Blöcke** — Git ist die History
6. **Keine Magic Numbers** — Konstanten mit sprechendem Namen
7. **Keine God-Files** über 300 Zeilen
8. **Keine Copy-Paste Duplikation** — DRY, aber nicht auf Kosten der Lesbarkeit
9. **Keine impliziten Dependencies** — alles in package.json / pyproject.toml
10. **Kein direkter Shell-Zugriff** aus dem Application-Code auf dem Host
11. **Keine Platzhalter-Funktionen oder Stubs** — nur echte, funktionierende Implementierungen
12. **Keine hardcodierten Mock-Daten** als Ersatz für echte Logik
