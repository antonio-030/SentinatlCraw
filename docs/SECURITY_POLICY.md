# SentinelClaw — Sicherheitsrichtlinien

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Klassifizierung: VERTRAULICH

---

## 1. Grundsätze

SentinelClaw ist ein offensives Sicherheitstool. Der eigene Code MUSS höchsten Sicherheitsstandards genügen. Ein unsicheres Pentest-Tool ist ein Widerspruch in sich.

### Kernprinzipien
1. **Defense in Depth** — Mehrere Sicherheitsschichten, nie nur eine
2. **Least Privilege** — Jede Komponente hat nur die minimal nötigen Rechte
3. **Zero Trust** — Kein Input wird vertraut, auch nicht von internen Services
4. **Fail Secure** — Bei Fehlern: Abbruch, nicht Weiterarbeit mit Fallback
5. **Audit Everything** — Jede sicherheitsrelevante Aktion wird geloggt

---

## 2. Sandbox-Sicherheit

### 2.1 Container-Isolation
```
┌─────────────────────────────────────────┐
│  Host-System                            │
│  ┌───────────────────────────────────┐  │
│  │  SentinelClaw Application         │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │  Sandbox-Container          │  │  │
│  │  │  - nmap, nuclei             │  │  │
│  │  │  - Kein Host-Zugriff        │  │  │
│  │  │  - Netzwerk-Whitelist       │  │  │
│  │  │  - Read-only Filesystem     │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 2.2 Container-Härtung (Pflichtmaßnahmen)

| Maßnahme | Umsetzung | Priorität |
|---|---|---|
| Capabilities droppen | `--cap-drop=ALL`, nur `NET_RAW` für nmap | MUSS |
| Non-root User | `USER scanner:scanner` im Dockerfile | MUSS |
| Read-only FS | `--read-only` + tmpfs für `/tmp` | MUSS |
| Resource Limits | CPU: 2 Cores, RAM: 2GB, PIDs: 100 | MUSS |
| No Privileged | `--privileged=false` (nie ändern) | MUSS |
| Seccomp-Profil | Default Docker seccomp-Profil aktiv | SOLL |
| AppArmor/SELinux | Profil für Sandbox-Container erstellen | SOLL |

### 2.3 Netzwerk-Policy

```yaml
# Erlaubt:
# - Kommunikation Sandbox ↔ MCP-Server (internes Netz)
# - Verbindung zu Whitelist-Zielen (Scan-Targets)
#
# Verboten:
# - Internetzugriff aus dem Sandbox-Container
# - Zugriff auf Host-Netzwerk
# - Zugriff auf andere Docker-Netzwerke
# - DNS zu externen Resolvern (nur interner DNS)
```

**Whitelist-Prinzip**: Ein Scan-Ziel MUSS vor dem Start explizit freigegeben werden. Der MCP-Server validiert jedes Ziel gegen die Whitelist BEVOR ein Tool gestartet wird.

---

## 3. Input-Validierung

### 3.1 Scan-Ziele
Jedes Scan-Ziel wird vor der Verarbeitung validiert:

- **IP-Adressen**: Muss gültige IPv4/IPv6 sein, NICHT in verbotenen Ranges
- **Domains**: Muss auflösbarer FQDN sein, keine internen Domains
- **Port-Ranges**: Nur 1-65535, keine negativen Werte

### 3.2 Verbotene Scan-Ziele (Blacklist)
Diese Ziele dürfen NIEMALS gescannt werden:
- `127.0.0.0/8` — Localhost
- `10.0.0.0/8` — Privates Netz (außer explizit freigegeben)
- `172.16.0.0/12` — Privates Netz (außer explizit freigegeben)
- `192.168.0.0/16` — Privates Netz (außer explizit freigegeben)
- `169.254.0.0/16` — Link-Local
- Jede Adresse des Host-Systems selbst

> **Ausnahme**: Private Ranges können in der Konfiguration explizit freigeschaltet werden (z.B. für interne Pentests). Dies erfordert eine bewusste Konfigurationsänderung.

### 3.3 Command Injection Prevention

**Verboten:**
```python
# NIEMALS — Command Injection möglich
os.system(f"nmap {user_input}")
subprocess.run(f"nmap {target}", shell=True)
```

**Erlaubt:**
```python
# Parametrisiert — sicher
subprocess.run(["nmap", "-sV", "-p", validated_ports, validated_target],
               shell=False, timeout=300)
