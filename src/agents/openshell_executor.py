"""
OpenShell-Sandbox-Executor für SentinelClaw.

Führt Befehle in der OpenShell-Sandbox via SSH aus.
Wird für Tool-Installation und -Prüfung genutzt.
Wiederverwendet das SSH-Pattern aus nemoclaw_runtime.py.
"""

import asyncio

from src.shared.config import get_settings
from src.shared.constants.agent_tools import AgentToolDefinition
from src.shared.logging_setup import get_logger
from src.shared.types.agent_runtime import OpenClawConfig

logger = get_logger(__name__)


def _build_ssh_args() -> list[str]:
    """Baut SSH-Argumente für die OpenShell-Sandbox-Verbindung."""
    settings = get_settings()
    config = OpenClawConfig(
        gateway_name=settings.openshell_gateway_name,
        sandbox_name=settings.openshell_sandbox_name,
    )
    proxy_cmd = (
        f"openshell ssh-proxy "
        f"--gateway-name {config.gateway_name} "
        f"--name {config.sandbox_name}"
    )
    return [
        "ssh",
        "-o", f"ProxyCommand={proxy_cmd}",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-o", f"ConnectTimeout={config.ssh_timeout}",
        f"sandbox@openshell-{config.sandbox_name}",
    ]


def _get_blocked_binaries() -> frozenset[str]:
    """Lädt die blockierten Binaries aus den Settings (konfigurierbar über UI)."""
    try:
        from src.shared.settings_service import get_setting_sync
        blocked_str = get_setting_sync(
            "agent_blocked_binaries",
            "pip,pip3,apt,apt-get,npm,yarn,brew,cargo,gem",
        )
        return frozenset(b.strip() for b in blocked_str.split(",") if b.strip())
    except Exception:
        # Fallback falls Settings-Service nicht verfügbar (z.B. beim Start)
        return frozenset({
            "pip", "pip3", "apt", "apt-get", "dpkg", "yum", "dnf",
            "pacman", "brew", "npm", "yarn", "pnpm", "cargo", "gem",
        })


def _is_package_manager_command(command: str) -> bool:
    """Prüft ob ein Befehl einen blockierten Binary aufruft."""
    first_word = command.strip().split()[0] if command.strip() else ""
    return first_word in _get_blocked_binaries()


async def run_in_sandbox(command: str, timeout: int = 60) -> tuple[str, int]:
    """Führt einen Befehl in der OpenShell-Sandbox via SSH aus.

    Gibt (stdout, return_code) zurück.
    Paketmanager-Befehle werden grundsätzlich blockiert.
    """
    if _is_package_manager_command(command):
        raise PermissionError(
            f"Paketmanager-Befehl blockiert: '{command.split()[0]}'. "
            f"Tool-Installation nur über die Web-UI."
        )

    ssh_args = _build_ssh_args()
    proc = await asyncio.create_subprocess_exec(
        *ssh_args, command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout,
        )
    except TimeoutError:
        proc.kill()
        raise RuntimeError(f"Sandbox-Befehl Timeout nach {timeout}s")

    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()

    # stderr an stdout anhaengen wenn vorhanden
    combined = f"{out}\n{err}".strip() if err else out
    return combined, proc.returncode or 0


async def check_tool(tool: AgentToolDefinition) -> tuple[bool, str]:
    """Prüft ob ein Tool in der Sandbox installiert ist.

    Gibt (ist_installiert, version_output) zurück.
    """
    try:
        output, code = await run_in_sandbox(tool.check_command, timeout=10)
        return code == 0, output[:200]
    except Exception as error:
        logger.warning("Tool-Check fehlgeschlagen", tool=tool.name, error=str(error))
        return False, str(error)


async def _run_privileged(command: str, timeout: int = 60) -> tuple[str, int]:
    """Führt einen Befehl OHNE Paketmanager-Blockade aus.

    NUR für admin-autorisierte Tool-Installation/Deinstallation.
    Wird NICHT vom Agent aufgerufen, sondern nur von der API.
    """
    ssh_args = _build_ssh_args()
    proc = await asyncio.create_subprocess_exec(
        *ssh_args, command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout,
        )
    except TimeoutError:
        proc.kill()
        raise RuntimeError(f"Sandbox-Befehl Timeout nach {timeout}s")

    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()
    combined = f"{out}\n{err}".strip() if err else out
    return combined, proc.returncode or 0


async def install_tool(tool: AgentToolDefinition) -> str:
    """Installiert ein Tool in der OpenShell-Sandbox.

    Verwendet den privilegierten Pfad (umgeht Paketmanager-Blockade),
    da der Aufruf nur über die authentifizierte API möglich ist.
    """
    logger.info("Tool-Installation gestartet", tool=tool.name)
    output, code = await _run_privileged(
        tool.install_command, timeout=tool.install_timeout,
    )
    if code != 0:
        raise RuntimeError(f"Installation fehlgeschlagen (Exit {code}): {output[:300]}")

    logger.info("Tool installiert", tool=tool.name)
    return output


async def uninstall_tool(tool: AgentToolDefinition) -> str:
    """Deinstalliert ein Tool aus der OpenShell-Sandbox.

    Verwendet den privilegierten Pfad — nur über authentifizierte API aufrufbar.
    """
    logger.info("Tool-Deinstallation gestartet", tool=tool.name)
    output, code = await _run_privileged(
        tool.uninstall_command, timeout=60,
    )
    if code != 0:
        raise RuntimeError(f"Deinstallation fehlgeschlagen (Exit {code}): {output[:300]}")

    logger.info("Tool deinstalliert", tool=tool.name)
    return output
