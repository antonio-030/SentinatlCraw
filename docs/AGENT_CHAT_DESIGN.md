# SentinelClaw — Agent-Chat & Interaktionsmodell

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Zweck: Design der zentralen Chat-Schnittstelle zwischen User und KI-Agent

---

## 1. Grundkonzept

Der Agent-Chat ist das **Herzstück** von SentinelClaw. Er ist kein Support-Chatbot — er ist ein **Command Interface** für Security-Profis.

### Was der Chat kann
- **Aufträge erteilen**: "Scanne 10.10.10.0/24 auf offene Ports und bekannte Schwachstellen"
- **Plan besprechen**: Agent zeigt seinen Plan, User kann anpassen
- **Live-Feedback**: Agent berichtet was er gerade tut
- **Entscheidungen genehmigen**: "Ich habe eine SQLi gefunden. Soll ich exploiten?"
- **Nachfragen**: "Erkläre mir das Finding auf Port 3306 genauer"
- **Ergebnisse analysieren**: "Fasse alle Critical Findings zusammen"
- **Reports anfordern**: "Erstelle einen Executive Summary Report"

### Was der Chat NICHT ist
- Kein allgemeiner Chatbot (keine Smalltalk-Fähigkeit)
- Kein Ersatz für die UI (Konfiguration bleibt in den Settings-Seiten)
- Kein unüberwachter Autopilot (Agent fragt bei kritischen Entscheidungen)

---

## 2. Interaktionsmodi

### 2.1 Drei Modi — je nach Phase

```
┌─────────────────────────────────────────────────────────────┐
│  MODUS 1: PLANUNG                                           │
│                                                             │
│  User gibt Auftrag → Agent erstellt Plan → User genehmigt  │
│                                                             │
│  Beispiel:                                                  │
│  User:  "Mach einen Full Recon auf 10.10.10.0/24"          │
│  Agent: "Ich schlage folgenden Plan vor:                    │
│          Phase 1: Port-Scan (nmap, ~5min)                   │
│          Phase 2: Service-Erkennung auf offene Ports        │
│          Phase 3: Vulnerability-Scan (nuclei)               │
│          Geschätzte Dauer: 8 Minuten                        │
│          Token-Verbrauch: ~35.000                           │
│          Soll ich starten?"                                 │
│  User:  "Ja, aber überspringe Phase 3 erstmal"              │
│  Agent: "Verstanden. Starte Phase 1+2 ohne Vuln-Scan."     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MODUS 2: AUSFÜHRUNG (Live)                                 │
│                                                             │
│  Agent führt aus → Berichtet live → User kann eingreifen    │
│                                                             │
│  Agent: "Phase 1 gestartet: nmap -sV -sC 10.10.10.0/24"   │
│  Agent: "5 Hosts gefunden, 23 offene Ports"                 │
│  Agent: "Phase 2: Analysiere Services..."                   │
│  Agent: "⚠ MySQL 5.7 auf 10.10.10.5:3306 — bekannte CVEs" │
│  User:  "Stopp, zeig mir die CVEs für den MySQL"            │
│  Agent: "CVE-2023-xxxx (CVSS 8.1): Remote Code Execution   │
│          CVE-2023-yyyy (CVSS 7.5): Auth Bypass              │
│          Soll ich einen Exploit versuchen? (Stufe 3)"       │
│  User:  "Nein, nur dokumentieren. Weiter mit dem Rest."     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MODUS 3: ANALYSE (Nach Scan)                               │
│                                                             │
│  Scan fertig → User fragt → Agent analysiert Ergebnisse     │
│                                                             │
│  User:  "Was sind die 3 kritischsten Probleme?"             │
│  Agent: "1. SQL Injection auf 10.10.10.5:3306 (CVSS 9.1)   │
│          2. XSS auf 10.10.10.5:443/search (CVSS 7.2)       │
│          3. Veraltetes OpenSSH 7.4 auf .10.3 (CVSS 7.0)    │
│                                                             │
│          Die SQL Injection ist am kritischsten weil sie     │
│          ohne Authentifizierung ausnutzbar ist."             │
│  User:  "Erstelle einen Report für das Management"          │
│  Agent: "Generiere Executive Summary... [Report fertig →]"  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Genehmigungssystem (Approval Flow)

### 3.1 Wann fragt der Agent?

Der Agent arbeitet NICHT komplett autonom. Bei bestimmten Aktionen **MUSS** er um Genehmigung fragen:

| Aktion | Agent fragt? | Wer darf genehmigen |
|---|---|---|
| Passiver Scan (Stufe 0) | Nein, nur informieren | — |
| Port-Scan (Stufe 1) | Nein, wenn im Plan genehmigt | — |
| Vuln-Check (Stufe 2) | Nein, wenn im Plan genehmigt | — |
| **Exploitation (Stufe 3)** | **JA, pro Ziel** | SECURITY_LEAD+ |
| **Post-Exploitation (Stufe 4)** | **JA, pro Aktion** | ORG_ADMIN |
| Scope-Erweiterung | **JA, immer** | ORG_ADMIN |
| Neues Tool das nicht im Plan war | **JA** | SECURITY_LEAD+ |
| Credential-Fund | Informiert sofort | — |
| Critical Finding | Informiert sofort | — |

### 3.2 Approval-Nachricht im Chat

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 Agent                                                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  ⚠ GENEHMIGUNG ERFORDERLICH                           │  │
│  │                                                        │  │
│  │  Ich habe eine ausnutzbare SQL-Injection auf            │  │
│  │  10.10.10.5:3306 gefunden (CVE-2024-1234, CVSS 9.1).  │  │
│  │                                                        │  │
│  │  Vorgeschlagene Aktion:                                │  │
│  │  → Exploit mit sqlmap ausführen um Zugriff zu beweisen │  │
│  │  → Eskalationsstufe: 3 (Exploitation)                  │  │
│  │  → Geschätzte Dauer: 2-5 Minuten                       │  │
│  │  → Risiko: Niedrig (Read-only, kein Schreibzugriff)    │  │
│  │                                                        │  │
│  │  [Genehmigen ✓]  [Ablehnen ✗]  [Mehr Details]         │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.3 Was passiert bei "Ablehnen"?

```
User klickt [Ablehnen ✗]
    │
    ▼
