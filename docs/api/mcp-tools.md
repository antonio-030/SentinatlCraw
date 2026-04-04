# MCP-Tools API-Dokumentation

- **Autor:** Jaciel Antonio Acea Ruiz
- **Datum:** 2026-04-04
- **Status:** Aktuell
- **Server:** SentinelClaw MCP-Server (FastMCP)

---

## Uebersicht

Der SentinelClaw MCP-Server exponiert 4 Tools ueber das Model Context Protocol (MCP). Alle Tools laufen isoliert im Docker-Sandbox-Container. Jeder Aufruf durchlaeuft den Scope-Validator (7 Checks) und wird im Audit-Log protokolliert.

| Tool | Zweck | Backend | Eskalationsstufe |
|---|---|---|---|
| `port_scan` | Port-Scanning und Service-Erkennung | nmap | 1 (aktiv) |
| `vuln_scan` | Vulnerability-Scanning | nuclei | 2 (Vuln-Check) |
| `exec_command` | Freie Befehlsausfuehrung in der Sandbox | nmap, nuclei | abhaengig vom Binary |
| `parse_output` | Parsing von Scan-Rohdaten | lokal (kein Docker) | keine |

---

## Tool 1: port_scan

Fuehrt einen nmap Port-Scan auf dem Ziel durch. Scannt die angegebenen Ports und identifiziert laufende Services und deren Versionen. Die nmap-Ausgabe wird als XML geparsed und als strukturiertes JSON zurueckgegeben.

### Parameter

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `target` | `string` | ja | -- | IP-Adresse, CIDR-Range oder Domain des Ziels. Komma-separierte Ziele sind erlaubt (z.B. `10.10.10.3,10.10.10.5`). |
| `ports` | `string` | nein | `1-1000` | Port-Range. Formate: Einzelport (`80`), Liste (`80,443,8080`), Bereich (`1-1000`), gemischt (`22,80,443,8000-8100`). |
| `flags` | `string` | nein | `-sV` | nmap-Flags als komma-separierter String. Nur Flags aus der Allowlist werden akzeptiert. |

### Erlaubte nmap-Flags

```
-sn, -sS, -sT, -sV, -sC, -sU,
-O, -A, -Pn, -p, -oX, -oN, -oG,
--top-ports, --open, --reason, --version-intensity,
-T0, -T1, -T2, -T3, -T4
```

Alle anderen Flags werden mit einem Validierungsfehler abgelehnt. Insbesondere sind `--script`, `-iL`, `--interactive` und aehnliche blockiert.

### Rueckgabeformat

```json
{
  "hosts": [
    {
      "address": "45.33.32.156",
      "hostname": "scanme.nmap.org",
      "ports": [
        {
          "port": 22,
          "protocol": "tcp",
          "state": "open",
          "service": "ssh",
          "version": "OpenSSH 6.6.1p1"
        },
        {
          "port": 80,
          "protocol": "tcp",
          "state": "open",
          "service": "http",
          "version": "Apache httpd 2.4.7"
        }
      ]
    }
  ],
  "summary": "1 Hosts, 2 offene Ports",
  "duration_seconds": 12.3
}
```

### Beispielaufruf

```python
# MCP-Tool-Aufruf (vom Agent ueber MCP-Protokoll)
result = await mcp.call_tool("port_scan", {
    "target": "scanme.nmap.org",
    "ports": "22,80,443",
    "flags": "-sV,-sC"
})
```

### Ablauf intern

1. `validate_target()` -- Prueft auf gueltige IP/CIDR/Domain, blockiert Shell-Metazeichen
2. `validate_ports()` -- Prueft Port-Range (1--65535), Format-Validierung
3. `validate_nmap_flags()` -- Prueft jedes Flag gegen die Allowlist
4. `ScopeValidator.validate()` -- 7 Scope-Checks (Target, Port, Eskalation, etc.)
5. Befehl wird als Liste zusammengebaut: `["nmap", "-sV", "-sC", "-p", "22,80,443", "-oX", "-", "scanme.nmap.org"]`
6. `SandboxExecutor.execute()` -- Fuehrt den Befehl via Docker-API im Container aus
7. nmap-XML wird geparsed und als JSON zurueckgegeben

---

## Tool 2: vuln_scan

Fuehrt einen nuclei Vulnerability-Scan auf dem Ziel durch. Prueft das Ziel anhand von Template-Kategorien auf bekannte Schwachstellen. Die nuclei-Ausgabe im JSONL-Format wird geparsed und als strukturiertes JSON mit Severity-Zusammenfassung zurueckgegeben.

### Parameter

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `target` | `string` | ja | -- | IP-Adresse oder Domain des Ziels. |
| `templates` | `string` | nein | `cves,vulnerabilities` | Komma-separierte Template-Kategorien. |

### Erlaubte Template-Kategorien

```
cves, vulnerabilities, misconfiguration,
default-logins, exposures, technologies
```

Andere Kategorien werden mit einem Validierungsfehler abgelehnt.

### Rueckgabeformat

