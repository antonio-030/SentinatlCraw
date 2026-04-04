# SentinelClaw — Kompletter Ablauf

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Zweck: Der rote Faden — von der Installation bis zum fertigen Report

---

## Gesamtübersicht

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ INSTALL  │───▶│  SETUP  │───▶│  SCAN   │───▶│  AGENT  │───▶│ REPORT  │
│          │    │ WIZARD  │    │ STARTEN │    │ ARBEITET│    │         │
│ docker   │    │ 7 Schri-│    │ Ziel,   │    │ autonom,│    │ PDF,    │
│ compose  │    │ tte,    │    │ Scope,  │    │ fragt   │    │ DOCX,   │
│ up       │    │ einmalig│    │ RoE,    │    │ bei     │    │ Compli- │
│          │    │         │    │ Disclai-│    │ Stufe3+ │    │ ance    │
│          │    │         │    │ mer     │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
  ~5 Min         ~5 Min        ~2 Min        1-10 Min        ~1 Min
```

---

## Phase 0: Installation

### Was passiert

```bash
# Der Kunde klont das Repo und startet Docker
git clone https://github.com/sentinelclaw/sentinelclaw.git
cd sentinelclaw
cp .env.example .env
docker compose up -d
```

### Was Docker hochfährt

```
docker compose up -d
    │
    ├── sentinelclaw-app        (API-Server + Web-UI)
    ├── sentinelclaw-mcp        (MCP-Server für Tool-Steuerung)
    ├── sentinelclaw-db         (PostgreSQL 16)
    ├── sentinelclaw-sandbox    (Sandbox-Container mit nmap, nuclei, etc.)
    └── sentinelclaw-watchdog   (Unabhängiger Sicherheits-Überwacher)
```

### Der User sieht

```
Browser öffnen → http://localhost:3000

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                     [SC]  SentinelClaw                       │
│                                                             │
│            Willkommen bei der Erstkonfiguration              │
│                                                             │
│            SentinelClaw wurde erfolgreich                    │
│            installiert. Bitte richten Sie die                │
│            Plattform ein.                                    │
│                                                             │
│                  [Konfiguration starten →]                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup-Wizard (einmalig)

### Schritt 1/7 — Administrator-Account