Agent: "Verstanden. Ich dokumentiere den Fund ohne Exploitation
        und fahre mit dem nächsten Ziel fort."
    │
    ▼
Audit-Log: "User J. Ruiz hat Exploit auf 10.10.10.5 abgelehnt"
    │
    ▼
Finding wird gespeichert als: "SQL Injection (nicht verifiziert durch Exploit)"
```

---

## 4. Chat-UI Design

### 4.1 Layout — Chat als rechtes Panel

Der Chat ist KEIN eigener Bildschirm — er ist ein **persistent Panel** das neben dem Hauptcontent steht:

```
┌─────────────────────────────────────────────────────────────────┐
│  Top Bar                                     [🔴 NOTAUS] [👤]   │
├──────────┬────────────────────────┬─────────────────────────────┤
│          │                        │                             │
│ Sidebar  │  MAIN CONTENT          │  AGENT CHAT                 │
│          │                        │  (400px, resizable)         │
│          │  (Dashboard, Findings, │                             │
│          │   Reports, Settings,   │  ┌───────────────────────┐  │
│          │   etc.)                │  │  Nachrichten...        │  │
│          │                        │  │                        │  │
│          │                        │  │  ...                   │  │
│          │                        │  │                        │  │
│          │                        │  │                        │  │
│          │                        │  │                        │  │
│          │                        │  │                        │  │
│          │                        │  │                        │  │
│          │                        │  ├────────────────────────┤  │
│          │                        │  │  [Nachricht eingeben]  │  │
│          │                        │  │  [Senden ↵]            │  │
│          │                        │  └───────────────────────┘  │
└──────────┴────────────────────────┴─────────────────────────────┘
```

**Verhalten:**
- Chat-Panel ist rechts, **immer verfügbar** (wie Slack-Sidebar)
- Ein/ausklappbar mit Tastatur `]` oder Chat-Icon in Top Bar
- Breite einstellbar (300px – 600px), Default 400px
- Chat bleibt erhalten beim Seitenwechsel (Kontext geht nicht verloren)
- Bei schmalem Bildschirm: Chat als Overlay / Slide-Over

### 4.2 Chat-Panel Detail

```
┌─────────────────────────────────────┐
│  Agent-Chat              [─] [□] [×]│
│  Scan: SC-042 (aktiv)    [📎] [⚙]  │
├─────────────────────────────────────┤
│                                     │
│  ┌─ 14:28 ──────────────────────┐   │
│  │ 👤 Du                        │   │
│  │ Mach einen vollständigen     │   │
│  │ Recon auf 10.10.10.0/24     │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 14:28 ──────────────────────┐   │
│  │ 🤖 Orchestrator              │   │
│  │                              │   │
│  │ Ich erstelle einen Plan:     │   │
│  │                              │   │
│  │ ┌──────────────────────────┐ │   │
│  │ │ 📋 Scan-Plan             │ │   │
│  │ │                          │ │   │
│  │ │ Ziel: 10.10.10.0/24     │ │   │
│  │ │ Stufe: 2 (Vuln-Check)   │ │   │
│  │ │                          │ │   │
│  │ │ Phase 1: Host Discovery  │ │   │
│  │ │   └ nmap -sn (~1 min)   │ │   │
│  │ │ Phase 2: Port-Scan       │ │   │
│  │ │   └ nmap -sV -sC (~5min)│ │   │
│  │ │ Phase 3: Vuln-Scan       │ │   │
│  │ │   └ nuclei (~3 min)     │ │   │
│  │ │                          │ │   │
│  │ │ Geschätzt: ~9 Min        │ │   │
│  │ │ Tokens: ~35.000          │ │   │
│  │ └──────────────────────────┘ │   │
│  │                              │   │
│  │ Soll ich so starten?        │   │
│  │                              │   │
│  │ [Plan anpassen] [Starten ✓] │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 14:29 ──────────────────────┐   │
│  │ 👤 Du                        │   │
│  │ Ja, starte.                  │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 14:29 ──────────────────────┐   │
│  │ 🤖 Orchestrator              │   │
│  │ ✓ Scan SC-042 gestartet.     │   │
│  │                              │   │
│  │ Phase 1: Host Discovery...   │   │
│  │ ⏳ nmap -sn 10.10.10.0/24   │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 14:30 ──────────────────────┐   │
│  │ 🔧 Recon-Agent               │   │
│  │ Host Discovery abgeschlossen │   │
│  │ → 7 aktive Hosts gefunden    │   │
│  │                              │   │
│  │ ┌──────────────────────────┐ │   │
│  │ │ 🖥 Hosts                 │ │   │
│  │ │ 10.10.10.1  (Gateway)   │ │   │
│  │ │ 10.10.10.3  (Linux)     │ │   │
│  │ │ 10.10.10.5  (Linux)     │ │   │
│  │ │ 10.10.10.10 (Windows)   │ │   │
│  │ │ 10.10.10.15 (Linux)     │ │   │
│  │ │ 10.10.10.20 (unbekannt) │ │   │
│  │ │ 10.10.10.25 (Linux)     │ │   │
│  │ └──────────────────────────┘ │   │
│  │                              │   │
│  │ Starte Phase 2: Port-Scan   │   │
│  └──────────────────────────────┘   │
│                                     │
│  ┌─ 14:34 ──────────────────────┐   │
│  │ 🔧 Recon-Agent               │   │
│  │ 🔴 CRITICAL Finding!         │   │
│  │                              │   │
│  │ ┌──────────────────────────┐ │   │
│  │ │ SQL Injection            │ │   │
│  │ │ 10.10.10.5:3306 (MySQL)  │ │   │
│  │ │ CVSS 9.1 — Critical      │ │   │
│  │ │ CVE-2024-1234            │ │   │
│  │ │                          │ │   │
│  │ │ [Details] [Zum Finding →]│ │   │
│  │ └──────────────────────────┘ │   │
│  │                              │   │
│  │ ⚠ GENEHMIGUNG ERFORDERLICH  │   │
│  │ Soll ich den Exploit         │   │
│  │ verifizieren? (Stufe 3)     │   │
│  │                              │   │
│  │ [Genehmigen] [Ablehnen]     │   │
│  │ [Nur dokumentieren]          │   │
│  └──────────────────────────────┘   │
│                                     │
│  ── Agent denkt nach... ──────      │
│  ███░░░░░░░░                        │
│                                     │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐    │
│  │ Nachricht an Agent...    [↵]│    │
│  └─────────────────────────────┘    │
│  [📎 Datei]  [📋 Template]  [⌘]   │
│                                     │
└─────────────────────────────────────┘
```

### 4.3 Nachrichtentypen im Chat

| Typ | Absender | Darstellung | Beispiel |
|---|---|---|---|
| **User-Nachricht** | User | Rechts, dunklerer Hintergrund | "Scanne das Netz" |
| **Agent-Text** | Orchestrator | Links, normaler Text | "Ich erstelle einen Plan..." |
| **Plan-Block** | Orchestrator | Strukturierte Karte (einklappbar) | Phasen, Dauer, Tokens |
| **Tool-Ausführung** | Recon/Sub-Agent | Kompakt, Monospace, mit Status-Icon | "nmap -sV ⏳ läuft..." |
| **Finding-Karte** | Agent | Farbige Karte mit Severity-Badge | CVSS, CVE, Target |
| **Approval-Request** | Agent | Hervorgehobene Karte mit Buttons | [Genehmigen] [Ablehnen] |
| **System-Nachricht** | System | Zentriert, grau, klein | "Scan SC-042 beendet" |
| **Fehler** | System/Agent | Rote Border, Fehler-Icon | "Timeout bei nmap" |
| **Host-/Service-Liste** | Agent | Kompakte Tabelle (einklappbar) | Hosts + Ports |

### 4.4 Rich-Content im Chat

Der Chat zeigt nicht nur Text — er rendert **strukturierte Inhalte**:

```
┌─ Plan-Karte (einklappbar) ───────────────────────────┐
│ 📋 Scan-Plan für 10.10.10.0/24                    [▾]│
│                                                       │
│ Phase 1: Host Discovery ─────── nmap -sn ─── ~1 min  │
│ Phase 2: Port-Scan ──────────── nmap -sV ─── ~5 min  │
│ Phase 3: Vulnerability ─────── nuclei ────── ~3 min  │
│                                                       │
│ Gesamt: ~9 Minuten | ~35.000 Tokens | Stufe 2        │
│                                                       │
│ [Plan bearbeiten ✏]                  [Starten ✓]     │
└───────────────────────────────────────────────────────┘

