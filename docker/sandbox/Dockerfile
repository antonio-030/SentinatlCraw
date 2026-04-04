# SentinelClaw Sandbox-Container
# Enthält nmap und nuclei für Security-Scans
# Läuft als non-root User mit minimalen Rechten

FROM ubuntu:22.04

LABEL maintainer="sentinelclaw" \
      description="SentinelClaw Sandbox — Isolierte Scan-Umgebung" \
      sentinelclaw="true" \
      sentinelclaw.role="sandbox"

# System-Dependencies installieren (selten geändert → oben für Cache)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap=7.91+dfsg1+really7.80+dfsg1-2ubuntu0.1 \
    wget \
    ca-certificates \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Nuclei installieren (aktuelle Version von GitHub)
ARG NUCLEI_VERSION=3.3.7
RUN wget -q "https://github.com/projectdiscovery/nuclei/releases/download/v${NUCLEI_VERSION}/nuclei_${NUCLEI_VERSION}_linux_arm64.zip" \
        -O /tmp/nuclei.zip \
    && unzip /tmp/nuclei.zip -d /usr/local/bin/ \
    && chmod +x /usr/local/bin/nuclei \
    && rm /tmp/nuclei.zip

# Arbeitsverzeichnis für Scan-Ergebnisse
RUN mkdir -p /opt/scan-results && chmod 755 /opt/scan-results

# Non-root User erstellen (Sicherheit: kein Root auf dem Host)
RUN groupadd -r scanner && useradd -r -g scanner -d /home/scanner -s /bin/bash scanner \
    && mkdir -p /home/scanner && chown scanner:scanner /home/scanner /opt/scan-results

USER scanner
WORKDIR /home/scanner

# Healthcheck: Prüft ob nmap und nuclei verfügbar sind
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD nmap --version > /dev/null 2>&1 && nuclei --version > /dev/null 2>&1

# Container bleibt am Leben für exec-Befehle (kein fester Entrypoint)
CMD ["sleep", "infinity"]
