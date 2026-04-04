# SentinelClaw — Betrieb & Operations

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026

---

## 1. Monitoring & Health-Checks

### 1.1 Health-Endpoints

Jeder Service exponiert einen Health-Endpoint:

| Service | Endpoint | Prüft |
|---|---|---|
| API-Server | `GET /health` | DB-Verbindung, Speicher, CPU |
| MCP-Server | `GET /health` | Sandbox erreichbar, Tools verfügbar |
| Sandbox | Docker HEALTHCHECK | Prozess läuft, nmap/nuclei installiert |
| PostgreSQL | pg_isready | Datenbank akzeptiert Verbindungen |

### 1.2 Metriken (Produkt)

| Metrik | Typ | Alarm bei |
|---|---|---|
| Scan-Dauer | Histogram | > 10 Minuten |
| API-Response-Time | Histogram | P95 > 2 Sekunden |
| Fehlgeschlagene Scans | Counter | > 3 in Folge |
| DB-Verbindungen | Gauge | > 80% Pool ausgelastet |
| Container-Restarts | Counter | > 2 in 10 Minuten |
| Disk-Usage | Gauge | > 85% |
| LLM-Token-Verbrauch | Counter | > 80% des Budgets |
| Fehlgeschlagene Logins | Counter | > 10 in 5 Minuten |

### 1.3 Monitoring-Stack (Empfehlung für Produkt)
- **Metriken**: Prometheus + Grafana
- **Logs**: Loki oder ELK Stack (Elasticsearch, Logstash, Kibana)
- **Alerting**: Grafana Alerts oder PagerDuty
- **Uptime**: Simple HTTP-Checks via Healthchecks.io oder eigener Cronjob

---

## 2. Backup & Disaster Recovery

### 2.1 Was wird gesichert?

| Daten | Methode | Frequenz | Aufbewahrung |
|---|---|---|---|
| PostgreSQL (komplett) | pg_dump + gpg | Täglich 02:00 UTC | 30 Tage |
| Konfigurationsdateien | Git-Repository | Bei jeder Änderung | Unbegrenzt (Git) |
| Docker-Volumes | Volume-Backup Script | Wöchentlich | 4 Wochen |
| Encryption Keys | Manuell, verschlüsselt | Bei Rotation | Aktuell + 1 vorher |

### 2.2 Backup-Regeln
- Backups werden **verschlüsselt** gespeichert (GPG, AES-256)
- Backup-Schlüssel wird GETRENNT vom Backup aufbewahrt
- Mindestens **1x pro Quartal** wird ein Restore getestet
- Backup-Logs werden im Audit-Trail protokolliert

### 2.3 Recovery-Ziele

| Metrik | Ziel | Beschreibung |
|---|---|---|
| RPO (Recovery Point Objective) | 24 Stunden | Max. akzeptabler Datenverlust |
| RTO (Recovery Time Objective) | 4 Stunden | Max. Ausfallzeit bis Wiederherstellung |

### 2.4 Disaster Recovery Schritte

1. Neuen Server mit Docker bereitstellen
2. SentinelClaw Docker-Images deployen
3. PostgreSQL-Backup einspielen (`pg_restore`)
4. Konfiguration aus Git-Repo wiederherstellen
5. Encryption Keys aus sicherem Speicher laden
6. Health-Checks verifizieren
7. Funktionstest: Einen Test-Scan durchführen

---

## 3. Kostenmanagement

### 3.1 LLM-Kosten kontrollieren

| Maßnahme | Umsetzung |
|---|---|
| Token-Budget pro Scan | `SENTINEL_LLM_MAX_TOKENS_PER_SCAN` (Default: 50.000) |
| Token-Budget pro Monat | `SENTINEL_LLM_MONTHLY_TOKEN_LIMIT` |
| Warnung bei 80% | Log-Eintrag + optionale Benachrichtigung |
| Harter Stop bei 100% | Scan wird pausiert, User informiert |
| Kosten-Dashboard | Verbrauch pro Organisation/User/Scan sichtbar |

### 3.2 Geschätzte Kosten pro Scan

| Provider | Modell | Geschätzte Kosten pro Scan* |
|---|---|---|
| Claude (Anthropic) | Sonnet 4 | ~$0.15 - $0.50 |
| Azure OpenAI | GPT-4o | ~$0.10 - $0.40 |
| Ollama | Llama 3.1 70B | $0 (nur Stromkosten) |

*Bei ~50.000 Tokens pro Scan. Tatsächliche Kosten variieren.

---

## 4. Update- & Patch-Management

### 4.1 SentinelClaw Updates
- Semantic Versioning: `MAJOR.MINOR.PATCH`
- CHANGELOG wird bei jedem Release aktualisiert
- Breaking Changes nur in MAJOR Releases
- Security-Patches als PATCH Release innerhalb 24-48h

### 4.2 Dependency Updates
- **Wöchentlich**: `npm audit` / `pip audit` automatisch
- **Monatlich**: Minor-Version-Updates prüfen
- **Sofort**: Critical CVE → Patch innerhalb 24h

### 4.3 Docker Image Updates
- Basis-Images monatlich auf Sicherheits-Patches prüfen
- Trivy oder Docker Scout für Image-Scanning
- Rebuild bei jedem Basis-Image-Update

---

## 5. Haftungsausschluss & Legal

### 5.1 Scan-Disclaimer (wird vor jedem Scan angezeigt)

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠  Rechtlicher Hinweis                                     │
│                                                              │
│  Dieses Tool darf ausschließlich für autorisierte            │
│  Sicherheitsüberprüfungen eingesetzt werden.                 │
│                                                              │
│  Der Betreiber ist verantwortlich für:                        │
│  • Schriftliche Genehmigung des Zielsystem-Eigentümers       │
│  • Einhaltung aller anwendbaren Gesetze (StGB §202a-c)      │
│  • Begrenzung des Scan-Umfangs auf genehmigte Systeme       │
│                                                              │
│  SentinelClaw übernimmt keine Haftung für Schäden die        │
│  durch unsachgemäßen oder unautorisierten Einsatz            │
│  entstehen.                                                  │
│                                                              │
│  [ ] Ich bestätige die Autorisierung für diesen Scan.        │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Bestätigung im Audit-Log
Jede Scan-Autorisierungsbestätigung wird gespeichert:
- Wer hat bestätigt (User-ID)
- Wann (Zeitstempel)
- Welches Ziel
- IP-Adresse des Bestätigenden

---

## 6. Responsible Disclosure

Falls Sicherheitslücken in SentinelClaw selbst gefunden werden:

### 6.1 Für externe Melder
- Kontakt: security@sentinelclaw.de (wird eingerichtet)
- PGP-Key für verschlüsselte Kommunikation bereitstellen
- Antwort innerhalb 48 Stunden
- Keine rechtliche Verfolgung bei verantwortungsvoller Meldung

### 6.2 Prozess
1. Meldung empfangen und bestätigen (48h)
2. Schweregrad bewerten (CVSS)
3. Fix entwickeln (je nach Schweregrad: 24h bis 30 Tage)
4. Melder informieren bevor Patch veröffentlicht wird
5. Advisory veröffentlichen nach Patch-Release
6. Melder in Credits nennen (wenn gewünscht)
