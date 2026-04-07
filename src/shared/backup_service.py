"""Backup-Service für SentinelClaw.

Erstellt sichere SQLite-Backups mittels VACUUM INTO (konsistent
auch bei laufender Datenbank). Verwaltet Backup-Retention.
"""

import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path

from src.shared.database import DatabaseManager
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

BACKUP_DIR = Path("data/backups")


async def create_backup(db: DatabaseManager) -> Path:
    """Erstellt ein konsistentes Datenbank-Backup.

    Verwendet SQLite VACUUM INTO für ein atomares, konsistentes Backup
    auch bei laufenden Schreibvorgängen.

    Returns:
        Pfad zur erstellten Backup-Datei.
    """
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"sentinelclaw_{timestamp}.db"

    conn = await db.get_connection()
    await conn.execute(f"VACUUM INTO '{backup_path}'")

    size_mb = backup_path.stat().st_size / (1024 * 1024)
    logger.info(
        "Backup erstellt",
        path=str(backup_path),
        size_mb=round(size_mb, 2),
    )
    return backup_path


def list_backups() -> list[dict]:
    """Listet alle vorhandenen Backups mit Größe und Zeitstempel."""
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for path in sorted(BACKUP_DIR.glob("sentinelclaw_*.db"), reverse=True):
        stat = path.stat()
        backups.append({
            "filename": path.name,
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        })
    return backups


async def restore_backup(backup_filename: str, db: DatabaseManager) -> None:
    """Stellt die Datenbank aus einem Backup wieder her.

    ACHTUNG: Überschreibt die aktuelle Datenbank irreversibel.
    """
    backup_path = BACKUP_DIR / backup_filename
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup '{backup_filename}' nicht gefunden")

    # Aktuelle DB-Datei ermitteln und ersetzen
    db_path = db._db_path
    await db.close()

    shutil.copy2(backup_path, db_path)
    logger.info("Backup wiederhergestellt", backup=backup_filename)

    # DB neu initialisieren
    await db.initialize()


def cleanup_old_backups(max_age_days: int | None = None) -> int:
    """Löscht Backups die älter als max_age_days sind.

    Returns:
        Anzahl gelöschter Backups.
    """
    if max_age_days is None:
        try:
            from src.shared.settings_service import get_setting_int
            max_age_days = get_setting_int("backup_retention_days", 30)
        except Exception:
            max_age_days = 30

    if not BACKUP_DIR.exists():
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    deleted = 0

    for path in BACKUP_DIR.glob("sentinelclaw_*.db"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if mtime < cutoff:
            path.unlink()
            deleted += 1

    if deleted:
        logger.info(f"{deleted} alte Backups gelöscht (>{max_age_days} Tage)")
    return deleted