┌─ Finding-Karte ──────────────────────────────────────┐
│ 🔴 CRITICAL                                          │
│                                                       │
│ SQL Injection in Login-Formular                       │
│ 10.10.10.5:3306 (MySQL 8.0)                          │
│ CVE-2024-1234 | CVSS 9.1                             │
│                                                       │
│ Unauthentifizierter Zugriff auf die Datenbank        │
│ über den Parameter "username" im Login-Formular.      │
│                                                       │
│ [Details anzeigen]  [Zum Finding in Findings-Tab →]  │
└───────────────────────────────────────────────────────┘

┌─ Tool-Ausführung (kompakt) ──────────────────────────┐
│ 🔧 nmap -sV -sC -p 1-1000 10.10.10.5                │
│ ⏳ Läuft seit 45s... | Fortschritt: ██████░░░░ 60%   │
└───────────────────────────────────────────────────────┘

┌─ Tool-Ergebnis (einklappbar) ────────────────────────┐
│ ✅ nmap abgeschlossen (52s)                       [▾]│
│                                                       │
│ PORT     STATE  SERVICE  VERSION                      │
│ 22/tcp   open   ssh      OpenSSH 8.9                  │
│ 80/tcp   open   http     nginx 1.24.0                 │
│ 443/tcp  open   https    nginx 1.24.0                 │
│ 3306/tcp open   mysql    MySQL 8.0.32                 │
│ 8080/tcp open   http     Apache Tomcat 9.0            │
└───────────────────────────────────────────────────────┘

