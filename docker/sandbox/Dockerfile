# SentinelClaw Sandbox-Container
# Vollständige Pentest-Umgebung: Recon → Exploitation → Post-Exploitation
# Läuft als non-root User mit minimalen Rechten

FROM ubuntu:22.04

LABEL maintainer="sentinelclaw" \
      description="SentinelClaw Sandbox — Isolierte Pentest-Umgebung" \
      sentinelclaw="true" \
      sentinelclaw.role="sandbox"

# Architektur-Erkennung für Multi-Arch-Builds
ARG TARGETARCH

# ─── Stufe 0-1: Recon + Netzwerk-Tools ──────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    dnsutils \
    whois \
    curl \
    wget \
    netcat-openbsd \
    socat \
    ca-certificates \
    unzip \
    jq \
    git \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# ─── Stufe 2: Vulnerability Assessment ──────────────────────────────
# Nikto — Web-Server-Scanner
RUN apt-get update && apt-get install -y --no-install-recommends \
    nikto \
    sslscan \
    dirb \
    && rm -rf /var/lib/apt/lists/*

# ─── Stufe 3: Exploitation ──────────────────────────────────────────
# Hydra — Netzwerk-Login-Brute-Forcer
RUN apt-get update && apt-get install -y --no-install-recommends \
    hydra \
    && rm -rf /var/lib/apt/lists/*

# John the Ripper — Passwort-Cracker
RUN apt-get update && apt-get install -y --no-install-recommends \
    john \
    && rm -rf /var/lib/apt/lists/*

# Hashcat — GPU-basierter Hash-Cracker (CPU-Fallback in Container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    hashcat \
    && rm -rf /var/lib/apt/lists/*

# Metasploit Framework
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 \
    && curl -fsSL https://apt.metasploit.com/metasploit-framework.gpg.key \
       | gpg --dearmor -o /usr/share/keyrings/metasploit.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/metasploit.gpg] https://apt.metasploit.com/ lucid main" \
       > /etc/apt/sources.list.d/metasploit.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends metasploit-framework \
    && rm -rf /var/lib/apt/lists/*

# ─── Stufe 4: Post-Exploitation ─────────────────────────────────────
# Nuclei — Template-basierter Vulnerability-Scanner
ARG NUCLEI_VERSION=3.3.7
RUN ARCH=$(case ${TARGETARCH} in amd64) echo "linux_amd64";; arm64) echo "linux_arm64";; *) echo "linux_amd64";; esac) \
    && wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_${ARCH}.zip" \
        -O /tmp/nuclei.zip \
    && unzip /tmp/nuclei.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip

# LinPEAS + WinPEAS — Privilege Escalation Analyse
RUN mkdir -p /opt/tools/peas \
    && wget -q "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh" \
        -O /opt/tools/peas/linpeas.sh \
    && wget -q "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe" \
        -O /opt/tools/peas/winpeas.exe \
    && chmod +x /opt/tools/peas/linpeas.sh

# Chisel — TCP/UDP Tunnel über HTTP (Pivoting)
ARG CHISEL_VERSION=1.9.1
RUN ARCH=$(case ${TARGETARCH} in amd64) echo "linux_amd64";; arm64) echo "linux_arm64";; *) echo "linux_amd64";; esac) \
    && wget -q "https://github.com/jpillora/chisel/releases/download/v${CHISEL_VERSION}/chisel_${CHISEL_VERSION}_${ARCH}.gz" \
        -O /tmp/chisel.gz \
    && gunzip /tmp/chisel.gz \
    && mv /tmp/chisel /usr/local/bin/chisel \
    && chmod +x /usr/local/bin/chisel

# pwncat — Reverse-Shell-Handler + Post-Exploitation
RUN pip3 install --no-cache-dir pwncat-cs 2>/dev/null || true

# ─── Python Security-Libraries (für Agent-Scripting) ────────────────
RUN pip3 install --no-cache-dir \
    impacket \
    paramiko \
    pycryptodome \
    requests \
    beautifulsoup4 \
    lxml \
    dnspython \
    python-nmap \
    2>/dev/null || true

# ─── Wortlisten für Brute-Force ─────────────────────────────────────
RUN mkdir -p /opt/wordlists \
    && wget -q "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt" \
        -O /opt/wordlists/common-passwords-10k.txt \
    && wget -q "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt" \
        -O /opt/wordlists/web-common.txt \
    && wget -q "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/top-usernames-shortlist.txt" \
        -O /opt/wordlists/usernames-short.txt

# ─── Aufräumen + Scan-Verzeichnis ───────────────────────────────────
RUN mkdir -p /opt/scan-results && chmod 755 /opt/scan-results

# Non-root User (Sicherheit: kein Root in Produktion)
RUN groupadd -r scanner && useradd -r -g scanner -d /home/scanner -s /bin/bash scanner \
    && mkdir -p /home/scanner \
    && chown scanner:scanner /home/scanner /opt/scan-results /opt/tools /opt/wordlists

USER scanner
WORKDIR /home/scanner

# Healthcheck: Kerntools verfügbar
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD nmap --version > /dev/null 2>&1 && nuclei --version > /dev/null 2>&1

# Container bleibt am Leben für exec-Befehle
CMD ["sleep", "infinity"]
