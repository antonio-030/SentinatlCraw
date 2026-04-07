"""Daten-Aufbewahrungsfristen-Service für SentinelClaw (DSGVO).

Löscht automatisch Scan-Daten die älter als die konfigurierte
Aufbewahrungsfrist sind. Wird beim Server-Start ausgeführt.
"""

from datetime import UTC, datetime, timedelta

from src.shared.database import DatabaseManager
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


async def run_retention_cleanup(db: DatabaseManager) -> int:
    """Löscht Scans und zugehörige Daten älter als die konfigurierte Frist.

    Die Frist wird aus system_settings (key='retention_scan_days') gelesen.
    Wert 0 = Cleanup deaktiviert.

    Returns:
        Anzahl der gelöschten Scans.
    """
    conn = await db.get_connection()

    # Aufbewahrungsfrist aus Settings laden
    cursor = await conn.execute(
        "SELECT value FROM system_settings WHERE key = 'retention_scan_days'"
    )
    row = await cursor.fetchone()
    retention_days = int(row[0]) if row else 0

    if retention_days <= 0:
        logger.debug("Retention-Cleanup deaktiviert (retention_scan_days=0)")
        return 0

    cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()

    # Alte Scan-IDs sammeln
    cursor = await conn.execute(
        "SELECT id FROM scan_jobs WHERE created_at < ? AND status IN ('completed', 'failed')",
        (cutoff,),
    )
    old_scan_ids = [r[0] for r in await cursor.fetchall()]

    if not old_scan_ids:
        return 0

    # Cascade-Löschung für jeden alten Scan
    for table in ["findings", "scan_phases", "discovered_hosts",
                   "open_ports", "scan_results", "approval_requests"]:
        for scan_id in old_scan_ids:
            await conn.execute(
                f"DELETE FROM {table} WHERE scan_job_id = ?", (scan_id,)  # noqa: S608
            )

    # Scan-Jobs selbst löschen
    placeholders = ",".join("?" for _ in old_scan_ids)
    await conn.execute(
        f"DELETE FROM scan_jobs WHERE id IN ({placeholders})",  # noqa: S608
        old_scan_ids,
    )
    await conn.commit()

    logger.info(
        "Retention-Cleanup abgeschlossen",
        deleted_scans=len(old_scan_ids),
        retention_days=retention_days,
        cutoff=cutoff,
    )
    return len(old_scan_ids)
