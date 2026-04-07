"""
System-Endpoints für die SentinelClaw REST-API.

Ausgelagert aus server.py (Phase 8 Refactoring).
Enthält: Health, Sandbox-Steuerung, Kill-Switch, Audit, Status.
"""

import shutil
import subprocess
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.shared.auth import require_role
from src.shared.config import get_settings
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["System"])


class KillRequest(BaseModel):
    """Kill-Switch Anfrage."""
    reason: str = Field(default="API Kill-Request")


class NemoClawHealthStatus(BaseModel):
    """NemoClaw-Verfügbarkeitsstatus im Health-Check."""
    available: bool
    provider: str
    last_check: str
    reason: str = ""


class HealthResponse(BaseModel):
    """System-Health-Status."""
    status: str
    version: str
    provider: str
    sandbox_running: bool
    db_connected: bool
    nemoclaw: NemoClawHealthStatus
    timestamp: str



async def _get_db():
    from src.api.server import get_db
    return await get_db()


def _get_openshell_version() -> str:
    """Ermittelt die OpenShell-Version."""
    try:
        result = subprocess.run(
            ["openshell", "version"], capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()[:50] if result.returncode == 0 else "nicht verfügbar"
    except Exception:
        return "nicht verfügbar"


def _check_sandbox_status() -> bool:
    """Prüft ob die OpenShell-Sandbox läuft."""
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "list"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0 and sandbox_name in result.stdout
    except Exception:
        return False



@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """System-Health-Check — wird von Monitoring und UI genutzt."""
    from src.agents.chat_agent import get_active_provider_name
    from src.agents.nemoclaw_runtime import NemoClawRuntime

    settings = get_settings()
    db = await _get_db()
    nemoclaw_status = NemoClawRuntime.check_availability()
    nemoclaw_available = nemoclaw_status.get("available", False)
    last_check_ts = nemoclaw_status.get("last_check", 0)
    last_check_iso = (
        datetime.fromtimestamp(last_check_ts, tz=UTC).isoformat()
        if last_check_ts
        else datetime.now(UTC).isoformat()
    )

    return HealthResponse(
        status="ok" if db is not None else "degraded",
        version="0.1.0",
        provider=settings.llm_provider,
        sandbox_running=_check_sandbox_status(),
        db_connected=db is not None,
        nemoclaw=NemoClawHealthStatus(
            available=nemoclaw_available,
            provider=get_active_provider_name(),
            last_check=last_check_iso,
            reason=nemoclaw_status.get("reason", ""),
        ),
        timestamp=datetime.now(UTC).isoformat(),
    )


@router.post("/api/v1/sandbox/start")
async def start_sandbox(request: Request) -> dict:
    """Erstellt/startet die OpenShell-Sandbox (security_lead+)."""
    require_role(request, "security_lead")
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name
        check = subprocess.run(
            ["openshell", "sandbox", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if check.returncode == 0 and sandbox_name in check.stdout:
            return {"status": "already_running", "message": "Sandbox läuft bereits"}
        result = subprocess.run(
            ["openshell", "sandbox", "create", sandbox_name],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return {"status": "started", "message": "OpenShell-Sandbox erstellt"}
        return {
            "status": "error",
            "message": f"Sandbox-Erstellung fehlgeschlagen: {result.stderr.strip()[:200]}",
        }
    except Exception as e:
        raise HTTPException(500, f"Sandbox konnte nicht gestartet werden: {e}")


@router.post("/api/v1/sandbox/stop")
async def stop_sandbox(request: Request) -> dict:
    """Löscht die OpenShell-Sandbox (security_lead+)."""
    require_role(request, "security_lead")
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "delete", sandbox_name, "--force"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return {"status": "stopped", "message": "OpenShell-Sandbox gelöscht"}

        stderr = result.stderr.strip()
        if "not found" in stderr.lower() or "does not exist" in stderr.lower():
            return {"status": "already_stopped", "message": "Sandbox existiert nicht"}
        return {
            "status": "error",
            "message": f"Sandbox-Löschung fehlgeschlagen: {stderr[:200]}",
        }
    except Exception as e:
        raise HTTPException(500, f"Sandbox konnte nicht gestoppt werden: {e}")


@router.post("/api/v1/kill")
async def emergency_kill(request: Request, body: KillRequest) -> dict:
    """Aktiviert den Kill-Switch — stoppt ALLE laufenden Scans (security_lead+)."""
    caller = require_role(request, "security_lead")
    from src.shared.kill_switch import KillSwitch
    from src.shared.repositories import AuditLogRepository, ScanJobRepository
    from src.shared.types.models import AuditLogEntry, ScanStatus

    ks = KillSwitch()
    ks.activate(triggered_by=caller.get("email", "api_user"), reason=body.reason)

    db = await _get_db()
    scan_repo = ScanJobRepository(db)
    audit_repo = AuditLogRepository(db)

    running = await scan_repo.list_by_status(ScanStatus.RUNNING)
    for job in running:
        await scan_repo.update_status(job.id, ScanStatus.EMERGENCY_KILLED)

    await audit_repo.create(AuditLogEntry(
        action="kill.activated",
        resource_type="system",
        details={"reason": body.reason, "scans_killed": len(running)},
        triggered_by=caller.get("email", "api_user"),
    ))

    return {"status": "killed", "scans_stopped": len(running), "reason": body.reason}


@router.post("/api/v1/kill/reset")
async def reset_kill_switch(request: Request) -> dict:
    """Setzt den Kill-Switch zurück und startet die Sandbox neu (security_lead+)."""
    caller = require_role(request, "security_lead")
    from src.shared.kill_switch import KillSwitch
    from src.shared.repositories import AuditLogRepository
    from src.shared.types.models import AuditLogEntry

    ks = KillSwitch()
    if not ks.is_active():
        return {"status": "already_reset", "message": "Kill-Switch ist nicht aktiv"}

    ks.reset()

    sandbox_started = False
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name
        result = subprocess.run(
            ["openshell", "sandbox", "create", sandbox_name],
            capture_output=True, text=True, timeout=30,
        )
        sandbox_started = result.returncode == 0
        if sandbox_started:
            logger.info("OpenShell-Sandbox nach Kill-Reset erstellt")
        else:
            logger.warning(
                "Sandbox-Erstellung fehlgeschlagen",
                stderr=result.stderr.strip()[:200],
            )
    except Exception as exc:
        logger.warning("Sandbox-Neustart fehlgeschlagen", error=str(exc))

    db = await _get_db()
    audit_repo = AuditLogRepository(db)
    await audit_repo.create(AuditLogEntry(
        action="kill.reset",
        resource_type="system",
        details={"sandbox_restarted": sandbox_started},
        triggered_by=caller.get("email", "api_user"),
    ))

    return {"status": "reset", "sandbox_started": sandbox_started, "message": "System wiederhergestellt"}


@router.get("/api/v1/audit")
async def list_audit_logs(request: Request, limit: int = 50, action: str | None = None) -> list[dict]:
    """Listet Audit-Log-Einträge (analyst+)."""
    require_role(request, "analyst")
    from src.shared.repositories import AuditLogRepository

    db = await _get_db()
    repo = AuditLogRepository(db)
    entries = await repo.list_by_action(action, limit) if action else await repo.list_recent(limit)

    return [
        {
            "id": str(e.id), "action": e.action, "resource_type": e.resource_type,
            "resource_id": e.resource_id, "details": e.details,
            "triggered_by": e.triggered_by, "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


@router.get("/api/v1/status")
async def system_status() -> dict:
    """Gibt den System-Status zurück."""
    from src.shared.kill_switch import KillSwitch
    from src.shared.repositories import ScanJobRepository
    from src.shared.types.models import ScanStatus

    settings = get_settings()
    openshell_version = _get_openshell_version()
    openshell_available = shutil.which("openshell") is not None
    nemoclaw_available = False
    nemoclaw_version = ""
    try:
        from src.agents.nemoclaw_runtime import NemoClawRuntime
        availability = NemoClawRuntime.check_availability()
        nemoclaw_available = availability.get("available", False)
        nemoclaw_version = "Aktiv" if nemoclaw_available else ""
    except Exception:
        pass

    db = await _get_db()
    scan_repo = ScanJobRepository(db)
    running = await scan_repo.list_by_status(ScanStatus.RUNNING)
    all_scans = await scan_repo.list_all(1000)

    return {
        "system": {
            "version": "0.1.0",
            "llm_provider": settings.llm_provider,
            "nemoclaw_available": nemoclaw_available,
            "nemoclaw_version": nemoclaw_version,
            "openshell_available": openshell_available,
            "openshell": openshell_version,
            "sandbox_running": _check_sandbox_status(),
            "kill_switch_active": KillSwitch().is_active(),
        },
        "scans": {"running": len(running), "total": len(all_scans)},
    }
