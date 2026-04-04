# Runbook: Erster Scan

- **Autor:** Jaciel Antonio Acea Ruiz
- **Datum:** 2026-04-04
- **Status:** Aktuell

---

## Voraussetzungen

Bevor ein Scan gestartet werden kann, muessen folgende Punkte erfuellt sein:

- [x] Setup abgeschlossen (siehe [docs/runbooks/setup.md](setup.md))
- [x] `python scripts/verify_m1.py` meldet alle Checks bestanden
- [x] Sandbox-Container laeuft: `docker ps --filter name=sentinelclaw-sandbox` zeigt Status `Up (healthy)`
- [x] `.env` ist konfiguriert mit gueltigem `SENTINEL_ALLOWED_TARGETS`
- [x] Virtuelle Umgebung ist aktiviert: `source .venv/bin/activate`

Sandbox-Status pruefen:

```bash
docker ps --filter name=sentinelclaw-sandbox --format "{{.Names}} {{.Status}}"
```

Erwartete Ausgabe: `sentinelclaw-sandbox Up X minutes (healthy)`

Falls der Container nicht laeuft:

```bash
docker compose up -d sandbox
```

---

## Scan-Befehle

SentinelClaw bietet zwei CLI-Befehle: `scan` (einzelner Recon-Scan) und `orchestrate` (koordinierter Mehrphasen-Scan).

### Einfacher Recon-Scan (`scan`)

```bash
python -m src.cli scan --target scanme.nmap.org --ports 22,80,443 --yes
```

| Parameter | Kurz | Default | Beschreibung |
|---|---|---|---|
| `--target` | `-t` | *(Pflicht)* | Scan-Ziel: IP-Adresse, CIDR-Range oder Domain |
| `--ports` | `-p` | `1-1000` | Port-Range: Einzelports (`80,443`) oder Bereiche (`1-1000`) |
| `--level` | `-l` | `2` | Eskalationsstufe: 0 (passiv), 1 (aktiv), 2 (Vuln-Checks) |
| `--output` | `-o` | `markdown` | Ausgabeformat: `markdown` oder `json` |
| `--yes` | `-y` | *(nicht gesetzt)* | Disclaimer automatisch bestaetigen |

### Orchestrierter Scan (`orchestrate`)

```bash
python -m src.cli orchestrate --target scanme.nmap.org --ports 22,80,443 --type full --yes
```

| Parameter | Kurz | Default | Beschreibung |
|---|---|---|---|
| `--target` | `-t` | *(Pflicht)* | Scan-Ziel |
| `--ports` | `-p` | `1-1000` | Port-Range |
| `--type` | | `recon` | Scan-Typ: `recon`, `vuln` oder `full` |
| `--output` | `-o` | `markdown` | Ausgabeformat: `markdown` oder `json` |
| `--yes` | `-y` | *(nicht gesetzt)* | Disclaimer automatisch bestaetigen |

Der `orchestrate`-Befehl erstellt einen Scan-Plan und fuehrt mehrere Phasen aus:
1. Host Discovery
2. Port-Scan mit Service-Erkennung
3. Vulnerability-Scan (bei Typ `vuln` oder `full`)
4. Executive Summary und Empfehlungen

---

## Ablauf eines Scans

### 1. Rechtlicher Hinweis

Beim Start zeigt SentinelClaw einen rechtlichen Hinweis an:

```
============================================================
  SentinelClaw — Orchestrierter Security-Scan
  Powered by NVIDIA NemoClaw
============================================================

  Ziel:     scanme.nmap.org
  Ports:    22,80,443
  Typ:      recon

  WARNUNG: Dieses Tool darf ausschliesslich fuer autorisierte
     Sicherheitsueberpruefungen eingesetzt werden. (StGB §202a-c)

  Autorisierung bestaetigen? [j/N]:
```

Mit `--yes` wird diese Abfrage uebersprungen. Ohne `--yes` muss `j` oder `ja` eingegeben werden.

### 2. Scan-Ausfuehrung

Der Agent arbeitet autonom. Im Terminal erscheint:

```
  Orchestrator erstellt Scan-Plan...

  Agent arbeitet...
```

Je nach Ziel und Port-Range dauert ein Scan zwischen 30 Sekunden und 5 Minuten. Waehrend der Ausfuehrung:

- Der Orchestrator erstellt einen Scan-Plan
- Die NemoClaw-Runtime startet Claude im Agent-Modus
- Claude fuehrt nmap/nuclei ueber `docker exec` in der Sandbox aus
- Ergebnisse werden analysiert und zusammengefasst

### 3. Scan-Ergebnis (Markdown-Ausgabe)

