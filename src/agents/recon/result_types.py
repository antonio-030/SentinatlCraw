"""
Ergebnis-Typen für den Recon-Agent.

Strukturierte Datenmodelle für Scan-Ergebnisse die der
Recon-Agent zurückgibt.
"""

from dataclasses import dataclass, field


@dataclass
class DiscoveredHost:
    """Ein entdeckter Host im Netzwerk."""

    address: str
    hostname: str = ""
    state: str = "up"
    os_guess: str = ""


@dataclass
class OpenPort:
    """Ein offener Port mit Service-Informationen."""

    host: str
    port: int
    protocol: str = "tcp"
    state: str = "open"
    service: str = ""
    version: str = ""


@dataclass
class VulnerabilityFinding:
    """Ein Schwachstellen-Fund."""

    title: str
    severity: str  # critical, high, medium, low, info
    cvss_score: float = 0.0
    cve_id: str | None = None
    host: str = ""
    port: int | None = None
    description: str = ""
    recommendation: str = ""


@dataclass
class ReconResult:
    """Gesamtergebnis eines Recon-Scans."""

    target: str
    discovered_hosts: list[DiscoveredHost] = field(default_factory=list)
    open_ports: list[OpenPort] = field(default_factory=list)
    vulnerabilities: list[VulnerabilityFinding] = field(default_factory=list)
    risk_assessment: str = ""
    agent_summary: str = ""
    scan_duration_seconds: float = 0.0
    total_tokens_used: int = 0
    phases_completed: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def total_hosts(self) -> int:
        return len(self.discovered_hosts)

    @property
    def total_open_ports(self) -> int:
        return len([p for p in self.open_ports if p.state == "open"])

    @property
    def total_vulnerabilities(self) -> int:
        return len(self.vulnerabilities)

    @property
    def severity_counts(self) -> dict[str, int]:
        """Zählt Findings nach Schweregrad."""
        counts: dict[str, int] = {}
        for vuln in self.vulnerabilities:
            sev = vuln.severity.lower()
            counts[sev] = counts.get(sev, 0) + 1
        return counts

    @property
    def has_critical(self) -> bool:
        return any(v.severity.lower() == "critical" for v in self.vulnerabilities)