┌─ Approval-Request ───────────────────────────────────┐
│ ⚠ GENEHMIGUNG ERFORDERLICH                           │
│                                                       │
│ Der Agent möchte die gefundene SQL-Injection          │
│ auf 10.10.10.5:3306 mit sqlmap verifizieren.          │
│                                                       │
│ Eskalation: Stufe 2 → Stufe 3 (Exploitation)         │
│ Tool: sqlmap --url ... --dbs                          │
│ Geschätzte Dauer: 2-5 Minuten                         │
│ Risiko: Niedrig (Read-only)                           │
│                                                       │
│ [✓ Genehmigen]  [✗ Ablehnen]  [Nur dokumentieren]   │
└───────────────────────────────────────────────────────┘
```

---

## 5. Eingabemöglichkeiten

### 5.1 Freitext-Eingabe (Hauptmethode)

```
┌──────────────────────────────────────────┐
│ Scanne alle Webserver im Netz auf XSS  [↵]│
└──────────────────────────────────────────┘
```

Der Agent versteht natürliche Sprache:
- "Scanne 10.10.10.5 auf offene Ports"
- "Zeig mir alle High/Critical Findings"
- "Erkläre den Fund auf Port 3306"
- "Wie gefährlich ist das XSS?"
- "Erstelle einen Report"
- "Stopp den aktuellen Scan"

### 5.2 Schnellbefehle (Slash-Commands)

```
/scan <ziel>              → Schnell-Scan starten
/plan                     → Aktuellen Plan anzeigen
/status                   → Scan-Status
/findings                 → Findings-Zusammenfassung
/report <typ>             → Report generieren
/stop                     → Aktuellen Scan stoppen
/approve                  → Letzte Anfrage genehmigen
/reject                   → Letzte Anfrage ablehnen
/help                     → Verfügbare Befehle
/explain <finding-id>     → Finding erklären
/escalate <stufe>         → Eskalationsstufe ändern (mit Genehmigung)
```

Slash-Commands erscheinen als Autocomplete beim Tippen von `/`:

```
┌──────────────────────────────────────────┐
│ /sc                                    [↵]│
├──────────────────────────────────────────┤
│ 📋 /scan <ziel>   Schnell-Scan starten  │
│ 📊 /status        Scan-Status anzeigen   │
│ 🛑 /stop          Scan stoppen           │
└──────────────────────────────────────────┘
```

### 5.3 Kontext-Aktionen (Buttons im Chat)

Statt nur Text zu tippen, kann der User auf Buttons in Agent-Nachrichten klicken:
- `[Starten ✓]` → Plan genehmigen und Scan starten
- `[Genehmigen]` / `[Ablehnen]` → Exploit-Genehmigung
- `[Details]` → Mehr Infos zu einem Finding
- `[Plan bearbeiten ✏]` → Plan-Editor öffnen
- `[Zum Finding →]` → Zum Finding in der Findings-Tab navigieren

### 5.4 Datei-Anhänge

```
[📎 Datei]  → Scope-Datei hochladen (YAML/JSON)
             → Nmap-Output importieren
             → Target-Liste hochladen (TXT, CSV)
