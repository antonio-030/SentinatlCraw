# SentinelClaw — Agent Safety Framework

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Zweck: Technische Sicherheitsmechanismen die verhindern, dass der Agent Schaden anrichtet

---

## 1. Grundprinzip: Traue dem Agent NICHT

Der KI-Agent ist intelligent, aber nicht unfehlbar. LLMs können:
- **Halluzinieren** — ein Ziel "erfinden" das nicht im Scope ist
- **Übereskalieren** — aggressivere Methoden wählen als erlaubt
- **Scope verlassen** — bei Lateral Movement in nicht-autorisierte Netze abbiegen
- **Fehlinterpretieren** — einen harmlosen Service für verwundbar halten

**Deshalb gilt: Jede kritische Entscheidung des Agents wird von einer nicht-KI-Schicht validiert.**

```
Agent entscheidet         MCP-Server validiert         Netzwerk erzwingt
(kann Fehler machen)  →   (Code-basiert, deterministisch)  →  (physisch)
       SOFT                        HARD                       HARDEST
```

---

## 2. Scope Lock — Der Agent kann den Scope nicht verlassen

### 2.1 Scope-Datenstruktur

```typescript
interface PentestScope {
  // Erlaubte Ziele
  targets: {
    include: CidrRange[];     // ["10.10.10.0/24"]
    exclude: CidrRange[];     // ["10.10.10.1/32"]
  };

  // Erlaubte Ports
  ports: {
    include: PortRange[];     // ["1-65535"]
    exclude: PortRange[];     // ["22"] (SSH nicht anfassen)
  };

  // Zeitfenster
  timeWindow: {
    start: IsoDateTime;
    end: IsoDateTime;
    timezone: string;
  };

  // Maximale Eskalationsstufe (0-4)
  maxEscalationLevel: EscalationLevel;

  // Erlaubte Tools pro Stufe
  allowedTools: Map<EscalationLevel, ToolName[]>;

  // Verbotene Aktionen (absolut, unabhängig von Stufe)
  forbidden: ForbiddenAction[];
}
```

### 2.2 Validierung bei jedem Tool-Aufruf

```python
class ScopeValidator:
    """Validiert JEDEN Tool-Aufruf gegen den definierten Scope.
    
    Wird im MCP-Server aufgerufen — der Agent hat keinen Bypass.
    """

    def validate_tool_request(
        self,
        request: ToolRequest,
        scope: PentestScope
    ) -> ValidationResult:
        """Prüft ob ein Tool-Aufruf im Scope liegt.

        Gibt BLOCK zurück wenn auch nur EINE Prüfung fehlschlägt.
        Es gibt kein 'teilweise erlaubt' — entweder alles ok oder BLOCK.
        """
        checks = [
            self._check_target_in_scope,
            self._check_target_not_excluded,
            self._check_port_in_scope,
            self._check_time_window,
            self._check_escalation_level,
            self._check_tool_allowed,
            self._check_not_forbidden,
        ]

        for check in checks:
            result = check(request, scope)
            if not result.passed:
                # Sofort blockieren + loggen
                self._log_scope_violation(request, result)
                return ValidationResult(
                    allowed=False,
                    reason=result.reason
                )

        return ValidationResult(allowed=True)
```

---

## 3. Eskalationskontrolle

### 3.1 Tool → Stufe Mapping (konfigurierbar über UI)

```python
# Diese Zuordnung wird aus der Datenbank geladen und ist über die
# Web-UI konfigurierbar (Konfiguration → Tools & Eskalationsstufen).
# Nur SYSTEM_ADMIN und ORG_ADMIN können die Zuordnung ändern.
# Jede Änderung wird im Audit-Log protokolliert.
# Default-Werte bei Erstinstallation:
TOOL_ESCALATION_MAP: dict[str, EscalationLevel] = {
    # Stufe 0: Passiv
    "whois":        0,
    "dig":          0,
    "host":         0,

    # Stufe 1: Aktive Scans
    "nmap":         1,
    "whatweb":      1,
    "dirsearch":    1,

    # Stufe 2: Vulnerability Checks
    "nuclei":       2,
    "nikto":        2,
    "sslscan":      2,
    "sqlmap_detect": 2,  # Nur --level 1, keine Exploitation

    # Stufe 3: Exploitation
    "metasploit":   3,
    "sqlmap_exploit": 3,  # Mit --exploit Flag
    "hydra":        3,
    "john":         3,
    "hashcat":      3,

    # Stufe 4: Post-Exploitation
    "mimikatz":     4,
    "linpeas":      4,
    "winpeas":      4,
    "chisel":       4,
}
```

### 3.2 Eskalations-Check

