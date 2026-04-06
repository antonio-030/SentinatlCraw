"""
Chat-Agent für SentinelClaw mit Chat-History.

Nutzt die NemoClaw-Runtime mit dem OpenClaw-Agent 'sentinelclaw'
in der OpenShell-Sandbox. Der Agent führt Security-Tools autonom
aus (curl, dig, whois, sqlmap, etc.) und analysiert Ergebnisse.

Chat-History wird als Messages-Liste übergeben, damit der Agent
den Konversationskontext behält.
"""

import time
from uuid import uuid4

from src.agents.chat_system_prompt import load_system_prompt
from src.agents.nemoclaw_runtime import NemoClawRuntime
from src.agents.report_persistence import attach_report_notice
from src.agents.scan_executor import execute_scan_command
from src.agents.tool_marker_parser import (
    parse_tool_markers,
    strip_tool_markers,
    validate_tool_command,
)
from src.shared.constants.defaults import (
    MAX_TOOL_CALLS_PER_TURN,
    MAX_TOOL_OUTPUT_LENGTH,
)
from src.shared.kill_switch import KillSwitch
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

# Typ-Alias für einzelne Tool-Step-Einträge (WebSocket + Metadata)
ToolStep = dict[str, str | int | bool]

# Globale Runtime-Instanz (wird beim ersten Aufruf erstellt)
_runtime: NemoClawRuntime | None = None

# Maximale Anzahl History-Nachrichten die an Claude gesendet werden
MAX_HISTORY_MESSAGES = 20


async def ask_agent(
    message: str,
    history: list[dict[str, str]] | None = None,
) -> tuple[str, list[ToolStep]]:
    """Sendet eine Nachricht an den Agent mit optionaler Chat-History.

    Der Agent kann autonom Tools aufrufen. Tool-Blöcke (```tool)
    werden in der Docker-Sandbox ausgeführt und das Ergebnis an den
    Agent zurückgesendet, bis er ohne Tool-Blöcke antwortet.

    Args:
        message: Aktuelle User-Nachricht.
        history: Vorherige Nachrichten als Liste von
                 {"role": "user"/"assistant", "content": "..."}.

    Returns:
        Tuple aus (Antworttext, Liste der Tool-Steps für Metadata).
    """
    global _runtime

    if _runtime is None:
        _runtime = NemoClawRuntime()

    session_id = f"sc-chat-{uuid4().hex[:8]}"

    # Messages-Liste aufbauen: History + aktuelle Nachricht
    messages = _build_messages(message, history)

    try:
        return await _run_tool_loop(messages, session_id)
    except RuntimeError as error:
        logger.error("Chat-Agent fehlgeschlagen", error=str(error))
        return f"Agent-Fehler: {error}", []
    except Exception as error:
        logger.error("Unerwarteter Chat-Agent-Fehler", error=str(error))
        return f"Fehler: {error}", []


