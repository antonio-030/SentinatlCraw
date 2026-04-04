"""
Vordefinierte Scan-Profile für SentinelClaw.

Jedes Profil definiert Ports, Eskalationsstufe und Phasen-Konfiguration.
Kunden wählen ein Profil beim Scan-Start statt manuell Ports einzugeben.
In der UI werden Profile als Dropdown angezeigt.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScanProfile:
    """Ein vordefiniertes Scan-Profil."""

    name: str
    description: str
    ports: str
    max_escalation_level: int
    skip_host_discovery: bool = False
    skip_vuln_scan: bool = False
    nmap_extra_flags: list[str] | None = None
    estimated_duration_minutes: int = 5


# Alle verfügbaren Scan-Profile
PROFILES: dict[str, ScanProfile] = {
    "quick": ScanProfile(
        name="Quick Scan",
        description="Schneller Scan der Top-100 Ports. Für einen ersten Überblick.",
        ports="--top-ports 100",
        max_escalation_level=1,
        skip_vuln_scan=True,
        estimated_duration_minutes=2,
    ),
    "standard": ScanProfile(
        name="Standard Recon",
        description="Standard-Scan auf Ports 1-1000 mit Service-Erkennung und Vuln-Check.",
        ports="1-1000",
        max_escalation_level=2,
        estimated_duration_minutes=5,
    ),
    "full": ScanProfile(
        name="Full Scan",
        description="Vollständiger Scan aller 65535 Ports. Dauert deutlich länger.",
        ports="1-65535",
        max_escalation_level=2,
        nmap_extra_flags=["-T4"],
        estimated_duration_minutes=15,
    ),
    "web": ScanProfile(
        name="Web Application",
        description="Fokus auf Web-Ports (80, 443, 8080, 8443, 3000, 5000, 8000, 9000).",
        ports="80,443,8080,8443,3000,5000,8000,9000",
        max_escalation_level=2,
        estimated_duration_minutes=4,
    ),
    "database": ScanProfile(
        name="Datenbank",
        description="Fokus auf Datenbank-Ports (MySQL, PostgreSQL, MSSQL, MongoDB, Redis).",
        ports="3306,5432,1433,27017,6379,9200,5984,8529",
        max_escalation_level=2,
        estimated_duration_minutes=3,
    ),
    "infrastructure": ScanProfile(
        name="Infrastruktur",
        description="Netzwerk-Infrastruktur: SSH, DNS, SMTP, SNMP, RDP, VNC.",
        ports="22,23,25,53,110,143,161,389,445,636,993,995,3389,5900",
        max_escalation_level=2,
        estimated_duration_minutes=4,
    ),
    "stealth": ScanProfile(
        name="Stealth Scan",
        description="Langsamer, unauffälliger Scan mit Timing T1. Für IDS-Umgehung.",
        ports="1-1000",
        max_escalation_level=1,
        nmap_extra_flags=["-T1", "-Pn"],
        skip_vuln_scan=True,
        estimated_duration_minutes=20,
    ),
}


def get_profile(name: str) -> ScanProfile:
    """Gibt ein Scan-Profil anhand des Namens zurück."""
    profile = PROFILES.get(name.lower())
    if profile is None:
        available = ", ".join(PROFILES.keys())
        raise ValueError(
            f"Unbekanntes Profil '{name}'. Verfügbar: {available}"
        )
    return profile


def list_profiles() -> list[ScanProfile]:
    """Gibt alle verfügbaren Profile zurück."""
    return list(PROFILES.values())


def list_profile_names() -> list[str]:
    """Gibt die Namen aller Profile zurück."""
    return list(PROFILES.keys())
