# ADR-003: LLM-Provider-Strategie

> Status: Akzeptiert
> Datum: 2026-04-04
> Autor: Jaciel Antonio Acea Ruiz

## Kontext

SentinelClaw richtet sich an **Enterprise-Kunden und Behörden** mit strengen Datenschutz-Anforderungen (DSGVO, BSI Grundschutz, ISO 27001). Scan-Ergebnisse, Findings und Ziel-Informationen sind hochsensibel. Diese Daten werden zur Analyse an ein LLM gesendet.

**Kernfrage**: Wohin fließen die Daten, und wer verarbeitet sie?

### Anforderungen
- Kunden mit strengster Compliance → Daten dürfen NICHT ins Ausland
- Kunden mit Standard-Compliance → Cloud-LLM akzeptabel MIT AVV
- Self-Hosted-Kunden → Alles lokal, kein Datenabfluss
- Flexibel: Kunden wählen ihren Provider beim Setup

## Entscheidung

SentinelClaw unterstützt **drei LLM-Provider-Klassen** mit abgestuftem Datenschutzniveau:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM-Provider-Hierarchie                          │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Stufe 1: MAXIMAL (Behörden, VS-NfD, strenge Compliance)   │   │
│  │                                                             │   │
│  │  ★ Ollama (Self-Hosted)                                     │   │
│  │  - Modell läuft auf eigener Hardware                        │   │
│  │  - KEIN Datenabfluss — 0 Bytes verlassen das Netzwerk       │   │
│  │  - Kein AVV nötig                                           │   │
│  │  - Modelle: Llama 3.1, Mistral, Qwen, CodeLlama            │   │
│  │  - Nachteil: Braucht GPU, geringere Qualität als GPT-4/    │   │
│  │             Claude bei komplexen Aufgaben                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Stufe 2: HOCH (Enterprise mit EU-Datenhaltung)             │   │
│  │                                                             │   │
│  │  ★ Azure OpenAI Service                                     │   │
│  │  - Daten bleiben in EU-Rechenzentren (Region wählbar)       │   │
│  │  - AVV im Azure Enterprise Agreement enthalten              │   │
│  │  - Microsoft verarbeitet KEINE Daten für Modelltraining     │   │
│  │  - Modelle: GPT-4o, GPT-4 Turbo                            │   │
│  │  - SOC 2 Type II, ISO 27001, BSI C5 zertifiziert           │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Stufe 3: STANDARD (Startups, Einzelnutzer, PoC)            │   │
│  │                                                             │   │
│  │  ★ Claude (Anthropic API / Max-Abo)                         │   │
│  │  - Beste Reasoning-Qualität für Security-Analyse            │   │
│  │  - Daten verlassen EU (Anthropic: US-Unternehmen)           │   │
│  │  - ⚠ AVV muss separat mit Anthropic geschlossen werden     │   │
│  │  - ⚠ Hinweis an Kunden bei Auswahl erforderlich            │   │
│  │  - Modelle: Claude Sonnet 4, Claude Opus 4                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Provider-Konfiguration

### Setup-Wizard (Produkt)

Beim ersten Start fragt der Setup-Wizard den Kunden:

```
Schritt 3 von 7: LLM-Provider wählen

Welchen KI-Provider möchten Sie für die Security-Analyse nutzen?

  ○ Ollama (Self-Hosted)
    → Höchste Datenschutzstufe. Modell läuft auf Ihrer Hardware.
    → Voraussetzung: GPU mit min. 16GB VRAM empfohlen.
    
  ○ Azure OpenAI Service
    → Daten bleiben in EU-Rechenzentren. AVV über Azure EA abgedeckt.
    → Voraussetzung: Azure-Abonnement mit OpenAI-Zugang.
    
  ○ Claude (Anthropic)
    → Beste Analyse-Qualität. Daten werden an Anthropic (USA) übertragen.
    → ⚠ Für DSGVO-pflichtigen Einsatz: AVV mit Anthropic erforderlich.
    → Voraussetzung: Anthropic API-Key oder Claude Max-Abo.
```

### AVV-Hinweis (Compliance-Warning)

