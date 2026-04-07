"""
Infrastruktur-Prüfungen für SentinelClaw.

Zentrale Funktionen um die Verfügbarkeit von OpenShell, Sandbox
und anderen Abhängigkeiten zu prüfen. Werden vor Scan-Start
und in Health-Checks verwendet.
"""

import subprocess

from src.shared.config import get_settings
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def check_openshell_ready() -> tuple[bool, str]:
    """Prüft ob OpenShell erreichbar ist."""
    try:
        result = subprocess.run(
            ["openshell", "status"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, "OpenShell erreichbar"
        return False, f"OpenShell Fehler: {result.stderr.strip()[:200]}"
    except FileNotFoundError:
        return False, "OpenShell CLI nicht installiert"
    except subprocess.TimeoutExpired:
        return False, "OpenShell Timeout"
    except Exception as error:
        return False, f"OpenShell nicht erreichbar: {error}"


async def check_sandbox_running() -> tuple[bool, str]:
    """Prüft ob die OpenShell-Sandbox läuft."""
    try:
        settings = get_settings()
        sandbox_name = settings.openshell_sandbox_name

        result = subprocess.run(
            ["openshell", "sandbox", "list"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return False, (
                "OpenShell nicht erreichbar. "
                "Starte mit: openshell sandbox create"
            )

        if sandbox_name in result.stdout:
            return True, "Sandbox läuft"
        return False, (
            f"Sandbox '{sandbox_name}' nicht gefunden. "
            f"Erstelle mit: openshell sandbox create {sandbox_name}"
        )
    except FileNotFoundError:
        return False, "OpenShell CLI nicht installiert"
    except Exception as error:
        return False, f"Sandbox-Prüfung fehlgeschlagen: {error}"
