"""
Scan-Tool-Executor für SentinelClaw.

Führt Scan-Befehle in der OpenShell-Sandbox aus (via SSH).
Validiert Binaries gegen eine Allowlist bevor sie ausgeführt werden.
"""

import asyncio

from src.shared.constants.defaults import ALLOWED_SANDBOX_BINARIES, TOOL_TIMEOUTS
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def execute_scan_command(
    command_parts: list[str],
    timeout: int | None = None,
) -> str:
    """Führt einen Scan-Befehl in der OpenShell-Sandbox aus.

    Validiert dass nur erlaubte Binaries ausgeführt werden.
    Gibt stdout zurück, loggt stderr als Warnung.
    """
    if not command_parts:
        raise ValueError("Leerer Scan-Befehl")

    # Binary gegen Allowlist prüfen, Timeout aus Tool-Tabelle
    binary = command_parts[0]
    if timeout is None:
        timeout = TOOL_TIMEOUTS.get(binary, 120)
    if binary not in ALLOWED_SANDBOX_BINARIES:
        raise ValueError(
            f"Binary '{binary}' nicht erlaubt. "
            f"Erlaubt: {', '.join(sorted(ALLOWED_SANDBOX_BINARIES))}"
        )

    # Tools die ein Ziel brauchen: mindestens ein Argument prüfen
    tools_requiring_target = {"nmap", "nuclei", "curl", "dig", "whois"}
    if binary in tools_requiring_target and len(command_parts) < 2:
        raise ValueError(
            f"'{binary}' braucht mindestens ein Argument (Ziel/URL/Domain)"
        )

    # Befehl als String für SSH zusammenbauen
    command_str = " ".join(command_parts)

    logger.info(
        "Scan-Befehl ausführen",
        binary=binary,
        runtime="openshell",
        args=command_parts[1:5],
    )

    from src.agents.openshell_executor import run_in_sandbox

    try:
        output, return_code = await run_in_sandbox(command_str, timeout=timeout)

        if return_code != 0 and not output:
            raise RuntimeError(
                f"Tool-Ausführung fehlgeschlagen: {command_str[:100]} "
                f"(Exit-Code: {return_code})"
            )

        logger.info(
            "Scan-Befehl abgeschlossen",
            binary=binary,
            output_length=len(output),
            exit_code=return_code,
        )

        return output

    except asyncio.TimeoutError:
        raise RuntimeError(
            f"Scan-Befehl Timeout nach {timeout}s: {' '.join(command_parts[:3])}"
        )
