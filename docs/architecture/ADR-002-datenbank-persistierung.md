# ADR-002: Datenbank & Persistierungs-Strategie

> Status: Akzeptiert
> Datum: 2026-04-04
> Autor: Jaciel Antonio Acea Ruiz

## Kontext

SentinelClaw braucht eine Persistierungsschicht für:

1. **Scan-Ergebnisse** — Port-Scans, Vulnerability-Findings, Agent-Reports
2. **Audit-Logs** — Wer hat wann welchen Scan gestartet? Welche Tools liefen?
3. **Benutzerverwaltung** — Users, Rollen, Berechtigungen (ab Produkt)
4. **Konfiguration** — Scan-Profile, Whitelist-Regeln, Agent-Einstellungen
5. **Job-Queue** — Laufende und geplante Scans

Im PoC reichen Dateisystem-Logs (JSON-Dateien). Aber die Architektur muss von Anfang an so gebaut sein, dass der Wechsel zu einer echten Datenbank ohne Umbau möglich ist.

### Anforderungen
- ACID-Transaktionen für Audit-Logs (keine verlorenen Einträge)
- Row-Level Security für Multi-Tenancy
- JSONB-Support für flexible Scan-Ergebnisse
- Self-hosted — keine Cloud-Datenbank (Datenschutz)
- Encryption at Rest möglich
- Bewährte Enterprise-Technologie

## Entscheidung

**PostgreSQL 16** als primäre Datenbank für alle persistenten Daten.

### PoC-Phase
- SQLite für lokale Entwicklung (Zero-Config)
- Repository-Pattern im Code → Datenbank ist austauschbar
- Prisma als ORM (TypeScript) / SQLAlchemy (Python)

### Produkt-Phase
- PostgreSQL 16 im Docker-Container
- Verschlüsselung at Rest via LUKS oder pgcrypto
- Automatische Backups via pg_dump + Cron
- Connection Pooling via PgBouncer (bei > 50 concurrent Users)

## Schema-Übersicht (Produkt)

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  organizations   │────▶│     users        │────▶│   user_roles    │
│  (Mandanten)     │     │  (Benutzer)      │     │  (Zuordnung)    │
└────────┬────────┘     └──────────────────┘     └────────┬────────┘
         │                                                 │
         │                                                 ▼
         │              ┌──────────────────┐     ┌─────────────────┐
         │              │   scan_targets   │     │     roles       │
         │              │  (Ziel-Whitelist)│     │  (Rollen)       │
         │              └────────┬─────────┘     └────────┬────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   scan_jobs     │────▶│  scan_results    │     │   permissions   │
│  (Aufträge)     │     │  (Ergebnisse)    │     │  (Berechtig.)   │
└────────┬────────┘     └──────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  audit_logs     │     │  agent_logs      │
│  (Prüfprotokoll)│     │  (Agent-Schritte)│
└─────────────────┘     └──────────────────┘
```

### Kerntabellen

#### organizations (Mandanten)
```sql
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    email           VARCHAR(255) UNIQUE NOT NULL,
    display_name    VARCHAR(255) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    mfa_secret      VARCHAR(255),          -- TOTP Secret (verschlüsselt)
    is_active       BOOLEAN DEFAULT true,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
-- Row-Level Security: User sieht nur eigene Organisation
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
```

#### scan_jobs
```sql
CREATE TABLE scan_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    created_by      UUID NOT NULL REFERENCES users(id),
    target          VARCHAR(255) NOT NULL,
    scan_type       VARCHAR(50) NOT NULL,   -- 'recon', 'vuln', 'full'
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
                    -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    config          JSONB DEFAULT '{}',     -- Scan-spezifische Konfiguration
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE scan_jobs ENABLE ROW LEVEL SECURITY;
```

#### scan_results
```sql
CREATE TABLE scan_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_job_id     UUID NOT NULL REFERENCES scan_jobs(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    tool_name       VARCHAR(100) NOT NULL,  -- 'nmap', 'nuclei'
    result_type     VARCHAR(50) NOT NULL,   -- 'port_scan', 'vuln_scan'
    findings        JSONB NOT NULL,         -- Strukturierte Ergebnisse
    raw_output      TEXT,                   -- Rohdaten (optional)
    severity_counts JSONB,                  -- { critical: 0, high: 2, medium: 5 }
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE scan_results ENABLE ROW LEVEL SECURITY;
```

#### audit_logs (Unveränderlich)
```sql
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,  -- 'scan.started', 'user.login', 'role.changed'
    resource_type   VARCHAR(100),           -- 'scan_job', 'user', 'organization'
    resource_id     UUID,
    details         JSONB,                  -- Zusätzliche Kontext-Daten
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
    -- KEIN updated_at — Audit-Logs sind unveränderlich
);
-- Audit-Logs sind INSERT-ONLY: Kein UPDATE, kein DELETE
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY audit_insert_only ON audit_logs
    FOR ALL USING (false)
    WITH CHECK (true);
-- Nur INSERT erlaubt, kein SELECT/UPDATE/DELETE ohne Admin-Rolle
```

## Alternativen

### Alternative A: MongoDB
- Vorteile: Flexibles Schema, gut für JSON-Dokumente
- Nachteile: Keine ACID-Transaktionen (bis v4), keine Row-Level Security nativ, weniger Enterprise-verbreitet in DACH
- Warum verworfen: PostgreSQL JSONB bietet die gleiche Flexibilität MIT Transaktionssicherheit

### Alternative B: SQLite (auch für Produkt)
- Vorteile: Zero-Config, kein separater Server
- Nachteile: Keine Concurrent Writes, kein Row-Level Security, nicht für Multi-User
- Warum verworfen: Reicht für PoC, nicht für Enterprise-Betrieb

### Alternative C: Elasticsearch
- Vorteile: Hervorragende Suche über Scan-Ergebnisse
- Nachteile: Kein ACID, komplexer Betrieb, hoher Ressourcenverbrauch
- Warum verworfen: Kann später als Search-Layer NEBEN PostgreSQL ergänzt werden

## Konsequenzen

### Positiv
- Row-Level Security garantiert Mandantentrennung auf DB-Ebene
- JSONB erlaubt flexible Scan-Ergebnis-Strukturen ohne Schema-Migration
- Bewährte Technologie — jeder Enterprise-Kunde kennt PostgreSQL
- pgcrypto für Encryption at Rest verfügbar
- Hervorragender Tooling-Support (Prisma, SQLAlchemy, pgAdmin)

### Negativ
- Zusätzlicher Docker-Container für PostgreSQL
- Backup-Strategie muss implementiert werden
- Schema-Migrationen müssen verwaltet werden (Prisma Migrate / Alembic)

### Migration PoC → Produkt
1. PoC: Repository-Pattern mit SQLite-Adapter
2. Produkt: Gleiche Interfaces, PostgreSQL-Adapter
3. Migration: Einmalige Datenübernahme via Script
