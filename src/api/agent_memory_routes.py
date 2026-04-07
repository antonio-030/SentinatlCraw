"""Agent-Workspace-Sync — Dateien zwischen Sandbox und UI synchronisieren.

Holt Workspace-Dateien (SOUL.md, IDENTITY.md, USER.md, AGENTS.md, MEMORY.md)
und Agent-eigene Erinnerungen aus der OpenShell-Sandbox zurück in die lokale
workspace/ Ordnerstruktur, damit die UI den aktuellen Stand zeigt.
"""

from pathlib import Path

from fastapi import APIRouter, Request

from src.shared.auth import require_role
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/nemoclaw", tags=["agent-memory"])

WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent / "workspace"
SANDBOX_WORKSPACE = "/sandbox/.openclaw/workspace"
SANDBOX_MEMORY = "/sandbox/.claude/projects/-sandbox/memory"

# Dateien die aus der Sandbox zurückgelesen werden
WORKSPACE_FILES = ("SOUL.md", "IDENTITY.md", "USER.md", "AGENTS.md", "MEMORY.md")


@router.post("/pull-workspace")
async def pull_workspace(request: Request) -> dict:
    """Holt alle Workspace-Dateien + Agent-Memories aus der Sandbox.

    1. Liest SOUL.md, IDENTITY.md, USER.md, AGENTS.md, MEMORY.md
       aus /sandbox/.openclaw/workspace/
    2. Liest Agent-eigene Erinnerungen aus /sandbox/.claude/.../memory/
    3. Schreibt alles in die lokale workspace/ Ordnerstruktur
    """
    require_role(request, "security_lead")

    from src.agents.openshell_executor import run_in_sandbox

    updated: list[str] = []

    # Schritt 1: Workspace-Dateien aus Sandbox holen
    for filename in WORKSPACE_FILES:
        try:
            output, code = await run_in_sandbox(
                f"cat {SANDBOX_WORKSPACE}/{filename} 2>/dev/null",
                timeout=10,
            )
            if code != 0 or not output.strip():
                continue

            local_path = WORKSPACE_DIR / filename
            old_content = local_path.read_text("utf-8") if local_path.exists() else ""
            if output.strip() != old_content.strip():
                local_path.write_text(output, encoding="utf-8")
                updated.append(filename)
        except Exception as error:
            logger.warning("Workspace-Pull fehlgeschlagen", file=filename, error=str(error))

    # Schritt 2: Agent-Memories holen und an MEMORY.md anhängen
    agent_memories = await _pull_agent_memories()
    if agent_memories:
        memory_path = WORKSPACE_DIR / "MEMORY.md"
        existing = memory_path.read_text("utf-8") if memory_path.exists() else ""

        marker = "## Agent-Erinnerungen"
        if marker in existing:
            before = existing.split(marker)[0].rstrip()
            new_content = f"{before}\n\n{marker}\n\n{agent_memories}\n"
        else:
            new_content = f"{existing.rstrip()}\n\n{marker}\n\n{agent_memories}\n"

        memory_path.write_text(new_content, encoding="utf-8")
        if "MEMORY.md" not in updated:
            updated.append("MEMORY.md (+ Agent-Erinnerungen)")

    if not updated:
        return {"success": True, "message": "Alles auf dem neuesten Stand."}

    logger.info("Workspace aus Sandbox aktualisiert", files=updated)
    return {
        "success": True,
        "message": f"{len(updated)} Datei(en) aktualisiert: {', '.join(updated)}",
    }


async def _pull_agent_memories() -> str:
    """Liest Agent-eigene Erinnerungen aus der Sandbox."""
    from src.agents.openshell_executor import run_in_sandbox

    try:
        output, code = await run_in_sandbox(
            f"find {SANDBOX_MEMORY} -name '*.md' ! -name 'MEMORY.md' "
            "-exec echo '### {{}}' \\; -exec cat {{}} \\; -exec echo '' \\; 2>/dev/null",
            timeout=10,
        )
    except Exception:
        return ""

    if code != 0 or not output.strip():
        return ""

    return _clean_memory_output(output)


def _clean_memory_output(output: str) -> str:
    """Entfernt Frontmatter und kürzt Pfade aus dem Memory-Output."""
    clean_lines: list[str] = []
    in_frontmatter = False

    for line in output.splitlines():
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter:
            continue
        if line.startswith("### /sandbox/"):
            clean_lines.append(f"### {line.split('/')[-1]}")
        else:
            clean_lines.append(line)

    return "\n".join(clean_lines).strip()
