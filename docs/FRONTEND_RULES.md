# SentinelClaw — Frontend-Regeln

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Hinweis: Im PoC gibt es keine UI. Diese Regeln greifen ab der Produktentwicklung.

---

## 1. Tech Stack

| Technologie | Version | Zweck |
|---|---|---|
| React | 18+ | UI-Framework |
| TypeScript | 5.x (strict) | Typsicherheit |
| Vite | 6.x | Build-Tool & Dev-Server |
| Tailwind CSS | 4.x | Styling |
| React Query (TanStack) | 5.x | Server State & Caching |
| Zustand | 5.x | Client State (nur wenn nötig) |
| React Router | 7.x | Routing |
| Zod | 3.x | Schema-Validierung |
| Vitest | 2.x | Unit Tests |
| Playwright | 1.x | E2E Tests |

### Verboten
- **Redux** — zu viel Boilerplate für dieses Projekt
- **CSS-in-JS** (styled-components, Emotion) — Tailwind reicht
- **Class Components** — nur funktionale Components
- **jQuery** — nein
- **Moment.js** — `date-fns` oder native `Intl` API

---

## 2. Projektstruktur (Frontend)

```
src/
├── ui/
│   ├── app/                    # App-Shell, Router, Providers
│   │   ├── App.tsx
│   │   ├── router.tsx
│   │   └── providers.tsx
│   ├── features/               # Feature-basierte Module
│   │   ├── dashboard/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── types.ts
│   │   │   └── index.ts        # Barrel Export
│   │   ├── scan/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   ├── types.ts
│   │   │   └── index.ts
│   │   └── report/
│   ├── shared/
│   │   ├── components/         # Wiederverwendbare UI-Komponenten
│   │   ├── hooks/              # Shared Hooks
│   │   ├── layouts/            # Page Layouts
│   │   └── utils/              # UI-Hilfsfunktionen
│   └── assets/                 # Bilder, Fonts, Icons
```

### Regeln
- **Feature-First**: Nicht nach Typ gruppieren (`components/`, `hooks/`), sondern nach Feature
- **Barrel Exports**: Jedes Feature hat eine `index.ts` die das öffentliche API exportiert
- **Keine Cross-Feature-Imports**: Features importieren nur aus `shared/` oder eigenem Ordner
- **Tiefe max. 4 Ebenen**: `src/ui/features/scan/components/ScanForm.tsx` — nicht tiefer

---

## 3. Component-Regeln

### 3.1 Eine Component pro Datei
```typescript
// scan-form.tsx — Nur ScanForm, nichts anderes
export function ScanForm({ onSubmit }: ScanFormProps) {
  // ...
}
```

### 3.2 Max. 200 Zeilen pro Component
Wird eine Component größer:
- UI-Logik in Custom Hooks auslagern
- Sub-Components extrahieren
- Berechnungen in Utility-Funktionen verschieben

### 3.3 Props als Interface

```typescript
// Immer explizites Interface — keine Inline-Typen
interface ScanResultCardProps {
  result: ScanResult;
  onRetry: (scanId: string) => void;
  isExpanded?: boolean;
}

export function ScanResultCard({
  result,
  onRetry,
  isExpanded = false,
}: ScanResultCardProps) {
  // ...
}
```

### 3.4 Keine Business-Logik in Components

```typescript
// Schlecht: Logik direkt in der Component
function ScanPage() {
  const [target, setTarget] = useState("");
  const [results, setResults] = useState<ScanResult[]>([]);

  async function handleScan() {
    const validated = validateTarget(target);
    const response = await fetch("/api/scan", { ... });
    const data = await response.json();
    setResults(data.results);
  }
  // ...
}

// Gut: Logik in Hook ausgelagert
function ScanPage() {
  const { target, setTarget, results, startScan, isScanning } = useScan();

  return (
    <ScanLayout>
      <ScanForm target={target} onChange={setTarget} onSubmit={startScan} />
      <ScanResults results={results} isLoading={isScanning} />
    </ScanLayout>
  );
}
```

---

## 4. State Management

