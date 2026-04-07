"""Extrahiert Findings aus Agent-Antworten im Chat.

Parst den Markdown-Text des Agents nach strukturierten
Schwachstellen-Beschreibungen und erstellt Finding-Einträge
in der Datenbank. So landen auch im Chat gefundene
Schwachstellen auf der Findings-Seite.
"""

import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.shared.database import DatabaseManager
from src.shared.logging_setup import get_logger
from src.shared.types.models import Finding

logger = get_logger(__name__)

# Severity-Mapping für verschiedene Schreibweisen
_SEVERITY_MAP: dict[str, str] = {
    "critical": "critical", "kritisch": "critical", "crit": "critical",
    "high": "high", "hoch": "high",
    "medium": "medium", "mittel": "medium", "moderate": "medium",
    "low": "low", "niedrig": "low", "gering": "low",
    "info": "info", "informational": "info", "hinweis": "info",
}

# Pattern für typische Agent-Finding-Blöcke
_FINDING_PATTERNS = [
    # "**Severity: High** — Title" oder "Severity: Critical"
    re.compile(
        r"\*{0,2}Severity[:\s]*(\w+)\*{0,2}[\s—\-:]+(.+?)(?:\n|$)",
        re.IGNORECASE,
    ),
    # "| Critical | Open Port 22 | SSH ..." (Tabellen)
    re.compile(
        r"\|\s*(critical|high|medium|low|info)\s*\|\s*(.+?)\s*\|",
        re.IGNORECASE,
    ),
    # "- **[HIGH]** Title" oder "- [Critical] Title"
    re.compile(
        r"[-*]\s*\*{0,2}\[?(critical|high|medium|low|info)\]?\*{0,2}\s*[:\-—]\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    ),
    # "### CVE-2024-XXXX: Title (High)"
    re.compile(
        r"#{1,4}\s*(CVE-\d{4}-\d+)[:\s]+(.+?)\s*\((\w+)\)",
        re.IGNORECASE,
    ),
]

# CVE-Pattern
_CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}", re.IGNORECASE)

# Host/Port-Pattern
_HOST_PORT_PATTERN = re.compile(
    r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w.-]+\.\w{2,})"
    r"(?::(\d{1,5}))?",
)


def _normalize_severity(raw: str) -> str:
    """Normalisiert einen Severity-String auf standard-Werte."""
    return _SEVERITY_MAP.get(raw.strip().lower(), "info")


def _extract_cvss(text: str) -> float:
    """Versucht einen CVSS-Score aus dem Text zu extrahieren."""
    match = re.search(r"CVSS[:\s]*(\d+\.?\d*)", text, re.IGNORECASE)
    if match:
        score = float(match.group(1))
        return min(10.0, max(0.0, score))
    # Fallback basierend auf Severity
    return 0.0


def extract_findings_from_text(
    text: str,
    scan_job_id: str | None = None,
) -> list[Finding]:
    """Extrahiert Findings aus Agent-Antwort-Text.

    Args:
        text: Markdown-Text der Agent-Antwort
        scan_job_id: Optionale Scan-Job-ID für die Zuordnung

    Returns:
        Liste von Finding-Objekten (kann leer sein).
    """
    findings: list[Finding] = []
    seen_titles: set[str] = set()

    # Host/Port aus dem Gesamttext extrahieren (erstes Vorkommen)
    host_match = _HOST_PORT_PATTERN.search(text)
    default_host = host_match.group(1) if host_match else ""
    default_port = int(host_match.group(2)) if host_match and host_match.group(2) else None

    for pattern in _FINDING_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()

            if len(groups) == 3:
                # CVE-Pattern: (cve, title, severity)
                cve_id = groups[0].upper()
                title = groups[1].strip()
                severity = _normalize_severity(groups[2])
            elif len(groups) == 2:
                severity = _normalize_severity(groups[0])
                title = groups[1].strip()
                cve_id = ""
            else:
                continue

            # Duplikate vermeiden
            title_key = title.lower()[:60]
            if title_key in seen_titles or len(title) < 5:
                continue
            seen_titles.add(title_key)

            # CVE aus Titel extrahieren falls nicht schon vorhanden
            if not cve_id:
                cve_match = _CVE_PATTERN.search(title)
                if cve_match:
                    cve_id = cve_match.group(0).upper()

            finding = Finding(
                id=uuid4(),
                scan_job_id=UUID(scan_job_id) if scan_job_id else uuid4(),
                tool_name="agent-chat",
                title=title[:200],
                severity=severity,
                cvss_score=_extract_cvss(title + " " + text[max(0, match.start() - 100):match.end() + 200]),
                cve_id=cve_id or None,
                target_host=default_host,
                target_port=default_port,
                service="",
                description=title,
                evidence="Vom Agent im Chat identifiziert",
                recommendation="",
                raw_output="",
                created_at=datetime.now(UTC),
            )
            findings.append(finding)

    return findings


async def persist_chat_findings(
    text: str,
    scan_job_id: str | None,
    db: DatabaseManager,
) -> int:
    """Extrahiert und speichert Findings aus einer Agent-Antwort.

    Returns:
        Anzahl der gespeicherten Findings.
    """
    findings = extract_findings_from_text(text, scan_job_id)

    if not findings:
        return 0

    from src.shared.finding_repository import FindingRepository
    repo = FindingRepository(db)

    saved = 0
    for finding in findings:
        try:
            await repo.create(finding)
            saved += 1
        except Exception as error:
            logger.debug("Finding-Duplikat oder Fehler", title=finding.title, error=str(error))

    if saved:
        logger.info(
            "Chat-Findings gespeichert",
            count=saved,
            scan_job_id=scan_job_id,
        )

    return saved