Wenn der Kunde **NICHT** Azure OpenAI oder Ollama wählt, erscheint folgender Hinweis:

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠  Datenschutz-Hinweis                                     │
│                                                              │
│  Sie haben einen Cloud-Provider gewählt, der Daten           │
│  außerhalb der EU verarbeitet (Anthropic, USA).              │
│                                                              │
│  Für den DSGVO-konformen Einsatz in Ihrem Unternehmen       │
│  benötigen Sie einen Auftragsverarbeitungsvertrag (AVV)      │
│  mit Anthropic.                                              │
│                                                              │
│  → Mehr Informationen: anthropic.com/privacy                 │
│                                                              │
│  Für maximalen Datenschutz empfehlen wir:                    │
│  • Azure OpenAI (EU-Rechenzentren, AVV inkludiert)           │
│  • Ollama (komplett lokal, kein Datenabfluss)                │
│                                                              │
│  [ ] Ich habe den Hinweis gelesen und akzeptiere die         │
│      Datenverarbeitung durch den gewählten Provider.         │
│                                                              │
│  [Zurück]                            [Weiter mit Auswahl]   │
└──────────────────────────────────────────────────────────────┘
```

Dieser Hinweis wird:
- Im Audit-Log protokolliert (wann akzeptiert, von wem)
- Bei jedem Provider-Wechsel erneut angezeigt
- NICHT blockierend — nur informierend (Checkbox reicht)

---

## Datenfluss pro Provider

### Was wird an das LLM gesendet?

| Datentyp | Wird gesendet? | Minimierung |
|---|---|---|
| Scan-Ziel (IP/Domain) | Ja | Nur die Ziel-Adresse, keine Metadaten |
| Offene Ports & Services | Ja | Zusammenfassung, nicht Rohdaten |
| Vulnerability-Findings | Ja | CVE-IDs + Kurzbeschreibung, nicht Raw-Output |
| Nmap-Rohausgabe | Nein | Wird lokal geparsed, nur Zusammenfassung geht ans LLM |
| Nuclei-Rohausgabe | Nein | Wird lokal geparsed, nur Findings gehen ans LLM |
| Interne Netzwerk-Topologie | Nein | Wird nie an LLM gesendet |
| Credentials / Zugangsdaten | Nein | Werden vor dem Senden gefiltert |
| Persönliche Daten (PII) | Vermeiden | PII-Filter vor LLM-Aufruf |

### Datenminimierungs-Pipeline

```
Scan-Ergebnis (Rohdaten)
    │
    ▼
[ Lokaler Parser ] ─── Rohausgabe bleibt lokal
    │
    ▼
[ PII-Filter ] ─── E-Mails, Namen, etc. entfernen
    │
    ▼
[ Zusammenfassung ] ─── Nur relevante Findings
    │
    ▼
[ LLM-Provider ] ─── Erhält minimalen, bereinigten Kontext
```

### Provider-spezifische Datenregeln

#### Ollama (Self-Hosted)
- Kein Datenfluss nach außen
- Keine Einschränkungen bei den gesendeten Daten
- PII-Filter optional (empfohlen trotzdem)
- **Hinweis**: "Ihre Daten verlassen das Netzwerk nicht."

#### Azure OpenAI
- Daten fließen zum Azure-Rechenzentrum (EU-Region konfigurierbar)
- Microsoft speichert KEINE Prompts für Modelltraining (bei Azure OpenAI)
- PII-Filter aktiv
- **Hinweis**: "Daten werden in EU-Rechenzentren von Microsoft verarbeitet. AVV ist über Ihr Azure-Abonnement abgedeckt."

#### Claude (Anthropic)
- Daten fließen zu Anthropic (USA)
- PII-Filter PFLICHT
- Datenminimierung PFLICHT
- **Hinweis**: "Daten werden an Anthropic (USA) übertragen. Bitte stellen Sie sicher, dass ein AVV vorliegt."

---

## Technische Umsetzung

### Provider-Abstraktion

```typescript
// Alle Provider implementieren das gleiche Interface
interface LlmProvider {
  readonly name: string;
  readonly complianceLevel: "maximal" | "hoch" | "standard";
  readonly dataLocation: "lokal" | "eu" | "usa";
  readonly requiresAvv: boolean;

