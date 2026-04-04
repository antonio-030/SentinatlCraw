# SentinelClaw — RBAC-Rollenmodell

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026
> Status: Entwurf (Umsetzung ab Produktentwicklung, nicht im PoC)

---

## 1. Überblick

SentinelClaw verwendet ein **rollenbasiertes Zugriffskontrollmodell (RBAC)** mit folgender Struktur:

```
Organization (Mandant)
  └── Users (Benutzer)
       └── Roles (Rollen)
            └── Permissions (Berechtigungen)
                 └── Scopes (Geltungsbereich)
```

### Prinzipien
1. **Least Privilege** — Jeder User bekommt nur die minimal nötigen Rechte
2. **Separation of Duties** — Wer scannt, darf nicht die Ergebnisse löschen
3. **Mandantentrennung** — Organisation A sieht NICHTS von Organisation B
4. **Audit-Trail** — Jede Rechteänderung wird protokolliert
5. **Default Deny** — Ohne explizite Berechtigung ist alles verboten

---

## 2. Rollen

### 2.1 Vordefinierte Rollen

```
┌─────────────────────────────────────────────────────────────┐
│                    ORGANIZATION ADMIN                        │
│  Volle Kontrolle über die Organisation                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  SECURITY LEAD                         │  │
│  │  Scans starten, Ergebnisse sehen, Reports erstellen   │  │
│  │  ┌───────────────────────────────────��─────────────┐  │  │
│  │  │              ANALYST                             │  │  │
│  │  │  Ergebnisse lesen, Reports lesen                 │  │  │
│  │  │  ┌─────────────────���─────────────────────���───┐  │  │  │
│  │  │  │            VIEWER                          │  │  │  │
│  │  │  │  Nur lesen, kein Export                    │  │  │  │
│  │  │  └────────���───────────────────────────��──────┘  │  │  │
│  │  └────────────────────────────���────────────────────┘  │  │
│  └───────��───────────────────────────────────────────────┘  │
└──────��───────────────────────────────���──────────────────────┘

Separate Rolle (nicht in Hierarchie):
┌─────────────────────────────────────────────────────────────┐
│                    SYSTEM ADMIN (Plattform)                  │
│  Verwaltet die gesamte SentinelClaw-Instanz                 │
└─────────────��───────────────────────���───────────────────────┘
```

### 2.2 Rollendefinitionen

#### SYSTEM_ADMIN (Plattform-Administrator)
- **Beschreibung**: Verwaltet die gesamte SentinelClaw-Instanz
- **Zielgruppe**: IT-Betriebsteam des Kunden
- **Typische Aufgaben**: Organisationen anlegen, System-Konfiguration, Updates
- **Besonderheit**: Steht ÜBER den Organisationen, nicht innerhalb

#### ORG_ADMIN (Organisations-Administrator)
- **Beschreibung**: Volle Kontrolle über seine Organisation
- **Zielgruppe**: CISO, Security-Manager, Abteilungsleiter
- **Typische Aufgaben**: User verwalten, Rollen zuweisen, Scan-Targets pflegen, Reports freigeben

#### SECURITY_LEAD (Security-Teamleiter)
- **Beschreibung**: Führt Assessments durch und sieht alle Ergebnisse
- **Zielgruppe**: Senior Penetration Tester, Security Engineers
- **Typische Aufgaben**: Scans starten/stoppen, Findings bewerten, Reports generieren

#### ANALYST (Sicherheitsanalyst)
- **Beschreibung**: Analysiert Ergebnisse, kann keine Scans selbst starten
- **Zielgruppe**: Junior Analysten, Compliance-Beauftragte
- **Typische Aufgaben**: Findings lesen, Kommentare hinzufügen, Reports lesen

#### VIEWER (Betrachter)
- **Beschreibung**: Kann nur ausgewählte Ergebnisse einsehen
- **Zielgruppe**: Management, Auditoren, externe Prüfer
- **Typische Aufgaben**: Dashboard ansehen, Reports lesen (kein Export)

---

## 3. Berechtigungsmatrix

