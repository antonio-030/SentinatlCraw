"""
Bewertungs-Funktionen für den Orchestrator.

Erstellt Executive Summary, Risk Assessment und Empfehlungen
basierend auf Recon-Ergebnissen.

Ausgelagert aus orchestrator/agent.py um die 300-Zeilen-Regel einzuhalten.
"""

from src.agents.recon.result_types import ReconResult


def create_executive_summary(recon: ReconResult) -> str:
    """Erstellt eine Management-Zusammenfassung."""
    if not recon.open_ports and not recon.vulnerabilities:
        return (
            f"Der Scan von {recon.target} hat keine offenen Ports "
            f"oder Schwachstellen ergeben."
        )

    sev = recon.severity_counts
    critical = sev.get("critical", 0)
    high = sev.get("high", 0)

    summary = (
        f"Scan von {recon.target}: "
        f"{recon.total_hosts} Host(s), "
        f"{recon.total_open_ports} offene Ports, "
        f"{recon.total_vulnerabilities} Findings. "
    )

    if critical > 0:
        summary += f"ACHTUNG: {critical} kritische Schwachstelle(n) gefunden! "
    if high > 0:
        summary += f"{high} Schwachstelle(n) mit hohem Risiko. "

    return summary


def create_risk_assessment(recon: ReconResult) -> str:
    """Erstellt eine Risikobewertung basierend auf den Findings."""
    if not recon.vulnerabilities and not recon.open_ports:
        return "Keine signifikanten Risiken identifiziert."

    risks = []
    for vuln in sorted(recon.vulnerabilities, key=lambda v: v.cvss_score, reverse=True)[:3]:
        risks.append(f"- {vuln.severity.upper()}: {vuln.title}")

    for port in recon.open_ports:
        if port.service in ("ssh", "mysql", "postgres", "ftp"):
            if "old" in port.version.lower() or any(
                v in port.version for v in ["5.", "6.", "7."]
            ):
                risks.append(f"- Veralteter Dienst: {port.service} {port.version} auf Port {port.port}")

    return "\n".join(risks) if risks else "Keine kritischen Risiken identifiziert."


def create_recommendations(recon: ReconResult) -> list[str]:
    """Erstellt Handlungsempfehlungen."""
    recs: list[str] = []

    if recon.has_critical:
        recs.append("SOFORT: Kritische Schwachstellen beheben (siehe Findings)")

    for port in recon.open_ports:
        if "OpenSSH" in port.version and any(
            v in port.version for v in ["5.", "6.", "7."]
        ):
            recs.append(f"SSH auf {port.host}:{port.port} aktualisieren ({port.version} → aktuell)")

        if "Apache" in port.version and "2.4.7" in port.version:
            recs.append(f"Apache auf {port.host}:{port.port} aktualisieren ({port.version})")

    if not recs:
        recs.append("Regelmäßige Scans durchführen um neue Schwachstellen zu erkennen")

    return recs
