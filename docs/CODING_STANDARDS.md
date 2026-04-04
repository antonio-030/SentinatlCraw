# SentinelClaw — Coding Standards

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026

---

## 1. Philosophie

**Code wird öfter gelesen als geschrieben.** Jede Zeile muss so klar sein, dass ein neuer Kollege sie ohne Erklärung versteht. Kein "Maschinencode", keine kryptischen Abkürzungen, keine cleveren Tricks.

### Leitprinzipien
1. **Lesbarkeit vor Kürze** — 5 klare Zeilen > 1 kryptische Zeile
2. **Explizit vor Implizit** — Lieber zu deutlich als zu vage
3. **Einfach vor Clever** — Der einfachste Ansatz der funktioniert
4. **Konsistent vor Individuell** — Team-Konventionen schlagen persönliche Vorlieben

---

## 2. Dateistruktur

### 2.1 Maximale Dateigröße: 300 Zeilen

Eine Datei über 300 Zeilen ist ein Zeichen, dass sie zu viel Verantwortung hat. In dem Fall:
- Logische Blöcke in eigene Dateien extrahieren
- Hilfsfunktionen auslagern
- Types/Interfaces in eigene Datei

### 2.2 Datei-Aufbau (TypeScript)
```typescript
// ============================================================
// Datei: recon-agent.ts
// Beschreibung: Führt Netzwerk-Reconnaissance auf Zielhost durch
// ============================================================

// 1. Externe Imports
import { z } from "zod";

// 2. Interne Imports (absolut)
import { ScanResult } from "@/shared/types/scan-result";
import { validateTarget } from "@/shared/utils/validation";

// 3. Typen & Interfaces (nur wenn dateilokal)
interface ReconPhase {
  name: string;
  tools: string[];
}

// 4. Konstanten
const MAX_RETRIES = 3;
const SCAN_TIMEOUT_MS = 300_000;

// 5. Hauptlogik (exportierte Funktionen)
export async function runReconnaissance(target: string): Promise<ScanResult> {
  // ...
}

// 6. Hilfsfunktionen (private, nicht exportiert)
function buildNmapCommand(target: string, ports: string): string[] {
  // ...
}
```

### 2.3 Datei-Aufbau (Python)
```python
"""
Datei: mcp_tools.py
Beschreibung: MCP-Tool-Definitionen für Pentest-Werkzeuge
"""

# 1. Standard Library
import subprocess
from pathlib import Path

# 2. Third Party
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# 3. Lokale Imports
from shared.types import ScanResult
from shared.validation import validate_target

# 4. Konstanten
MAX_SCAN_TIMEOUT = 300
ALLOWED_BINARIES = ["nmap", "nuclei"]

# 5. Typen / Models
class PortScanParams(BaseModel):
    """Parameter für einen Port-Scan."""
    target: str = Field(..., description="Ziel-IP oder Domain")
    ports: str = Field(default="1-1000", description="Port-Range")

# 6. Hauptlogik
def run_port_scan(params: PortScanParams) -> ScanResult:
    """Führt einen nmap Port-Scan auf dem Ziel durch."""
    ...

# 7. Hilfsfunktionen
def _parse_nmap_output(raw: str) -> dict:
    """Parst die nmap-Ausgabe in ein strukturiertes Format."""
    ...
```

---

## 3. Benennungsregeln

### 3.1 Variablen — Selbsterklärend

**Verboten:**
```typescript
const r = await scan(t);          // Was ist r? Was ist t?
const d = Date.now() - s;         // Kryptisch
const tmp = processData(input);   // "tmp" sagt nichts aus
```

**Erlaubt:**
```typescript
const scanResult = await runPortScan(targetAddress);
const elapsedTimeMs = Date.now() - scanStartTime;
const parsedVulnerabilities = parseNucleiOutput(rawOutput);
```

### 3.2 Funktionen — Verb + Substantiv

```typescript
// Gut: Klar was passiert
function validateScanTarget(target: string): boolean { ... }
function buildNmapCommand(target: string): string[] { ... }
function parsePortScanResult(output: string): PortInfo[] { ... }
function formatReportAsMarkdown(findings: Finding[]): string { ... }

// Schlecht: Zu vage
function process(data: any): any { ... }
function handle(input: string): void { ... }
function doStuff(): void { ... }
```

### 3.3 Booleans — Frage-Form

```typescript
const isPortOpen = port.state === "open";
const hasVulnerabilities = findings.length > 0;
const canReachTarget = await checkConnectivity(target);
const shouldRetry = attemptCount < MAX_RETRIES;
```

### 3.4 Collections — Plural

```typescript
const openPorts: PortInfo[] = [];           // Plural = Liste
const vulnerabilityMap: Map<string, Vuln>;  // "Map" Suffix = Map
const scannedTargetSet: Set<string>;        // "Set" Suffix = Set
```

---

## 4. Funktionen

### 4.1 Maximale Länge: 50 Zeilen
Eine Funktion über 50 Zeilen macht zu viel. Aufteilen in:
- Validierung → eigene Funktion
- Datenaufbereitung → eigene Funktion
- Hauptlogik → bleibt
- Formatierung → eigene Funktion

### 4.2 Maximale Parameter: 3
Mehr als 3 Parameter → Options-Objekt verwenden:

```typescript
// Schlecht: Zu viele Parameter
function scanTarget(ip: string, ports: string, timeout: number,
                    flags: string[], retries: number): Promise<ScanResult> { ... }

// Gut: Options-Objekt
interface ScanOptions {
  target: string;
  ports: string;
  timeout: number;
  flags: string[];
  retries: number;
}

function scanTarget(options: ScanOptions): Promise<ScanResult> { ... }
```