  sendPrompt(prompt: SanitizedPrompt): Promise<LlmResponse>;
  estimateTokenCost(prompt: string): number;
  checkAvailability(): Promise<boolean>;
}

// Konkreter Provider wird beim Setup konfiguriert
// und zur Laufzeit über eine Factory geladen
```

### Provider-Konfiguration (.env)

```bash
# Provider-Auswahl: "ollama" | "azure" | "claude"
SENTINEL_LLM_PROVIDER=azure

# --- Ollama (nur wenn Provider = ollama) ---
SENTINEL_OLLAMA_BASE_URL=http://localhost:11434
SENTINEL_OLLAMA_MODEL=llama3.1:70b

# --- Azure OpenAI (nur wenn Provider = azure) ---
SENTINEL_AZURE_ENDPOINT=https://meine-firma.openai.azure.com
SENTINEL_AZURE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SENTINEL_AZURE_DEPLOYMENT=gpt-4o
SENTINEL_AZURE_API_VERSION=2024-08-01-preview

# --- Claude (nur wenn Provider = claude) ---
SENTINEL_CLAUDE_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
SENTINEL_CLAUDE_MODEL=claude-sonnet-4-20250514

# --- Übergreifend ---
SENTINEL_LLM_MAX_TOKENS_PER_SCAN=50000
SENTINEL_LLM_TIMEOUT=120
```

### Token-Budget pro Scan

Um Kosten zu kontrollieren und Endlos-Analysen zu verhindern:

| Parameter | Default | Konfigurierbar |
|---|---|---|
| Max. Tokens pro Scan | 50.000 | Ja |
| Max. Tokens pro Tool-Aufruf | 10.000 | Ja |
| Max. API-Aufrufe pro Scan | 20 | Ja |
| Warnung bei | 80% des Budgets | Ja |
| Harter Stop bei | 100% des Budgets | Ja |

---

## Finding-Benachrichtigung

Wenn der Agent Findings entdeckt, wird der Ablauf wie folgt gesteuert:

```
Finding entdeckt
    │
    ▼
[ 1. Lokal speichern ] ─── Finding sofort in DB persistieren
    │
    ▼
[ 2. Provider informieren ] ─── LLM analysiert den Fund und gibt
    │                           Empfehlungen / Severity-Bewertung
    ▼
[ 3. Ergebnis zusammenführen ] ─── Finding + LLM-Bewertung = Report-Eintrag
    │
    ▼
[ 4. Audit-Log ] ─── Wer hat was gefunden, welcher Provider hat bewertet
```

**Wichtig**: Das Finding wird ZUERST lokal gespeichert, DANN ans LLM geschickt.
Falls der LLM-Provider ausfällt, gehen keine Findings verloren.

---

## Alternativen

### Alternative: Nur ein Provider
- Vorteile: Einfacher zu entwickeln
- Nachteile: Schließt Enterprise-Kunden mit Compliance-Anforderungen aus
- Warum verworfen: Kernzielgruppe sind genau diese Kunden

### Alternative: Eigenes Fine-Tuned Modell
- Vorteile: Volle Kontrolle, keine externen Abhängigkeiten
- Nachteile: Enormer Aufwand, Trainings-Infrastruktur nötig
- Warum verworfen: Nicht im PoC-Scope, evtl. später als Stufe 0

## Konsequenzen

### Positiv
- Jeder Kundentyp findet einen passenden Provider
- DSGVO-Compliance durch Azure und Ollama gewährleistet
- Klare Kommunikation über Datenschutzrisiken
- Provider-Wechsel ohne Code-Änderung möglich

### Negativ
- Drei Provider = dreifacher Integrationsaufwand
- Unterschiedliche Modellqualität (Ollama < Azure ≈ Claude)
- Agent-Prompts müssen für alle Provider funktionieren
- Ollama braucht GPU-Hardware beim Kunden

### Mitigation
- Provider-Abstraktion: Ein Interface, drei Implementierungen
- Prompt-Engineering: Modell-agnostische Prompts
- Empfehlung in Docs: Mindest-Modellgröße für Ollama (70B Parameter)