```

### 5.5 Quick-Templates

```
[📋 Template] → Vorgefertigte Aufträge:
  • "Standard Recon (Stufe 1-2)"
  • "Full Pentest (Stufe 1-4)"
  • "Web Application Assessment"
  • "Netzwerk-Perimeter-Scan"
  • "Nur Vulnerability-Check (kein Exploit)"
```

---

## 6. Multi-Agent-Kommunikation im Chat

### 6.1 Wer spricht im Chat?

```
🤖 Orchestrator    — Plant, koordiniert, fasst zusammen
🔧 Recon-Agent     — Berichtet über Scans und Findings
🗡️ Exploit-Agent   — Berichtet über Exploitation (später)
🌐 Web-Agent       — Berichtet über Web-App-Tests (später)
🔍 OSINT-Agent     — Berichtet über öffentliche Informationen (später)
⚙️ System          — Technische Meldungen (Timeout, Fehler, etc.)
👤 User            — Der Bediener
```

### 6.2 Agent-Nachrichten unterscheiden

Jeder Agent hat eine eigene visuelle Kennung:

```
┌─ 14:30 ─────────────────────────────┐
│ 🤖 Orchestrator                      │
│ Starte Phase 1: Host Discovery       │
│ Delegiere an Recon-Agent...          │
└──────────────────────────────────────┘

┌─ 14:30 ─────────────────────────────┐
│ 🔧 Recon-Agent                       │
│ nmap -sn 10.10.10.0/24              │
│ ⏳ Läuft...                          │
└──────────────────────────────────────┘

┌─ 14:31 ─────────────────────────────┐
│ 🔧 Recon-Agent                       │
│ ✅ 7 Hosts gefunden                  │
└──────────────────────────────────────┘

┌─ 14:31 ─────────────────────────────┐
│ 🤖 Orchestrator                      │
│ Phase 1 abgeschlossen. 7 Hosts.     │
│ Starte Phase 2: Port-Scan auf       │
│ allen gefundenen Hosts...            │
└──────────────────────────────────────┘
```

### 6.3 Verbosity-Level (einstellbar)

| Level | Was wird angezeigt | Für wen |
|---|---|---|
| **Minimal** | Nur Ergebnisse und Genehmigungsanfragen | Management, Viewer |
| **Normal** (Default) | Phasen-Updates, Findings, Zusammenfassungen | Security Lead, Analyst |
| **Detailliert** | Jeder Tool-Aufruf, jeder Parameter, Raw-Output einklappbar | Pentester, Entwickler |

Einstellbar über `[⚙]` im Chat-Header.

---

## 7. Chat-Kontext & Sessions

### 7.1 Chat ist an einen Scan gebunden

```
┌─ Chat-Header ───────────────────────────────────────┐
│ Agent-Chat                                           │
│ ┌────────────────────────────────────────────────┐   │
│ │ [SC-042 (aktiv) ▾]                             │   │
│ │  ○ SC-042 — 10.10.10.0/24 (aktiv)             │   │
│ │  ○ SC-041 — webapp.test.de (fertig)            │   │
│ │  ○ Neuer Chat (kein Scan)                      │   │
│ └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

- Jeder Scan hat seinen eigenen Chat-Verlauf
- Chat wechseln = Scan-Kontext wechseln
- "Neuer Chat" = Allgemeine Fragen oder neuen Scan starten
- Chat-Verlauf bleibt gespeichert (in DB, pro Scan)