```
┌─────────────────────────────────────────────────────────────┐
│  ━━●━━━━○━━━━○━━━━○━━━━○━━━━○━━━━○                          │
│  Admin  Provider  DB  Netzwerk  Targets  Test  Fertig        │
│                                                             │
│  Administrator-Account erstellen                             │
│                                                             │
│  Anzeigename:  [Jaciel Acea Ruiz                ]           │
│  E-Mail:       [admin@firma.de                   ]           │
│  Passwort:     [••••••••••••••••                 ]           │
│                 ✓ Min. 12 Zeichen  ✓ Groß+Klein             │
│                 ✓ Zahl             ✓ Sonderzeichen           │
│                                                             │
│  MFA einrichten (Pflicht für Admin):                         │
│  ┌──────────────┐                                           │
│  │  [QR-Code]   │  Scannen Sie diesen Code mit              │
│  │              │  Ihrer Authenticator-App                   │
│  └──────────────┘                                           │
│  Bestätigungscode: [______]                                  │
│                                                             │
│                              [Weiter →]                      │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 2/7 — LLM-Provider

```
┌─────────────────────────────────────────────────────────────┐
│  ━━━━━━●━━━━○━━━━○━━━━○━━━━○━━━━○                            │
│                                                             │
│  LLM-Provider wählen                                         │
│                                                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐ │
│  │  Ollama          │ │ ● Azure OpenAI  │ │  Claude        │ │
│  │  (Self-Hosted)   │ │   (EU Cloud)    │ │  (Anthropic)   │ │
│  │                  │ │                 │ │                │ │
│  │  🟢 Max. Daten-  │ │ 🟢 DSGVO via    │ │ 🟡 AVV separat │ │
│  │    schutz        │ │   Azure EA      │ │   erforderlich │ │
│  │  🟡 Braucht GPU  │ │ 🟢 EU-Rechen-   │ │ 🟢 Beste       │ │
│  │                  │ │   zentren       │ │   Qualität     │ │
│  └─────────────────┘ └─────────────────┘ └────────────────┘ │
│                                                             │
│  ─── Azure OpenAI Konfiguration ────────────────────────    │
│                                                             │
│  Endpoint:    [https://firma.openai.azure.com    ]          │
│  API-Key:     [••••••••••••••••••]       [Testen ✓]         │
│  Deployment:  [gpt-4o                    ]                   │
│                                                             │
│  Status: ✅ Verbindung erfolgreich                           │
│                                                             │
│  [← Zurück]                          [Weiter →]             │
└─────────────────────────────────────────────────────────────┘
```

Bei Claude-Auswahl erscheint:
```
┌─ ⚠ Datenschutz-Hinweis ────────────────────────────────────┐
│ Daten werden an Anthropic (USA) übertragen.                 │
│ Für DSGVO-konformen Einsatz: AVV mit Anthropic nötig.       │
│                                                             │
│ ☐ Ich habe den Hinweis gelesen und akzeptiere die           │
│   Datenverarbeitung durch den gewählten Provider.           │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 3/7 — Datenbank

```
┌─────────────────────────────────────────────────────────────┐
│  Datenbank                                                   │
│                                                             │
│  ● Eingebettete Datenbank (SQLite)                           │
│    Für PoC und Einzelnutzer — kein Setup nötig               │
│                                                             │
│  ○ PostgreSQL (empfohlen für Teams)                          │
│    Für Multi-User, RBAC und produktiven Einsatz              │
│                                                             │
│  ✅ SQLite wird automatisch eingerichtet.                     │
│  Migration zu PostgreSQL ist jederzeit möglich.              │
│                                                             │
│  [← Zurück]                          [Weiter →]             │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 4/7 — Netzwerk & Sandbox

```
┌─────────────────────────────────────────────────────────────┐
│  Netzwerk & Sandbox prüfen                                   │
│                                                             │
│  Automatische Prüfung:                                       │
│                                                             │
│  ✅ Docker läuft                    (Docker 27.1.0)          │
│  ✅ Sandbox-Image verfügbar         (sentinelclaw/sandbox)   │
│  ✅ Internes Netzwerk erstellt       (sentinel-internal)      │
│  ✅ Scan-Netzwerk erstellt           (sentinel-scanning)      │
│  ✅ Sandbox startet korrekt          (Container-Test ok)      │
│  ✅ nmap verfügbar                   (v7.94)                  │
│  ✅ nuclei verfügbar                 (v3.2.1)                 │
│  ✅ Netzwerk-Isolation funktioniert  (Kein Internet-Zugriff)  │
│  ✅ Watchdog aktiv                   (PID 4521)               │
│                                                             │
│  Alle 9 Prüfungen bestanden.                                │
│                                                             │
│  [← Zurück]                          [Weiter →]             │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 5/7 — Erstes Scan-Target

```
┌─────────────────────────────────────────────────────────────┐
│  Scan-Ziele konfigurieren                                    │
│                                                             │
│  Fügen Sie mindestens ein Ziel hinzu, das gescannt           │
│  werden darf. Nur Adressen in dieser Liste können            │
│  vom Agent erreicht werden.                                  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ Ziel-Adresse:    [10.10.10.0/24              ]         │  │
│  │ Beschreibung:    [Internes Testnetz           ]        │  │
│  │                                    [Hinzufügen +]      │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                             │
│  Aktuelle Ziele:                                             │
│  ┌────────────────────┬──────────────────┬────────────────┐  │
│  │ 10.10.10.0/24      │ Internes Testnetz│ [🗑 Entfernen]  │  │
│  └────────────────────┴──────────────────┴────────────────┘  │
│                                                             │
│  ⚠ Private Netzwerke (10.x, 172.x, 192.168.x) sind nur     │
│    erlaubt wenn Sie hier explizit eingetragen sind.          │
│                                                             │
│  [← Zurück]                          [Weiter →]             │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 6/7 — Funktionstest

```
┌─────────────────────────────────────────────────────────────┐
│  Funktionstest                                               │
│                                                             │
│  SentinelClaw führt einen kurzen Test durch um                │
│  sicherzustellen, dass alles funktioniert.                   │
│                                                             │
│  [Test starten]                                              │
│                                                             │
│  ⏳ Test läuft...                                            │
│                                                             │
│  ✅ LLM-Provider antwortet          (Azure GPT-4o, 1.2s)    │
│  ✅ MCP-Server erreichbar            (localhost:8080)         │
│  ✅ Sandbox führt Befehl aus         (nmap --version: ok)     │
│  ✅ Datenbank schreib-/lesbar        (INSERT + SELECT: ok)    │
│  ✅ Audit-Log funktioniert           (Testeintrag: ok)       │
│  ✅ Kill Switch funktioniert         (Kill + Verify: ok)     │
│  ✅ Watchdog reagiert                (Health-Check: ok)       │
│                                                             │
│  Alle 7 Tests bestanden. SentinelClaw ist einsatzbereit.    │
│                                                             │
│  [← Zurück]                          [Weiter →]             │
└─────────────────────────────────────────────────────────────┘
```

### Schritt 7/7 — Fertig

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    ✅ Einrichtung abgeschlossen               │
│                                                             │
│  SentinelClaw ist bereit.                                    │
│                                                             │
│  Zusammenfassung:                                            │
│  ───────────────────────────────────                         │
│  Admin:      admin@firma.de (MFA aktiv)                      │
│  Provider:   Azure OpenAI (GPT-4o, EU West)                  │
│  Datenbank:  SQLite (lokal)                                  │
│  Sandbox:    Docker, nmap 7.94, nuclei 3.2.1                 │
│  Targets:    10.10.10.0/24                                   │
│  Watchdog:   Aktiv                                           │
│                                                             │
│                  [Zum Dashboard →]                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Setup-Wizard erscheint NUR beim allerersten Start. Danach nie wieder.**

---

## Phase 2: Dashboard (nach Login)

### Login

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    [SC]  SentinelClaw                         │
│                                                             │
│  E-Mail:    [admin@firma.de                      ]           │
│  Passwort:  [••••••••••••                        ]           │
│                                                             │
│                         [Anmelden]                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘

→ MFA-Abfrage (wenn aktiv):

┌─────────────────────────────────────────────────────────────┐
│  Zwei-Faktor-Authentifizierung                               │
│                                                             │
│  Geben Sie den Code aus Ihrer Authenticator-App ein:         │
│                                                             │
│           [ _ ] [ _ ] [ _ ] [ _ ] [ _ ] [ _ ]                │
│                                                             │
│                        [Bestätigen]                           │
└─────────────────────────────────────────────────────────────┘
```

### Dashboard — erste Ansicht

```
┌─────────────────────────────────────────────────────────────────┐
│  SC  Dashboard                                 [🔴 NOTAUS] [👤]│
├──────────┬──────────────────────────────────┬───────────────────┤
│          │                                  │                   │
│ ● Dashb. │  Willkommen, Jaciel.             │  Agent-Chat    ]  │
│   Scans  │                                  │                   │
│   Finding│  Noch keine Scans durchgeführt.   │  🤖 Hallo!       │
│   Reports│                                  │  Ich bin bereit.  │
│  ──────  │  ┌────────────────────────────┐  │  Sag mir was du   │
│   Config │  │                            │  │  scannen möchtest │
│   Users  │  │   Ersten Scan starten      │  │  oder tippe       │
│   Audit  │  │                            │  │  /help für        │
│   System │  │   Gib mir ein Ziel und     │  │  Befehle.         │
│          │  │   ich analysiere es für    │  │                   │
│          │  │   dich.                    │  │                   │
│          │  │                            │  │                   │
│          │  │   [+ Neuen Scan starten]   │  │                   │
│          │  │                            │  │                   │
│          │  └────────────────────────────┘  │ ┌───────────────┐ │
│          │                                  │ │ Nachricht...↵ │ │
│  v0.1    │  System: ✅ Alle Dienste online   │ └───────────────┘ │
└──────────┴──────────────────────────────────┴───────────────────┘
```

---

## Phase 3: Scan starten

### Weg A: Über den Chat (schnell, natürliche Sprache)

```
👤 Du:
Scanne 10.10.10.0/24 — ich will wissen welche Dienste laufen
und ob es bekannte Schwachstellen gibt.

🤖 Orchestrator:
Verstanden. Ich erstelle einen Scan-Plan:

┌ 📋 Scan-Plan ───────────────────────────────────────────┐
│                                                          │
│ Ziel:      10.10.10.0/24                                 │
│ Stufe:     2 (Vulnerability Check)                       │
│ Zeitfenster: Jetzt bis +2 Stunden                        │
│                                                          │
│ Phase 1 — Host Discovery ─────── nmap -sn ────── ~1 min │
│ Phase 2 — Port-Scan ──────────── nmap -sV -sC ── ~5 min │
│ Phase 3 — Vulnerability Scan ─── nuclei ──────── ~3 min │
│                                                          │
│ Geschätzt: ~9 Minuten | ~35.000 Tokens                   │
│                                                          │
│ [Plan anpassen ✏]                     [Starten ✓]        │
└──────────────────────────────────────────────────────────┘

⚠ Rechtlicher Hinweis
Dieses Tool darf ausschließlich für autorisierte
Sicherheitsüberprüfungen eingesetzt werden.
(StGB §202a-c)

☐ Ich bestätige die Autorisierung für diesen Scan.

[Starten ✓] (erst aktiv nach Checkbox)
```

### Weg B: Über die UI-Seite "Scan starten" (ausführlich)

→ Wie in UI_DESIGN_PLAN.md Seite 4.3 beschrieben: Formular mit Ziel, Stufe, Zeitfenster, Disclaimer.

### Was nach Klick auf "Starten" passiert

```
User bestätigt Disclaimer und klickt "Starten"
    │
    ▼
┌─ System-Checks (< 1 Sekunde) ──────────────────────────────┐
│ ✓ Ziel in Whitelist?                    → Ja                │
│ ✓ Ausgeschlossene Adressen entfernt?    → Ja                │
│ ✓ Eskalationsstufe erlaubt?             → Ja (Stufe 2)      │
│ ✓ RoE nötig? (Stufe < 3)               → Nein              │
│ ✓ User hat Berechtigung? (SECURITY_LEAD)→ Ja                │
│ ✓ Zeitfenster gültig?                   → Ja                │
│ ✓ Token-Budget ausreichend?             → Ja (50K verfügbar)│
│ ✓ Sandbox-Container bereit?             → Ja                │
│ ✓ LLM-Provider erreichbar?              → Ja                │
│ ✓ Kill Switch getestet?                 → Ja                │
└──────────────────────────────────────────────────────────────┘
    │ Alle 10 Checks bestanden
    ▼
┌─ Scan wird erstellt ────────────────────────────────────────┐
│ Scan-ID:     SC-042                                         │
│ Status:      RUNNING                                        │
│ Audit-Log:   "User J. Ruiz startet Scan SC-042"             │
│ Audit-Log:   "Disclaimer akzeptiert um 14:28:00"            │
│ Chat:        Neuer Chat für SC-042 erstellt                  │
│ Dashboard:   Scan erscheint unter "Laufende Scans"          │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
Agent beginnt zu arbeiten (Phase 4)
```

---

## Phase 4: Agent arbeitet

### Ablauf im Detail

```
SC-042 gestartet
    │
    ▼
┌═══════════════════════════════════════════════════════════════┐
║  ORCHESTRATOR empfängt Auftrag                               ║
║                                                              ║
║  "Scanne 10.10.10.0/24, finde Dienste und Schwachstellen"    ║
║                                                              ║
║  Orchestrator denkt nach (LLM-Aufruf #1):                    ║
║  → Ziel ist ein /24 Netz (bis zu 254 Hosts)                  ║
║  → Erst Host Discovery um aktive Hosts zu finden             ║
║  → Dann gezielter Port-Scan auf aktive Hosts                 ║
║  → Dann Vulnerability-Scan auf gefundene Services            ║
║                                                              ║
║  Orchestrator erstellt Plan und delegiert an Recon-Agent      ║
╚═══════════════════════════════════════════════════════════════╝
    │
    ▼
┌─ PHASE 1: Host Discovery (~1 Min) ─────────────────────────┐
│                                                             │
│  Orchestrator → Recon-Agent:                                │
│  "Finde alle aktiven Hosts in 10.10.10.0/24"                │
│                                                             │
│  Recon-Agent → MCP-Server:                                  │
│  Tool: port_scan                                            │
│  Parameter: { target: "10.10.10.0/24", flags: ["-sn"] }    │
│                                                             │
│  MCP-Server prüft:                                          │
│  ✓ Scope-Check: 10.10.10.0/24 ist erlaubt                  │
│  ✓ Stufen-Check: nmap = Stufe 1, erlaubt bei Stufe 2       │
│  ✓ Zeitfenster: OK                                          │
│  → ERLAUBT                                                  │
│                                                             │
│  MCP-Server → Sandbox-Container:                            │
│  nmap -sn 10.10.10.0/24                                     │
│                                                             │
│  Ergebnis: 7 aktive Hosts                                   │
│  10.10.10.1, .3, .5, .10, .15, .20, .25                    │
│                                                             │
│  Recon-Agent → Orchestrator:                                │
│  "7 Hosts gefunden. Bereit für Port-Scan."                   │
│                                                             │
│  Chat: "Phase 1 abgeschlossen — 7 aktive Hosts gefunden"    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ PHASE 2: Port-Scan (~5 Min) ──────────────────────────────┐
│                                                             │
│  Orchestrator → Recon-Agent:                                │
│  "Scanne alle 7 Hosts auf offene Ports + Service-Versionen" │
│                                                             │
│  Recon-Agent → MCP-Server:                                  │
│  Tool: port_scan                                            │
│  Parameter: {                                               │
│    target: "10.10.10.3,5,10,15,20,25",                     │
│    ports: "1-10000",                                        │
│    flags: ["-sV", "-sC"]                                    │
│  }                                                          │
│                                                             │
│  (10.10.10.1 = Gateway, wird vom Agent übersprungen)         │
│                                                             │
│  MCP-Server: Scope-Check ✓, Stufen-Check ✓ → ERLAUBT        │
│                                                             │
│  Sandbox: nmap -sV -sC -p 1-10000 10.10.10.3,5,10,15,20,25│
│                                                             │
│  Ergebnis (vereinfacht):                                     │
│  ┌────────────────┬───────┬──────────┬────────────────────┐ │
│  │ Host           │ Port  │ Service  │ Version            │ │
│  ├────────────────┼───────┼──────────┼────────────────────┤ │
│  │ 10.10.10.3     │ 22    │ ssh      │ OpenSSH 7.4        │ │
│  │ 10.10.10.3     │ 443   │ https    │ nginx 1.24         │ │
│  │ 10.10.10.5     │ 80    │ http     │ nginx 1.24         │ │
│  │ 10.10.10.5     │ 443   │ https    │ nginx 1.24         │ │
│  │ 10.10.10.5     │ 3306  │ mysql    │ MySQL 8.0.32       │ │
│  │ 10.10.10.10    │ 8080  │ http     │ Tomcat 9.0.71      │ │
│  │ 10.10.10.15    │ 5432  │ postgres │ PostgreSQL 15.4    │ │
│  │ 10.10.10.20    │ 80    │ http     │ Apache 2.4.57      │ │
│  │ 10.10.10.25    │ 22    │ ssh      │ OpenSSH 8.9        │ │
│  └────────────────┴───────┴──────────┴────────────────────┘ │
│                                                             │
│  Orchestrator analysiert (LLM-Aufruf #2):                    │
│  → OpenSSH 7.4 auf .3 ist veraltet (EOL) → prüfen          │
│  → MySQL 8.0.32 auf .5 → bekannte CVEs möglich              │
│  → Tomcat 9.0.71 auf .10 → Manager-Interface prüfen         │
│  → PostgreSQL 15.4 auf .15 → relativ aktuell                │
│                                                             │
│  Chat: "Phase 2 abgeschlossen — 9 offene Ports auf 6 Hosts" │
│  Chat: Zeigt Tabelle mit Hosts + Ports                       │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ PHASE 3: Vulnerability Scan (~3 Min) ─────────────────────┐
│                                                             │
│  Orchestrator → Recon-Agent:                                │
│  "Scanne alle gefundenen Services auf bekannte Schwachstellen│
│   mit nuclei. Fokus auf Web-Services und Datenbanken."      │
│                                                             │
│  Recon-Agent → MCP-Server:                                  │
│  Tool: vuln_scan                                            │
│  Parameter: {                                               │
│    target: "10.10.10.3,5,10,15,20",                        │
│    templates: ["cves", "vulnerabilities",                   │
│                "misconfiguration", "default-logins"]        │
│  }                                                          │
│                                                             │
│  MCP-Server: Scope-Check ✓, nuclei = Stufe 2 ✓ → ERLAUBT   │
│                                                             │
│  Sandbox: nuclei -u 10.10.10.3,5,10,15,20                  │
│           -t cves,vulnerabilities,misconfiguration           │
│                                                             │
│  Findings kommen rein (Live im Chat):                        │
│                                                             │
│  14:34:12  🔴 CRITICAL — SQL Injection                       │
│            10.10.10.5:3306 | CVE-2024-1234 | CVSS 9.1       │
│            → Sofort in DB gespeichert                        │
│            → Chat: Finding-Karte erscheint                   │
│                                                             │
│  14:34:30  🟠 HIGH — XSS Reflected                           │
│            10.10.10.5:443/search | CVSS 7.2                  │
│            → In DB gespeichert                               │
│                                                             │
│  14:34:45  🟠 HIGH — Tomcat Manager Default Credentials      │
│            10.10.10.10:8080 | CVSS 7.5                       │
│            → In DB gespeichert                               │
│                                                             │
│  14:35:00  🟠 HIGH — OpenSSH 7.4 (veraltet, CVEs)           │
│            10.10.10.3:22 | CVE-2023-xxxx | CVSS 7.0         │
│            → In DB gespeichert                               │
│                                                             │
│  14:35:15  🟡 MEDIUM — TLS 1.0 aktiviert                    │
│            10.10.10.3:443 | CVSS 5.3                         │
│            → In DB gespeichert                               │
│                                                             │
│  14:35:20  🟡 MEDIUM — Directory Listing                     │
│            10.10.10.5:80 | CVSS 5.0                          │
│            → In DB gespeichert                               │
│                                                             │
│  Recon-Agent → Orchestrator: "Vuln-Scan abgeschlossen."      │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─ Orchestrator: Ergebnis-Analyse (LLM-Aufruf #3) ──────────┐
│                                                             │
│  Orchestrator analysiert alle Findings und erstellt           │
│  eine Zusammenfassung:                                       │
│                                                             │
│  Chat-Nachricht:                                             │
│  ────────────────────────────────────────────────────        │
│  🤖 Orchestrator:                                            │
│                                                             │
│  Scan SC-042 abgeschlossen.                                  │
│                                                             │
│  ┌ Zusammenfassung ───────────────────────────────────┐      │
│  │                                                    │      │
│  │ Dauer:     9 Minuten 22 Sekunden                   │      │
│  │ Hosts:     6 gescannt (von 7 aktiven)              │      │
│  │ Ports:     9 offen                                 │      │
│  │ Findings:  6 gesamt                                │      │
│  │                                                    │      │
│  │ 🔴 Critical:  1  (SQL Injection)                   │      │
│  │ 🟠 High:      3  (XSS, Tomcat, OpenSSH)           │      │
│  │ 🟡 Medium:    2  (TLS 1.0, Directory Listing)     │      │
│  │                                                    │      │
│  │ Tokens:    28.400 von 50.000 (57%)                 │      │
│  │                                                    │      │
│  └────────────────────────────────────────────────────┘      │
│                                                             │
│  Kritischstes Problem:                                       │
│  Die SQL-Injection auf 10.10.10.5:3306 erlaubt              │
│  unauthentifizierten Datenbankzugriff. Das sollte           │
│  sofort behoben werden.                                     │
│                                                             │
│  Was möchtest du als nächstes?                               │
│  • "Erkläre [Finding]" — Details zu einem Fund              │
│  • "Erstelle Report" — PDF/DOCX generieren                   │
│  • "Exploit verifizieren" — Schwachstelle ausnutzen (Stufe 3)│
│  • /findings — Alle Findings anzeigen                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Optionale Exploitation (Stufe 3)

### Wenn der User Exploit will

```
👤 Du:
Verifiziere die SQL-Injection auf 10.10.10.5.

🤖 Orchestrator:
⚠ GENEHMIGUNG ERFORDERLICH

Das erfordert Eskalation auf Stufe 3 (Exploitation).

┌ Vorgeschlagene Aktion ───────────────────────────────────┐
│                                                          │
│ Tool:     sqlmap                                         │
│ Ziel:     10.10.10.5:3306                                │
│ Methode:  SQL-Injection Verification (Read-only)         │
│ Risiko:   Niedrig (keine Datenänderung)                  │
│ Dauer:    2-5 Minuten                                    │
│                                                          │
│ Was passiert:                                             │
│ → sqlmap testet ob die SQLi tatsächlich ausnutzbar ist   │
│ → Bei Erfolg: Datenbankname + Version als Beweis         │
│ → Keine Daten werden gelesen, geändert oder gelöscht     │
│                                                          │
│ [✓ Genehmigen]   [✗ Ablehnen]   [Nur dokumentieren]     │
└──────────────────────────────────────────────────────────┘

👤 Du:
[Klickt: ✓ Genehmigen]

🤖 Orchestrator:
Genehmigung erhalten. Eskaliere auf Stufe 3 für 10.10.10.5.
Audit-Log: "User J. Ruiz genehmigt Exploit auf 10.10.10.5"

🔧 Recon-Agent:
sqlmap --url "http://10.10.10.5/login" --forms --dbs --batch
⏳ Läuft...

🔧 Recon-Agent (nach 3 Min):
✅ SQL-Injection bestätigt!

┌ Exploit-Ergebnis ────────────────────────────────────────┐
│                                                          │
│ 🔴 SQL INJECTION VERIFIZIERT                              │
│                                                          │
│ Typ:        Boolean-based blind                          │
│ Parameter:  username (POST)                              │
│ Datenbank:  MySQL 8.0.32                                 │
│                                                          │
│ Beweis:                                                   │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ available databases [3]:                              │ │
│ │ [*] information_schema                               │ │
│ │ [*] webapp_production                                │ │
│ │ [*] mysql                                            │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Zugriff auf 3 Datenbanken möglich.                       │
│ Keine Daten gelesen (nur Datenbanknamen als Proof).      │
│                                                          │
│ Evidence-Hash: sha256:a1b2c3d4e5f6...                    │
└──────────────────────────────────────────────────────────┘

🤖 Orchestrator:
Die SQL-Injection ist bestätigt und verifiziert.
Ein Angreifer könnte alle Daten in der Datenbank
"webapp_production" lesen und ändern.

CVSS bleibt bei 9.1 (Critical).
Empfehlung: Sofortige Behebung.

Soll ich einen Report erstellen?
```

---

## Phase 6: Report erstellen

```
👤 Du:
Erstelle einen Executive Summary und einen technischen Report.

🤖 Orchestrator:
Generiere Reports für Scan SC-042...

⏳ Executive Summary (2-3 Seiten, für Management)...
✅ Fertig → [Download PDF ⬇]

⏳ Technischer Report (Alle Findings mit Details)...
✅ Fertig → [Download PDF ⬇]

Beide Reports sind auch unter Reports → SC-042 verfügbar.

┌ Report-Vorschau (Executive Summary) ─────────────────────┐
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │          SECURITY ASSESSMENT REPORT                │  │
│  │          Executive Summary                         │  │
│  │                                                    │  │
│  │  Kunde:    [Organisation]                          │  │
│  │  Ziel:     10.10.10.0/24                           │  │
│  │  Datum:    14. April 2026                          │  │
│  │  Stufe:    Vulnerability Assessment                │  │
│  │                                                    │  │
│  │  ERGEBNISÜBERSICHT                                 │  │
│  │  ████████████████████ 1 Critical                   │  │
│  │  ██████████████       3 High                       │  │
│  │  ████████             2 Medium                     │  │
│  │                                                    │  │
│  │  HANDLUNGSEMPFEHLUNGEN                             │  │
│  │  1. SQL Injection beheben (Priorität: SOFORT)      │  │
│  │  2. Tomcat Manager sichern (Priorität: 7 Tage)    │  │
│  │  3. OpenSSH aktualisieren (Priorität: 7 Tage)     │  │
│  │  ...                                               │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Phase 7: Nach dem Scan

### Was bleibt

```
Scan SC-042 ist abgeschlossen. Folgendes ist gespeichert:

┌─ Datenbank ──────────────────────────────────────────────┐
│ • Scan-Job (ID, Ziel, Konfiguration, Status, Dauer)     │
│ • 6 Findings (Severity, CVE, CVSS, Beweis, Empfehlung)  │
│ • 1 Exploit-Ergebnis (verifizierte SQLi)                 │
│ • Chat-Verlauf (alle Nachrichten, Genehmigungen)         │
│ • Audit-Log (wer hat was wann getan)                     │
└──────────────────────────────────────────────────────────┘

┌─ Reports ────────────────────────────────────────────────┐
│ • Executive Summary (PDF)                                │
│ • Technischer Report (PDF)                               │
│ • Jederzeit neu generierbar (auch in anderen Formaten)   │
└──────────────────────────────────────────────────────────┘

┌─ Audit-Trail ────────────────────────────────────────────┐
│ 14:28:00  User J. Ruiz erstellt Scan SC-042              │
│ 14:28:00  Disclaimer akzeptiert von J. Ruiz              │
│ 14:28:01  Scan SC-042 gestartet (Stufe 2)                │
│ 14:29:00  Tool nmap gestartet (Host Discovery)           │
│ 14:30:00  Tool nmap abgeschlossen (7 Hosts)              │
│ 14:30:05  Tool nmap gestartet (Port-Scan)                │
│ 14:33:00  Tool nmap abgeschlossen (9 Ports)              │
│ 14:33:05  Tool nuclei gestartet (Vuln-Scan)              │
│ 14:34:12  Finding: SQL Injection (Critical, CVSS 9.1)    │
│ 14:34:30  Finding: XSS Reflected (High, CVSS 7.2)        │
│ 14:34:45  Finding: Tomcat Default Creds (High, CVSS 7.5) │
│ 14:35:00  Finding: OpenSSH 7.4 (High, CVSS 7.0)         │
│ 14:35:15  Finding: TLS 1.0 (Medium, CVSS 5.3)           │
│ 14:35:20  Finding: Directory Listing (Medium, CVSS 5.0)  │
│ 14:35:22  Scan Phase 1-3 abgeschlossen                   │
│ 14:35:30  User J. Ruiz genehmigt Exploit auf .5 (Stufe 3)│
│ 14:35:31  Tool sqlmap gestartet (SQL Injection Verify)   │
│ 14:38:30  Tool sqlmap abgeschlossen (Exploit bestätigt)  │
│ 14:39:00  Report Executive Summary generiert             │
│ 14:39:30  Report Technischer Report generiert            │
│ 14:39:30  Scan SC-042 abgeschlossen                      │
└──────────────────────────────────────────────────────────┘
```

### Was der User danach tun kann

```
Nach dem Scan:
│
├── Findings ansehen + filtern (Seite: Findings)
├── Reports herunterladen oder neu generieren (Seite: Reports)
├── Ergebnisse mit dem Agent besprechen (Chat)
│   "Was ist das größte Risiko?"
│   "Wie behebe ich die SQL Injection?"
│   "Vergleiche mit dem letzten Scan"
│
├── Neuen Scan starten
│   Auf gleichem Ziel (Retest nach Fix)
│   Auf anderem Ziel
│   Mit höherer Stufe (Exploitation)
│
└── Ergebnisse teilen
    Report per E-Mail senden (Feature)
    Report für Viewer freigeben (RBAC)
    Findings in Ticketsystem exportieren (später)
```

---

## Datenfluss — Gesamtübersicht

```
User                App-Server           MCP-Server         Sandbox          LLM
 │                      │                    │                 │              │
 │  "Scanne Netz"       │                    │                 │              │
 │─────────────────────▶│                    │                 │              │
 │                      │  Plan erstellen     │                 │              │
 │                      │───────────────────────────────────────────────────▶│
 │                      │                    │                 │    Plan      │
 │                      │◀───────────────────────────────────────────────────│
 │  Plan anzeigen       │                    │                 │              │
 │◀─────────────────────│                    │                 │              │
 │                      │                    │                 │              │
 │  "Starten"           │                    │                 │              │
 │─────────────────────▶│                    │                 │              │
 │                      │  port_scan(target)  │                 │              │
 │                      │───────────────────▶│                 │              │
 │                      │                    │  nmap -sV ...    │              │
 │                      │                    │────────────────▶│              │
 │                      │                    │  Ergebnis        │              │
 │                      │                    │◀────────────────│              │
 │                      │  Scan-Ergebnis     │                 │              │
 │                      │◀───────────────────│                 │              │
 │                      │                    │                 │              │
 │                      │  Ergebnis analysieren                │              │
 │                      │───────────────────────────────────────────────────▶│
 │                      │                    │                 │   Analyse    │
 │                      │◀───────────────────────────────────────────────────│
 │  Findings (Live)     │                    │                 │              │
 │◀═════════════════════│                    │                 │              │
 │  (WebSocket)         │                    │                 │              │
 │                      │                    │                 │              │
 │  "Report erstellen"  │                    │                 │              │
 │─────────────────────▶│                    │                 │              │
 │                      │  Report generieren  │                 │              │
 │                      │───────────────────────────────────────────────────▶│
 │                      │◀───────────────────────────────────────────────────│
 │  Report (PDF)        │                    │                 │              │
 │◀─────────────────────│                    │                 │              │
 │                      │                    │                 │              │
```
