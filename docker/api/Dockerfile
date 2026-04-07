# SentinelClaw API — FastAPI Backend mit OpenShell CLI
# Enthält openshell (pip), openssh-client für Sandbox-Zugriff

FROM python:3.12-slim

LABEL maintainer="sentinelclaw" \
      description="SentinelClaw API — FastAPI mit OpenShell-Integration" \
      sentinelclaw="true" \
      sentinelclaw.role="api"

WORKDIR /app

# System-Dependencies (curl=Healthcheck, ssh=Sandbox-Tunnel)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl openssh-client && rm -rf /var/lib/apt/lists/*

# OpenShell CLI installieren (stellt ssh-proxy, status, policy bereit)
RUN pip install --no-cache-dir openshell

# Python-Dependencies (Layer-Caching optimiert)
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# App-Code und Workspace kopieren
COPY src/ src/
COPY workspace/ workspace/

# Daten-Verzeichnis erstellen
RUN mkdir -p data

# Non-root User (docker-compose überschreibt mit root für Socket-Zugriff)
RUN useradd -m sentinelclaw && chown -R sentinelclaw:sentinelclaw /app

# Entrypoint passt OpenShell-Gateway-Endpoint für Docker an
COPY docker/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER sentinelclaw
EXPOSE 3001

HEALTHCHECK --interval=15s --timeout=5s --retries=3 --start-period=10s \
    CMD curl -sf http://localhost:3001/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "3001"]