### 7.2 Kontext-Awareness

Der Agent weiß immer:
- Welcher Scan gerade läuft
- Welche Findings schon gefunden wurden
- Welche Phase gerade aktiv ist
- Was der User vorher gefragt hat

```
User: "Was hast du auf dem MySQL gefunden?"
Agent: (weiß dass User 10.10.10.5:3306 meint, weil das der
        einzige MySQL im aktuellen Scan ist)
       "Auf 10.10.10.5:3306 habe ich folgendes gefunden:
        1. SQL Injection (CVSS 9.1)
        2. Veraltete MySQL-Version 8.0.32
        3. Remote-Zugriff ohne IP-Beschränkung"
```

### 7.3 Chat-History durchsuchbar

- `Ctrl+F` im Chat → Suche durch Chat-Verlauf
- Filter nach: Agent, Nachrichtentyp, Zeitraum
- Export als Markdown oder PDF (für Audit)

---

## 8. Agent-Persönlichkeit & Tonalität

### 8.1 Wie der Agent kommuniziert

| Eigenschaft | Beschreibung | Beispiel |
|---|---|---|
| **Sachlich** | Keine Smalltalk, kein "Hallo!" | "Scan SC-042 gestartet." |
| **Präzise** | Zahlen, Fakten, keine Vermutungen | "5 Ports offen, 3 Services identifiziert" |
| **Proaktiv** | Schlägt nächste Schritte vor | "Soll ich die CVEs prüfen?" |
| **Transparent** | Zeigt was er tut und warum | "Nutze nmap -sV weil Service-Version gebraucht wird" |
| **Respektvoll** | Fragt bei kritischen Entscheidungen | "Soll ich exploiten? Stufe 3 erforderlich." |
| **Sprache** | Deutsch oder Englisch (nach UI-Sprache) | Passt sich an User-Setting an |

### 8.2 Was der Agent NICHT tut

- Keine Emojis (außer Severity-Icons und Status-Icons)
- Kein Humor oder Sarkasmus
- Keine Entschuldigungen ("Es tut mir leid...") — stattdessen Fakten
- Keine Vermutungen als Fakten darstellen
- Keine sensiblen Daten im Chat-Text (Passwörter werden maskiert)

### 8.3 Beispiel-Konversation (vollständig)

