"""
Report-Persistierung für den Chat-Agent.

Erkennt automatisch ob eine Agent-Antwort ein strukturierter Report ist
(OSINT, Vulnerability, etc.) und speichert ihn in der agent_reports Tabelle.
"""

import re
from datetime import UTC, datetime
from uuid import uuid4

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

# Report-Marker die auf einen strukturierten Report hindeuten
# Breit gefasst: Titel-Marker ODER strukturelle Marker (Tabellen + Findings)
TITLE_MARKERS = [
    "# OSINT-Bericht", "# OSINT-Report", "# Scan-Bericht",
    "# Security-Report", "# Technischer Report",
    "# Executive Summary", "# Vulnerability Report",
    "# Sicherheitstest", "# Pentest-Report",
    "# Admin-Routen", "# Reconnaissance",
    "\U0001f4ca OSINT", "\U0001f50d Reconnaissance",
]

# Strukturelle Marker — wenn mehrere davon vorkommen, ist es ein Report
STRUCTURE_MARKERS = [
    "Kritischer Befund", "CVSS-Score", "Risiko-Matrix",
    "Empfehlungen", "Zusammenfassung", "Übersicht",
    "Schwachstelle", "Severity", "Scan-Datum",
    "## Empfehlungen", "🔴 Kritisch", "🟠 Mittel",
    "🚨 Kritisch", "🛡️ Empfehlungen", "🎯 Risiko",
    "| HTTP-Code", "| Severity", "| Schwere",
]

# Mindestlänge damit nicht jede kurze Antwort als Report gespeichert wird
MIN_REPORT_LENGTH = 400


async def maybe_persist_report(response: str) -> str | None:
    """Erkennt ob die Agent-Antwort ein Report ist und speichert ihn in der DB.

    Gibt die Report-ID zurück wenn gespeichert, sonst None.
    """
    if len(response) < MIN_REPORT_LENGTH:
        return None

    # Erkennung: Titel-Marker ODER 3+ strukturelle Marker
    has_title = any(marker in response for marker in TITLE_MARKERS)
    structure_hits = sum(1 for m in STRUCTURE_MARKERS if m in response)
    is_report = has_title or structure_hits >= 3

    if not is_report:
        return None

    title = _extract_title(response)
    target = _extract_target(title, response)
    report_type = _detect_report_type(response)

    report_id = str(uuid4())

    try:
        from src.api.server import get_db
        db = await get_db()
        conn = await db.get_connection()
        await conn.execute(
            "INSERT INTO agent_reports (id, title, report_type, content, target, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (report_id, title, report_type, response, target, datetime.now(UTC).isoformat()),
        )
        await conn.commit()
        logger.info("Agent-Report gespeichert", id=report_id, title=title, type=report_type)
        return report_id
    except Exception as error:
        logger.warning("Agent-Report nicht gespeichert", error=str(error))
        return None


async def attach_report_notice(response: str) -> str:
    """Prüft ob die Antwort ein Report ist und hängt ggf. einen Hinweis an."""
    report_id = await maybe_persist_report(response)
    if report_id:
        response += (
            "\n\n---\n*Dieser Report wurde automatisch gespeichert "
            "und ist auf der Reports-Seite verfügbar.*"
        )
    return response


def _extract_title(response: str) -> str:
    """Extrahiert den Titel aus der ersten Markdown-Überschrift."""
    for line in response.split("\n"):
        if line.startswith("# "):
            return line.lstrip("# ").strip()
    return "Agent-Report"


def _extract_target(title: str, response: str) -> str:
    """Extrahiert das Scan-Target (Domain/IP) aus Titel oder Inhalt."""
    search_text = title + " " + response[:1000]

    # Muster: "Bericht: domain.de", "Scan — domain.de", "Ziel: domain.de"
    patterns = [
        r"(?:Bericht|Report|Scan|Ziel|Target).*?[:\s—–-]+\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:\s*\||\s*$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, search_text)
        if match:
            target = match.group(1)
            # Filter: keine generischen Domains
            if target not in ("github.com", "example.com", "test.de"):
                return target
    return ""


def _detect_report_type(response: str) -> str:
    """Erkennt den Report-Typ anhand von Schlüsselwörtern."""
    lower = response.lower()
    if "sicherheitstest" in lower or "auth-guard" in lower or "admin-routen" in lower:
        return "security_test"
    if "vulnerability" in lower or "schwachstelle" in lower or "cvss" in lower:
        return "vulnerability"
    if "compliance" in lower:
        return "compliance"
    if "executive" in lower:
        return "executive"
    if "pentest" in lower or "penetration" in lower:
        return "pentest"
    return "osint"
