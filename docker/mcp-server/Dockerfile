# SentinelClaw MCP-Server
# Python-basierter Tool-Server der Pentest-Tools über MCP exponiert

# === Stage 1: Dependencies installieren ===
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml ./
RUN pip install --no-cache-dir --target=/build/deps .

# === Stage 2: Runtime-Image ===
FROM python:3.12-slim AS runtime

LABEL maintainer="sentinelclaw" \
      description="SentinelClaw MCP-Server — Tool-Abstraktion für Agents" \
      sentinelclaw="true" \
      sentinelclaw.role="mcp-server"

# Non-root User erstellen
RUN groupadd -r sentinel && useradd -r -g sentinel -d /app sentinel

WORKDIR /app

# Dependencies aus Builder-Stage kopieren
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages/

# Application Code kopieren
COPY src/ ./src/

# Rechte setzen
RUN chown -R sentinel:sentinel /app

USER sentinel

# Health-Check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

EXPOSE 8080

ENTRYPOINT ["python", "-m", "src.mcp_server"]
