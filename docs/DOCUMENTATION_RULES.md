# SentinelClaw — Dokumentationsregeln

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026

---

## 1. Grundsatz

Dokumentation ist kein Nachgedanke. Sie wird **zusammen mit dem Code** geschrieben und ist genauso wichtig wie der Code selbst. Undokumentierter Code ist technische Schuld.

### Sprache
- **Dokumentation**: Deutsch
- **Code-Kommentare**: Deutsch
- **API-Referenz**: Deutsch mit englischen Fachbegriffen wo nötig
- **Git-Commits**: Deutsch

---

## 2. Dokumentationsarten

### 2.1 Übersicht

```
docs/
├── architecture/           # Architektur-Entscheidungen (ADRs)
│   ├── ADR-001-*.md
│   └── ADR-002-*.md
├── api/                    # API- und MCP-Tool-Dokumentation
│   ├── mcp-tools.md
│   └── endpoints.md
├── runbooks/               # Betriebsanleitungen
│   ├── setup.md
│   ├── deployment.md
│   └── troubleshooting.md
├── SECURITY_POLICY.md      # Sicherheitsrichtlinien
├── CODING_STANDARDS.md     # Code-Konventionen
├── FRONTEND_RULES.md       # Frontend-Regeln
├── DOCKER_RULES.md         # Docker-Regeln
└── DOCUMENTATION_RULES.md  # Dieses Dokument
```

---

## 3. Architecture Decision Records (ADRs)

### 3.1 Wann wird ein ADR geschrieben?
- Bei jeder **signifikanten technischen Entscheidung**
- Wenn es **mehrere Alternativen** gab und eine gewählt wurde
- Wenn die Entscheidung **schwer rückgängig zu machen** ist
- Wenn zukünftige Entwickler fragen könnten: "Warum wurde das so gemacht?"

### 3.2 ADR-Template

```markdown
# ADR-XXX: [Titel der Entscheidung]

> Status: Vorgeschlagen | Akzeptiert | Abgelehnt | Ersetzt durch ADR-YYY
> Datum: YYYY-MM-DD
> Autor: Name

## Kontext

Was ist die Ausgangssituation? Welches Problem muss gelöst werden?
Welche Rahmenbedingungen und Einschränkungen gibt es?

## Entscheidung

Was wurde entschieden? Kurz und klar formuliert.

## Alternativen

### Alternative A: [Name]
- Vorteile: ...
- Nachteile: ...
- Warum verworfen: ...

### Alternative B: [Name]
- Vorteile: ...
- Nachteile: ...
- Warum verworfen: ...

## Konsequenzen

### Positiv
- Was wird dadurch besser?

### Negativ
- Welche Trade-offs nehmen wir in Kauf?

### Neutral
- Was ändert sich, ist aber weder besser noch schlechter?
```

### 3.3 Nummerierung
- Fortlaufend: `ADR-001`, `ADR-002`, etc.
- Dateiname: `ADR-001-nemoclaw-als-agent-runtime.md`
- Keine Lücken in der Nummerierung

---

## 4. API-Dokumentation

### 4.1 MCP-Tool-Dokumentation
Jedes MCP-Tool wird dokumentiert mit:

```markdown
## Tool: port_scan

### Beschreibung
Führt einen nmap Port-Scan auf dem angegebenen Ziel durch.

### Parameter

| Parameter | Typ | Pflicht | Default | Beschreibung |
|---|---|---|---|---|
| target | string | Ja | — | IP-Adresse oder Domain des Ziels |
| ports | string | Nein | "1-1000" | Port-Range (z.B. "80,443" oder "1-65535") |
| flags | string[] | Nein | ["-sV"] | Zusätzliche nmap-Flags |
| timeout | number | Nein | 300 | Timeout in Sekunden |

### Rückgabe

| Feld | Typ | Beschreibung |
|---|---|---|
| openPorts | PortInfo[] | Liste der gefundenen offenen Ports |
| scanDuration | number | Scan-Dauer in Sekunden |
| targetInfo | TargetInfo | Informationen zum Zielhost |

### Beispiel

Aufruf:
\`\`\`json
{
  "tool": "port_scan",
  "params": {
    "target": "10.10.10.1",
    "ports": "1-1000",
    "flags": ["-sV", "-sC"]
  }
}
\`\`\`

Ergebnis:
\`\`\`json
{
  "openPorts": [
    { "port": 22, "protocol": "tcp", "service": "ssh", "version": "OpenSSH 8.9" },
    { "port": 80, "protocol": "tcp", "service": "http", "version": "nginx 1.24" }
  ],
  "scanDuration": 45,
  "targetInfo": { "hostname": "target.local", "os": "Linux" }
}
\`\`\`

### Fehlerfälle

| Fehler | Ursache | Lösung |
|---|---|---|
| ValidationError | Ungültiges Ziel oder Port-Range | Eingabe prüfen |
| TimeoutError | Scan hat Zeitlimit überschritten | Timeout erhöhen oder Port-Range verkleinern |
| SandboxError | Container nicht erreichbar | Docker-Status prüfen |
```

---

## 5. Runbooks (Betriebsanleitungen)

### 5.1 Aufbau

