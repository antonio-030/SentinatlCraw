"""
Netzwerk-Kill für SentinelClaw (Kill-Pfad 3).

Blockiert allen ausgehenden Traffic der Sandbox über OpenShell-Sandbox-Löschung.
Im OpenShell-Modell wird die gesamte Sandbox zerstört, was alle Netzwerk-
verbindungen sofort trennt. Alle Funktionen fangen Fehler ab und crashen
niemals — der Kill-Pfad muss immer durchlaufen.
"""

import asyncio
import subprocess

from src.shared.config import get_settings
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def block_scanning_network() -> bool:
    """Blockiert das Scan-Netzwerk vollständig.

    Löscht die OpenShell-Sandbox mit --force, was alle Netzwerkverbindungen
    sofort trennt. Die Sandbox kann nach dem Kill-Reset neu erstellt werden.

    Gibt True zurück wenn die Sandbox erfolgreich gelöscht wurde.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _delete_sandbox)


def _delete_sandbox() -> bool:
    """Löscht die OpenShell-Sandbox (synchron)."""
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "delete", sandbox_name, "--force"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            logger.info("sandbox_deleted_for_network_kill", sandbox=sandbox_name)
            return True

        # Sandbox existiert möglicherweise nicht mehr — auch ein Erfolg
        stderr = result.stderr.strip()
        if "not found" in stderr.lower() or "does not exist" in stderr.lower():
            logger.info("sandbox_already_gone", sandbox=sandbox_name)
            return True

        logger.warning(
            "sandbox_delete_failed",
            sandbox=sandbox_name,
            returncode=result.returncode,
            stderr=stderr[:200],
        )
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("sandbox_delete_error", error=str(exc))
        return False


async def verify_network_blocked() -> bool:
    """Prüft ob die Sandbox nicht mehr existiert.

    Gibt True zurück wenn die Sandbox nicht mehr in der Liste auftaucht.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _check_sandbox_absent)


def _check_sandbox_absent() -> bool:
    """Prüft synchron ob die Sandbox nicht mehr existiert."""
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            # openshell nicht erreichbar — konservativer Ansatz: nicht blockiert
            logger.warning("openshell_list_failed", returncode=result.returncode)
            return False

        # Prüfe ob der Sandbox-Name in der Ausgabe vorkommt
        if sandbox_name in result.stdout:
            logger.warning("sandbox_still_running", sandbox=sandbox_name)
            return False
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        logger.debug("sandbox_check_error", error=str(exc))
        # openshell nicht verfügbar — Sandbox kann nicht laufen
        return True


async def get_network_status() -> dict:
    """Gibt den OpenShell-Sandbox-Status zurück."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _collect_sandbox_status)


def _collect_sandbox_status() -> dict:
    """Sammelt Sandbox-Status-Informationen synchron."""
    status: dict = {"sandbox_exists": False, "sandbox_name": ""}
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name
        status["sandbox_name"] = sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            status["sandbox_exists"] = sandbox_name in result.stdout
        else:
            status["error"] = f"openshell returncode {result.returncode}"
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        status["error"] = str(exc)

    return status
