# SentinelClaw — UI Design Plan

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Zweck: Visuelles Konzept, Seitenstruktur und Komponenten-Plan für die Web-UI

---

## 1. Design-Philosophie

### 1.1 Ästhetische Richtung: "Tactical Precision"

SentinelClaw orientiert sich an der Designsprache von **hochklassigen Militär- und Aerospace-Interfaces** — nicht die Hollywood-Version mit blinkenden Alarmen, sondern die echte: ruhig, präzise, informationsdicht, fehlerfrei lesbar unter Stress.

**Referenzen:**
- Bloomberg Terminal (Informationsdichte, Effizienz)
- Palantir Gotham (Sicherheits-Ästhetik, Dark UI)
- Linear.app (Modernes SaaS, aufgeräumt, schnell)
- Vercel Dashboard (Developer-Eleganz, klare Hierarchie)

**Was wir NICHT wollen:**
- Neon-Hacker-Ästhetik (Matrix-Terminals, grüne Schrift auf Schwarz)
- Langweilige Behörden-Software (grau, Windows-XP-Look)
- Überladenes Dashboard mit 50 Widgets
- Spielerische/verspielte UI-Elemente

### 1.2 Design-Leitsätze

1. **Information zuerst** — Jedes UI-Element hat einen Grund. Kein dekoratives Füllmaterial.
2. **Ruhe unter Druck** — Wenn ein Critical Finding reinkommt, bleibt die UI ruhig und zeigt klar was zu tun ist.
3. **Progressive Disclosure** — Nicht alles auf einmal zeigen. Details erst bei Bedarf aufklappen.
4. **Vertrauen durch Transparenz** — Der User sieht immer was der Agent gerade tut und warum.

---

## 2. Design System

### 2.1 Farbpalette

```
DARK MODE (Default)
────────────────────────────────────────────

Hintergründe:
  --bg-primary:       #0C0E12    Haupthintergrund (fast Schwarz, leichter Blauschimmer)
  --bg-secondary:     #13161C    Karten, Panels
  --bg-tertiary:      #1A1E27    Hover-States, Sidebar
  --bg-elevated:      #222733    Modals, Dropdowns, Tooltips

Borders & Dividers:
  --border-subtle:    #1E2330    Trennlinien, Kartenränder
  --border-default:   #2A3040    Aktive Borders, Inputs
  --border-strong:    #3A4255    Fokus-States

Text:
  --text-primary:     #E8ECF4    Haupttext (nicht reines Weiß — angenehmer)
  --text-secondary:   #8B95A8    Sekundärtext, Labels
  --text-tertiary:    #5A6478    Platzhalter, deaktivierte Elemente

Akzentfarbe (SentinelClaw Brand):
  --accent-primary:   #3B82F6    Blau — Hauptakzent (Vertrauen, Professionalität)
  --accent-hover:     #2563EB    Blau hover
  --accent-subtle:    #3B82F620  Blau 12% Opacity (Highlights, Badges)

Severity-Farben (CVSS):
  --severity-critical: #EF4444   Rot — Critical (9.0-10.0)
  --severity-high:     #F97316   Orange — High (7.0-8.9)
  --severity-medium:   #EAB308   Gelb — Medium (4.0-6.9)
  --severity-low:      #3B82F6   Blau — Low (0.1-3.9)
  --severity-info:     #6B7280   Grau — Informational

Status-Farben:
  --status-success:   #22C55E    Grün — Erfolgreich, sicher, online
  --status-warning:   #EAB308    Gelb — Warnung, Aufmerksamkeit
  --status-error:     #EF4444    Rot — Fehler, kritisch
  --status-running:   #3B82F6    Blau — Laufend, in Bearbeitung
  --status-idle:      #6B7280    Grau — Inaktiv, gestoppt


LIGHT MODE (Optional)
────────────────────────────────────────────

  --bg-primary:       #F8F9FC
  --bg-secondary:     #FFFFFF
  --bg-tertiary:      #F1F3F8
  --text-primary:     #111827
  --text-secondary:   #4B5563
  (Rest invertiert — Akzent + Severity bleiben gleich)
```

### 2.2 Typografie

```
Headline / Navigation:
  Font: "Geist" (von Vercel, Open Source)
  Fallback: "SF Pro Display", -apple-system, sans-serif
  Gewicht: 500 (Medium) für Headlines, 600 (Semi-Bold) für Nav
  Tracking: -0.02em (leicht enger — wirkt professioneller)

Body / Content:
  Font: "Geist" (gleiche Familie, hohe Lesbarkeit)
  Gewicht: 400 (Regular)
  Größe: 14px Base, 1.6 Line-Height

Monospace (Code, Logs, Scan-Output):
  Font: "Geist Mono" oder "JetBrains Mono"
  Größe: 13px
  Ligatures: ein (für bessere Lesbarkeit von Operatoren)

Daten / Tabellen / Metriken:
  Font: "Geist" Tabular Nums (tnum)
  Damit Zahlen in Tabellen sauber untereinander stehen
```

**Größen-Skala:**
```
--text-xs:    11px    Badges, Timestamps
--text-sm:    12px    Sekundärer Text, Labels
--text-base:  14px    Body Text (Default)
--text-lg:    16px    Subheadings, Card-Titles
--text-xl:    20px    Page Titles
--text-2xl:   24px    Section Headers
--text-3xl:   32px    Dashboard Metriken (große Zahlen)
```

### 2.3 Spacing & Layout

