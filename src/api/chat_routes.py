"""
Chat-Routen fuer die SentinelClaw REST-API.

Agent-Chat — nutzt Anthropic API direkt (schnell, kein CLI-Overhead)
oder Claude CLI als Fallback.
"""

import asyncio
import re
import shutil
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.shared.config import get_settings
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# ─── Request/Response Modelle ──────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(description="Nachricht an den Agent")
    scan_id: str | None = Field(default=None, description="Optionale Scan-ID fuer Kontext")


class ChatResponseModel(BaseModel):
    response: str
    scan_started: bool = False
    scan_id: str | None = None


class ChatMessageOut(BaseModel):
    id: str
    role: str
    content: str
    message_type: str
    created_at: str
    scan_id: str | None = None


# ─── DB-Zugriff ──────────────────────────────────────────────────────


async def _get_db():
    from src.api.server import get_db
    return await get_db()


async def _save_message(role: str, content: str, scan_id: str | None = None,
                        message_type: str = "text") -> None:
    """Speichert eine Chat-Nachricht in der DB."""
    db = await _get_db()
    conn = await db.get_connection()
    await conn.execute(
        "INSERT INTO chat_messages (id, scan_id, role, content, message_type, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(uuid4()), scan_id, role, content, message_type, datetime.now(UTC).isoformat()),
    )
    await conn.commit()


# ─── Scan-Befehl-Erkennung ──────────────────────────────────────────


def _detect_scan_command(message: str) -> tuple[bool, str | None]:
    """Erkennt Scan-Befehle und extrahiert das Ziel."""
    scan_pattern = re.compile(
        r"(?:scanne?|teste?|pr[uü]fe|check|scan)\s+(\S+)", re.IGNORECASE
    )
    match = scan_pattern.search(message)
    if match:
        target = match.group(1).strip(".,;:!?\"'")
        if "." in target or ":" in target or "/" in target:
            return True, target
    return False, None


async def _start_scan_from_chat(target: str, scan_id_ref: list[str]) -> None:
    """Erstellt und startet einen Scan-Job aus dem Chat."""
    from src.shared.repositories import ScanJobRepository
    from src.shared.types.models import ScanJob

    db = await _get_db()
    scan_repo = ScanJobRepository(db)
    job = ScanJob(target=target, scan_type="recon", config={"ports": "1-1000", "source": "chat"})
    await scan_repo.create(job)
    scan_id_ref.append(str(job.id))

    from src.api.scan_routes import _run_scan_background
    asyncio.create_task(_run_scan_background(str(job.id), target, "1-1000", 2))
    logger.info("Scan aus Chat gestartet", scan_id=str(job.id), target=target)


# ─── Claude-Aufruf: API zuerst, CLI als Fallback ────────────────────


async def _ask_claude(prompt: str) -> str:
    """Fragt Claude — API wenn Key vorhanden, sonst CLI."""
    settings = get_settings()

    # 1. Anthropic API (schnell, 5-15s)
    if settings.has_claude_key():
        try:
            return await _ask_claude_api(prompt, settings.claude_api_key, settings.claude_model)
        except Exception as e:
            logger.warning("Anthropic API fehlgeschlagen, versuche CLI", error=str(e))

    # 2. Claude CLI Fallback
    return await _ask_claude_cli(prompt)