### 3.1 Scan-Berechtigungen

| Aktion | SYSTEM_ADMIN | ORG_ADMIN | SECURITY_LEAD | ANALYST | VIEWER |
|---|---|---|---|---|---|
| Scan starten | - | ja | ja | nein | nein |
| Scan abbrechen | - | ja | ja | nein | nein |
| Scan-Ergebnisse lesen | - | ja | ja | ja | eingeschränkt* |
| Scan-Ergebnisse exportieren | - | ja | ja | ja | nein |
| Scan-Ergebnisse löschen | - | ja | nein | nein | nein |
| Scan-Ziele verwalten | - | ja | ja | nein | nein |
| Scan-Profile konfigurieren | - | ja | ja | nein | nein |

*Viewer sehen nur freigegebene Reports, keine Rohdaten

### 3.2 User-Management

| Aktion | SYSTEM_ADMIN | ORG_ADMIN | SECURITY_LEAD | ANALYST | VIEWER |
|---|---|---|---|---|---|
| Organisation erstellen | ja | nein | nein | nein | nein |
| Organisation löschen | ja | nein | nein | nein | nein |
| User einladen | ja | ja | nein | nein | nein |
| User deaktivieren | ja | ja | nein | nein | nein |
| Rollen zuweisen | ja | ja | nein | nein | nein |
| Eigenes Profil bearbeiten | ja | ja | ja | ja | ja |
| MFA aktivieren/deaktivieren | ja | ja | ja | ja | ja |
| Passwort ändern (eigenes) | ja | ja | ja | ja | ja |
| Passwort zurücksetzen (andere) | ja | ja | nein | nein | nein |

### 3.3 Report-Berechtigungen

| Aktion | SYSTEM_ADMIN | ORG_ADMIN | SECURITY_LEAD | ANALYST | VIEWER |
|---|---|---|---|---|---|
| Report generieren (PDF/DOCX) | - | ja | ja | nein | nein |
| Report lesen | - | ja | ja | ja | ja |
| Report freigeben (für Viewer) | - | ja | ja | nein | nein |
| Report löschen | - | ja | nein | nein | nein |
| Report-Template anpassen | - | ja | ja | nein | nein |

### 3.4 System-Berechtigungen

| Aktion | SYSTEM_ADMIN | ORG_ADMIN | SECURITY_LEAD | ANALYST | VIEWER |
|---|---|---|---|---|---|
| System-Konfiguration ändern | ja | nein | nein | nein | nein |
| LLM-Provider konfigurieren | ja | ja | nein | nein | nein |
| Audit-Logs einsehen | ja | ja | nein | nein | nein |
| Docker-Container verwalten | ja | nein | nein | nein | nein |
| Backup erstellen/wiederherstellen | ja | nein | nein | nein | nein |

---

## 4. Technische Umsetzung

### 4.1 Datenbank-Schema

```sql
-- Rollen-Definition
CREATE TABLE roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_system   BOOLEAN DEFAULT false,  -- System-Rollen nicht löschbar
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Berechtigungen
CREATE TABLE permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource    VARCHAR(100) NOT NULL,   -- 'scan', 'user', 'report', 'system'
    action      VARCHAR(50) NOT NULL,    -- 'create', 'read', 'update', 'delete'
    scope       VARCHAR(50) DEFAULT 'own',-- 'own', 'organization', 'all'
    description TEXT,
    UNIQUE(resource, action, scope)
);

-- Rollen ↔ Berechtigungen (N:M)
CREATE TABLE role_permissions (
    role_id       UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- User ↔ Rollen (N:M, pro Organisation)
CREATE TABLE user_roles (
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    role_id         UUID REFERENCES roles(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    assigned_by     UUID REFERENCES users(id),
    assigned_at     TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, role_id, organization_id)
);
```

### 4.2 Permission-Check im Code

