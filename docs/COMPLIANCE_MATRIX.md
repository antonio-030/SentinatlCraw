# SentinelClaw — Compliance-Matrix

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Zweck: Mapping der Anforderungen aus DSGVO, BSI Grundschutz und ISO 27001 auf SentinelClaw

---

## 1. DSGVO-Compliance

| Artikel | Anforderung | SentinelClaw-Umsetzung | Status |
|---|---|---|---|
| Art. 5 | Datenminimierung | PII-Filter vor LLM-Aufruf, nur nötige Daten senden | Geplant |
| Art. 5 | Speicherbegrenzung | Konfigurierbare Retention (Default: 90 Tage für Scans) | Geplant |
| Art. 6 | Rechtsgrundlage | Berechtigtes Interesse (Security Assessment im Auftrag) | Dokumentiert |
| Art. 13/14 | Informationspflicht | Hinweis im Setup-Wizard welcher Provider Daten erhält | Geplant |
| Art. 15 | Auskunftsrecht | JSON-Export aller User-Daten | Geplant |
| Art. 17 | Recht auf Löschung | Account-Löschung entfernt personenbezogene Daten | Geplant |
| Art. 20 | Datenübertragbarkeit | Export in maschinenlesbarem Format | Geplant |
| Art. 25 | Privacy by Design | Verschlüsselung, Pseudonymisierung, Datenminimierung | Geplant |
| Art. 28 | Auftragsverarbeitung | AVV-Hinweis bei Cloud-LLM-Provider (nicht Azure EU) | Geplant |
| Art. 30 | Verarbeitungsverzeichnis | Dokumentation aller Datenflüsse in `docs/` | Dieses Dokument |
| Art. 32 | Technische Maßnahmen | TLS, Encryption at Rest, RBAC, Sandbox-Isolation | Dokumentiert |
| Art. 33 | Meldepflicht bei Breach | Incident Response Prozess in SECURITY_POLICY.md | Dokumentiert |
| Art. 35 | DSFA (Folgenabschätzung) | Empfohlen für Kunden vor produktivem Einsatz | Hinweis |

---

## 2. BSI Grundschutz (Auszug, relevante Bausteine)

| Baustein | Anforderung | SentinelClaw-Umsetzung | Status |
|---|---|---|---|
| APP.3.1 | Web-Anwendungen | OWASP Top 10, CSP-Header, XSS/CSRF-Schutz | Dokumentiert |
| APP.3.2 | Webserver | TLS 1.3, HSTS, Security-Header | Dokumentiert |
| CON.1 | Kryptokonzept | AES-256, Argon2id, TLS 1.3, Key-Rotation | Dokumentiert |
| CON.3 | Datensicherungskonzept | Backup-Strategie für DB und Scan-Ergebnisse | Geplant |
| INF.9 | Mobiler Arbeitsplatz | Session-Timeout 30 Min, MFA, Token-Rotation | Dokumentiert |
| OPS.1.1 | Allg. IT-Betrieb | Logging, Monitoring, Patch-Management | Teilweise |
| OPS.1.2 | Ordnungsgemäße IT-Administration | RBAC, Audit-Trail, Vier-Augen-Prinzip | Dokumentiert |
| ORP.4 | Identitäts-/Berechtigungsmanagement | 5-Rollen-Modell, Least Privilege, MFA | Dokumentiert |
| SYS.1.3 | Server unter Linux | Container-Härtung, Non-root, Capabilities | Dokumentiert |
| SYS.1.6 | Containerisierung | Docker Security, Image-Scanning, Network-Policy | Dokumentiert |

---

## 3. ISO 27001 (Auszug, Annex A Controls)