```

### 3.4 Tool-Parameter-Validierung
Jeder MCP-Tool-Aufruf wird gegen ein Schema validiert:

```python
# Beispiel: port_scan Parameter-Schema (Pydantic)
class PortScanParams(BaseModel):
    target: ValidatedTarget        # Eigener Typ mit Validierung
    ports: PortRange               # 1-65535, validiert
    flags: list[AllowedNmapFlag]   # Nur erlaubte Flags
    timeout: int = Field(ge=1, le=600)  # Max. 10 Minuten
```

---

## 4. Secret Management

### 4.1 Regeln
1. **Keine Secrets im Quellcode** — niemals, auch nicht auskommentiert
2. **Keine Secrets in Docker-Images** — kein `COPY .env` im Dockerfile
3. **Keine Secrets in Logs** — automatische Maskierung
4. **Keine Secrets in Git-History** — Pre-commit Hook prüft

### 4.2 Umgebungsvariablen

| Variable | Zweck | Beispiel |
|---|---|---|
| `SENTINEL_CLAUDE_API_KEY` | Anthropic API Key | `sk-ant-...` |
| `SENTINEL_ALLOWED_TARGETS` | Whitelist für Scan-Ziele | `10.10.10.0/24` |
| `SENTINEL_LOG_LEVEL` | Log-Verbosity | `INFO` |
| `SENTINEL_SANDBOX_TIMEOUT` | Max. Tool-Laufzeit in Sekunden | `300` |

### 4.3 Pre-Commit Checks
Ein Git Pre-Commit Hook prüft auf:
- API-Keys (Pattern: `sk-ant-`, `sk-proj-`, etc.)
- Private Keys (Pattern: `-----BEGIN.*PRIVATE KEY-----`)
- Passwörter in Config-Dateien
- `.env` Dateien (dürfen nicht committed werden)

---

## 5. Logging & Audit-Trail

### 5.1 Was wird geloggt

| Event | Log-Level | Daten |
|---|---|---|
| Scan gestartet | INFO | Ziel, Zeitstempel, User |
| Tool-Aufruf | INFO | Tool-Name, Parameter (ohne Secrets) |
| Tool-Ergebnis | DEBUG | Gekürzte Ausgabe |
| Validierungsfehler | WARN | Was fehlgeschlagen ist |
| Sicherheitsverstoß | ERROR | Details + Stack Trace |
| Verbotenes Ziel | ERROR | Ziel-Adresse, Grund der Ablehnung |

### 5.2 Was NICHT geloggt wird
- API-Keys oder Tokens
- Vollständige Scan-Rohdaten (nur Zusammenfassung)
- Persönliche Daten von Zielsystemen (PII)

### 5.3 Log-Format
```
[2026-04-04T14:30:00Z] [INFO] [mcp-server] [scan-123] Tool port_scan gestartet: target=10.10.10.1, ports=1-1000
[2026-04-04T14:30:45Z] [INFO] [mcp-server] [scan-123] Tool port_scan beendet: 5 offene Ports gefunden (45s)
[2026-04-04T14:30:46Z] [WARN] [sandbox]    [scan-123] Verbindungsversuch zu nicht-autorisiertem Ziel blockiert: 192.168.1.1
```

---

## 6. Dependency-Sicherheit

### 6.1 Regeln
- Nur Packages mit aktiver Maintenance (letztes Update < 12 Monate)
- Keine Packages mit bekannten Critical/High CVEs
- Lock-Files werden immer committed
- Minimale Dependency-Tiefe: Weniger ist mehr

### 6.2 Erlaubte Package-Quellen
- **npm**: Nur npmjs.com Registry
- **Python**: Nur PyPI
- **Docker**: Nur Docker Hub Official Images oder verifizierte Publisher

### 6.3 Regelmäßige Prüfungen
- `npm audit` / `pip audit` — bei jedem Build
- Dependabot oder Renovate für automatische Updates (später)
- Manuelle Review bei Major-Version-Updates

---

## 7. Verschlüsselung (Encryption)

### 7.1 In Transit (Datenübertragung)

| Verbindung | Verschlüsselung | Mindeststandard |
|---|---|---|
| Browser → Web-UI (Produkt) | TLS 1.3 | MUSS |
| Web-UI → API-Server | TLS 1.3 | MUSS |
| MCP-Server → Sandbox | mTLS oder internes Netz + Netzwerk-Isolation | MUSS |
| App → Claude API | TLS 1.3 (von Anthropic erzwungen) | MUSS |
| App → PostgreSQL | TLS 1.2+ mit Client-Zertifikat | SOLL |

**Regeln:**
- Kein HTTP — nur HTTPS, auch intern im Produkt
- TLS 1.0 und 1.1 sind deaktiviert
- Selbstsignierte Zertifikate nur in Entwicklung, nie in Produktion
- HSTS-Header setzen (min. 1 Jahr)

### 7.2 At Rest (Datenspeicherung)

| Datentyp | Verschlüsselung | Methode |
|---|---|---|
| Scan-Ergebnisse in DB | Ja | PostgreSQL pgcrypto (AES-256) |
| Audit-Logs | Ja | Verschlüsselte Partition oder pgcrypto |
| API-Keys in DB | Ja | AES-256-GCM, Schlüssel aus Umgebungsvariable |
| Passwort-Hashes | Ja | Argon2id (nicht umkehrbar) |
| MFA-Secrets | Ja | AES-256-GCM |
| Backup-Dateien | Ja | gpg-verschlüsselt |
| Log-Dateien auf Disk | Nein (PoC) / Ja (Produkt) | Verschlüsselte Partition |

### 7.3 Schlüssel-Management

- Verschlüsselungsschlüssel werden NIEMALS im Code oder in der DB gespeichert
- Schlüssel kommen aus Umgebungsvariablen (`SENTINEL_ENCRYPTION_KEY`)
- PoC: Manuelle Schlüsselverwaltung
- Produkt: HashiCorp Vault oder äquivalenter Secret Store
- Schlüssel-Rotation: Mindestens alle 90 Tage

---

## 8. API-Authentifizierung & -Autorisierung

### 8.1 Interne API (MCP-Server ↔ Orchestrator)

| Aspekt | PoC | Produkt |
|---|---|---|
| Auth-Methode | Shared Secret (Token) | mTLS (gegenseitige Zertifikate) |
| Transport | Internes Docker-Netzwerk | TLS 1.3 |
| Rate Limiting | Kein (Einzelbenutzer) | 100 Requests/Minute pro User |

### 8.2 Externe API (Web-UI ↔ Backend, Produkt)

| Aspekt | Umsetzung |
|---|---|
| Authentifizierung | JWT (RS256) in HttpOnly Cookie |
| Token-Lebensdauer | Access: 15 Min, Refresh: 7 Tage |
| Refresh-Rotation | Ja — alter Refresh-Token wird invalidiert |
| CORS | Nur eigene Domain, keine Wildcards |
| Rate Limiting | Login: 5/Min, API: 100/Min, Scan-Start: 10/Min |
| IP-Whitelisting | Optional konfigurierbar |

### 8.3 API-Key-Management (für CI/CD-Integration)
- API-Keys werden gehasht in der DB gespeichert (wie Passwörter)
- Jeder Key hat einen Scope (z.B. nur `scan:create`, kein `user:*`)
- Keys haben ein Ablaufdatum (max. 1 Jahr)
- Jede Key-Nutzung wird im Audit-Log protokolliert

---

## 9. DSGVO & Datenschutz

### 9.1 Grundsatz
SentinelClaw ist **self-hosted**. Alle Daten bleiben auf der Infrastruktur des Kunden. Dennoch gelten DSGVO-Anforderungen, insbesondere wenn Scan-Ergebnisse personenbezogene Daten enthalten können.

### 9.1.1 LLM-Provider und Datenschutz

| Provider | Datenhaltung | AVV | Empfehlung |
|---|---|---|---|
| **Ollama** | Lokal (kein Datenabfluss) | Nicht nötig | Behörden, VS-NfD, maximale Compliance |
| **Azure OpenAI** | EU-Rechenzentren | Im Azure EA enthalten | Enterprise mit EU-Anforderung |
| **Claude (Anthropic)** | USA | Separat abzuschließen | Startups, PoC, Einzelnutzer |

**Pflicht-Hinweis bei Nicht-Azure/Nicht-Ollama-Providern:**
Wenn der Kunde einen Provider wählt der Daten außerhalb der EU verarbeitet, MUSS ein Hinweis erscheinen:
> "Für den DSGVO-konformen Einsatz benötigen Sie einen Auftragsverarbeitungsvertrag (AVV) mit dem gewählten Provider."

Dieser Hinweis wird im Audit-Log protokolliert (Akzeptanz-Zeitstempel + User).
Siehe [ADR-003: LLM-Provider-Strategie](architecture/ADR-003-llm-provider-strategie.md) für Details.

### 9.2 Datenklassifizierung

| Datentyp | Personenbezug | Speicherdauer | Löschbar |
|---|---|---|---|
| Scan-Ergebnisse | Möglich (E-Mail, Hostnamen) | Konfigurierbar (Default: 90 Tage) | Ja |
| Audit-Logs | Ja (User-ID, IP) | Min. 1 Jahr (Compliance) | Nur durch SYSTEM_ADMIN |
| User-Daten | Ja (E-Mail, Name) | Bis Löschung | Ja (Recht auf Vergessenwerden) |
| Agent-Logs | Möglich | 30 Tage | Ja (automatisch) |
| Passwort-Hashes | Nein (nicht umkehrbar) | Bis Löschung | Ja |

### 9.3 Datenverarbeitung

**Claude API (Anthropic):**
- Scan-Ziele und Tool-Ergebnisse werden an Claude zur Analyse gesendet
- **Pflicht**: Auftragsverarbeitungsvertrag (AVV/DPA) mit Anthropic
- **Minimierung**: Nur das Nötigste an Claude senden — keine Rohdaten
- **Hinweis an Kunden**: Im Setup-Wizard muss der Kunde bestätigen, dass er die Datenverarbeitung durch Anthropic akzeptiert

### 9.4 Betroffenenrechte (DSGVO Art. 15-22)

| Recht | Umsetzung |
|---|---|
| Auskunft (Art. 15) | Export aller User-Daten als JSON |
| Berichtigung (Art. 16) | User kann Profildaten selbst ändern |
| Löschung (Art. 17) | Account-Löschung entfernt alle personenbezogenen Daten |
| Datenübertragbarkeit (Art. 20) | Export in maschinenlesbarem Format (JSON) |
| Widerspruch (Art. 21) | Konfigurierbar: Opt-out für bestimmte Verarbeitungen |

### 9.5 Technische Maßnahmen
- Pseudonymisierung von User-Daten in Logs wo möglich
- Automatische Datenlöschung nach konfigurierbarer Frist
- Verschlüsselung at Rest und in Transit (siehe Abschnitt 7)
- Zugriffskontrolle über RBAC (siehe RBAC_MODEL.md)
- Regelmäßige Datenschutz-Folgenabschätzung (DSFA) empfohlen

---

## 10. Web-UI Sicherheit (OWASP Top 10)

> Gilt ab Produktentwicklung. Im PoC gibt es keine UI.

### 10.1 OWASP Top 10 Maßnahmen

| # | Risiko | Maßnahme |
|---|---|---|
| A01 | Broken Access Control | RBAC mit Default Deny + Row-Level Security in DB |
| A02 | Cryptographic Failures | TLS 1.3, AES-256, Argon2id, keine eigene Crypto |
| A03 | Injection | Parametrisierte Queries (Prisma ORM), kein Raw SQL |
| A04 | Insecure Design | Threat Modeling vor jedem Feature, Security-Reviews |
| A05 | Security Misconfiguration | Härtungs-Checkliste, kein Default-Admin-Passwort |
| A06 | Vulnerable Components | npm/pip audit im CI, Dependabot-Alerts |
| A07 | Auth Failures | MFA, Account-Lockout, Passwort-Policy, JWT-Rotation |
| A08 | Data Integrity Failures | Signierte Docker-Images, Lock-Files, SBOM |
| A09 | Logging Failures | Strukturiertes Audit-Logging, kein PII in Logs |
| A10 | SSRF | Whitelist für ausgehende Verbindungen, kein User-kontrollierter URL-Fetch |

### 10.2 HTTP-Security-Header

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 0 (veraltet, CSP ersetzt dies)
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 10.3 CSRF-Schutz
- **SameSite=Strict** Cookie-Attribut für Session-Cookies
- **CSRF-Token** als Double-Submit-Cookie für zustandsändernde Requests
- Alle `POST/PUT/DELETE`-Endpoints validieren den CSRF-Token

### 10.4 XSS-Schutz
- React escaped standardmäßig — `dangerouslySetInnerHTML` ist VERBOTEN
- Content Security Policy (CSP) blockiert Inline-Scripts
- Scan-Ergebnisse werden vor der Darstellung sanitized (DOMPurify)
- Keine Nutzung von `eval()`, `innerHTML`, `document.write()`

---

## 11. Secret-Rotation

### 11.1 Rotationsintervalle

| Secret | Rotationsintervall | Automatisierbar |
|---|---|---|
| Claude API Key | 90 Tage | Nein (manuell bei Anthropic) |
| JWT Signing Key | 30 Tage | Ja (Key-Pair-Rotation) |
| Datenbank-Passwort | 90 Tage | Ja (via Script) |
| Encryption Key | 90 Tage | Ja (Key-Versioning) |
| MCP Internal Token (PoC) | Bei jedem Neustart | Ja (Auto-generated) |

### 11.2 Rotation ohne Downtime
- **JWT**: Neuer + alter Key parallel aktiv für Übergangszeit (max. 1 Stunde)
- **DB-Passwort**: Erst neues Passwort setzen, dann App-Config aktualisieren, dann altes löschen
- **Encryption Key**: Key-Versioning — neue Daten mit neuem Key, alte bleiben lesbar

---

## 12. Incident Response (PoC-Phase)

Falls ein Sicherheitsproblem im eigenen Code entdeckt wird:

1. **Sofort stoppen** — Betroffene Funktion deaktivieren
2. **Dokumentieren** — Was, Wann, Wie entdeckt
3. **Fixen** — Patch entwickeln und testen
4. **Verifizieren** — Sicherstellen, dass der Fix greift
5. **Lessons Learned** — ADR schreiben, Regeln anpassen

### Eskalation (Produkt)
- **P0 (Kritisch)**: Aktive Ausnutzung → Sofort patchen, Kunden informieren
- **P1 (Hoch)**: Ausnutzbar ohne Auth → Fix innerhalb 24h
- **P2 (Mittel)**: Ausnutzbar mit Auth → Fix innerhalb 7 Tage
- **P3 (Niedrig)**: Theoretisch ausnutzbar → Nächstes Release

---

## 13. Checkliste für Code-Reviews

Bei jedem Code-Review müssen folgende Punkte geprüft werden:

- [ ] Keine Secrets im Code oder in Konfigurationsdateien
- [ ] Alle externen Inputs werden validiert
- [ ] Keine Command Injection möglich
- [ ] Container-Isolation wird nicht aufgeweicht
- [ ] Timeouts sind gesetzt für alle externen Aufrufe
- [ ] Fehler werden sicher gehandhabt (Fail Secure)
- [ ] Logging ist vorhanden, aber keine sensiblen Daten
- [ ] Dependencies haben keine bekannten CVEs
- [ ] Kein `any`, kein `eval()`, kein `exec()` mit dynamischem Input
- [ ] RBAC-Checks vorhanden für alle Endpoints
- [ ] CSRF-Token validiert bei zustandsändernden Requests
- [ ] Kein `dangerouslySetInnerHTML` oder unsanitized Output
- [ ] Verschlüsselung für sensible Daten at Rest
- [ ] TLS für alle externen Verbindungen