```typescript
// Middleware-Konzept für API-Requests
interface PermissionCheck {
  resource: "scan" | "user" | "report" | "system" | "audit";
  action: "create" | "read" | "update" | "delete";
  scope?: "own" | "organization" | "all";
}

// Beispiel: Scan starten erfordert scan:create
// Dekorator-Pattern (später als Middleware)
@requirePermission({ resource: "scan", action: "create" })
async function startScan(request: AuthenticatedRequest): Promise<ScanJob> {
  // Wird nur ausgeführt wenn User die Berechtigung hat
}
```

### 4.3 Row-Level Security (PostgreSQL)

```sql
-- Jede Tabelle mit Organisationsbezug bekommt RLS
-- Beispiel: scan_jobs
CREATE POLICY scan_jobs_org_isolation ON scan_jobs
    USING (organization_id = current_setting('app.current_org_id')::UUID);

-- Die App setzt bei jedem Request den Kontext:
-- SET LOCAL app.current_org_id = 'uuid-der-organisation';
-- Danach sieht der User NUR seine eigenen Daten — DB-seitig garantiert
```

---

## 5. Authentifizierung

### 5.1 Login-Mechanismen

| Methode | PoC | Produkt | Beschreibung |
|---|---|---|---|
| E-Mail + Passwort | nein | ja | Standard-Login |
| MFA (TOTP) | nein | ja | Pflicht für ORG_ADMIN und SYSTEM_ADMIN |
| LDAP / Active Directory | nein | optional | Enterprise-SSO |
| SAML 2.0 / OIDC | nein | optional | Federated Identity |
| API-Key | nein | ja | Für CI/CD-Integration und API-Zugriff |

### 5.2 Session-Management

| Regel | Wert | Begründung |
|---|---|---|
| Session-Timeout (Inaktivität) | 30 Minuten | BSI-Grundschutz Empfehlung |
| Maximale Session-Dauer | 8 Stunden | Arbeitstag-Limit |
| Concurrent Sessions | Max. 3 | Schutz vor Account-Sharing |
| Token-Typ | JWT (RS256) | Asymmetrisch, verifizierbar ohne Shared Secret |
| Refresh-Token-Rotation | Ja | Jeder Refresh invalidiert den alten Token |
| Token in Cookie | HttpOnly, Secure, SameSite=Strict | Kein JavaScript-Zugriff auf Token |

### 5.3 Passwort-Policy

| Regel | Wert |
|---|---|
| Minimale Länge | 12 Zeichen |
| Komplexität | Min. 1 Groß, 1 Klein, 1 Zahl, 1 Sonderzeichen |
| Passwort-History | Letzte 5 nicht wiederverwendbar |
| Max. Fehlversuche | 5 (danach 15 Min. Sperre) |
| Hashing-Algorithmus | Argon2id |
| MFA-Pflicht | Ab ORG_ADMIN aufwärts |

---

## 6. Wichtige Sicherheitsregeln für RBAC

### 6.1 Privilege Escalation verhindern
- User kann sich NICHT selbst eine höhere Rolle geben
- Nur ORG_ADMIN kann Rollen zuweisen — und nur innerhalb seiner Organisation
- SYSTEM_ADMIN-Rolle kann nur vom initialen Setup vergeben werden
- Jede Rollenänderung wird im Audit-Log protokolliert

### 6.2 Default Deny
```typescript
// FALSCH: Blacklist-Ansatz (alles erlaubt, einzelnes verbieten)
if (user.role === "VIEWER") {
  throw new ForbiddenError("Viewer dürfen das nicht");
}

// RICHTIG: Whitelist-Ansatz (alles verboten, einzelnes erlauben)
if (!user.hasPermission({ resource: "scan", action: "create" })) {
  throw new ForbiddenError("Keine Berechtigung für scan:create");
}
```

### 6.3 Audit-Logging für Rechteänderungen

Folgende Events werden IMMER geloggt:
- User-Erstellung und -Deaktivierung
- Rollen-Zuweisung und -Entzug
- Login (erfolgreich und fehlgeschlagen)
- Passwort-Änderung und -Reset
- MFA-Aktivierung und -Deaktivierung
- Session-Timeout und -Invalidierung