```
👤 Du (14:28):
Ich möchte das interne Testnetz 10.10.10.0/24 auf Schwachstellen
prüfen. Fokus auf Webservices und Datenbanken.

🤖 Orchestrator (14:28):
Verstanden. Ich erstelle einen Scan-Plan für 10.10.10.0/24 mit
Fokus auf Web und Datenbank-Services.

📋 Scan-Plan
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ziel:     10.10.10.0/24
Fokus:    Webservices (HTTP/HTTPS) + Datenbanken (MySQL, PostgreSQL, MSSQL)
Stufe:    2 (Vulnerability Check)

Phase 1 — Host Discovery                        ~1 min
  └ nmap -sn: Aktive Hosts finden

Phase 2 — Port-Scan (nur Web + DB Ports)         ~3 min
  └ nmap -sV -p 80,443,3306,5432,1433,8080,8443

Phase 3 — Web Vulnerability Scan                  ~5 min
  └ nuclei -t cves,vulnerabilities,misconfiguration
  └ Fokus auf OWASP Top 10

Geschätzte Dauer:  9 Minuten
Token-Budget:      ~35.000 von 50.000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Soll ich so starten?

[Plan anpassen ✏]  [Starten ✓]

👤 Du (14:29):
Port 8080 auch noch mit aufnehmen.

🤖 Orchestrator (14:29):
Port 8080 ist bereits im Plan enthalten (Zeile 2).
Soll ich weitere Ports hinzufügen?

👤 Du (14:29):
Stimmt, übersehen. Starte.

🤖 Orchestrator (14:29):
✓ Scan SC-042 gestartet.

🔧 Recon-Agent (14:29):
Phase 1: Host Discovery
nmap -sn 10.10.10.0/24
⏳ Läuft...

🔧 Recon-Agent (14:30):
✅ Phase 1 abgeschlossen (48s)
7 aktive Hosts gefunden.

🤖 Orchestrator (14:30):
7 Hosts im Netz. Starte Port-Scan auf Web- und DB-Ports.

🔧 Recon-Agent (14:30):
Phase 2: Port-Scan
nmap -sV -p 80,443,3306,5432,1433,8080,8443 10.10.10.3,5,10,15,20,25
⏳ Läuft...

🔧 Recon-Agent (14:33):
✅ Phase 2 abgeschlossen (2min 45s)

┌ Ergebnisse ──────────────────────────────────┐
│ Host          Port   Service    Version       │
│ 10.10.10.3    443    https      nginx 1.24    │
│ 10.10.10.5    80     http       nginx 1.24    │
│ 10.10.10.5    443    https      nginx 1.24    │
│ 10.10.10.5    3306   mysql      MySQL 8.0.32  │
│ 10.10.10.10   8080   http       Tomcat 9.0    │
│ 10.10.10.15   5432   postgresql PostgreSQL 15  │
└──────────────────────────────────────────────┘

4 Hosts mit Web/DB-Services. Starte Vulnerability-Scan.

🔧 Recon-Agent (14:33):
Phase 3: Vulnerability Scan
nuclei -t cves,vulnerabilities,misconfiguration
Ziele: 10.10.10.3, .5, .10, .15
⏳ Läuft...

🔧 Recon-Agent (14:34):
🔴 CRITICAL Finding!

┌ SQL Injection ──────────────────────────────┐
│ 10.10.10.5:3306 (MySQL 8.0.32)              │
│ CVSS 9.1 — Critical                         │
│ CVE-2024-1234                                │
│                                              │
│ Login-Formular anfällig für SQL Injection    │
│ im Parameter "username". Unauthentifizierter │
│ Zugriff auf Datenbank möglich.               │
│                                              │
│ [Details ↗]  [Zum Finding →]                 │
└──────────────────────────────────────────────┘

⚠ GENEHMIGUNG ERFORDERLICH

Ich kann die SQL-Injection mit sqlmap verifizieren.
Das wäre Eskalationsstufe 3 (Exploitation).

Aktion: sqlmap — nur Lesezugriff, kein Schreibzugriff
Risiko: Niedrig
Dauer: 2-5 Minuten

[✓ Genehmigen]  [✗ Ablehnen]  [Nur dokumentieren]

👤 Du (14:35):
Nur dokumentieren. Was hast du noch gefunden?

🤖 Orchestrator (14:35):
Verstanden, dokumentiere ohne Exploit-Verifikation.

Bisherige Findings:

 # │ Severity │ Finding              │ Ziel
 1 │ 🔴 9.1   │ SQL Injection        │ .5:3306
 2 │ 🟠 7.2   │ XSS Reflected        │ .5:443
 3 │ 🟠 7.0   │ Tomcat Manager offen  │ .10:8080
 4 │ 🟡 5.3   │ TLS 1.0 aktiv        │ .3:443
 5 │ 🟡 4.8   │ Directory Listing     │ .5:80

Scan läuft noch — nuclei prüft .15 (PostgreSQL).

👤 Du (14:36):
Der Tomcat Manager offen ist auch kritisch. Kannst du prüfen
ob Default-Credentials funktionieren?

🤖 Orchestrator (14:36):
Default-Credential-Check auf Tomcat Manager wäre
Eskalationsstufe 3 (Brute-Force mit hydra).

Vorgeschlagene Aktion:
→ hydra mit Tomcat-Default-Liste (admin:admin, tomcat:tomcat, etc.)
→ Nur 5 gängige Kombinationen, kein vollständiger Bruteforce
→ Dauer: ~30 Sekunden

[✓ Genehmigen]  [✗ Ablehnen]

👤 Du (14:36):
Genehmigt.

🔧 Recon-Agent (14:36):
hydra -L tomcat_defaults.txt -P tomcat_defaults.txt
  10.10.10.10 http-get /manager/html
⏳ Läuft...

🔧 Recon-Agent (14:37):
🔴 CRITICAL Finding!

Default-Credentials funktionieren!
Login: tomcat / tomcat
Zugriff auf Tomcat Manager bestätigt.

┌ Tomcat Default Credentials ─────────────────┐
│ 10.10.10.10:8080 (Apache Tomcat 9.0)        │
│ CVSS 9.8 — Critical                         │
│                                              │
│ Tomcat Manager mit Default-Passwort          │
│ erreichbar. Ermöglicht WAR-Deployment        │
│ → Remote Code Execution möglich.             │
│                                              │
│ Credentials: tomcat:████████                 │
│ (maskiert — Details im Finding)              │
└──────────────────────────────────────────────┘

🤖 Orchestrator (14:37):
Das ist das kritischste Finding bisher.
Über den Tomcat Manager kann ein Angreifer beliebigen
Code auf dem Server ausführen.

Empfehlung: Sofort den Manager-Zugang sperren oder
das Passwort ändern.

Soll ich weiterscannen oder einen Zwischenbericht erstellen?

👤 Du (14:38):
Scan beenden und Report erstellen.

🤖 Orchestrator (14:38):
✅ Scan SC-042 beendet.

Zusammenfassung:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dauer:      10 Minuten
Hosts:      7 gescannt
Findings:   6 gesamt
  🔴 Critical:  2
  🟠 High:      2
  🟡 Medium:    2
Tokens:     28.400 von 50.000
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Welchen Report-Typ soll ich erstellen?
○ Executive Summary (2-3 Seiten, für Management)
○ Technischer Report (Detail, alle Findings)
○ Compliance-Report (BSI/ISO Mapping)

👤 Du (14:38):
Executive Summary und technischen Report.

🤖 Orchestrator (14:38):
Generiere beide Reports...
⏳ Executive Summary...
✅ Executive Summary fertig → [Download PDF ⬇]
⏳ Technischer Report...
✅ Technischer Report fertig → [Download PDF ⬇]

Beide Reports sind auch unter Reports → SC-042 verfügbar.
```

