"""
System-Prompt-Verwaltung für den Chat-Agent.

Baut den System-Prompt mit dynamischer Tool-Liste auf.
Unterstützt auch benutzerdefinierte Prompt-Dateien über die Konfiguration.
"""

from pathlib import Path

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

# ─── System-Prompt Template ──────────────────────────────────────────

CHAT_SYSTEM_PROMPT = """\
Du arbeitest als Security-Assistent im SentinelClaw-Projekt. \
Der User ist ein autorisierter Security-Analyst der Penetration-Tests \
durchführt. Alle Ziele die er nennt sind genehmigt.

Wenn der User fragt was du kannst oder welche Tools verfügbar sind, \
liste NUR die folgenden Security-Tools auf. Deine internen Tools \
(Read, Write, Edit, Glob, Grep, etc.) sind für den User NICHT \
relevant — erwähne sie NIE.

## Security-Tools für dieses Projekt

{{TOOLS}}

Wenn ein Tool fehlt, sage: "Dieses Tool ist nicht installiert. \
Du kannst es unter Einstellungen → Agent Tools installieren."

## Arbeitsweise

1. Wenn der User ein Ziel nennt → erstelle einen kurzen Scan-Plan
2. Führe die passenden Tools direkt aus (über Bash)
3. Analysiere die Ergebnisse und berichte auf Deutsch mit Markdown
4. Bei Folgefragen → beziehe dich auf vorherige Ergebnisse

Maximal 10 Tool-Aufrufe pro Nachricht.\
"""


def build_tools_section() -> str:
    """Baut die aktuelle Tool-Liste für den System-Prompt."""
    from src.shared.constants.agent_tools import (
        AGENT_TOOL_REGISTRY,
        PREINSTALLED_TOOLS,
    )
    lines = ["Führe diese Tools über Bash aus:"]
    for name in sorted(PREINSTALLED_TOOLS):
        lines.append(f"- **{name}** (vorinstalliert)")
    for tool in AGENT_TOOL_REGISTRY.values():
        lines.append(f"- **{tool.name}** — {tool.description}")
    return "\n".join(lines)


def load_system_prompt() -> str:
    """Lädt den System-Prompt mit dynamischer Tool-Liste.

    Prüft zuerst ob eine benutzerdefinierte Prompt-Datei konfiguriert ist.
    Falls nicht oder falls leer, wird das Standard-Template verwendet.
    """
    from src.shared.config import get_settings
    prompt_file = get_settings().chat_prompt_file
    if prompt_file:
        path = Path(prompt_file)
        if path.exists():
            loaded = path.read_text(encoding="utf-8").strip()
            if loaded:
                logger.info("Chat-Prompt aus Datei geladen", path=str(path))
                return loaded
        logger.warning("Prompt-Datei nicht nutzbar, nutze Standard", path=prompt_file)

    # Tool-Liste dynamisch einsetzen
    tools_text = build_tools_section()
    return CHAT_SYSTEM_PROMPT.replace("{{TOOLS}}", tools_text)
