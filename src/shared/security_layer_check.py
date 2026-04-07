"""Sicherheitsschichten-Prüfung für SentinelClaw.

Prüft ob ALLE kritischen Sicherheitsschichten aktiv sind bevor
ein Scan oder Agent-Aufruf ausgeführt werden darf.
Ein Firmenumfeld erfordert: Kein Scan ohne vollständige Absicherung.
"""

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def check_all_security_layers() -> tuple[bool, list[str]]:
    """Prüft alle Sicherheitsschichten und gibt Status + Fehler zurück.

    Returns:
        (all_active, error_messages) — True wenn alles OK, sonst Fehlerliste.
    """
    errors: list[str] = []

    # 1. Kill-Switch darf NICHT aktiv sein
    from src.shared.kill_switch import KillSwitch
    if KillSwitch().is_active():
        errors.append("Kill-Switch ist aktiv — alle Operationen gesperrt")

    # 2. Datenbank muss verbunden sein
    try:
        from src.api.server import get_db
        db = await get_db()
        if db is None:
            errors.append("Datenbank nicht verbunden")
        else:
            conn = await db.get_connection()
            await conn.execute("SELECT 1")
    except Exception:
        errors.append("Datenbank nicht erreichbar")

    # 3. Docker muss verfügbar sein
    try:
        from src.shared.infrastructure import check_docker_ready
        docker_ok, docker_msg = await check_docker_ready()
        if not docker_ok:
            errors.append(f"Docker: {docker_msg}")
    except Exception:
        errors.append("Docker nicht erreichbar")

    # 4. Sandbox-Container muss laufen
    try:
        from src.shared.infrastructure import check_sandbox_running
        sandbox_ok, sandbox_msg = await check_sandbox_running()
        if not sandbox_ok:
            errors.append(f"Sandbox: {sandbox_msg}")
    except Exception:
        errors.append("Sandbox-Status unbekannt")

    # 5. NemoClaw/OpenShell muss erreichbar sein (wenn konfiguriert)
    try:
        from src.shared.settings_service import get_setting_sync
        gateway = get_setting_sync("nemoclaw_gateway_name", "nemoclaw")
        if gateway:
            from src.agents.nemoclaw_runtime import NemoClawRuntime
            runtime = NemoClawRuntime()
            status = await runtime.check_sandbox_status()
            if status.get("status") == "unreachable":
                errors.append("NemoClaw-Sandbox nicht erreichbar")
    except Exception:
        # NemoClaw ist optional — wenn nicht konfiguriert, kein Fehler
        pass

    all_active = len(errors) == 0

    if not all_active:
        logger.warning(
            "Sicherheitsschichten nicht vollständig aktiv",
            inactive_count=len(errors),
            errors=errors,
        )

    return all_active, errors