```json
{
  "findings": [
    {
      "name": "Apache HTTP Server Path Traversal",
      "severity": "critical",
      "host": "http://45.33.32.156",
      "port": 80,
      "cve_id": "CVE-2021-41773",
      "description": "A path traversal vulnerability in Apache HTTP Server 2.4.49...",
      "matched_at": "http://45.33.32.156:80"
    },
    {
      "name": "HTTP Missing HSTS Header",
      "severity": "info",
      "host": "http://45.33.32.156",
      "port": 80,
      "cve_id": null,
      "description": "The HTTP Strict-Transport-Security header is not set...",
      "matched_at": "http://45.33.32.156:80"
    }
  ],
  "severity_counts": {
    "critical": 1,
    "info": 1
  },
  "summary": "2 Findings gefunden",
  "duration_seconds": 28.7
}
```

### Beispielaufruf

```python
result = await mcp.call_tool("vuln_scan", {
    "target": "10.10.10.5",
    "templates": "cves,vulnerabilities,misconfiguration"
})
```

### Ablauf intern

1. `validate_target()` -- Prueft auf gueltige IP/Domain
2. `validate_nuclei_templates()` -- Prueft Template-Kategorien gegen Allowlist
3. `ScopeValidator.validate()` -- 7 Scope-Checks (Tool `nuclei` erfordert Eskalationsstufe 2)
4. Befehl wird zusammengebaut: `["nuclei", "-u", "10.10.10.5", "-t", "cves,vulnerabilities,misconfiguration", "-jsonl", "-silent", "-no-color", "-severity", "critical,high,medium,low,info"]`
5. `SandboxExecutor.execute()` -- Ausfuehrung im Docker-Container
6. JSONL-Ausgabe wird zeilenweise geparsed, CVE-IDs und Referenzen extrahiert
7. Findings werden nach Schweregrad sortiert (Critical zuerst)

---

## Tool 3: exec_command

Fuehrt einen Befehl in der isolierten Sandbox aus. Dieses Tool bietet direkten Zugriff auf die Sandbox fuer Faelle, in denen die spezialisierten Tools (`port_scan`, `vuln_scan`) nicht ausreichen. Strenge Sicherheitsvalidierung: Nur Binaries aus der Allowlist werden akzeptiert.

### Parameter

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `command` | `string` | ja | -- | Der auszufuehrende Befehl als String (wird intern in Teile gesplittet). |
| `timeout` | `integer` | nein | `60` | Maximale Ausfuehrungszeit in Sekunden. Wird auf maximal 600 Sekunden begrenzt. |

### Erlaubte Binaries

Nur diese Binaries duerfen ausgefuehrt werden:

```
nmap, nuclei
```

Jede andere Binary wird mit einem `PermissionError` abgelehnt. Es gibt keinen Weg, diese Einschraenkung zu umgehen -- die Pruefung erfolgt sowohl im `exec_command`-Tool als auch im `SandboxExecutor`.

### Rueckgabeformat

```json
{
  "stdout": "Starting Nmap 7.80 ( https://nmap.org ) ...\nHost is up (0.023s latency).\n...",
  "stderr": "",
  "exit_code": 0,
  "duration_seconds": 5.2,
  "timed_out": false
}
```

Bei einer Scope-Verletzung:

```json
{
  "error": "Binary 'curl' nicht erlaubt. Nur: nmap, nuclei",
  "blocked": true
}
```

### Beispielaufruf

```python
# Host Discovery mit nmap Ping-Scan
result = await mcp.call_tool("exec_command", {
    "command": "nmap -sn 10.10.10.0/24",
    "timeout": 120
})

# Nuclei mit spezifischen Optionen
result = await mcp.call_tool("exec_command", {
    "command": "nuclei -u https://10.10.10.5 -t cves -severity critical,high -jsonl -silent",
    "timeout": 300
})
```

### Ablauf intern

1. Befehl wird in Teile gesplittet (`command.split()`)
2. Binary (erstes Element) wird gegen `ALLOWED_SANDBOX_BINARIES` geprueft
3. Ziel-IPs und Domains werden aus den Argumenten extrahiert (Regex fuer IPv4, CIDR, Domain)
4. Jedes extrahierte Ziel wird durch den `ScopeValidator` geprueft
5. Timeout wird auf maximal 600 Sekunden begrenzt
6. `SandboxExecutor.execute()` -- Befehl wird via Docker-API ausgefuehrt
7. stdout, stderr, Exit-Code und Dauer werden zurueckgegeben

### Ziel-Extraktion aus Befehlsargumenten

Das Tool erkennt automatisch Scan-Ziele in den Befehlsargumenten:

- IPv4-Adressen: `10.10.10.5`
- CIDR-Ranges: `10.10.10.0/24`
- Domains: `scanme.nmap.org`

Flags und deren Werte (z.B. `-p 80`, `-oX output.xml`, `-t cves`) werden dabei uebersprungen.

---

## Tool 4: parse_output

Parst Scan-Rohdaten in strukturiertes JSON. Dieses Tool laeuft rein lokal (kein Docker, kein Netzwerk). Es wird verwendet, um die Rohausgabe von nmap oder nuclei nachtraeglich zu analysieren.