```
  Scan-Plan:
    OK Phase 1: Host Discovery
    OK Phase 2: Port Scan
    OK Phase 3: Vulnerability Scan

============================================================
  SCAN-ERGEBNIS: scanme.nmap.org
============================================================

  Hosts:           1
  Offene Ports:    3
  Vulnerabilities: 2
  Dauer:           45.3s
  Tokens:          12500

  --- Offene Ports ---
  45.33.32.156:22/tcp   ssh      OpenSSH 6.6.1p1
  45.33.32.156:80/tcp   http     Apache httpd 2.4.7
  45.33.32.156:443/tcp  https    Apache httpd 2.4.7

  --- Vulnerabilities ---
  ROT    CRITICAL  Apache RCE CVE-2024-XXXXX (CVE-2024-XXXXX)
                   45.33.32.156:80
  GELB   MEDIUM    HTTP Missing Security Headers
                   45.33.32.156:80

  --- Executive Summary ---
  ...

  --- Empfehlungen ---
    -> Apache auf aktuelle Version aktualisieren
    -> Security-Header (HSTS, CSP, X-Frame-Options) hinzufuegen
    -> SSH-Key-Authentication erzwingen, Passwort-Login deaktivieren

  Dauer:  47.1s
  Tokens: 13200
```

### 4. JSON-Ausgabe

Fuer maschinelle Weiterverarbeitung:

```bash
python -m src.cli scan --target scanme.nmap.org --ports 22,80,443 --output json --yes
```

Die JSON-Ausgabe enthaelt:

```json
{
  "target": "scanme.nmap.org",
  "hosts": [
    {"address": "45.33.32.156", "hostname": "scanme.nmap.org"}
  ],
  "open_ports": [
    {"host": "45.33.32.156", "port": 22, "service": "ssh", "version": "OpenSSH 6.6.1p1"},
    {"host": "45.33.32.156", "port": 80, "service": "http", "version": "Apache httpd 2.4.7"}
  ],
  "vulnerabilities": [
    {"title": "...", "severity": "critical", "cvss": 9.8, "cve": "CVE-2024-XXXXX", "host": "45.33.32.156"}
  ],
  "summary": {
    "total_hosts": 1,
    "total_open_ports": 3,
    "total_vulnerabilities": 2,
    "severity_counts": {"critical": 1, "medium": 1},
    "duration_seconds": 45.3,
    "tokens_used": 12500
  }
}
```

---

## Audit-Logs pruefen

Alle Scan-Aktivitaeten werden in der SQLite-Datenbank unter `data/sentinelclaw.db` protokolliert. Die Audit-Logs koennen mit einem beliebigen SQLite-Client eingesehen werden:

### Mit sqlite3 (Kommandozeile)

```bash
sqlite3 data/sentinelclaw.db
```

Letzte Audit-Eintraege anzeigen:

```sql
SELECT created_at, action, resource_type, resource_id, details
FROM audit_logs
ORDER BY created_at DESC
LIMIT 10;
```

Erwartete Eintraege nach einem Scan:

| Zeitstempel | Aktion | Ressource | Details |
|---|---|---|---|
| 2026-04-04T... | `scan.started` | scan_job | `{"target": "scanme.nmap.org", "level": 2}` |
| 2026-04-04T... | `scan.completed` | scan_job | `{"hosts": 1, "ports": 3, "vulns": 2, ...}` |

### Scan-Jobs anzeigen

```sql
SELECT id, target, scan_type, status, tokens_used, created_at
FROM scan_jobs
ORDER BY created_at DESC
LIMIT 5;
```

### Findings anzeigen

```sql
SELECT severity, title, target_host, target_port, cve_id
FROM findings
ORDER BY cvss_score DESC;
```

---

## Haeufige Szenarien

### Scan mit begrenzter Port-Range

Nur die gaengigsten Web-Ports scannen (schneller):

```bash
python -m src.cli scan --target 10.10.10.5 --ports 80,443,8080,8443 --yes
```

### Nur passive Reconnaissance (Stufe 0)

```bash
python -m src.cli scan --target 10.10.10.5 --level 0 --yes
```

Stufe 0 erlaubt nur passive Tools (whois, dig, host). nmap und nuclei benoetigen mindestens Stufe 1 bzw. 2.

### Vollstaendiger orchestrierter Scan

```bash
python -m src.cli orchestrate --target 10.10.10.5 --ports 1-65535 --type full --yes
```

Hinweis: Ein Full-Port-Scan (1--65535) kann mehrere Minuten dauern.

---

## Scan abbrechen

Waehrend ein Scan laeuft, kann er mit `Ctrl+C` abgebrochen werden. Der Kill-Switch sorgt dafuer, dass der Sandbox-Container gestoppt wird und keine weiteren Befehle ausgefuehrt werden.

Falls der Container haengen bleibt:

```bash
docker kill sentinelclaw-sandbox
docker compose up -d sandbox
```