```
Spacing Scale (8px Basis):
  --space-1:   4px
  --space-2:   8px
  --space-3:   12px
  --space-4:   16px
  --space-5:   20px
  --space-6:   24px
  --space-8:   32px
  --space-10:  40px
  --space-12:  48px
  --space-16:  64px

Border Radius:
  --radius-sm:   4px     Buttons, Inputs
  --radius-md:   8px     Karten, Panels
  --radius-lg:   12px    Modals, große Container
  --radius-full: 9999px  Pills, Avatare

Schatten (subtil, nicht aufdringlich):
  --shadow-sm:   0 1px 2px rgba(0,0,0,0.3)
  --shadow-md:   0 4px 12px rgba(0,0,0,0.4)
  --shadow-lg:   0 8px 24px rgba(0,0,0,0.5)
```

### 2.4 Animationen

```
Grundsatz: Dezent und zweckgebunden. Keine Spielereien.

Transitions:
  --transition-fast:    150ms ease-out   Hover, Fokus
  --transition-normal:  250ms ease-out   Panels öffnen/schließen
  --transition-slow:    400ms ease-out   Modals, Seitenwechsel

Wo Animationen:
  ✓ Sidebar ein/ausklappen
  ✓ Karten-Hover (subtiler Lift)
  ✓ Live-Scan: Neue Findings gleiten ein
  ✓ Severity-Badge pulst einmal bei Critical
  ✓ Kill-Switch-Button: Subtiles Glühen wenn Scan aktiv
  ✓ Progress-Indikator bei laufenden Scans

Wo KEINE Animationen:
  ✗ Seitenwechsel (sofort laden, kein Fade)
  ✗ Tabellen (Daten sofort anzeigen)
  ✗ Formulare (keine Slide-in-Effekte)
```

---

## 3. App-Shell & Navigation

### 3.1 Layout-Struktur

```
┌──────────────────────────────────────────────────────────────────┐
│  TOP BAR (56px Höhe)                                             │
│  ┌──────┬────────────────────────────────────┬─────────────────┐ │
│  │ Logo │  Breadcrumb / Seitenname           │ 🔴 KILL  👤 User│ │
│  └──────┴────────────────────────────────────┴─────────────────┘ │
├──────────┬───────────────────────────────────────────────────────┤
│          │                                                       │
│ SIDEBAR  │  MAIN CONTENT                                         │
│ (240px)  │                                                       │
│          │  ┌─────────────────────────────────────────────────┐  │
│ Dashboard│  │                                                 │  │
│ Scans    │  │  Page Content                                   │  │
│ Findings │  │                                                 │  │
│ Reports  │  │                                                 │  │
│ ──────── │  │                                                 │  │
│ Config   │  │                                                 │  │
│ Users    │  │                                                 │  │
│ Audit    │  │                                                 │  │
│ System   │  │                                                 │  │
│          │  │                                                 │  │
│          │  └─────────────────────────────────────────────────┘  │
│          │                                                       │
│ ──────── │  ┌─────────────────────────────────────────────────┐  │
│ v0.1-poc │  │  Status Bar (optional): Laufende Scans, Alerts  │  │
│          │  └─────────────────────────────────────────────────┘  │
└──────────┴───────────────────────────────────────────────────────┘
```

### 3.2 Top Bar — Immer sichtbar

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  [SC Logo]  Dashboard › Scan SC-042 › Live                      │
│                                                                 │
│                          [🔍 Suche... ⌘K]                       │
│                                                                 │
│           [DE|EN]  [🌙]  [🔔 3]  [🔴 NOTAUS]  [👤 J. Ruiz ▾]  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Elemente:
- Logo: "SC" Monogramm + "SentinelClaw" (nur auf breiten Screens)
- Breadcrumb: Zeigt wo man ist, klickbar
- Command Palette: ⌘K öffnet Suchfeld (wie Linear, VS Code)
- Sprache: DE/EN Toggle
- Theme: Dark/Light Toggle
- Notifications: Bell mit Badge-Count
- NOTAUS: Kill Switch — ROT, immer sichtbar, leuchtet subtil wenn Scan aktiv
- User: Avatar + Name + Dropdown (Profil, Logout)
```

### 3.3 Sidebar — Hauptnavigation

```
Oberer Bereich (Tagesgeschäft):
  📊  Dashboard
  🎯  Scans            → Badge: "2 aktiv"
  🔍  Findings         → Badge: "5 neue"
  📄  Reports

Trenner ─────────

Mittlerer Bereich (Konfiguration):
  ⚙️  Konfiguration    → Sub: Provider, Targets, Tools, RoE
  👥  Benutzer          → Sub: User-Liste, Rollen, Einladungen
  📋  Audit-Log
  🖥️  System           → Sub: Docker, Netzwerk, Backup, Encryption

Trenner ─────────

Unterer Bereich (Meta):
  📖  Dokumentation     → Öffnet /docs (kontextsensitiv)
  SentinelClaw v0.1
  Organisation: [Firmenname]