### 4.3 Early Returns

```typescript
// Schlecht: Tiefe Verschachtelung
function processTarget(target: string): Result {
  if (target) {
    if (isValidIp(target)) {
      if (isInWhitelist(target)) {
        // ... eigentliche Logik ganz tief verschachtelt
      }
    }
  }
}

// Gut: Early Returns, flache Struktur
function processTarget(target: string): Result {
  if (!target) {
    throw new ValidationError("Kein Ziel angegeben");
  }

  if (!isValidIp(target)) {
    throw new ValidationError("Ungültige IP-Adresse");
  }

  if (!isInWhitelist(target)) {
    throw new SecurityError("Ziel nicht in Whitelist");
  }

  // Hauptlogik auf oberster Ebene — leicht lesbar
  return executeScan(target);
}
```

### 4.4 Verschachtelungstiefe: Max. 3

```typescript
// Schlecht: 5 Ebenen tief
if (a) {
  for (const b of items) {
    if (c) {
      try {
        if (d) {  // Hier verliert man den Überblick
        }
      }
    }
  }
}

// Gut: Flach durch Extraktion
const relevantItems = items.filter(item => meetsCondition(item));
for (const item of relevantItems) {
  await processItem(item);
}
```

---

## 5. Kommentare (Deutsch)

### 5.1 Regel: Erkläre WARUM, nicht WAS

```typescript
// Schlecht: Wiederholt nur den Code
// Inkrementiere den Counter um 1
retryCount += 1;

// Gut: Erklärt die Absicht
// Nuclei braucht manchmal einen zweiten Anlauf wenn das Ziel
// den ersten TCP-Handshake verwirft (bekanntes Verhalten bei IDS)
retryCount += 1;
```

### 5.2 Wann Kommentare nötig sind
- **Business-Logik**: Warum genau dieser Grenzwert / diese Regel?
- **Workarounds**: Was ist das Problem und wo ist der Upstream-Bug?
- **Sicherheitsentscheidungen**: Warum diese Validierung / Einschränkung?
- **Nicht-offensichtliche Abhängigkeiten**: Warum muss A vor B passieren?

### 5.3 Wann KEINE Kommentare
- Offensichtlicher Code: `const port = 443;` braucht keinen Kommentar
- Wenn ein besserer Variablenname den Kommentar überflüssig machen würde
- TODOs ohne Ticket-Referenz — entweder Ticket erstellen oder löschen

---

## 6. Error Handling

### 6.1 Typisierte Errors

```typescript
// Eigene Error-Klassen für verschiedene Fehlerarten
class ScanError extends Error {
  constructor(
    message: string,
    public readonly target: string,
    public readonly tool: string
  ) {
    super(message);
    this.name = "ScanError";
  }
}

class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string,
    public readonly receivedValue: unknown
  ) {
    super(message);
    this.name = "ValidationError";
  }
}

class SandboxError extends Error {
  constructor(
    message: string,
    public readonly containerId: string
  ) {
    super(message);
    this.name = "SandboxError";
  }
}
```

### 6.2 Error-Handling-Regeln
- Fange nur Errors, die du sinnvoll behandeln kannst
- Kein leeres `catch {}` — mindestens loggen
- Error-Messages auf Deutsch für User-facing, Englisch für technische Logs
- Stack Traces nur im DEBUG-Level loggen

---

## 7. Async & Concurrency

### 7.1 Async/Await bevorzugen

```typescript
// Schlecht: Callback-Hölle / Promise-Chains
scanTarget(target)
  .then(result => parseResult(result))
  .then(parsed => formatOutput(parsed))
  .catch(err => handleError(err));

// Gut: Async/Await — linearer Lesefluss
const scanResult = await scanTarget(target);
const parsedResult = parseResult(scanResult);
const formattedOutput = formatOutput(parsedResult);
```

### 7.2 Timeouts überall
Jeder externe Aufruf MUSS einen Timeout haben:

```typescript
const scanResult = await withTimeout(
  runPortScan(target),
  SCAN_TIMEOUT_MS,
  `Port-Scan auf ${target} hat Timeout überschritten`
);
```

---

## 8. Projekt-Imports

### 8.1 Import-Reihenfolge
1. Standard Library / Node Built-ins
2. Externe Packages (npm / PyPI)
3. Interne Shared-Module (`@/shared/...`)
4. Lokale Dateien (relatives Import)

Leerzeile zwischen jeder Gruppe.

### 8.2 Path Aliases

```json
// tsconfig.json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@shared/*": ["./src/shared/*"],
      "@agents/*": ["./src/agents/*"]
    }
  }
}
```

---

## 9. Code-Review-Checkliste

Bei jedem Review diese Punkte prüfen:

- [ ] Datei unter 300 Zeilen?
- [ ] Funktionen unter 50 Zeilen?
- [ ] Variablennamen selbsterklärend?
- [ ] Max. 3 Ebenen Verschachtelung?
- [ ] Deutsche Kommentare erklären das WARUM?
- [ ] Keine Magic Numbers — Konstanten genutzt?
- [ ] Typen explizit — kein `any`?
- [ ] Error Handling mit typisierten Errors?
- [ ] Timeouts für externe Aufrufe gesetzt?
- [ ] Keine auskommentierten Code-Blöcke?
- [ ] Keine Copy-Paste-Duplikation?
- [ ] Imports sortiert und gruppiert?