---

## 9. Technische Umsetzung

### 9.1 WebSocket für Echtzeit

```typescript
// Chat nutzt WebSocket für bidirektionale Echtzeit-Kommunikation
interface ChatWebSocket {
  // User → Server
  sendMessage(text: string, scanId?: string): void;
  sendApproval(requestId: string, approved: boolean): void;
  sendCommand(command: SlashCommand): void;

  // Server → User (Events)
  onAgentMessage(callback: (msg: AgentMessage) => void): void;
  onToolExecution(callback: (exec: ToolExecution) => void): void;
  onFindingDiscovered(callback: (finding: Finding) => void): void;
  onApprovalRequest(callback: (req: ApprovalRequest) => void): void;
  onScanStatusChange(callback: (status: ScanStatus) => void): void;
}
```

### 9.2 Nachrichtentypen (TypeScript)

```typescript
type ChatMessage =
  | UserMessage           // Text vom User
  | AgentTextMessage      // Text vom Agent
  | PlanMessage           // Strukturierter Scan-Plan
  | ToolExecutionMessage  // Tool-Aufruf + Status
  | FindingMessage        // Entdecktes Finding
  | ApprovalRequest       // Genehmigungsanfrage
  | SystemMessage         // Systemmeldung
  | ErrorMessage          // Fehlermeldung
  | ReportReadyMessage;   // Report fertig

interface AgentTextMessage {
  id: string;
  type: "agent_text";
  agent: "orchestrator" | "recon" | "exploit" | "web" | "osint";
  content: string;          // Markdown-fähig
  timestamp: string;        // ISO 8601
  scanId: string;
  richContent?: RichContent; // Tabellen, Code-Blöcke, Listen
}

interface ApprovalRequest {
  id: string;
  type: "approval_request";
  agent: string;
  action: string;           // "Exploit SQL Injection mit sqlmap"
  escalationLevel: number;  // 3
  target: string;           // "10.10.10.5:3306"
  tool: string;             // "sqlmap"
  risk: "low" | "medium" | "high";
  estimatedDuration: string; // "2-5 Minuten"
  status: "pending" | "approved" | "rejected";
  respondedBy?: string;     // User-ID wenn beantwortet
  respondedAt?: string;
}
```

### 9.3 Chat-Persistierung

```sql
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id         UUID REFERENCES scan_jobs(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    sender_type     VARCHAR(20) NOT NULL,  -- 'user', 'agent', 'system'
    sender_name     VARCHAR(50),           -- 'orchestrator', 'recon-agent', etc.
    message_type    VARCHAR(30) NOT NULL,  -- 'text', 'plan', 'finding', 'approval', etc.
    content         JSONB NOT NULL,        -- Strukturierter Inhalt
    metadata        JSONB,                 -- Zusätzliche Daten (Tool, Severity, etc.)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- Index für schnelle Abfragen pro Scan
CREATE INDEX idx_chat_messages_scan ON chat_messages(scan_id, created_at);
```

---

## 10. Tastatur-Shortcuts im Chat

| Shortcut | Aktion |
|---|---|
| `Enter` | Nachricht senden |
| `Shift+Enter` | Neue Zeile (kein Senden) |
| `]` | Chat-Panel öffnen/schließen |
| `/` | Slash-Command starten |
| `Ctrl+F` | Im Chat suchen |
| `Esc` | Chat-Suche schließen / Input leeren |
| `↑` | Letzte eigene Nachricht bearbeiten |
| `Ctrl+Shift+A` | Letzte Approval-Anfrage genehmigen |
| `Ctrl+Shift+R` | Letzte Approval-Anfrage ablehnen |