```python
def check_escalation(
    tool_name: str,
    scan_job: ScanJob,
    tool_config: ToolConfigRepository,  # Aus DB laden, über UI konfiguriert
) -> bool:
    """Prüft ob das Tool innerhalb der erlaubten Eskalationsstufe liegt.
    
    Die Tool-Stufen-Zuordnung kommt aus der Datenbank und wird
    über die Web-UI konfiguriert (Konfiguration → Tools).
    """
    tool_entry = tool_config.get_tool(tool_name)
    
    if tool_entry is None or not tool_entry.is_enabled:
        # Unbekanntes oder deaktiviertes Tool → blockieren
        return False
    
    if tool_entry.escalation_level > scan_job.max_escalation_level:
        # Tool ist aggressiver als erlaubt → blockieren
        return False
    
    return True
```

---

## 4. Kill Switch — Technische Umsetzung

### 4.1 Zwei Wege zum Sofort-Stop

```
Weg 1: API (für Web-UI)
────────────────────────────────
POST /api/emergency/kill
Authorization: Bearer <any_valid_token>
→ Kein RBAC-Check. Jeder eingeloggte User darf killen.

Weg 2: Docker (Notfall, kein Login nötig)
────────────────────────────────
$ docker stop $(docker ps -q --filter "label=sentinelclaw.role=sandbox")
```

### 4.2 Was der Kill Switch tut (Reihenfolge)

```python
async def emergency_kill(triggered_by: str, reason: str) -> None:
    """Sofort-Stop aller Aktivitäten. Unumkehrbar für laufende Scans."""

    # 1. Netzwerk sofort sperren (schnellste Wirkung)
    await sandbox_network.disconnect_all()

    # 2. Alle Tool-Prozesse in der Sandbox beenden
    await sandbox.kill_all_processes(signal=SIGKILL)

    # 3. Alle laufenden Scan-Jobs auf ABGEBROCHEN setzen
    await scan_jobs.cancel_all(reason=f"Emergency Kill: {reason}")

    # 4. Sandbox-Container stoppen
    await docker.stop_containers(label="sentinelclaw.role=sandbox")

    # 5. Audit-Log (MUSS auch bei Systemfehler geschrieben werden)
    await audit_log.write_critical(
        action="EMERGENCY_KILL",
        triggered_by=triggered_by,
        reason=reason,
        timestamp=utc_now(),
    )

    # 6. Benachrichtigung an alle Admins
    await notify_admins(
        subject="⚠ SentinelClaw Emergency Kill ausgelöst",
        body=f"Ausgelöst von: {triggered_by}\nGrund: {reason}",
    )
```

---

## 5. Automatische Sicherheits-Stops

### 5.1 Scope-Violation-Counter

```python
class ScopeViolationMonitor:
    """Zählt Scope-Verletzungen und stoppt bei zu vielen."""

    MAX_VIOLATIONS = 3
    WINDOW_SECONDS = 300  # 5 Minuten

    async def on_violation(self, scan_id: str, details: str) -> None:
        """Wird bei jeder Scope-Verletzung aufgerufen."""
        
        self.violations[scan_id].append(utc_now())

        # Alte Einträge aufräumen (außerhalb des Fensters)
        recent = [v for v in self.violations[scan_id]
                  if v > utc_now() - timedelta(seconds=self.WINDOW_SECONDS)]

        if len(recent) >= self.MAX_VIOLATIONS:
            # 3 Verstöße in 5 Minuten → Scan stoppen
            await self.stop_scan(scan_id, reason=(
                f"Automatischer Stop: {len(recent)} Scope-Verletzungen "
                f"in {self.WINDOW_SECONDS}s. Mögliche LLM-Halluzination."
            ))
```

### 5.2 Zeitfenster-Enforcement

```python
class TimeWindowEnforcer:
    """Stoppt Scans die außerhalb des erlaubten Zeitfensters laufen."""

    async def check(self, scan_job: ScanJob) -> None:
        """Wird jede Minute aufgerufen (Cronjob)."""

        now = utc_now()
        if now < scan_job.scope.time_window.start:
            # Noch nicht gestartet → blockieren
            return

        if now > scan_job.scope.time_window.end:
            # Zeitfenster abgelaufen → sofort stoppen
            await self.stop_scan(scan_job.id, reason=(
                f"Zeitfenster abgelaufen: Ende war "
                f"{scan_job.scope.time_window.end.isoformat()}"
            ))
```

### 5.3 System-Stabilitäts-Checks

```python
class TargetHealthMonitor:
    """Überwacht ob das Zielsystem noch reagiert."""

    TIMEOUT_SECONDS = 60
    MAX_RETRIES = 3

    async def check_target_alive(self, target: str) -> bool:
        """Prüft ob das Ziel noch erreichbar ist.
        
        Wenn nicht: Scan pausieren. Zielsystem könnte durch
        unseren Exploit abgestürzt sein.
        """
        for attempt in range(self.MAX_RETRIES):
            if await self.ping(target, timeout=self.TIMEOUT_SECONDS):
                return True
            # Warten bevor nächster Versuch
            await asyncio.sleep(10)

        # Ziel antwortet nicht nach 3 Versuchen
        return False
```

---

## 6. Daten-Schutzschichten vor dem LLM