async def _ask_claude_api(prompt: str, api_key: str, model: str) -> str:
    """Direkte Anthropic API — schnell, keine Session-Konflikte."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        system="Du bist der SentinelClaw Orchestrator-Agent. Antworte auf Deutsch, nutze Markdown. Sei ein proaktiver Security-Assistent.",
    )

    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)

    return "\n".join(text_parts) or "Keine Antwort erhalten."


async def _ask_claude_cli(prompt: str) -> str:
    """Claude CLI im Agent-Modus — kann Bash-Tools nutzen für echte Arbeit."""
    claude_bin = shutil.which("claude")
    if not claude_bin:
        return "Claude ist gerade nicht verfügbar."

    try:
        short_prompt = prompt[:3000]

        # Agent-Modus mit Bash-Tool — Claude kann echte Befehle ausführen
        proc = await asyncio.create_subprocess_exec(
            claude_bin, "--print",
            "--output-format", "json",
            "--permission-mode", "bypassPermissions",
            "--max-turns", "5",
            "--allowedTools", "Bash,Read,Grep,Glob",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=short_prompt.encode("utf-8")), timeout=300
        )

        raw = stdout.decode("utf-8", errors="replace").strip()

        if raw:
            try:
                import json as _json
                data = _json.loads(raw)
                return data.get("result", data.get("content", raw))
            except Exception:
                return raw

        # Auch bei Exit 1 — wenn Output da ist, nutzen
        if proc.returncode != 0:
            err = stderr.decode("utf-8", errors="replace").strip()
            logger.warning("Claude Agent Exit-Code", code=proc.returncode, err=err[:200])
            if raw:
                return raw

        return "Claude konnte nicht antworten. Versuche es erneut."

    except asyncio.TimeoutError:
        try:
            proc.kill()
        except Exception:
            pass
        return (
            "Die Analyse dauert länger als 5 Minuten. "
            "Versuche eine spezifischere Frage, z.B.:\n\n"
            "- **\"Prüfe ob /api/v1/scans SQL-Injection-sicher ist\"**\n"
            "- **\"Teste den Auth-Endpoint\"**\n"
        )
    except Exception as e:
        logger.error("Claude Agent fehlgeschlagen", error=str(e))
        return f"Fehler bei der Analyse: {e}"


# ─── Chat-Endpoint ──────────────────────────────────────────────────


@router.post("", response_model=ChatResponseModel)
async def send_chat_message(request: ChatRequest) -> ChatResponseModel:
    """Chat mit dem Orchestrator-Agent."""
    message = request.message.strip()
    scan_id = request.scan_id

    if not message:
        return ChatResponseModel(response="Bitte gib eine Nachricht ein.")

    try:
        await _save_message("user", message, scan_id=scan_id)
    except Exception:
        pass

    try:
        return await _process_chat(message, scan_id)
    except Exception as e:
        logger.error("Chat fehlgeschlagen", error=str(e))
        return ChatResponseModel(response=f"Fehler: {e}")


async def _process_chat(message: str, scan_id: str | None) -> ChatResponseModel:
    """Verarbeitet die Chat-Nachricht."""

    # 1. Scan-Befehl?
    is_scan, target = _detect_scan_command(message)
    if is_scan and target:
        scan_id_ref: list[str] = []
        await _start_scan_from_chat(target, scan_id_ref)
        new_scan_id = scan_id_ref[0] if scan_id_ref else None

        response_text = (
            f"Ich starte einen Scan auf **{target}**.\n\n"
            f"🔍 Phase 1: Host Discovery\n"
            f"🔌 Phase 2: Port-Scan\n"
            f"⚠️ Phase 3: Vulnerability Assessment\n"
            f"📊 Phase 4: Analyse\n\n"
            f"Verfolge den Fortschritt in der Live-Ansicht."
        )

        try:
            await _save_message("system", f"Scan gestartet: {target}",
                                scan_id=new_scan_id, message_type="scan_started")
            await _save_message("agent", response_text, scan_id=new_scan_id)
        except Exception:
            pass

        return ChatResponseModel(response=response_text, scan_started=True, scan_id=new_scan_id)

    # 2. Alles andere → Claude als Agent (mit Tools!)
    prompt = (
        f"Du bist der SentinelClaw Orchestrator-Agent im Projekt /Users/antonio/Desktop/SentinelClaw.\n"
        f"API läuft auf Port 3001. Du hast Zugriff auf Bash, Read, Grep, Glob.\n"
        f"Antworte auf Deutsch. Nutze Markdown. Sei konkret.\n\n"
        f"Aufgabe: {message}"
    )
    response_text = await _ask_claude(prompt)

    try:
        await _save_message("agent", response_text, scan_id=scan_id)
    except Exception:
        pass

    return ChatResponseModel(response=response_text, scan_started=False)


# ─── Chat-History ────────────────────────────────────────────────────


@router.get("/history", response_model=list[ChatMessageOut])
async def get_chat_history(
    scan_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ChatMessageOut]:
    """Gibt den Chat-Verlauf zurück."""
    db = await _get_db()
    conn = await db.get_connection()

    if scan_id:
        cursor = await conn.execute(
            "SELECT * FROM chat_messages WHERE scan_id = ? ORDER BY created_at DESC LIMIT ?",
            (scan_id, limit),
        )
    else:
        cursor = await conn.execute(
            "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )

    rows = await cursor.fetchall()
    return [
        ChatMessageOut(
            id=row[0], scan_id=row[1], role=row[2], content=row[3],
            message_type=row[4], created_at=row[5],
        )
        for row in reversed(rows)
    ]