### Parameter

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| `raw_output` | `string` | ja | -- | Rohe Scan-Ausgabe (nmap-XML, nuclei-JSONL oder Plaintext). |
| `output_format` | `string` | nein | `nmap_xml` | Format der Eingabe. |

### Unterstuetzte Formate

| Format | Beschreibung | Eingabeformat |
|---|---|---|
| `nmap_xml` | nmap XML-Ausgabe (`-oX -`) | XML mit `<host>`, `<port>`, `<service>` Elementen |
| `nuclei_jsonl` | nuclei JSONL-Ausgabe (`-jsonl`) | Eine JSON-Zeile pro Finding |
| `plaintext` | Unstrukturierter Text | Beliebiger Text, wird zeilenweise zurueckgegeben |

Bei einem Parse-Fehler (z.B. ungueltiges XML) wird automatisch auf den `plaintext`-Parser zurueckgefallen.

### Rueckgabeformat (nmap_xml)

```json
{
  "format": "nmap_xml",
  "data": [
    {
      "address": "45.33.32.156",
      "hostname": "scanme.nmap.org",
      "ports": [
        {
          "port": 22,
          "protocol": "tcp",
          "state": "open",
          "service": "ssh",
          "version": "OpenSSH 6.6.1p1"
        }
      ]
    }
  ],
  "summary": "1 Hosts aktiv, 1 offene Ports"
}
```

### Rueckgabeformat (nuclei_jsonl)

```json
{
  "format": "nuclei_jsonl",
  "data": [
    {
      "template_id": "CVE-2021-41773",
      "name": "Apache HTTP Server Path Traversal",
      "severity": "critical",
      "description": "A path traversal vulnerability...",
      "host": "http://45.33.32.156",
      "matched_at": "http://45.33.32.156:80",
      "cve_id": "CVE-2021-41773"
    }
  ],
  "severity_counts": {
    "critical": 1
  },
  "summary": "1 Findings: 1x critical"
}
```

### Rueckgabeformat (plaintext)

```json
{
  "format": "plaintext",
  "data": [
    "Starting Nmap 7.80 ( https://nmap.org )",
    "Host is up (0.023s latency).",
    "PORT   STATE SERVICE",
    "22/tcp open  ssh",
    "80/tcp open  http"
  ],
  "summary": "5 Zeilen Ausgabe"
}
```

### Beispielaufruf

```python
# nmap-XML parsen
result = await mcp.call_tool("parse_scan_output", {
    "raw_output": "<nmaprun>...</nmaprun>",
    "output_format": "nmap_xml"
})

# nuclei-JSONL parsen
result = await mcp.call_tool("parse_scan_output", {
    "raw_output": '{"template-id":"CVE-2021-41773","info":{"name":"Apache Path Traversal","severity":"critical"}}\n',
    "output_format": "nuclei_jsonl"
})

# Plaintext-Fallback
result = await mcp.call_tool("parse_scan_output", {
    "raw_output": "PORT   STATE SERVICE\n22/tcp open  ssh\n80/tcp open  http\n",
    "output_format": "plaintext"
})
```

---

## Sicherheitsmechanismen (alle Tools)

### Scope-Validierung

Jeder Aufruf von `port_scan`, `vuln_scan` und `exec_command` durchlaeuft den Scope-Validator mit 7 Checks:

1. **target_in_scope** -- Ziel muss in `targets_include` enthalten sein
2. **target_not_excluded** -- Ziel darf nicht in `targets_exclude` stehen
3. **target_not_forbidden** -- Ziel darf nicht in verbotenen Ranges liegen (127.0.0.0/8, 169.254.0.0/16, 224.0.0.0/4)
4. **port_in_scope** -- Port muss im erlaubten Bereich liegen
5. **time_window** -- Aktuelle Zeit muss im Scan-Fenster liegen
6. **escalation_level** -- Tool-Stufe darf die konfigurierte Max-Stufe nicht ueberschreiten
7. **tool_allowed** -- Tool muss in der Allowlist sein (falls gesetzt)

Bei einer Verletzung wird ein `PermissionError` geworfen und der Aufruf im Log protokolliert.

### Input-Validierung

- Targets: IPv4, IPv6, CIDR, FQDN. Shell-Metazeichen (`;|&$` etc.) werden blockiert.
- Ports: 1--65535, Formate mit Komma und Bindestrich.
- nmap-Flags: Nur explizit erlaubte Flags (Allowlist, keine Blocklist).
- nuclei-Templates: Nur erlaubte Kategorien.

### Sandbox-Isolation

Alle Tool-Aufrufe (ausser `parse_output`) laufen im gehaerteten Docker-Container:

- `cap_drop: ALL`, nur `NET_RAW` fuer nmap SYN-Scans
- Read-only Filesystem
- Non-root User `scanner`
- PID-Limit: 100
- Separates Docker-Netzwerk

### Audit-Logging

Jeder Tool-Aufruf wird in der SQLite-Datenbank (`audit_logs` Tabelle) protokolliert mit Zeitstempel, Tool-Name, Parametern und Ergebnis.