```markdown
# Runbook: [Titel]

> Zuletzt aktualisiert: YYYY-MM-DD
> Autor: Name

## Voraussetzungen
- Was muss installiert sein?
- Welche Zugänge werden benötigt?

## Schritte
1. Erster Schritt (mit Befehl)
2. Zweiter Schritt
   - Erwartete Ausgabe: ...
3. Dritter Schritt

## Überprüfung
- Wie prüft man, ob alles funktioniert hat?

## Häufige Probleme
| Problem | Ursache | Lösung |
|---|---|---|
| ... | ... | ... |
```

### 5.2 Pflicht-Runbooks
- `setup.md` — Lokale Entwicklungsumgebung einrichten
- `deployment.md` — Docker-Deployment Schritt für Schritt
- `troubleshooting.md` — Bekannte Probleme und Lösungen

---

## 6. Code-Kommentare

### 6.1 Deutsch, nicht Englisch
Alle Kommentare im Code werden auf Deutsch geschrieben:

```typescript
// Validiere die Ziel-IP gegen die Whitelist bevor der Scan gestartet wird.
// Private Netzwerke sind standardmäßig blockiert (siehe SECURITY_POLICY.md).
const isAllowed = validateTargetAgainstWhitelist(target, config.whitelist);
```

### 6.2 Wann kommentieren?

| Situation | Kommentar nötig? | Beispiel |
|---|---|---|
| Nicht-offensichtliche Business-Logik | Ja | "Nuclei Templates werden vor jedem Scan aktualisiert weil..." |
| Workaround für bekannten Bug | Ja | "Workaround für nmap Bug #1234: ..." |
| Sicherheitsentscheidung | Ja | "Raw-Socket ist nötig für SYN-Scan, deshalb NET_RAW" |
| Offensichtlicher Code | Nein | `port = 443` braucht keinen Kommentar |
| Temporärer Code | TODO mit Ticket | `// TODO(SC-15): Timeout konfigurierbar machen` |

### 6.3 Docstrings / JSDoc

**Python (Google Style):**
```python
def run_port_scan(target: str, ports: str = "1-1000") -> ScanResult:
    """Führt einen nmap Port-Scan auf dem Ziel durch.

    Validiert zuerst das Ziel gegen die Whitelist, startet dann
    den Scan im Sandbox-Container mit den angegebenen Parametern.

    Args:
        target: IP-Adresse oder Domain des Scan-Ziels.
        ports: Port-Range im nmap-Format (z.B. "80,443" oder "1-1000").

    Returns:
        ScanResult mit gefundenen Ports und Service-Informationen.

    Raises:
        ValidationError: Wenn das Ziel ungültig oder nicht freigegeben ist.
        SandboxError: Wenn der Container nicht erreichbar ist.
        TimeoutError: Wenn der Scan das Zeitlimit überschreitet.
    """
```

**TypeScript (JSDoc):**
```typescript
/**
 * Führt einen nmap Port-Scan auf dem Ziel durch.
 *
 * Validiert zuerst das Ziel gegen die Whitelist, startet dann
 * den Scan im Sandbox-Container mit den angegebenen Parametern.
 *
 * @param target - IP-Adresse oder Domain des Scan-Ziels
 * @param options - Konfiguration für den Scan
 * @returns ScanResult mit gefundenen Ports und Service-Informationen
 * @throws {ValidationError} Wenn das Ziel ungültig ist
 * @throws {SandboxError} Wenn der Container nicht erreichbar ist
 */
```

---

## 7. README-Standard

### 7.1 Projekt-README (Root)
```markdown
# SentinelClaw

Kurze Beschreibung (1-2 Sätze).

## Schnellstart
Wie man das Projekt in 5 Minuten zum Laufen bringt.

## Architektur
Kurze Übersicht + Link zu docs/architecture/

## Voraussetzungen
- Node.js 20+
- Docker Desktop
- Python 3.12+
- Claude API Key

## Installation
Schritt-für-Schritt Anleitung.

## Entwicklung
Wie man lokal entwickelt und Tests ausführt.

## Dokumentation
Links zu docs/ Unterordnern.

## Lizenz
[Lizenzinformation]
```

### 7.2 Modul-READMEs
Jedes Modul (`src/orchestrator/`, `src/mcp-server/`, etc.) hat eine eigene README mit:
1. Was macht dieses Modul?
2. Wie wird es gestartet?
3. Welche Umgebungsvariablen braucht es?
4. Welche Dependencies hat es?
5. Wie testet man es?

---

## 8. CHANGELOG

### 8.1 Format: Keep a Changelog

```markdown
# Changelog

Alle bemerkenswerten Änderungen an diesem Projekt werden hier dokumentiert.

## [Unveröffentlicht]

### Hinzugefügt
- MCP-Server mit port_scan und vuln_scan Tools (FA-03)

### Geändert
- Timeout für nmap-Scans von 60s auf 300s erhöht

### Behoben
- Sandbox-Container startet jetzt korrekt mit NET_RAW Capability

### Sicherheit
- Input-Validierung für Scan-Ziele hinzugefügt

## [0.1.0] - 2026-04-XX

### Hinzugefügt
- Initiale PoC-Version
- Orchestrator-Agent (FA-01)
- Recon-Agent (FA-02)
- MCP-Server mit 4 Tools (FA-03)
```

### 8.2 Regeln
- Jeder PR aktualisiert den CHANGELOG unter `[Unveröffentlicht]`
- Bei Release: Datum und Versionsnummer eintragen
- Kategorien: Hinzugefügt, Geändert, Behoben, Entfernt, Sicherheit, Veraltet
- Referenz auf Lastenheft-IDs wo relevant (FA-01, FA-02, etc.)