```

**Sidebar-Verhalten:**
- Einklappbar auf Icon-Only (64px) für mehr Platz
- Tastatur: `[` zum Toggling
- Badge-Counts aktualisieren sich live
- Aktiver Menüpunkt: Linker blauer Akzent-Strich

### 3.4 Kill Switch — Immer präsent

```
Zustand: KEIN Scan aktiv
┌──────────┐
│  NOTAUS  │  Grau, deaktiviert, kein Hover-Effekt
└──────────┘

Zustand: Scan AKTIV
┌──────────┐
│ 🔴 NOTAUS│  Rot, subtiles Pulsieren (alle 3s), Hover zeigt Bestätigungsdialog
└──────────┘

Klick → Bestätigungsdialog:
┌─────────────────────────────────────────┐
│  ⚠ Alle laufenden Scans sofort stoppen? │
│                                         │
│  Dies beendet:                          │
│  • 2 aktive Scans                       │
│  • 3 laufende Tool-Prozesse             │
│                                         │
│  Diese Aktion kann nicht rückgängig     │
│  gemacht werden.                        │
│                                         │
│  [Abbrechen]       [ALLE SCANS STOPPEN] │
│                              ↑ Rot      │
└─────────────────────────────────────────┘
```

---

## 4. Seiten im Detail

### 4.1 Setup-Wizard (Erstkonfiguration)

**Wann:** Beim allerersten Start von SentinelClaw — bevor irgendetwas anderes geht.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    [SC]  SentinelClaw                            │
│                    Erstkonfiguration                            │
│                                                                 │
│  ━━━━━━━●━━━━━━━○━━━━━━━○━━━━━━━○━━━━━━━○━━━━━━━○━━━━━━━○      │
│  Willk.  Admin   Provider  DB    Netzwerk  Scan   Fertig        │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  Schritt 1: Willkommen                                    │  │
│  │                                                           │  │
│  │  SentinelClaw ist eine self-hosted Security Assessment    │  │
│  │  Plattform. Dieser Assistent führt Sie durch die          │  │
│  │  Erstkonfiguration.                                       │  │
│  │                                                           │  │
│  │  Sie benötigen:                                           │  │
│  │  ✓ Einen Administrator-Account                            │  │
│  │  ✓ Einen LLM-Provider (Azure OpenAI, Claude, oder Ollama)│  │
│  │  ✓ Docker muss installiert sein                           │  │
│  │                                                           │  │
│  │  Geschätzte Dauer: 5 Minuten                              │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│                                      [Konfiguration starten →]  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

7 Schritte:
1. Willkommen (Übersicht was konfiguriert wird)
2. Admin-Account (E-Mail, Passwort, MFA-Setup)
3. LLM-Provider (Azure/Claude/Ollama + Credentials + AVV-Hinweis)
4. Datenbank (SQLite für PoC / PostgreSQL-Verbindung testen)
5. Netzwerk & Sandbox (Docker-Prüfung, Netzwerk-Policy)
6. Erster Scan-Scope (Testziel konfigurieren)
7. Zusammenfassung & Abschluss (alles prüfen, starten)
```

**Design-Details:**
- Vollbildschirm, kein Sidebar — volle Aufmerksamkeit
- Fortschrittsbalken oben (7 Punkte)
- Jeder Schritt validiert bevor man weiter kann
- Zurück-Button immer verfügbar
- Schritt 3 (Provider): AVV-Hinweis als gelbe Infobox bei Claude-Auswahl

---

### 4.2 Dashboard

**Zweck:** Auf einen Blick sehen was los ist. Keine Interaktion nötig — nur Information.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Dashboard                                   Letzte 24 Stunden ▾│
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │    2     │ │   14     │ │    3     │ │  System: Online  │   │
│  │  aktive  │ │ Findings │ │ Critical │ │  Agent: Bereit   │   │
│  │  Scans   │ │  gesamt  │ │ Findings │ │  LLM: Claude ✓   │   │
│  │  🔵      │ │  🟡      │ │  🔴      │ │  Sandbox: ✓      │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────┐ ┌─────────────────┐   │
│  │  Laufende Scans                     │ │ Letzte Findings  │   │
│  │                                     │ │                  │   │
│  │  SC-042  10.10.10.0/24    ██░░ 45%  │ │ 🔴 SQL Injection │   │
│  │  └ Recon Agent: nmap läuft...       │ │    10.10.10.5    │   │
│  │                                     │ │    vor 12 Min    │   │
│  │  SC-041  webapp.test.de   ████ 100% │ │                  │   │
│  │  └ Abgeschlossen, 5 Findings       │ │ 🟠 XSS Reflected │   │
│  │                                     │ │    webapp.test   │   │
│  │                                     │ │    vor 34 Min    │   │
│  │  [+ Neuen Scan starten]             │ │                  │   │
│  └─────────────────────────────────────┘ │ 🟡 TLS 1.0      │   │
│                                          │    10.10.10.3    │   │
│  ┌─────────────────────────────────────┐ │    vor 1 Std     │   │
│  │  Severity-Verteilung (Woche)        │ │                  │   │
│  │                                     │ │ [Alle anzeigen →]│   │
│  │  ████                Critical: 3    │ └─────────────────┘   │
│  │  ██████████          High: 7        │                       │
│  │  ████████            Medium: 5      │ ┌─────────────────┐   │
│  │  ██                  Low: 2         │ │ Token-Verbrauch  │   │
│  │                      Info: 12       │ │                  │   │
│  └─────────────────────────────────────┘ │ ██████████░ 78%  │   │
│                                          │ 39K / 50K Tokens │   │
│                                          │ diesen Monat     │   │
│                                          └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Komponenten:**
- **Metric Cards** (oben): 4 KPI-Karten — große Zahl + Label + Farbe
- **Laufende Scans**: Live-Fortschrittsbalken, Agent-Status, klickbar für Details
- **Letzte Findings**: Chronologisch, Severity-Badge + Ziel + Zeit
- **Severity-Chart**: Horizontales Balkendiagramm (kein Pie-Chart — schwer lesbar)
- **System-Status**: Grün/Rot pro Komponente (Agent, LLM, Sandbox, DB)
- **Token-Verbrauch**: Fortschrittsbalken mit Budget-Warnung

---

### 4.3 Scan starten

**Zweck:** Neuen Pentest-Auftrag konfigurieren und starten. Mehrstufiges Formular.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Neuen Scan starten                                             │
│                                                                 │
│  ┌─ Ziel ─────────────────────────────────────────────────────┐ │
│  │                                                            │ │
│  │  Ziel-Adresse *                                            │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │ 10.10.10.0/24                                      │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  │  ✓ Ziel ist in der Whitelist                               │ │
│  │                                                            │ │
│  │  Ausgeschlossene Adressen (optional)                       │ │
│  │  ┌────────────────────────────────────────────────────┐    │ │
│  │  │ 10.10.10.1, 10.10.10.50                            │    │ │
│  │  └────────────────────────────────────────────────────┘    │ │
│  │                                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─ Eskalationsstufe ────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ○ Stufe 0: Passiv (DNS, WHOIS)                           │  │
│  │  ○ Stufe 1: Aktiver Scan (nmap, Service Detection)        │  │
│  │  ● Stufe 2: Vulnerability Check (nuclei, nikto)           │  │
│  │  ○ Stufe 3: Exploitation (Metasploit, SQLMap)    🔒       │  │
│  │  ○ Stufe 4: Post-Exploitation (PrivEsc, CredDump) 🔒🔒    │  │
│  │                                                           │  │
│  │  🔒 = Erfordert Rules of Engagement                       │  │
│  │  🔒🔒 = Erfordert RoE + ORG_ADMIN Bestätigung             │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Zeitfenster ─────────────────────────────────────────────┐  │
│  │  Start: [2026-04-14] [08:00]  Ende: [2026-04-14] [18:00] │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Erweitert (einklappbar) ─────────────────────────────────┐  │
│  │  Token-Budget:  [50000] Tokens                            │  │
│  │  LLM-Provider:  [Claude Sonnet 4 ▾]  (aus Systemconfig)  │  │
│  │  Scan-Profil:   [Standard Recon ▾]                        │  │
│  │  Notfallkontakt: [+49 170 1234567]                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌─ Autorisierung ───────────────────────────────────────────┐  │
│  │                                                           │  │
│  │  ⚠ Rechtlicher Hinweis                                    │  │
│  │                                                           │  │
│  │  Dieses Tool darf ausschließlich für autorisierte         │  │
│  │  Sicherheitsüberprüfungen eingesetzt werden.              │  │
│  │  Der Betreiber ist verantwortlich für die schriftliche    │  │
│  │  Genehmigung des Zielsystem-Eigentümers und die           │  │
│  │  Einhaltung aller anwendbaren Gesetze (StGB §202a-c).    │  │
│  │                                                           │  │
│  │  ☐ Ich bestätige die Autorisierung für diesen Scan.       │  │
│  │                                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  [Abbrechen]                              [Scan starten →]     │
│                                           (deaktiviert ohne ☑) │
└─────────────────────────────────────────────────────────────────┘
```

**Wichtige UX-Details:**
- Stufe 3+4 nur wählbar wenn RoE hinterlegt UND User = ORG_ADMIN+
- Disclaimer-Checkbox MUSS gecheckt sein bevor "Scan starten" aktiv wird
- Ziel wird live gegen Whitelist validiert (grüner Haken)
- Ausgeschlossene Adressen werden aus dem Scope entfernt
- "Erweitert" ist standardmäßig eingeklappt — weniger Überladung

---

### 4.4 Live-Scan-Ansicht

**Zweck:** In Echtzeit sehen was der Agent tut. Die spannendste Seite.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Scan SC-042                          ██████░░░░ 62%  ⏱ 04:32  │
│  10.10.10.0/24 · Stufe 2 · Läuft                  [🔴 STOPPEN] │
│                                                                 │
│  ┌─ Agent-Aktivität (Live) ─────────────────────────────────┐   │
│  │                                                          │   │
│  │  14:32:45  Orchestrator                                  │   │
│  │            "Starte Phase 2: Vulnerability Scanning        │   │
│  │             auf 5 entdeckte Services"                     │   │
│  │                                                          │   │
│  │  14:32:46  Recon-Agent → nuclei                          │   │
│  │            Ziel: 10.10.10.5:443 (nginx)                  │   │
│  │            Templates: cves, vulnerabilities               │   │
│  │            ⏳ Läuft...                                    │   │
│  │                                                          │   │
│  │  14:31:20  Recon-Agent → nmap (abgeschlossen ✓)          │   │
│  │            5 offene Ports: 22, 80, 443, 3306, 8080       │   │
│  │            Dauer: 45s                                     │   │
│  │                                                          │   │
│  │  14:30:00  Orchestrator                                  │   │
│  │            "Plane Reconnaissance für 10.10.10.0/24.       │   │
│  │             Phase 1: Port-Scan, Phase 2: Vuln-Check"     │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ Findings (Live) ──────────────┐ ┌─ Scan-Info ───────────┐  │
│  │                                │ │                        │  │
│  │  🔴 CRITICAL  SQL Injection    │ │ Ziel: 10.10.10.0/24   │  │
│  │     10.10.10.5:3306            │ │ Stufe: 2 (Vuln-Check) │  │
│  │     CVE-2024-1234              │ │ Start: 14:28:00        │  │
│  │     CVSS 9.1                   │ │ Agent: Recon-01        │  │
│  │     vor 2 Min  [Details →]     │ │ Tools: nmap, nuclei    │  │
│  │                                │ │ Provider: Claude       │  │
│  │  🟠 HIGH  XSS Reflected       │ │ Tokens: 12.4K / 50K   │  │
│  │     10.10.10.5:443             │ │                        │  │
│  │     CVSS 7.2                   │ │ Scope-Checks: 14/14 ✓ │  │
│  │     vor 5 Min  [Details →]     │ │ Violations: 0          │  │
│  │                                │ │                        │  │
│  │  🟡 MEDIUM  TLS 1.0 aktiv     │ └────────────────────────┘  │
│  │     10.10.10.3:443             │                             │
│  │     CVSS 5.3                   │                             │
│  │     vor 8 Min  [Details →]     │                             │
│  │                                │                             │
│  └────────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

**Besondere Features:**
- **Live-Stream**: Agent-Aktivität scrollt automatisch (wie Logs)
- **Neue Findings gleiten ein** (Animation, subtil)
- **Critical Finding**: Kurzes rotes Pulsieren am Rand — Aufmerksamkeit ohne Panik
- **Token-Verbrauch**: Live-Fortschritt, wird gelb bei 80%
- **Scope-Violations-Counter**: Immer sichtbar, zeigt "0 ✓" im Normalfall
- **STOPPEN-Button**: Rot, nur für diesen Scan (nicht Kill-All)

---

### 4.5 Findings / Results

**Zweck:** Alle Findings durchsuchen, filtern, bewerten, exportieren.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Findings                          [Exportieren ▾] [Filter ▾]  │
│                                                                 │
│  ┌─ Filter-Bar ─────────────────────────────────────────────┐   │
│  │ Severity: [Alle ▾]  Scan: [Alle ▾]  Zeitraum: [7 Tage ▾]│   │
│  │ Suche: [CVE, Tool, IP, Beschreibung...]                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────┬───────────────────────┬──────────┬────────┬────────┐  │
│  │ Sev. │ Finding               │ Ziel     │ CVSS   │ Datum  │  │
│  ├──────┼───────────────────────┼──────────┼────────┼────────┤  │
│  │ 🔴   │ SQL Injection Login   │ .10.5    │  9.1   │ 14:32  │  │
│  │ 🟠   │ XSS Reflected /search│ .10.5    │  7.2   │ 14:27  │  │
│  │ 🟠   │ OpenSSH 7.4 (CVE-...)│ .10.3    │  7.0   │ 14:25  │  │
│  │ 🟡   │ TLS 1.0 aktiv        │ .10.3    │  5.3   │ 14:22  │  │
│  │ 🟡   │ Directory Listing /   │ .10.5    │  5.0   │ 14:20  │  │
│  │ 🔵   │ SSH Password Auth     │ .10.3    │  3.1   │ 14:18  │  │
│  │ ⚪   │ Server Header leakt   │ .10.5    │  0.0   │ 14:15  │  │
│  └──────┴───────────────────────┴──────────┴────────┴────────┘  │
│                                                                 │
│  Seite 1 von 3                    [← Zurück] [1] [2] [3] [→]   │
└─────────────────────────────────────────────────────────────────┘

Finding-Detail (Slide-Over Panel von rechts):
┌──────────────────────────────────────────┐
│  🔴 SQL Injection in Login-Formular   [×]│
│                                          │
│  CVSS 9.1 (Critical)                     │
│  AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N   │
│                                          │
│  ─── Ziel ────────────────────────       │
│  10.10.10.5:3306 (MySQL 8.0)            │
│  Scan: SC-042 | Agent: Recon-01          │
│  Gefunden: 14.04.2026, 14:32:45          │
│                                          │
│  ─── Beschreibung ────────────────       │
│  Das Login-Formular unter /login ist     │
│  anfällig für SQL Injection im           │
│  Parameter "username". ...                │
│                                          │
│  ─── Beweis ──────────────────────       │
│  ┌──────────────────────────────────┐    │
│  │ POST /login HTTP/1.1             │    │
│  │ username=admin' OR 1=1--         │    │
│  │ → 200 OK (Login erfolgreich)     │    │
│  └──────────────────────────────────┘    │
│                                          │
│  ─── Empfehlung ──────────────────       │
│  • Parametrisierte Queries verwenden     │
│  • Input-Validierung implementieren      │
│  • WAF-Regel für SQL Injection           │
│                                          │
│  ─── CVE-Referenz ────────────────       │
│  CVE-2024-1234                           │
│                                          │
│  [Report hinzufügen]  [Als PDF]          │
└──────────────────────────────────────────┘
```

---

### 4.6 Reports

**Zweck:** Compliance-fähige Reports generieren. PDF/DOCX mit Firmenlogo.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Reports                                    [+ Neuer Report]    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Neuen Report erstellen                                  │   │
│  │                                                          │   │
│  │  Template:  [Executive Summary ▾]                        │   │
│  │             ○ Executive Summary (Management, 2-3 Seiten) │   │
│  │             ○ Technischer Report (Detail, 20+ Seiten)    │   │
│  │             ○ Compliance-Report (BSI/ISO Mapping)        │   │
│  │             ○ Findings-Only (Nur die Findings-Tabelle)   │   │
│  │                                                          │   │
│  │  Scan(s):   [SC-042 ▾] (Mehrfachauswahl möglich)        │   │
│  │  Format:    [PDF ▾]  ○ PDF  ○ DOCX  ○ Markdown          │   │
│  │  Sprache:   [Deutsch ▾]                                  │   │
│  │  Logo:      [firma-logo.png hochladen]                   │   │
│  │  Klassif.:  [VERTRAULICH ▾]                              │   │
│  │                                                          │   │
│  │  [Vorschau]                        [Report generieren]   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ── Bisherige Reports ──────────────────────────────────────    │
│                                                                 │
│  📄 SC-042 Executive Summary     PDF  14.04.2026  [⬇ Download] │
│  📄 SC-041 Technischer Report    DOCX 13.04.2026  [⬇ Download] │
│  📄 SC-039 BSI Compliance Report PDF  10.04.2026  [⬇ Download] │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.7 Konfiguration (Das Herzstück — alles konfigurierbar)

**Zweck:** Hier wird ALLES eingestellt. Kein Config-File, kein CLI-Flag — alles in der UI.

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Konfiguration                                                  │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ LLM-Provider │  Scan-Targets  Tools  Eskalation  RoE        │
│  └──────────────┘                                               │
│                                                                 │
│  ─── Aktiver Provider ──────────────────────────────────────    │
│                                                                 │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐         │
│  │               │ │  ●            │ │               │         │
│  │    Ollama     │ │  Azure OpenAI │ │    Claude     │         │
│  │   (Lokal)     │ │  (EU)         │ │  (Anthropic)  │         │
│  │               │ │               │ │               │         │
│  │  Kein Daten-  │ │  DSGVO via    │ │  ⚠ AVV nötig  │         │
│  │  abfluss      │ │  Azure EA     │ │  (Nicht-EU)   │         │
│  │               │ │               │ │               │         │
│  └───────────────┘ └───────────────┘ └───────────────┘         │
│                                                                 │
│  ─── Azure OpenAI Konfiguration ────────────────────────────    │
│                                                                 │
│  Endpoint:    [https://firma.openai.azure.com      ]            │
│  API-Key:     [••••••••••••••••••••]  [Anzeigen] [Testen]       │
│  Deployment:  [gpt-4o              ]                            │
│  API-Version: [2024-08-01-preview  ▾]                           │
│                                                                 │
│  Token-Budget:                                                  │
│  Pro Scan:    [50.000    ] Tokens                               │
│  Pro Monat:   [1.000.000 ] Tokens                               │
│  Timeout:     [120       ] Sekunden                             │
│                                                                 │
│  Status: ✓ Verbindung erfolgreich (getestet vor 2 Min)          │
│                                                                 │
│  [Änderungen speichern]                                         │
└─────────────────────────────────────────────────────────────────┘
```

**Tabs in der Konfiguration:**

**Tab: Scan-Targets (Whitelist)**
```
┌─────────────────────────────────────────────────────────────────┐
│  Scan-Targets  │                           [+ Ziel hinzufügen]  │
│                                                                 │
│  ┌──────────────────┬────────────────┬──────────┬────────────┐  │
│  │ Ziel             │ Beschreibung   │ Status   │ Aktionen   │  │
│  ├──────────────────┼────────────────┼──────────┼────────────┤  │
│  │ 10.10.10.0/24    │ Internes Test  │ ✓ Aktiv  │ [✏][🗑]    │  │
│  │ webapp.test.de   │ Web-App Staging│ ✓ Aktiv  │ [✏][🗑]    │  │
│  │ 192.168.1.0/24   │ Office-Netz    │ ⏸ Pausiert│ [✏][🗑]    │  │
│  └──────────────────┴────────────────┴──────────┴────────────┘  │
│                                                                 │
│  ⚠ Nur Ziele in dieser Liste können gescannt werden.            │
│    Ohne Eintrag ist kein Scan möglich.                          │
└─────────────────────────────────────────────────────────────────┘
```

**Tab: Tools & Eskalationsstufen**
```
┌─────────────────────────────────────────────────────────────────┐
│  Tools  │                                                       │
│                                                                 │
│  ┌──────┬──────────┬──────────────────────┬────────┬─────────┐  │
│  │Stufe │ Tool     │ Beschreibung         │ Status │ Aktion  │  │
│  ├──────┼──────────┼──────────────────────┼────────┼─────────┤  │
│  │  0   │ whois    │ Domain-Informationen │ ✓ Ein  │ [⚙]     │  │
│  │  0   │ dig      │ DNS-Lookup           │ ✓ Ein  │ [⚙]     │  │
│  │  1   │ nmap     │ Port-Scanner         │ ✓ Ein  │ [⚙]     │  │
│  │  1   │ whatweb  │ Web-Tech-Erkennung   │ ✓ Ein  │ [⚙]     │  │
│  │  2   │ nuclei   │ Vuln-Scanner         │ ✓ Ein  │ [⚙]     │  │
│  │  2   │ nikto    │ Web-Server-Scanner   │ ✓ Ein  │ [⚙]     │  │
│  │  3   │ metasploit│ Exploit-Framework   │ ○ Aus  │ [⚙]     │  │
│  │  3   │ sqlmap   │ SQL-Injection        │ ○ Aus  │ [⚙]     │  │
│  │  3   │ hydra    │ Brute-Force          │ ○ Aus  │ [⚙]     │  │
│  │  4   │ linpeas  │ Privilege Escalation │ ○ Aus  │ [⚙]     │  │
│  └──────┴──────────┴──────────────────────┴────────┴─────────┘  │
│                                                                 │
│  ⚙ = Tool-spezifische Einstellungen (Timeouts, Flags, etc.)    │
│                                                                 │
│  Maximale Eskalationsstufe für diese Organisation:              │
│  [■■■□□] Stufe 2: Vulnerability Check                          │
│                                                                 │
│  ⚠ Stufe 3+ erfordert hinterlegte Rules of Engagement          │
│                                                                 │
│  [+ Eigenes Tool hinzufügen]                                    │
└─────────────────────────────────────────────────────────────────┘
```

**Tab: Rules of Engagement**
```
┌─────────────────────────────────────────────────────────────────┐
│  Rules of Engagement  │                      [+ Neue RoE]       │
│                                                                 │
│  ┌──────────────────────┬──────────┬──────────────┬──────────┐  │
│  │ Name                 │ Gültig   │ Max. Stufe   │ Status   │  │
│  ├──────────────────────┼──────────┼──────────────┼──────────┤  │
│  │ Pentest Q2 2026      │ Apr-Mai  │ Stufe 3      │ ✓ Aktiv  │  │
│  │ Webapp-Audit Extern  │ Apr 14-18│ Stufe 2      │ ✓ Aktiv  │  │
│  │ Netzwerk-Check Q1    │ Jan-Mär  │ Stufe 1      │ Abgelauf.│  │
│  └──────────────────────┴──────────┴──────────────┴──────────┘  │
│                                                                 │
│  [RoE bearbeiten → volles Formular mit allen Feldern]           │
│  [RoE als PDF exportieren → für Kundenunterschrift]             │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.8 User-Management

```
┌─────────────────────────────────────────────────────────────────┐
│  Benutzer                                  [+ User einladen]    │
│                                                                 │
│  ┌────────┬─────────────────┬────────────────┬────────┬──────┐  │
│  │ Status │ Name            │ E-Mail         │ Rolle  │ MFA  │  │
│  ├────────┼─────────────────┼────────────────┼────────┼──────┤  │
│  │ 🟢     │ J. Acea Ruiz    │ j@firma.de     │ Admin  │ ✓    │  │
│  │ 🟢     │ M. Schmidt      │ m@firma.de     │ Lead   │ ✓    │  │
│  │ 🟡     │ L. Weber        │ l@firma.de     │ Analyst│ ✗    │  │
│  │ ⚪     │ K. Müller       │ k@firma.de     │ Viewer │ ✗    │  │
│  └────────┴─────────────────┴────────────────┴────────┴──────┘  │
│                                                                 │
│  ── Rollen verwalten ───────────────────────────────────────    │
│  [Rollen & Berechtigungen konfigurieren →]                      │
│                                                                 │
│  Rollen-Übersicht:                                              │
│  ┌─────────────────┬──────┬──────┬───────┬───────┬──────────┐  │
│  │                 │Scans │Users │Reports│System │Audit-Log  │  │
│  │ System Admin    │  ✓   │  ✓   │  ✓    │  ✓    │  ✓       │  │
│  │ Org Admin       │  ✓   │  ✓   │  ✓    │  ○    │  ✓       │  │
│  │ Security Lead   │  ✓   │  ○   │  ✓    │  ○    │  ○       │  │
│  │ Analyst         │  👁  │  ○   │  👁   │  ○    │  ○       │  │
│  │ Viewer          │  👁  │  ○   │  👁   │  ○    │  ○       │  │
│  └─────────────────┴──────┴──────┴───────┴───────┴──────────┘  │
│  ✓ = Voll  👁 = Nur lesen  ○ = Kein Zugriff                    │
│                                                                 │
│  [Berechtigungen anpassen →]                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.9 Audit-Log

```
┌─────────────────────────────────────────────────────────────────┐
│  Audit-Log                     [Exportieren] [Filter ▾]         │
│                                                                 │
│  ⓘ Audit-Einträge sind unveränderbar und können nicht           │
│    gelöscht werden.                                             │
│                                                                 │
│  ┌────────────────────┬──────────┬──────────────────┬────────┐  │
│  │ Zeitpunkt          │ User     │ Aktion           │ Detail │  │
│  ├────────────────────┼──────────┼──────────────────┼────────┤  │
│  │ 14:32:45 14.04.26  │ J. Ruiz  │ scan.started     │  [→]   │  │
│  │ 14:32:44 14.04.26  │ J. Ruiz  │ disclaimer.accept│  [→]   │  │
│  │ 14:30:00 14.04.26  │ System   │ agent.tool_call  │  [→]   │  │
│  │ 14:28:00 14.04.26  │ J. Ruiz  │ scan.created     │  [→]   │  │
│  │ 13:45:12 14.04.26  │ M.Schmidt│ user.login       │  [→]   │  │
│  │ 13:44:50 14.04.26  │ M.Schmidt│ user.login_failed│  [→]   │  │
│  │ 10:00:00 14.04.26  │ System   │ backup.completed │  [→]   │  │
│  └────────────────────┴──────────┴──────────────────┴────────┘  │
│                                                                 │
│  Filter: [Alle Aktionen ▾] [Alle User ▾] [Zeitraum: 7 Tage ▾] │
│  Suche: [Freitext-Suche in Audit-Einträgen...]                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.10 System-Settings

```
┌─────────────────────────────────────────────────────────────────┐
│  System                                                         │
│                                                                 │
│  ┌──────────────┐                                               │
│  │ Übersicht    │  Docker  Netzwerk  Backup  Verschlüsselung   │
│  └──────────────┘                                               │
│                                                                 │
│  ── Systemstatus ───────────────────────────────────────────    │
│                                                                 │
│  ┌────────────────┬──────────┬─────────────┬────────────────┐   │
│  │ Komponente     │ Status   │ Version     │ Letzte Prüfung │   │
│  ├────────────────┼──────────┼─────────────┼────────────────┤   │
│  │ API-Server     │ 🟢 Online│ 0.1.0       │ vor 30s        │   │
│  │ MCP-Server     │ 🟢 Online│ 0.1.0       │ vor 30s        │   │
│  │ Sandbox        │ 🟢 Bereit│ Ubuntu 22.04│ vor 30s        │   │
│  │ PostgreSQL     │ 🟢 Online│ 16.2        │ vor 30s        │   │
│  │ LLM (Azure)    │ 🟢 OK   │ GPT-4o      │ vor 2 Min      │   │
│  └────────────────┴──────────┴─────────────┴────────────────┘   │
│                                                                 │
│  ── Ressourcen ─────────────────────────────────────────────    │
│                                                                 │
│  CPU:     ████████░░░░░░░░  52%                                 │
│  RAM:     ██████░░░░░░░░░░  38%  (6.1 GB / 16 GB)              │
│  Disk:    ████████████░░░░  73%  (58 GB / 80 GB)               │
│  Sandbox: ██░░░░░░░░░░░░░░  12%  (0.5 / 2 CPU, 400MB / 2GB)   │
│                                                                 │
│  ── Schnellaktionen ────────────────────────────────────────    │
│                                                                 │
│  [Sandbox neustarten]  [Logs herunterladen]  [Health-Check]     │
│  [Backup jetzt]        [Updates prüfen]      [Systeminfo]       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Responsive Verhalten

| Breakpoint | Verhalten |
|---|---|
| **> 1440px** (Desktop XL) | Sidebar + Content + Detail-Panel nebeneinander |
| **1024-1440px** (Desktop) | Sidebar + Content, Detail als Slide-Over |
| **768-1024px** (Tablet) | Sidebar einklappbar, Content voll |
| **< 768px** (Mobile) | Hamburger-Menü, vereinfachtes Dashboard, kein Live-Scan |

**Desktop-First**: Die volle Erfahrung ist für 1440px+ optimiert. Mobile zeigt eine reduzierte Version (Dashboard + Findings lesen). Scan starten und Konfiguration sind Desktop-only.

---

## 6. Komponenten-Bibliothek (Zusammenfassung)

### Core Components

| Komponente | Varianten | Zweck |
|---|---|---|
| `Button` | primary, secondary, danger, ghost, icon-only | Aktionen |
| `Input` | text, password, number, search, textarea | Formulare |
| `Select` | single, multi, searchable | Auswahlen |
| `Badge` | severity (5 Farben), status, count | Labels |
| `Card` | default, metric, action | Container |
| `Table` | sortierbar, filterbar, paginiert | Daten |
| `Modal` | confirm, form, alert, fullscreen | Dialoge |
| `SlideOver` | right (Detail-Panels) | Detail-Ansichten |
| `Tabs` | horizontal, vertical | Navigation |
| `Toast` | success, warning, error, info | Benachrichtigungen |
| `Tooltip` | top, bottom, left, right | Hilfe-Texte |
| `Progress` | bar, circle, steps | Fortschritt |
| `Skeleton` | card, table-row, text | Ladezustände |

### Domain-spezifische Components

| Komponente | Zweck |
|---|---|
| `SeverityBadge` | CVSS-Severity mit Farbe (Critical-Info) |
| `ScanProgressCard` | Laufender Scan mit Agent-Status |
| `FindingCard` | Einzelnes Finding mit Severity + Details |
| `ToolExecutionLog` | Live-Anzeige der Tool-Aufrufe |
| `ScopeValidator` | Zeigt ob Ziel im Scope ist (✓/✗) |
| `ProviderSelector` | LLM-Provider-Auswahl mit Datenschutz-Hinweis |
| `KillSwitchButton` | Immer sichtbarer Notaus-Button |
| `DisclaimerCheckbox` | Rechtlicher Hinweis + Bestätigung |
| `AuditLogEntry` | Einzelner Audit-Eintrag mit Details |
| `EscalationSlider` | Stufe 0-4 Auswahl mit Beschreibung |
| `TokenBudgetBar` | Verbrauchsanzeige mit Warnschwelle |
| `RolePermissionMatrix` | Berechtigungsmatrix-Tabelle |

---

## 7. Internationalisierung (i18n)

### 7.1 Unterstützte Sprachen
- **Deutsch** (Default für DACH-Markt)
- **Englisch** (International)

### 7.2 Umsetzung
- Alle UI-Texte über i18n-Keys (kein hardcoded Text)
- Sprache wählbar im Top-Bar (DE/EN Toggle)
- Sprache wird pro User gespeichert
- Datums-/Zeitformat passt sich an Locale an
- Severity-Labels bleiben Englisch (Critical, High, Medium — internationaler Standard)

---

## 8. Barrierefreiheit (Accessibility)

- WCAG 2.1 Level AA
- Alle interaktiven Elemente per Tastatur erreichbar
- Screen-Reader-kompatibel (ARIA-Labels)
- Fokus-Ring immer sichtbar (kein `outline: none`)
- Farbe nie einziger Informationsträger (Icons + Text zu Severity-Farben)
- Kontrast min. 4.5:1 (auch im Dark Mode)
- Keyboard Shortcuts für Power-User (⌘K Suche, [ Sidebar, etc.)