### 4.1 Hierarchie
1. **Component State** (`useState`) — UI-only State (Formulare, Toggles)
2. **React Query** — Server State (API-Daten, Scan-Ergebnisse)
3. **Zustand** — Globaler Client State (nur wenn 1+2 nicht reichen)

### 4.2 Regel: Server State ≠ Client State
- Scan-Ergebnisse, Agent-Status → **React Query** (automatisches Caching/Refetching)
- Offenes Modal, Sidebar-State → **useState** (lokal)
- Globale UI-Settings, Theme → **Zustand** (global, aber selten)

---

## 5. Styling mit Tailwind

### 5.1 Regeln
- Utility-First: Tailwind-Klassen direkt auf Elementen
- Keine Custom CSS Dateien (außer für globale Resets/Fonts)
- Komplexe Styles: `@apply` in Component-CSS oder `cn()` Helper

### 5.2 Responsiveness
- Mobile First: Basis-Styles für Mobile, Breakpoints für größere Screens
- Breakpoints: `sm:` → `md:` → `lg:` → `xl:`

### 5.3 Dark Mode
- Von Anfang an einplanen: `dark:` Varianten für alle Farben
- Farben über CSS Variables / Tailwind Theme — keine hardcodierten Hex-Werte

---

## 6. Accessibility (Barrierefreiheit)

### 6.1 Pflicht
- Semantisches HTML (`<button>`, `<nav>`, `<main>`, nicht `<div onClick>`)
- Alle Bilder haben `alt`-Text
- Formular-Felder haben zugehörige `<label>`
- Focus-States sind sichtbar (kein `outline: none` ohne Ersatz)
- Farbe ist nie der einzige Informationsträger

### 6.2 Keyboard-Navigation
- Alle interaktiven Elemente per Tab erreichbar
- Escape schließt Modals/Dropdowns
- Enter/Space aktiviert Buttons
- Sinnvolle Tab-Reihenfolge

### 6.3 Mindeststandard
- **WCAG 2.1 Level AA**
- Farbkontrast: Min. 4.5:1 für normalen Text, 3:1 für großen Text

---

## 7. Security (OWASP für Frontend)

### 7.1 Verbotene Praktiken
- **NIEMALS** `dangerouslySetInnerHTML` verwenden
- **NIEMALS** `eval()`, `new Function()`, `document.write()`
- **NIEMALS** User-Input unescaped in DOM rendern
- **NIEMALS** Secrets im Frontend-Code (auch nicht in `process.env`)
- **NIEMALS** `target="_blank"` ohne `rel="noopener noreferrer"`

### 7.2 XSS-Prävention
- React escaped standardmäßig — dieses Verhalten nie umgehen
- Scan-Ergebnisse aus der API vor Darstellung mit DOMPurify sanitizen
- Content Security Policy (CSP) Header konfigurieren (kein `unsafe-eval`)

### 7.3 Auth & Sessions
- JWT in HttpOnly Cookie — NIEMALS in localStorage oder sessionStorage
- CSRF-Token bei allen zustandsändernden Requests mitsenden
- Session-Timeout: Automatischer Logout nach 30 Min. Inaktivität
- Bei 401/403: Sofort zum Login, Token verwerfen

### 7.4 API-Kommunikation
- Alle API-Calls über zentralen HTTP-Client (axios/fetch Wrapper)
- Basis-URL aus Konfiguration, NICHT hardcoded
- Error-Responses: Keine technischen Details dem User zeigen
- Sensitive Daten: Aus dem State entfernen wenn nicht mehr gebraucht

### 7.5 Dependency-Sicherheit
- Keine Packages mit bekannten XSS-Schwachstellen
- `npm audit` als Pre-Push Hook
- Subresource Integrity (SRI) für externe Scripts (wenn überhaupt nötig)

---

## 8. Performance

- Lazy Loading für Routes (`React.lazy` + `Suspense`)
- Bilder: WebP Format, `loading="lazy"`
- Keine unnötigen Re-Renders: `useMemo` / `useCallback` nur bei gemessenen Problemen
- Bundle-Analyse: Kein Package über 100KB ohne guten Grund