| Control | Anforderung | SentinelClaw-Umsetzung | Status |
|---|---|---|---|
| A.5.15 | Access Control | RBAC-Modell mit 5 Rollen | Dokumentiert |
| A.5.23 | Informationssicherheit bei Cloud-Diensten | Provider-Auswahl mit Compliance-Level | Dokumentiert |
| A.5.34 | Datenschutz | DSGVO-Mapping (oben), PII-Filter | Dokumentiert |
| A.8.3 | Zugriffsbeschränkung | Row-Level Security, Mandantentrennung | Dokumentiert |
| A.8.5 | Sichere Authentifizierung | MFA, Argon2id, Passwort-Policy | Dokumentiert |
| A.8.9 | Configuration Management | Env-Vars, Config-Dateien, keine Hardcodes | Dokumentiert |
| A.8.12 | Data Leakage Prevention | PII-Filter, Datenminimierung vor LLM | Geplant |
| A.8.15 | Logging | Strukturiertes Audit-Logging | Dokumentiert |
| A.8.16 | Monitoring | Health-Checks, Log-Aggregation | Geplant |
| A.8.24 | Kryptographie | TLS 1.3, AES-256, pgcrypto | Dokumentiert |
| A.8.25 | Secure Development | Coding Standards, Code-Reviews, SAST | Dokumentiert |
| A.8.28 | Secure Coding | Input-Validierung, Command-Injection-Schutz | Dokumentiert |

---

## 4. Datenfluss-Dokumentation (Art. 30 DSGVO)

### 4.1 Verarbeitungsübersicht

```
                            ┌──────────────┐
                            │   Benutzer   │
                            │  (Browser)   │
                            └──────┬───────┘
                                   │ HTTPS/TLS 1.3
                                   ▼
                            ┌──────────────┐
                            │   Web-UI /   │
                            │   API-Server │
                            └──────┬───────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼               ▼
             ┌────────────┐ ┌──────────┐   ┌────────────┐
             │ PostgreSQL │ │  Audit   │   │Orchestrator│
             │    (DB)    │ │  Logs    │   │  Agent     │
             └────────────┘ └──────────┘   └─────┬──────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │ MCP-Server   │
                                          └──────┬───────┘
                                    ┌────────────┤
                                    ▼            ▼
                             ┌──────────┐  ┌──────────────┐
                             │ Sandbox  │  │ LLM-Provider │
                             │(nmap etc)│  │(Azure/Claude/│
                             └──────────┘  │   Ollama)    │
                                           └──────────────┘
```

### 4.2 Welche Daten fließen wohin?

| Von → Nach | Daten | Personenbezug | Verschlüsselt |
|---|---|---|---|
| Benutzer → Web-UI | Login-Daten, Scan-Ziel | Ja (E-Mail) | TLS 1.3 |
| Web-UI → PostgreSQL | User-Daten, Scan-Jobs | Ja | TLS + at Rest |
| Orchestrator → MCP | Scan-Befehle, Parameter | Nein | Internes Netz |
| MCP → Sandbox | Tool-Befehle | Nein | Internes Netz |
| Sandbox → MCP | Scan-Rohdaten | Möglich | Internes Netz |
| MCP → LLM-Provider | Bereinigte Findings | Minimiert | TLS 1.3 |
| LLM → MCP | Analyse, Empfehlungen | Nein | TLS 1.3 |

### 4.3 Daten die das Netzwerk VERLASSEN

| Provider | Daten nach außen | Zielland | AVV nötig |
|---|---|---|---|
| Ollama | Keine | — | Nein |
| Azure OpenAI | Bereinigte Findings | EU (konfigurierbar) | Im Azure EA |
| Claude (Anthropic) | Bereinigte Findings | USA | Ja (separat) |

---

## 5. Aufbewahrungsfristen

| Datentyp | Aufbewahrung | Löschung | Rechtsgrundlage |
|---|---|---|---|
| Scan-Ergebnisse | 90 Tage (konfigurierbar) | Automatisch | Berechtigtes Interesse |
| Audit-Logs | Min. 1 Jahr | Manuell durch SYSTEM_ADMIN | Compliance-Pflicht |
| User-Accounts | Bis Löschung | Auf Anfrage (Art. 17) | Vertrag |
| Agent-Logs | 30 Tage | Automatisch | Betriebserfordernis |
| Backup-Dateien | 30 Tage | Automatische Rotation | Datensicherung |
| LLM-Prompts/Responses | Nicht gespeichert* | — | — |

*LLM-Prompts und -Responses werden NICHT dauerhaft gespeichert. Sie existieren nur während der Verarbeitung im Arbeitsspeicher.
