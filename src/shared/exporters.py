"""
Exportfunktionen fuer Scan-Findings aus der Datenbank.

Unterstuetzte Formate:
  - CSV:   Standard-CSV mit Kopfzeile
  - JSONL: Ein JSON-Objekt pro Zeile (fuer Streaming/Pipelines)
  - SARIF: Static Analysis Results Interchange Format v2.1.0
           (kompatibel mit GitHub Code Scanning und Azure DevOps)

Jede Exportfunktion laedt die Findings per FindingRepository
und gibt einen formatierten String zurueck.
"""

import csv
import io
import json
from uuid import UUID

from src.shared.database import DatabaseManager
from src.shared.repositories import FindingRepository
from src.shared.types.models import Finding

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

# SARIF-Schema-URL (offizielle OASIS-Spezifikation)
_SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/"
    "sarif-2.1/schema/sarif-schema-2.1.0.json"
)

# CSV-Spaltennamen in fester Reihenfolge
_CSV_HEADERS: list[str] = [
    "Severity",
    "Title",
    "Host",
    "Port",
    "CVE",
    "CVSS",
    "Description",
]


async def _load_findings(db: DatabaseManager, scan_job_id: UUID) -> list[Finding]:
    """Laedt alle Findings eines Scans, sortiert nach CVSS absteigend."""
    repo = FindingRepository(db)
    return await repo.list_by_scan(scan_job_id)


def _severity_to_sarif_level(severity: str) -> str:
    """Mappt SentinelClaw-Severity auf SARIF-Level.

    Zuordnung gemaess SARIF-Spezifikation:
      critical / high -> error
      medium          -> warning
      low / info      -> note
    """
    mapping: dict[str, str] = {
        "critical": "error",
        "high": "error",
        "medium": "warning",
        "low": "note",
        "info": "note",
    }
    return mapping.get(severity.lower(), "note")


def _finding_to_csv_row(finding: Finding) -> list[str]:
    """Konvertiert ein Finding in eine CSV-Zeile (gleiche Reihenfolge wie _CSV_HEADERS)."""
    return [
        finding.severity.value,
        finding.title,
        finding.target_host,
        str(finding.target_port) if finding.target_port is not None else "",
        finding.cve_id or "",
        f"{finding.cvss_score:.1f}",
        finding.description,
    ]


def _finding_to_dict(finding: Finding) -> dict:
    """Konvertiert ein Finding in ein JSON-serialisierbares Dictionary."""
    return {
        "id": str(finding.id),
        "scan_job_id": str(finding.scan_job_id),
        "title": finding.title,
        "severity": finding.severity.value,
        "cvss_score": finding.cvss_score,
        "cve_id": finding.cve_id,
        "target_host": finding.target_host,
        "target_port": finding.target_port,
        "service": finding.service,
        "description": finding.description,
        "evidence": finding.evidence,
        "recommendation": finding.recommendation,
        "tool_name": finding.tool_name,
        "created_at": finding.created_at.isoformat(),
    }


def _finding_to_sarif_result(finding: Finding, rule_index: int) -> dict:
    """Erzeugt ein SARIF-Result-Objekt aus einem Finding.

    Jedes Finding wird als einzelnes Result abgebildet. Die Location
    nutzt das physicalLocation-Schema mit dem Host als URI.
    """
    port_suffix = f":{finding.target_port}" if finding.target_port else ""
    location_uri = f"{finding.target_host}{port_suffix}"

    result: dict = {
        "ruleId": finding.cve_id or f"SC-{str(finding.id)[:8]}",
        "ruleIndex": rule_index,
        "level": _severity_to_sarif_level(finding.severity.value),
        "message": {
            "text": finding.description or finding.title,
        },
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": location_uri,
                    },
                },
            },
        ],
    }

    # Optionale Felder anfuegen
    if finding.recommendation:
        result["fixes"] = [
            {
                "description": {
                    "text": finding.recommendation,
                },
            },
        ]

    return result


def _finding_to_sarif_rule(finding: Finding) -> dict:
    """Erzeugt eine SARIF-Rule-Descriptor fuer ein Finding.

    Rules werden im Tool-Objekt unter reportingDescriptor aufgelistet.
    """
    rule: dict = {
        "id": finding.cve_id or f"SC-{str(finding.id)[:8]}",
        "shortDescription": {
            "text": finding.title,
        },
        "defaultConfiguration": {
            "level": _severity_to_sarif_level(finding.severity.value),
        },
    }

    if finding.description:
        rule["fullDescription"] = {"text": finding.description}

    # CVSS als Property anfuegen
    rule["properties"] = {
        "severity": finding.severity.value,
        "cvss_score": finding.cvss_score,
    }

    return rule


# ---------------------------------------------------------------------------
# Oeffentliche Exportfunktionen
# ---------------------------------------------------------------------------


async def export_findings_csv(db: DatabaseManager, scan_job_id: UUID) -> str:
    """Exportiert Findings als CSV-String mit Kopfzeile.

    Spalten: Severity, Title, Host, Port, CVE, CVSS, Description
    Rueckgabe ist ein kompletter CSV-Text (UTF-8, CRLF-Zeilenenden
    gemaess RFC 4180).
    """
    findings = await _load_findings(db, scan_job_id)

    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(_CSV_HEADERS)

    for finding in findings:
        writer.writerow(_finding_to_csv_row(finding))

    return buffer.getvalue()


async def export_findings_jsonl(db: DatabaseManager, scan_job_id: UUID) -> str:
    """Exportiert Findings als JSON Lines (ein JSON-Objekt pro Zeile).

    JSONL eignet sich besonders fuer Streaming-Verarbeitung und
    grosse Datenmengen, da jede Zeile unabhaengig geparst werden kann.
    """
    findings = await _load_findings(db, scan_job_id)

    lines: list[str] = []
    for finding in findings:
        line = json.dumps(_finding_to_dict(finding), ensure_ascii=False)
        lines.append(line)

    return "\n".join(lines) + ("\n" if lines else "")


async def export_findings_sarif(db: DatabaseManager, scan_job_id: UUID) -> str:
    """Exportiert Findings im SARIF 2.1.0 Format.

    SARIF (Static Analysis Results Interchange Format) wird von
    GitHub Code Scanning, Azure DevOps und anderen CI/CD-Plattformen
    unterstuetzt.

    Struktur:
      {
        "$schema": "...",
        "version": "2.1.0",
        "runs": [{
          "tool": { "driver": { "name": ..., "rules": [...] } },
          "results": [...]
        }]
      }
    """
    findings = await _load_findings(db, scan_job_id)

    # Rules und Results parallel aufbauen
    rules: list[dict] = []
    results: list[dict] = []

    for index, finding in enumerate(findings):
        rules.append(_finding_to_sarif_rule(finding))
        results.append(_finding_to_sarif_result(finding, rule_index=index))

    sarif_document: dict = {
        "$schema": _SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "SentinelClaw",
                        "informationUri": "https://github.com/sentinelclaw/sentinelclaw",
                        "version": "0.1.0",
                        "rules": rules,
                    },
                },
                "results": results,
            },
        ],
    }

    return json.dumps(sarif_document, indent=2, ensure_ascii=False) + "\n"