def _build_messages(
    current_message: str,
    history: list[dict[str, str]] | None,
) -> list[dict[str, str]]:
    """Baut die Messages-Liste aus History + aktueller Nachricht."""
    messages: list[dict[str, str]] = []
    if history:
        for msg in history[-MAX_HISTORY_MESSAGES:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": current_message})
    return messages


async def _run_tool_loop(
    messages: list[dict[str, str]],
    session_id: str,
) -> tuple[str, list[ToolStep]]:
    """Agent-Loop: Claude aufrufen, Tools ausführen, wiederholen bis fertig.

    Returns:
        Tuple aus (Antworttext, gesammelte Tool-Steps für Metadata).
    """
    total_tool_calls = 0
    system_prompt = load_system_prompt()
    all_tool_steps: list[ToolStep] = []

    for _iteration in range(MAX_TOOL_CALLS_PER_TURN + 1):
        # Kill-Switch prüfen
        if KillSwitch().is_active():
            return "Agent gestoppt — Kill-Switch ist aktiv.", all_tool_steps

        # WebSocket: Denk-Phase signalisieren
        await _push_agent_step({
            "type": "thinking",
            "message": f"Agent analysiert... (Iteration {_iteration + 1})",
            "iteration": _iteration + 1,
            "total_tools": total_tool_calls,
        })

        # Claude mit voller Message-History aufrufen
        result = await _runtime.run_agent(
            system_prompt=system_prompt,
            messages=messages,
            session_id=session_id,
        )

        agent_text = result.final_output

        # Tool-Marker parsen
        markers = parse_tool_markers(agent_text)

        # Keine Marker → Agent ist fertig — Report-Persistierung prüfen
        if not markers:
            response = strip_tool_markers(agent_text)
            return await attach_report_notice(response), all_tool_steps

        # Iteration-Limit erreicht
        if total_tool_calls + len(markers) > MAX_TOOL_CALLS_PER_TURN:
            logger.warning("Tool-Limit erreicht", total=total_tool_calls)
            response = strip_tool_markers(agent_text) + (
                "\n\n*(Tool-Limit erreicht — maximal "
                f"{MAX_TOOL_CALLS_PER_TURN} Aufrufe pro Anfrage)*"
            )
            return await attach_report_notice(response), all_tool_steps

        # Claude's Antwort (mit Markern) als Assistant-Message anhängen
        messages.append({"role": "assistant", "content": agent_text})

        # Tools ausführen — Steps werden gesammelt und per WebSocket gepusht
        tool_results, steps = await _execute_tools(markers, session_id)
        all_tool_steps.extend(steps)
        total_tool_calls += len(markers)

        # Ergebnisse als User-Message anhängen
        results_text = _format_tool_results(tool_results)
        messages.append({"role": "user", "content": results_text})

    # Sollte nicht erreicht werden — trotzdem Report-Persistierung prüfen
    response = strip_tool_markers(agent_text)
    return await attach_report_notice(response), all_tool_steps


async def _execute_tools(
    markers: list, session_id: str,
) -> tuple[list[tuple[str, str]], list[ToolStep]]:
    """Führt Tool-Marker in der Sandbox aus.

    Returns:
        Tuple aus (Ergebnis-Liste, Tool-Steps für Metadata/WebSocket).
    """
    results: list[tuple[str, str]] = []
    steps: list[ToolStep] = []

    for marker in markers:
        validated = validate_tool_command(marker.raw_command)
        tool_name = validated.binary if validated.is_valid else "unknown"

        if not validated.is_valid:
            results.append((
                marker.raw_command,
                f"ABGELEHNT: {validated.rejection_reason}",
            ))
            steps.append({
                "type": "tool_result", "tool": tool_name,
                "success": False, "output_preview": validated.rejection_reason or "",
                "duration_ms": 0,
            })
            logger.warning(
                "Tool-Aufruf abgelehnt",
                command=marker.raw_command[:80],
                reason=validated.rejection_reason,
                session_id=session_id,
            )
            continue

        # WebSocket: Tool startet
        await _push_agent_step({
            "type": "tool_start",
            "tool": tool_name,
            "command": marker.raw_command[:200],
        })

        start_time = time.monotonic()
        try:
            output = await execute_scan_command(
                [validated.binary, *validated.arguments],
            )
            duration = time.monotonic() - start_time

            # Output begrenzen
            if len(output) > MAX_TOOL_OUTPUT_LENGTH:
                output = output[:MAX_TOOL_OUTPUT_LENGTH] + "\n... (gekürzt)"

            results.append((marker.raw_command, output))

            # WebSocket: Tool fertig (Erfolg)
            step: ToolStep = {
                "type": "tool_result", "tool": tool_name,
                "success": True, "output_preview": output[:300],
                "duration_ms": int(duration * 1000),
            }
            steps.append(step)
            await _push_agent_step(step)

            logger.info(
                "Tool ausgeführt",
                binary=validated.binary,
                output_length=len(output),
                session_id=session_id,
            )
        except Exception as error:
            duration = time.monotonic() - start_time
            results.append((marker.raw_command, f"FEHLER: {error}"))

            # WebSocket: Tool fertig (Fehler)
            step = {
                "type": "tool_result", "tool": tool_name,
                "success": False, "output_preview": str(error)[:300],
                "duration_ms": int(duration * 1000),
            }
            steps.append(step)
            await _push_agent_step(step)

            logger.error(
                "Tool-Ausführung fehlgeschlagen",
                command=marker.raw_command[:80],
                error=str(error),
                session_id=session_id,
            )

    return results, steps


async def _push_agent_step(data: ToolStep) -> None:
    """Pusht einen Tool-Step über WebSocket an alle verbundenen Clients.

    Fehler werden stillschweigend ignoriert — WebSocket ist optional.
    """
    try:
        from src.api.websocket_manager import ws_manager
        await ws_manager.broadcast("agent_step", data)
    except Exception:
        pass


def _format_tool_results(tool_results: list[tuple[str, str]]) -> str:
    """Formatiert Tool-Ergebnisse als Text fuer den naechsten Claude-Aufruf."""
    parts: list[str] = ["Hier sind die Tool-Ergebnisse:\n"]

    for command, output in tool_results:
        parts.append(f"━━━ {command} ━━━\n{output}\n")

    parts.append("Analysiere die Ergebnisse und fahre fort.")

    return "\n".join(parts)
