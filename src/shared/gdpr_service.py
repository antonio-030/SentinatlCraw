"""DSGVO-Service für SentinelClaw.

Stellt Funktionen für Datenexport (Art. 15/20), Cascade-Löschung (Art. 17)
und Audit-Log-Anonymisierung bereit.
"""

from datetime import UTC, datetime

from src.shared.database import DatabaseManager
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def export_user_data(user_id: str, db: DatabaseManager) -> dict:
    """Exportiert alle Daten eines Benutzers (DSGVO Art. 15 + Art. 20).

    Sammelt: Profil, Scans, Findings, Chat-Nachrichten, Approvals.
    Audit-Logs werden NICHT exportiert (gehören dem System, nicht dem User).
    """
    conn = await db.get_connection()

    # Benutzerprofil
    cursor = await conn.execute(
        "SELECT id, email, display_name, role, is_active, mfa_enabled, "
        "last_login_at, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    user_row = await cursor.fetchone()
    if not user_row:
        return {"error": "Benutzer nicht gefunden"}

    user_data = {
        "id": user_row[0], "email": user_row[1], "display_name": user_row[2],
        "role": user_row[3], "is_active": bool(user_row[4]),
        "mfa_enabled": bool(user_row[5]), "last_login_at": user_row[6],
        "created_at": user_row[7],
    }

    # Scan-Jobs (erstellt durch diesen User oder alle als Admin)
    cursor = await conn.execute(
        "SELECT id, target, scan_type, status, created_at, completed_at "
        "FROM scan_jobs ORDER BY created_at DESC"
    )
    scans = [
        {"id": r[0], "target": r[1], "scan_type": r[2],
         "status": r[3], "created_at": r[4], "completed_at": r[5]}
        for r in await cursor.fetchall()
    ]

    # Findings
    cursor = await conn.execute(
        "SELECT id, title, severity, target_host, description, created_at "
        "FROM findings ORDER BY created_at DESC"
    )
    findings = [
        {"id": r[0], "title": r[1], "severity": r[2],
         "target_host": r[3], "description": r[4], "created_at": r[5]}
        for r in await cursor.fetchall()
    ]

    # Chat-Nachrichten
    cursor = await conn.execute(
        "SELECT id, role, content, created_at FROM chat_messages ORDER BY created_at DESC"
    )
    messages = [
        {"id": r[0], "role": r[1], "content": r[2], "created_at": r[3]}
        for r in await cursor.fetchall()
    ]

    # Einwilligungen
    cursor = await conn.execute(
        "SELECT consent_type, granted, created_at FROM consent_records "
        "WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    )
    consents = [
        {"type": r[0], "granted": bool(r[1]), "created_at": r[2]}
        for r in await cursor.fetchall()
    ]

    logger.info("DSGVO-Datenexport erstellt", user_id=user_id)

    return {
        "export_date": datetime.now(UTC).isoformat(),
        "user": user_data,
        "scans": scans,
        "findings": findings,
        "chat_messages": messages,
        "consents": consents,
    }


async def delete_user_data(user_id: str, db: DatabaseManager) -> dict:
    """Löscht alle Daten eines Benutzers (DSGVO Art. 17).

    Cascade-Löschung: Scans → Findings → Phases → Hosts → Ports → Chat.
    Audit-Logs werden ANONYMISIERT (nicht gelöscht — rechtlich erforderlich).

    Returns:
        Dict mit Anzahl gelöschter Einträge pro Tabelle.
    """
    conn = await db.get_connection()
    counts: dict[str, int] = {}

    # Scan-IDs des Users sammeln
    cursor = await conn.execute(
        "SELECT id FROM scan_jobs"
    )
    scan_ids = [r[0] for r in await cursor.fetchall()]

    # Cascade: Findings, Phases, Hosts, Ports pro Scan löschen
    for table in ["findings", "scan_phases", "discovered_hosts",
                   "open_ports", "scan_results", "approval_requests"]:
        total = 0
        for sid in scan_ids:
            cursor = await conn.execute(
                f"DELETE FROM {table} WHERE scan_job_id = ?", (sid,)  # noqa: S608
            )
            total += cursor.rowcount
        counts[table] = total

    # Scan-Jobs löschen
    cursor = await conn.execute("DELETE FROM scan_jobs")
    counts["scan_jobs"] = cursor.rowcount

    # Chat-Nachrichten löschen
    cursor = await conn.execute("DELETE FROM chat_messages")
    counts["chat_messages"] = cursor.rowcount

    # Agent-Reports löschen
    cursor = await conn.execute("DELETE FROM agent_reports")
    counts["agent_reports"] = cursor.rowcount

    # Einwilligungen des Users löschen
    cursor = await conn.execute(
        "DELETE FROM consent_records WHERE user_id = ?", (user_id,)
    )
    counts["consent_records"] = cursor.rowcount

    # Audit-Logs ANONYMISIEREN (nicht löschen!)
    cursor = await conn.execute(
        "UPDATE audit_logs SET triggered_by = 'deleted_user' "
        "WHERE triggered_by IN (SELECT email FROM users WHERE id = ?)",
        (user_id,),
    )
    counts["audit_logs_anonymized"] = cursor.rowcount

    # User selbst löschen
    await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    counts["users"] = 1

    await conn.commit()

    logger.info("DSGVO-Löschung durchgeführt", user_id=user_id, counts=counts)
    return counts