### 6.1 Was wird NIEMALS an das LLM gesendet

```python
class LlmDataSanitizer:
    """Filtert sensible Daten bevor sie ans LLM gehen."""

    # Pattern die IMMER entfernt werden
    REDACT_PATTERNS = [
        # Passwörter
        r"password[:\s=]+\S+",
        r"passwd[:\s=]+\S+",
        r"pwd[:\s=]+\S+",
        # API Keys
        r"sk-ant-[a-zA-Z0-9_-]+",
        r"api[_-]?key[:\s=]+\S+",
        # Private Keys
        r"-----BEGIN.*PRIVATE KEY-----[\s\S]*?-----END.*PRIVATE KEY-----",
        # Hashes (reduziert, nicht komplett)
        r"\$[0-9a-z]+\$[./a-zA-Z0-9]+\$[./a-zA-Z0-9]+",
        # E-Mail-Adressen
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        # Kreditkartennummern
        r"\b[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}[- ]?[0-9]{4}\b",
    ]

    def sanitize(self, text: str) -> str:
        """Ersetzt alle sensiblen Daten durch [REDACTED]."""
        sanitized = text
        for pattern in self.REDACT_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized)
        return sanitized
```

### 6.2 Datenminimierung: Was der Agent dem LLM zeigt

```
Rohdaten (nmap):      → 2.000 Zeilen XML
Nach Parsing:         → 50 Zeilen JSON (nur offene Ports + Services)
Nach Sanitizing:      → 50 Zeilen JSON, Credentials entfernt
AN DAS LLM:          → 50 Zeilen bereinigtes JSON

Rohdaten (nuclei):    → 500 Zeilen JSON Findings
Nach Parsing:         → 20 Findings (CVE + Severity + Beschreibung)
Nach Sanitizing:      → 20 Findings, PII entfernt
AN DAS LLM:          → 20 bereinigte Findings
```

---

## 7. Agent-Verhalten bei Findings

### 7.1 Entscheidungsbaum des Agents

```
Agent findet Schwachstelle
    │
    ├── Schweregrad: INFORMATIONAL oder LOW
    │   └── Dokumentieren + weiter scannen
    │
    ├── Schweregrad: MEDIUM
    │   └── Dokumentieren + Exploitation versuchen WENN Stufe ≥ 3
    │
    ├── Schweregrad: HIGH
    │   ├── Dokumentieren (sofort in DB)
    │   ├── Exploitation versuchen WENN Stufe ≥ 3
    │   └── Im Report hervorheben
    │
    └── Schweregrad: CRITICAL
        ├── Dokumentieren (sofort in DB)
        ├── Exploitation versuchen WENN Stufe ≥ 3
        ├── SOFORT melden an Notfallkontakt (wenn in RoE konfiguriert)
        └── Im Report als TOP PRIORITY markieren
```

### 7.2 Agent-Grenzen (was er NICHT entscheiden darf)

| Entscheidung | Wer entscheidet | Agent darf NICHT |
|---|---|---|
| Scope erweitern | ORG_ADMIN (Mensch) | Eigenständig neue Ziele hinzufügen |
| Stufe erhöhen | ORG_ADMIN (Mensch) | Von Scan auf Exploit wechseln |
| DoS als Test | NIEMAND | Niemals, auch nicht "zur Prüfung" |
| Daten exfiltrieren | Nur mit expliziter RoE | Datenbanken dumpen |
| Lateral Movement | Nur wenn RoE es erlaubt | Eigenständig zu anderen Hosts springen |
| Backdoor setzen | Nur wenn RoE es zeitlich begrenzt erlaubt | Permanente Backdoors installieren |
| Scan fortsetzen nach Kill | SECURITY_LEAD (Mensch) | Nach Kill eigenständig weitermachen |

---

## 8. Logging-Anforderungen für Exploitation

### 8.1 Jeder Exploit wird detailliert geloggt

```json
{
  "timestamp": "2026-04-14T14:32:00.000Z",
  "event": "EXPLOIT_ATTEMPT",
  "scan_id": "scan-abc-123",
  "agent": "recon-agent-01",
  "target": "10.10.10.5",
  "port": 3306,
  "service": "mysql",
  "tool": "metasploit",
  "module": "exploit/multi/mysql/mysql_udf_payload",
  "escalation_level": 3,
  "scope_check": "PASSED",
  "result": "SUCCESS",
  "proof": "whoami=root, hostname=db-server-01",
  "evidence_hash": "sha256:a1b2c3d4e5f6...",
  "duration_seconds": 12,
  "next_action": "Dokumentieren und zum nächsten Ziel"
}
```

### 8.2 Audit-Log-Integritätsschutz

Exploit-Logs dürfen NICHT manipuliert werden:
- Append-Only: Kein UPDATE, kein DELETE
- Hash-Chain: Jeder Eintrag enthält den Hash des vorherigen
- Zeitstempel: Vom Server, nicht vom Agent
- Backup: Logs werden sofort auf zweites Volume geschrieben
