"""
DSGVO-Routen für die SentinelClaw REST-API.

Endpoints unter /api/v1/gdpr:
  - GET  /export         -> Eigene Daten exportieren (Art. 15 + 20)
  - POST /consent        -> Einwilligung erteilen/widerrufen
  - DELETE /account      -> Eigenes Konto + alle Daten löschen (Art. 17)
  - POST /admin/delete   -> Admin löscht Benutzer-Daten (system_admin)
"""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.shared.auth import extract_user_from_request, require_role
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/gdpr", tags=["DSGVO"])


class ConsentRequest(BaseModel):
    """Einwilligungserklärung."""
    consent_type: str = Field(description="Art der Einwilligung (z.B. 'data_processing')")
    granted: bool = Field(description="True=erteilt, False=widerrufen")


class AdminDeleteRequest(BaseModel):
    """Admin-Löschung eines Benutzerkontos."""
    user_id: str = Field(description="ID des zu löschenden Benutzers")


async def _get_db():
    from src.api.server import get_db
    return await get_db()


@router.get("/export")
async def export_own_data(request: Request) -> dict:
    """Exportiert alle eigenen Daten als JSON (DSGVO Art. 15 + 20)."""
    caller = extract_user_from_request(request)
    from src.shared.gdpr_service import export_user_data

    db = await _get_db()
    data = await export_user_data(caller["sub"], db)

    logger.info("DSGVO-Datenexport", user_id=caller["sub"])
    return data


@router.post("/consent")
async def record_consent(request: Request, body: ConsentRequest) -> dict:
    """Speichert eine Einwilligungserklärung (DSGVO Art. 6/7)."""
    caller = extract_user_from_request(request)
    client_ip = request.client.host if request.client else "unknown"

    db = await _get_db()
    conn = await db.get_connection()

    consent_id = str(uuid4())
    now = datetime.now(UTC).isoformat()

    await conn.execute(
        "INSERT INTO consent_records (id, user_id, consent_type, granted, ip_address, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (consent_id, caller["sub"], body.consent_type, body.granted, client_ip, now),
    )
    await conn.commit()

    action = "erteilt" if body.granted else "widerrufen"
    logger.info(f"Einwilligung {action}", user_id=caller["sub"], type=body.consent_type)
    return {"status": action, "consent_id": consent_id}


@router.delete("/account")
async def delete_own_account(request: Request) -> dict:
    """Löscht das eigene Konto und alle zugehörigen Daten (DSGVO Art. 17).

    ACHTUNG: Diese Aktion ist IRREVERSIBEL. Alle Scans, Findings,
    Chat-Nachrichten und Reports werden gelöscht.
    """
    caller = extract_user_from_request(request)
    from src.shared.gdpr_service import delete_user_data

    db = await _get_db()
    counts = await delete_user_data(caller["sub"], db)

    logger.info("DSGVO-Selbstlöschung", user_id=caller["sub"], counts=counts)
    return {"status": "deleted", "deleted_counts": counts}


@router.post("/admin/delete")
async def admin_delete_user_data(request: Request, body: AdminDeleteRequest) -> dict:
    """Löscht alle Daten eines Benutzers (nur system_admin).

    Für den Fall dass ein Benutzer die Löschung beantragt aber
    sich nicht selbst einloggen kann.
    """
    caller = require_role(request, "system_admin")
    from src.shared.gdpr_service import delete_user_data

    if caller["sub"] == body.user_id:
        raise HTTPException(400, "Eigenes Konto nicht über Admin-Löschung entfernen")

    db = await _get_db()
    counts = await delete_user_data(body.user_id, db)

    logger.info("DSGVO-Admin-Löschung", user_id=body.user_id, by=caller["sub"], counts=counts)
    return {"status": "deleted", "user_id": body.user_id, "deleted_counts": counts}
