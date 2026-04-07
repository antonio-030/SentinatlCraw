# Shared — Gemeinsame Infrastruktur

> Zentrale Module für Datenbank, Auth, Konfiguration, Typen und Validierung.

## Was macht dieses Modul?

Stellt alle gemeinsam genutzten Komponenten bereit: Datenbankzugriff (SQLite im PoC),
JWT-Authentifizierung, Pydantic-basierte Konfiguration, Scope-Validierung, Kill-Switch,
Report-Generierung, DSGVO-Services und das Repository-Pattern für Datenzugriff.

## Dateien

| Datei | Funktion |
|---|---|
| `config.py` | Pydantic-Settings, Umgebungsvariablen |
| `database.py` | SQLite-Datenbankmanager, Schema, Migrationen |
| `auth.py` | JWT-Token-Erzeugung und -Validierung, RBAC |
| `repositories.py` | Repository-Pattern (Scan, Audit, Finding) |
| `scope_validator.py` | Scope-Validierung gegen IP/CIDR/Domain |
| `kill_switch.py` | 4-Pfad Kill-Switch (DB, Docker, OS, Netzwerk) |
| `sanitizer.py` | Input-Sanitierung, PII-Maskierung |
| `logging_setup.py` | Strukturiertes Logging |
| `migrations.py` | Datenbank-Migrationen |
| `report_generator.py` | Markdown/PDF-Report-Generierung |
| `gdpr_service.py` | DSGVO: Export, Löschung, Retention |
| `settings_service.py` | Dynamische Einstellungsverwaltung |
| `types/` | Pydantic-Modelle, Enums, Interfaces |
| `constants/` | Zentrale Defaults und Konstanten |

## Starten

Wird nicht eigenständig gestartet. Wird von allen anderen Modulen importiert.

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_DB_PATH` | Pfad zur SQLite-Datenbank |
| `SENTINEL_JWT_SECRET` | JWT-Signierungsschlüssel |
| `SENTINEL_LOG_LEVEL` | Log-Level: DEBUG, INFO, WARN, ERROR |
| `SENTINEL_DATA_DIR` | Verzeichnis für persistente Daten |

## Dependencies

- `pydantic`, `pydantic-settings` (Validierung, Konfiguration)
- `aiosqlite` (Asynchroner SQLite-Zugriff)
- `python-jose` (JWT)
- `bcrypt` (Passwort-Hashing)
