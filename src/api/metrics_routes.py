"""
Prometheus-Metriken-Endpoint für SentinelClaw.

Stellt Metriken im Prometheus-Expositionsformat bereit.
Kein prometheus_client nötig — einfaches Text-Format.

Endpoint: GET /metrics (öffentlich für Prometheus-Scraper)
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from starlette.responses import PlainTextResponse

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Metrics"])

# Server-Startzeit für Uptime-Berechnung
_start_time = datetime.now(UTC)


async def _get_db():
    from src.api.server import get_db
    return await get_db()


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics() -> str:
    """Gibt Metriken im Prometheus-Expositionsformat zurück."""
    db = await _get_db()
    conn = await db.get_connection()
    lines: list[str] = []

    # ── Scan-Metriken ──────────────────────────────────────────
    cursor = await conn.execute(
        "SELECT status, COUNT(*) FROM scan_jobs GROUP BY status"
    )
    lines.append("# HELP sentinelclaw_scans_total Anzahl Scans nach Status")
    lines.append("# TYPE sentinelclaw_scans_total gauge")
    for row in await cursor.fetchall():
        lines.append(f'sentinelclaw_scans_total{{status="{row[0]}"}} {row[1]}')

    # ── Finding-Metriken ───────────────────────────────────────
    cursor = await conn.execute(
        "SELECT severity, COUNT(*) FROM findings GROUP BY severity"
    )
    lines.append("# HELP sentinelclaw_findings_total Anzahl Findings nach Severity")
    lines.append("# TYPE sentinelclaw_findings_total gauge")
    for row in await cursor.fetchall():
        lines.append(f'sentinelclaw_findings_total{{severity="{row[0]}"}} {row[1]}')

    # ── Token-Verbrauch ────────────────────────────────────────
    cursor = await conn.execute(
        "SELECT COALESCE(SUM(tokens_used), 0) FROM scan_jobs"
    )
    row = await cursor.fetchone()
    lines.append("# HELP sentinelclaw_tokens_used_total Gesamter Token-Verbrauch")
    lines.append("# TYPE sentinelclaw_tokens_used_total counter")
    lines.append(f"sentinelclaw_tokens_used_total {row[0]}")

    # ── Benutzer-Metriken ──────────────────────────────────────
    cursor = await conn.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
    row = await cursor.fetchone()
    lines.append("# HELP sentinelclaw_users_active Aktive Benutzer")
    lines.append("# TYPE sentinelclaw_users_active gauge")
    lines.append(f"sentinelclaw_users_active {row[0]}")

    # ── Audit-Log-Metriken ─────────────────────────────────────
    cursor = await conn.execute("SELECT COUNT(*) FROM audit_logs")
    row = await cursor.fetchone()
    lines.append("# HELP sentinelclaw_audit_entries_total Audit-Log-Einträge")
    lines.append("# TYPE sentinelclaw_audit_entries_total counter")
    lines.append(f"sentinelclaw_audit_entries_total {row[0]}")

    # ── Uptime ─────────────────────────────────────────────────
    uptime = (datetime.now(UTC) - _start_time).total_seconds()
    lines.append("# HELP sentinelclaw_uptime_seconds Server-Uptime in Sekunden")
    lines.append("# TYPE sentinelclaw_uptime_seconds gauge")
    lines.append(f"sentinelclaw_uptime_seconds {uptime:.0f}")

    # ── Sandbox-Status ─────────────────────────────────────────
    try:
        import docker as docker_lib
        client = docker_lib.from_env()
        container = client.containers.get("sentinelclaw-sandbox")
        sandbox_up = 1 if container.status == "running" else 0
    except Exception:
        sandbox_up = 0

    lines.append("# HELP sentinelclaw_sandbox_running Sandbox-Container Status (1=läuft)")
    lines.append("# TYPE sentinelclaw_sandbox_running gauge")
    lines.append(f"sentinelclaw_sandbox_running {sandbox_up}")

    return "\n".join(lines) + "\n"
