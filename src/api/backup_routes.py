"""
Backup-Management-Routen für die SentinelClaw REST-API.

Endpoints unter /api/v1/backup:
  - POST /          -> Manuelles Backup erstellen (system_admin)
  - GET  /          -> Alle Backups auflisten (system_admin)
  - POST /restore   -> Backup wiederherstellen (system_admin)
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.shared.auth import require_role
from src.shared.backup_service import (
    cleanup_old_backups,
    create_backup,
    list_backups,
    restore_backup,
)
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/backup", tags=["Backup"])


class RestoreRequest(BaseModel):
    """Backup-Wiederherstellung."""
    filename: str = Field(description="Dateiname des Backups")


async def _get_db():
    from src.api.server import get_db
    return await get_db()


@router.post("")
async def trigger_backup(request: Request) -> dict:
    """Erstellt ein manuelles Datenbank-Backup (system_admin)."""
    require_role(request, "system_admin")
    db = await _get_db()

    backup_path = await create_backup(db)
    cleanup_old_backups(max_age_days=30)

    return {
        "status": "created",
        "filename": backup_path.name,
        "size_mb": round(backup_path.stat().st_size / (1024 * 1024), 2),
    }


@router.get("")
async def get_backups(request: Request) -> list[dict]:
    """Listet alle verfügbaren Backups (system_admin)."""
    require_role(request, "system_admin")
    return list_backups()


@router.post("/restore")
async def trigger_restore(request: Request, body: RestoreRequest) -> dict:
    """Stellt die Datenbank aus einem Backup wieder her (system_admin).

    ACHTUNG: Überschreibt die aktuelle Datenbank irreversibel.
    """
    require_role(request, "system_admin")
    db = await _get_db()

    try:
        await restore_backup(body.filename, db)
    except FileNotFoundError:
        raise HTTPException(404, f"Backup '{body.filename}' nicht gefunden")

    logger.info("Backup wiederhergestellt via API", filename=body.filename)
    return {"status": "restored", "filename": body.filename}
