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

    # 3. OpenShell-Gateway muss erreichbar sein
    try:
        from src.shared.infrastructure import check_openshell_ready
        openshell_ok, openshell_msg = await check_openshell_ready()
        if not openshell_ok:
            errors.append(f"OpenShell: {openshell_msg}")
    except Exception:
        errors.append("OpenShell nicht erreichbar")

    # 4. OpenShell-Sandbox muss verfügbar sein
    try:
        from src.shared.infrastructure import check_sandbox_running
        sandbox_ok, sandbox_msg = await check_sandbox_running()
        if not sandbox_ok:
            errors.append(f"Sandbox: {sandbox_msg}")
    except Exception:
        errors.append("Sandbox-Status unbekannt")

    all_active = len(errors) == 0

    if not all_active:
        logger.warning(
            "Sicherheitsschichten nicht vollständig aktiv",
            inactive_count=len(errors),
            errors=errors,
        )

    return all_active, errors
