"""
Organisations-Management-Routen für die SentinelClaw REST-API.

Multi-Tenancy: Organisationen erstellen, verwalten und Benutzer zuweisen.

Endpoints unter /api/v1/organizations:
  - GET    /               -> Alle Organisationen (system_admin)
  - POST   /               -> Organisation erstellen (system_admin)
  - PUT    /{id}           -> Organisation bearbeiten (system_admin)
  - POST   /{id}/users     -> Benutzer zuweisen (org_admin+)
  - DELETE /{id}/users/{uid} -> Benutzer entfernen (org_admin+)
"""

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.shared.auth import require_role
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/organizations", tags=["Organizations"])


class CreateOrgRequest(BaseModel):
    """Neue Organisation erstellen."""
    name: str = Field(min_length=2, max_length=100)
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    max_users: int = Field(default=10, ge=1, le=1000)


class UpdateOrgRequest(BaseModel):
    """Organisation bearbeiten."""
    name: str | None = None
    max_users: int | None = Field(default=None, ge=1, le=1000)


class AssignUserRequest(BaseModel):
    """Benutzer einer Organisation zuweisen."""
    user_id: str


async def _get_db():
    from src.api.server import get_db
    return await get_db()


@router.get("")
async def list_organizations(request: Request) -> list[dict]:
    """Listet alle Organisationen (system_admin)."""
    require_role(request, "system_admin")
    db = await _get_db()
    conn = await db.get_connection()
    cursor = await conn.execute(
        "SELECT id, name, slug, max_users, created_at FROM organizations ORDER BY name"
    )
    return [
        {"id": r[0], "name": r[1], "slug": r[2], "max_users": r[3], "created_at": r[4]}
        for r in await cursor.fetchall()
    ]


@router.post("")
async def create_organization(request: Request, body: CreateOrgRequest) -> dict:
    """Erstellt eine neue Organisation (system_admin)."""
    require_role(request, "system_admin")
    db = await _get_db()
    conn = await db.get_connection()

    # Prüfe ob Name oder Slug bereits existiert
    cursor = await conn.execute(
        "SELECT id FROM organizations WHERE name = ? OR slug = ?",
        (body.name, body.slug),
    )
    if await cursor.fetchone():
        raise HTTPException(409, "Organisation mit diesem Namen oder Slug existiert bereits")

    org_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    await conn.execute(
        "INSERT INTO organizations (id, name, slug, max_users, created_at) VALUES (?, ?, ?, ?, ?)",
        (org_id, body.name, body.slug, body.max_users, now),
    )
    await conn.commit()

    logger.info("Organisation erstellt", org_id=org_id, name=body.name)
    return {"id": org_id, "name": body.name, "slug": body.slug}


@router.put("/{org_id}")
async def update_organization(org_id: str, body: UpdateOrgRequest, request: Request) -> dict:
    """Bearbeitet eine Organisation (system_admin)."""
    require_role(request, "system_admin")
    db = await _get_db()
    conn = await db.get_connection()

    cursor = await conn.execute("SELECT id FROM organizations WHERE id = ?", (org_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Organisation nicht gefunden")

    updates = []
    params = []
    if body.name is not None:
        updates.append("name = ?")
        params.append(body.name)
    if body.max_users is not None:
        updates.append("max_users = ?")
        params.append(body.max_users)

    if updates:
        params.append(org_id)
        await conn.execute(
            f"UPDATE organizations SET {', '.join(updates)} WHERE id = ?",  # noqa: S608
            params,
        )
        await conn.commit()

    return {"status": "updated", "org_id": org_id}


@router.post("/{org_id}/users")
async def assign_user_to_org(org_id: str, body: AssignUserRequest, request: Request) -> dict:
    """Weist einen Benutzer einer Organisation zu (org_admin+)."""
    require_role(request, "org_admin")
    db = await _get_db()
    conn = await db.get_connection()

    cursor = await conn.execute("SELECT id FROM organizations WHERE id = ?", (org_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Organisation nicht gefunden")

    cursor = await conn.execute("SELECT id FROM users WHERE id = ?", (body.user_id,))
    if not await cursor.fetchone():
        raise HTTPException(404, "Benutzer nicht gefunden")

    await conn.execute(
        "UPDATE users SET organization_id = ? WHERE id = ?",
        (org_id, body.user_id),
    )
    await conn.commit()

    logger.info("Benutzer zu Organisation zugewiesen", user_id=body.user_id, org_id=org_id)
    return {"status": "assigned", "user_id": body.user_id, "org_id": org_id}


@router.delete("/{org_id}/users/{user_id}")
async def remove_user_from_org(org_id: str, user_id: str, request: Request) -> dict:
    """Entfernt einen Benutzer aus einer Organisation (org_admin+)."""
    require_role(request, "org_admin")
    db = await _get_db()
    conn = await db.get_connection()

    # Zurück zur Default-Organisation
    await conn.execute(
        "UPDATE users SET organization_id = 'default-org' WHERE id = ? AND organization_id = ?",
        (user_id, org_id),
    )
    await conn.commit()

    logger.info("Benutzer aus Organisation entfernt", user_id=user_id, org_id=org_id)
    return {"status": "removed", "user_id": user_id}
