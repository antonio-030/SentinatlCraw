"""
Kuratierte Registry aller Security-Tools für die OpenShell-Sandbox.

NUR diese Tools können über die Web-UI installiert werden.
Stufen: 0=Passiv, 1=Aktiv, 2=Vulnerability, 3=Exploitation
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentToolDefinition:
    """Definition eines installierbaren Security-Tools."""

    name: str
    display_name: str
    description: str
    category: str  # reconnaissance | vulnerability | analysis | exploitation | utility
    escalation_level: int  # 0-3, korreliert mit Scope-Validator
    install_command: str
    uninstall_command: str
    check_command: str
    install_timeout: int = 120


# ─── Stufe 0: Passive Reconnaissance (OSINT) ────────────────────────

_RECON_PASSIVE = [
    AgentToolDefinition(
        name="shodan",
        display_name="Shodan CLI",
        description="Suchmaschine für öffentlich erreichbare Geräte und Services",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install shodan",
        uninstall_command="pip3 uninstall -y shodan",
        check_command="python3 -c 'import shodan; print(shodan.__version__)'",
    ),
    AgentToolDefinition(
        name="censys",
        display_name="Censys",
        description="Internet-weite Scan-Datenbank — Zertifikate, Hosts, Services",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install censys",
        uninstall_command="pip3 uninstall -y censys",
        check_command="python3 -c 'import censys; print(censys.__version__)'",
    ),
    AgentToolDefinition(
        name="theharvester",
        display_name="theHarvester",
        description="E-Mail, Subdomain und Host-Enumeration aus öffentlichen Quellen",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install theHarvester",
        uninstall_command="pip3 uninstall -y theHarvester",
        check_command="theHarvester --help 2>&1 | head -1",
        install_timeout=180,
    ),
    AgentToolDefinition(
        name="sublist3r",
        display_name="Sublist3r",
        description="Subdomain-Enumeration über Suchmaschinen und DNS-Dienste",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install sublist3r",
        uninstall_command="pip3 uninstall -y sublist3r",
        check_command="python3 -c 'import sublist3r; print(\"ok\")'",
    ),
    AgentToolDefinition(
        name="dnspython",
        display_name="dnspython",
        description="Erweiterte DNS-Abfragen — Zone-Transfers, DNSSEC, alle Record-Typen",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install dnspython",
        uninstall_command="pip3 uninstall -y dnspython",
        check_command="python3 -c 'import dns; print(dns.version.version)'",
    ),
    AgentToolDefinition(
        name="python-whois",
        display_name="python-whois",
        description="Erweiterte WHOIS-Abfragen mit strukturiertem Parsing",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install python-whois",
        uninstall_command="pip3 uninstall -y python-whois",
        check_command="python3 -c 'import whois; print(\"ok\")'",
    ),
    AgentToolDefinition(
        name="holehe",
        display_name="Holehe",
        description="E-Mail-OSINT — prüft ob eine Adresse bei Diensten registriert ist",
        category="reconnaissance", escalation_level=0,
        install_command="pip3 install holehe",
        uninstall_command="pip3 uninstall -y holehe",
        check_command="holehe --help 2>&1 | head -1",
    ),
]

# ─── Stufe 1: Aktive Reconnaissance ─────────────────────────────────

_RECON_ACTIVE = [
    AgentToolDefinition(
        name="wafw00f",
        display_name="wafw00f",
        description="Web Application Firewall Erkennung und Fingerprinting",
        category="reconnaissance", escalation_level=1,
        install_command="pip3 install wafw00f",
        uninstall_command="pip3 uninstall -y wafw00f",
        check_command="wafw00f --version 2>&1 | head -1",
    ),
    AgentToolDefinition(
        name="sslyze",
        display_name="SSLyze",
        description="TLS/SSL-Konfigurationsanalyse — Cipher-Suites, Zertifikate, Schwächen",
        category="reconnaissance", escalation_level=1,
        install_command="pip3 install sslyze",
        uninstall_command="pip3 uninstall -y sslyze",
        check_command="python3 -c 'import sslyze; print(sslyze.__version__)'",
        install_timeout=180,
    ),
    AgentToolDefinition(
        name="arjun",
        display_name="Arjun",
        description="HTTP-Parameter-Discovery — findet versteckte GET/POST-Parameter",
        category="reconnaissance", escalation_level=1,
        install_command="pip3 install arjun",
        uninstall_command="pip3 uninstall -y arjun",
        check_command="arjun --help 2>&1 | head -1",
    ),
    AgentToolDefinition(
        name="dirsearch",
        display_name="dirsearch",
        description="Verzeichnis- und Datei-Bruteforce auf Webservern",
        category="reconnaissance", escalation_level=1,
        install_command="pip3 install dirsearch",
        uninstall_command="pip3 uninstall -y dirsearch",
        check_command="dirsearch --version 2>&1 | head -1",
    ),
    AgentToolDefinition(
        name="httpie",
        display_name="HTTPie",
        description="HTTP-Client für API-Tests, Header-Analyse und Redirect-Verfolgung",
        category="utility", escalation_level=1,
        install_command="pip3 install httpie",
        uninstall_command="pip3 uninstall -y httpie",
        check_command="http --version",
    ),
    AgentToolDefinition(
        name="paramiko",
        display_name="Paramiko",
        description="SSH-Protokoll-Library — Verbindungstests, Cipher-Analyse, Banner-Grabbing",
        category="utility", escalation_level=1,
        install_command="pip3 install paramiko",
        uninstall_command="pip3 uninstall -y paramiko",
        check_command="python3 -c 'import paramiko; print(paramiko.__version__)'",
    ),
]

# ─── Stufe 2: Vulnerability Assessment ──────────────────────────────

_VULN_ASSESSMENT = [
    AgentToolDefinition(
        name="wapiti",
        display_name="Wapiti",
        description="Web-Vulnerability-Scanner — XSS, SQLi, SSRF, Command Injection",
        category="vulnerability", escalation_level=2,
        install_command="pip3 install wapiti3",
        uninstall_command="pip3 uninstall -y wapiti3",
        check_command="wapiti --version 2>&1 | head -1",
        install_timeout=180,
    ),
    AgentToolDefinition(
        name="python-nmap",
        display_name="python-nmap",
        description="Python-Wrapper für Nmap — Netzwerk-Scanning per Script",
        category="vulnerability", escalation_level=2,
        install_command="pip3 install python-nmap",
        uninstall_command="pip3 uninstall -y python-nmap",
        check_command="python3 -c 'import nmap; print(nmap.__version__)'",
    ),
    AgentToolDefinition(
        name="pyjwt",
        display_name="PyJWT",
        description="JWT-Token-Analyse — Dekodierung, Signatur-Prüfung, Schwachstellen-Check",
        category="vulnerability", escalation_level=2,
        install_command="pip3 install pyjwt[crypto]",
        uninstall_command="pip3 uninstall -y pyjwt",
        check_command="python3 -c 'import jwt; print(jwt.__version__)'",
    ),
    AgentToolDefinition(
        name="tlsx",
        display_name="tlsx (Python)",
        description="TLS-Grabber — extrahiert Zertifikatsketten, Cipher, JARM-Fingerprints",
        category="vulnerability", escalation_level=2,
        install_command="pip3 install tlsx",
        uninstall_command="pip3 uninstall -y tlsx",
        check_command="python3 -c 'import tlsx; print(\"ok\")'",
    ),
]

# ─── Stufe 3: Exploitation (erfordert Genehmigung) ──────────────────

_EXPLOITATION = [
    AgentToolDefinition(
        name="sqlmap",
        display_name="sqlmap",
        description="Automatisierte SQL-Injection-Erkennung und -Exploitation",
        category="exploitation", escalation_level=3,
        install_command="pip3 install sqlmap",
        uninstall_command="pip3 uninstall -y sqlmap",
        check_command="sqlmap --version",
    ),
    AgentToolDefinition(
        name="impacket",
        display_name="Impacket",
        description="Netzwerk-Protokoll-Toolkit — SMB, LDAP, Kerberos, NTLM-Angriffe",
        category="exploitation", escalation_level=3,
        install_command="pip3 install impacket",
        uninstall_command="pip3 uninstall -y impacket",
        check_command="python3 -c 'import impacket; print(impacket.version.VER_MINOR)'",
        install_timeout=180,
    ),
    AgentToolDefinition(
        name="crackmapexec",
        display_name="CrackMapExec",
        description="Post-Exploitation-Framework — SMB, WinRM, SSH, LDAP, MSSQL",
        category="exploitation", escalation_level=3,
        install_command="pip3 install crackmapexec",
        uninstall_command="pip3 uninstall -y crackmapexec",
        check_command="crackmapexec --version 2>&1 | head -1",
        install_timeout=240,
    ),
]

# ─── Analyse-Utilities ──────────────────────────────────────────────

_ANALYSIS = [
    AgentToolDefinition(
        name="requests",
        display_name="Requests",
        description="HTTP-Library für Web-Scraping, API-Tests und Redirect-Analyse",
        category="utility", escalation_level=0,
        install_command="pip3 install requests",
        uninstall_command="pip3 uninstall -y requests",
        check_command="python3 -c 'import requests; print(requests.__version__)'",
    ),
    AgentToolDefinition(
        name="beautifulsoup4",
        display_name="BeautifulSoup",
        description="HTML/XML-Parser für Web-Content-Analyse und Informationsextraktion",
        category="analysis", escalation_level=0,
        install_command="pip3 install beautifulsoup4 lxml",
        uninstall_command="pip3 uninstall -y beautifulsoup4 lxml",
        check_command="python3 -c 'import bs4; print(bs4.__version__)'",
    ),
    AgentToolDefinition(
        name="pycryptodome",
        display_name="PyCryptodome",
        description="Kryptographie-Library — Hash-Analyse, Cipher-Tests, Key-Generierung",
        category="analysis", escalation_level=1,
        install_command="pip3 install pycryptodome",
        uninstall_command="pip3 uninstall -y pycryptodome",
        check_command="python3 -c 'import Crypto; print(Crypto.__version__)'",
    ),
    AgentToolDefinition(
        name="jq",
        display_name="jq (Python)",
        description="JSON-Prozessor für strukturierte API-Response-Analyse",
        category="utility", escalation_level=0,
        install_command="pip3 install jq",
        uninstall_command="pip3 uninstall -y jq",
        check_command="python3 -c 'import jq; print(\"ok\")'",
    ),
]


# ─── Gesamtregistry ─────────────────────────────────────────────────

AGENT_TOOL_REGISTRY: dict[str, AgentToolDefinition] = {
    tool.name: tool
    for tool in (
        _RECON_PASSIVE + _RECON_ACTIVE + _VULN_ASSESSMENT + _EXPLOITATION + _ANALYSIS
    )
}

# Basis-Tools die im Sandbox-Container vorinstalliert sind
PREINSTALLED_TOOLS = frozenset({
    # Stufe 0: Passiv
    "curl", "dig", "whois", "jq", "wget",
    # Stufe 1: Aktive Scans
    "nmap", "dirb", "sslscan", "netcat", "socat",
    # Stufe 2: Vulnerability Assessment
    "nuclei", "nikto",
    # Stufe 3: Exploitation
    "hydra", "john", "hashcat", "msfconsole", "msfvenom",
    # Stufe 4: Post-Exploitation
    "linpeas", "chisel", "pwncat-cs",
    # Python + vorinstallierte Libraries
    "python3", "impacket", "paramiko",
})


def get_tool(name: str) -> AgentToolDefinition | None:
    """Gibt die Tool-Definition zurück oder None wenn unbekannt."""
    return AGENT_TOOL_REGISTRY.get(name)


def get_all_tool_names() -> frozenset[str]:
    """Alle bekannten Tool-Namen (Registry + vorinstalliert)."""
    return PREINSTALLED_TOOLS | frozenset(AGENT_TOOL_REGISTRY.keys())


def get_tools_by_escalation(max_level: int) -> list[AgentToolDefinition]:
    """Gibt alle Tools zurück die bis zur angegebenen Eskalationsstufe erlaubt sind."""
    return [t for t in AGENT_TOOL_REGISTRY.values() if t.escalation_level <= max_level]
