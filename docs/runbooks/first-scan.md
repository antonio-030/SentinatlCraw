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

## Scan starten (API)

Scans werden ueber die REST-API oder die Web-UI gestartet.

### Einfacher Recon-Scan

```bash
curl -X POST http://localhost:8080/api/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "ports": "22,80,443",
    "level": 2,
    "disclaimerAccepted": true
  }'
```

| Parameter | Default | Beschreibung |
|---|---|---|
| `target` | *(Pflicht)* | Scan-Ziel: IP-Adresse, CIDR-Range oder Domain |
| `ports` | `1-1000` | Port-Range: Einzelports (`80,443`) oder Bereiche (`1-1000`) |
| `level` | `2` | Eskalationsstufe: 0 (passiv), 1 (aktiv), 2 (Vuln-Checks) |
| `disclaimerAccepted` | `false` | Rechtlichen Hinweis bestaetigen (Pflicht) |

### Orchestrierter Scan (Mehrphasen)

```bash
curl -X POST http://localhost:8080/api/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target": "scanme.nmap.org",
    "ports": "22,80,443",
    "scanType": "full",
    "disclaimerAccepted": true
  }'
```

| Parameter | Default | Beschreibung |
|---|---|---|
| `target` | *(Pflicht)* | Scan-Ziel |
| `ports` | `1-1000` | Port-Range |
| `scanType` | `recon` | Scan-Typ: `recon`, `vuln` oder `full` |
| `disclaimerAccepted` | `false` | Rechtlichen Hinweis bestaetigen (Pflicht) |

Der orchestrierte Scan erstellt einen Scan-Plan und fuehrt mehrere Phasen aus:
1. Host Discovery
2. Port-Scan mit Service-Erkennung
3. Vulnerability-Scan (bei Typ `vuln` oder `full`)
4. Executive Summary und Empfehlungen

---

## Ablauf eines Scans

### 1. Rechtlicher Hinweis

Beim Start muss der rechtliche Disclaimer bestaetigt werden. In der Web-UI geschieht dies ueber ein Bestaetigungsdialog. Ueber die API muss `disclaimerAccepted: true` gesetzt werden.

```
WARNUNG: Dieses Tool darf ausschliesslich fuer autorisierte
Sicherheitsueberpruefungen eingesetzt werden. (StGB §202a-c)
```

Ohne Bestaetigungen (`disclaimerAccepted: true`) wird der Scan abgelehnt.

### 2. Scan-Ausfuehrung

Der Agent arbeitet autonom. Der Scan-Status kann ueber die API abgefragt werden:

```bash
curl -s http://localhost:8080/api/scans/<scan-id> \
  -H "Authorization: Bearer $SENTINEL_TOKEN"
```

Je nach Ziel und Port-Range dauert ein Scan zwischen 30 Sekunden und 5 Minuten. Waehrend der Ausfuehrung:

- Der Orchestrator erstellt einen Scan-Plan
- Die NemoClaw-Runtime startet Claude im Agent-Modus
- Claude fuehrt nmap/nuclei ueber `docker exec` in der Sandbox aus
- Ergebnisse werden analysiert und zusammengefasst

### 3. Scan-Ergebnis

Ergebnisse sind in der Web-UI unter dem jeweiligen Scan einsehbar. Ueber die API koennen sie als JSON abgerufen werden:

```bash
curl -s http://localhost:8080/api/scans/<scan-id>/results \
  -H "Authorization: Bearer $SENTINEL_TOKEN"
```

Die JSON-Antwort enthaelt:

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
curl -X POST http://localhost:8080/api/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "10.10.10.5", "ports": "80,443,8080,8443", "disclaimerAccepted": true}'
```

### Nur passive Reconnaissance (Stufe 0)

```bash
curl -X POST http://localhost:8080/api/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "10.10.10.5", "level": 0, "disclaimerAccepted": true}'
```

Stufe 0 erlaubt nur passive Tools (whois, dig, host). nmap und nuclei benoetigen mindestens Stufe 1 bzw. 2.

### Vollstaendiger orchestrierter Scan

```bash
curl -X POST http://localhost:8080/api/scans \
  -H "Authorization: Bearer $SENTINEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"target": "10.10.10.5", "ports": "1-65535", "scanType": "full", "disclaimerAccepted": true}'
```

Hinweis: Ein Full-Port-Scan (1--65535) kann mehrere Minuten dauern.

---

## Scan abbrechen

Waehrend ein Scan laeuft, kann er ueber die Web-UI (NOTAUS-Button) oder die API abgebrochen werden:

```bash
curl -X POST http://localhost:8080/api/emergency/kill \
  -H "Authorization: Bearer $SENTINEL_TOKEN"
```

Der Kill-Switch sorgt dafuer, dass der Sandbox-Container gestoppt wird und keine weiteren Befehle ausgefuehrt werden.

Falls der Container haengen bleibt:

```bash
docker kill sentinelclaw-sandbox
docker compose up -d sandbox
```
