# SentinelClaw — Docker-Regeln

> Version: 0.1 | Autor: Jaciel Antonio Acea Ruiz | Datum: April 2026

---

## 1. Image-Regeln

### 1.1 Basis-Images

| Service | Basis-Image | Begründung |
|---|---|---|
| MCP-Server | `python:3.12-slim` | Minimal, offiziell, regelmäßig gepatcht |
| Sandbox | `ubuntu:22.04` | nmap/nuclei brauchen bestimmte System-Libs |
| Frontend (später) | `node:20-alpine` | Klein, schnell, reicht für Vite Build |

### 1.2 Regeln
- **Immer versioniert pinnen**: `python:3.12.4-slim`, NICHT `python:latest`
- **Offizielle Images** von Docker Hub — keine Community-Images ohne Review
- **Multi-Stage Builds** für jedes Production-Image
- **Minimale Größe**: Nur installieren was gebraucht wird

### 1.3 Multi-Stage Build Beispiel

```dockerfile
# ============================================================
# Stage 1: Build-Umgebung
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev --no-root

COPY src/ ./src/

# ============================================================
# Stage 2: Runtime-Image (schlank)
# ============================================================
FROM python:3.12-slim AS runtime

# Sicherheit: Kein Root
RUN groupadd -r sentinel && useradd -r -g sentinel sentinel

WORKDIR /app
COPY --from=builder /build ./

USER sentinel
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "print('ok')"

ENTRYPOINT ["python", "-m", "mcp_server"]
```

---

## 2. Dockerfile-Standards

### 2.1 Pflicht-Elemente
Jedes Dockerfile MUSS enthalten:
- `LABEL` mit Maintainer und Beschreibung
- `USER` Directive (non-root)
- `HEALTHCHECK`
- `.dockerignore` im selben Verzeichnis

### 2.2 Struktur

```dockerfile
# Beschreibung des Images
# Autor: SentinelClaw Team

FROM image:version AS stage-name

LABEL maintainer="sentinelclaw" \
      description="Beschreibung des Services"

# 1. System-Dependencies (selten geändert → oben für Cache)
RUN apt-get update && apt-get install -y --no-install-recommends \
    package1 \
    package2 \
    && rm -rf /var/lib/apt/lists/*

# 2. App-Dependencies (mitteloft geändert)
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3. Application Code (oft geändert → unten)
COPY src/ ./src/

# 4. Sicherheit
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# 5. Health & Startup
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080
ENTRYPOINT ["python", "-m", "app"]
```

### 2.3 Verboten in Dockerfiles
- `COPY . .` ohne `.dockerignore` — kopiert alles inkl. `.git`, `node_modules`
- `RUN chmod 777` — zu viele Rechte
- `ENV` mit Secrets — werden in Image-Layer gespeichert
- `--privileged` in RUN-Befehlen
- `apt-get upgrade` — unkontrollierte Paket-Updates

---

## 3. Docker Compose

### 3.1 Dateistruktur

```
docker/
├── sandbox/
│   ├── Dockerfile
│   └── .dockerignore
├── mcp-server/
│   ├── Dockerfile
│   └── .dockerignore
docker-compose.yml              # Im Projektroot
docker-compose.dev.yml          # Dev-Overrides
.env.example                    # Platzhalter für Secrets
```

### 3.2 Compose-Regeln

```yaml
# docker-compose.yml
services:
  mcp-server:
    build:
      context: .
      dockerfile: docker/mcp-server/Dockerfile
    restart: unless-stopped
    # Ressource-Limits sind Pflicht
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
    # Netzwerk-Isolation
    networks:
      - sentinel-internal
    # Health Check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  sandbox:
    build:
      context: .
      dockerfile: docker/sandbox/Dockerfile
    restart: unless-stopped
    # Sicherheits-Härtung
    cap_drop:
      - ALL
    cap_add:
      - NET_RAW        # Für nmap Raw Sockets
    read_only: true
    tmpfs:
      - /tmp:size=100M
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
          pids: 100       # Begrenzt Prozessanzahl
    networks:
      - sentinel-internal
      - sentinel-scanning  # Nur für Scan-Ziele

# Netzwerk-Definition
networks:
  sentinel-internal:
    driver: bridge
    internal: true          # Kein Internet-Zugang
  sentinel-scanning:
    driver: bridge
    # Scan-Netzwerk — Zugriff auf Ziele wird via Firewall-Rules kontrolliert
```

### 3.3 Environment Variables

```yaml
# Secrets NICHT direkt in docker-compose.yml
# Stattdessen:
services:
  mcp-server:
    env_file:
      - .env                # Wird nicht committed (in .gitignore)
    environment:
      - SENTINEL_LOG_LEVEL=INFO  # Nur nicht-sensible Werte hier
```

---

## 4. Sandbox-Container (Spezialregeln)

### 4.1 Sicherheits-Checkliste

- [ ] `cap_drop: ALL` gesetzt
- [ ] Nur `NET_RAW` Capability hinzugefügt (für nmap)
- [ ] `read_only: true` aktiviert
- [ ] `no-new-privileges: true` gesetzt
- [ ] Non-root User im Dockerfile
- [ ] Resource Limits (CPU, RAM, PIDs)
- [ ] Internes Netzwerk (kein direkter Internet-Zugang)
- [ ] Kein Host-Netzwerk-Modus
- [ ] Kein Volume-Mount auf Host-Root

### 4.2 Erlaubte Tools im Sandbox-Container

| Tool | Version | Zweck |
|---|---|---|
| nmap | 7.94+ | Port-Scanning & Service-Erkennung |
| nuclei | 3.x | Template-basierter Vulnerability-Scan |

Alle anderen Tools müssen explizit genehmigt und dokumentiert werden.

### 4.3 Netzwerk-Regeln für Sandbox

```
Erlaubt:
  Sandbox → MCP-Server (internes Netzwerk, Port 8080)
  Sandbox → Scan-Ziel (nur via sentinel-scanning Netzwerk)

Verboten:
  Sandbox → Internet (blockiert)
  Sandbox → Host-System (blockiert)
  Sandbox → Andere Container (blockiert, außer MCP-Server)
```

---

## 5. Development vs. Production

| Aspekt | Development | Production |
|---|---|---|
| Volumes | Source-Code gemounted für Hot-Reload | Kein Mount, Code im Image |
| Ports | Alle Ports exposed für Debugging | Nur nötige Ports |
| Logs | DEBUG Level, stdout | INFO Level, strukturiert |
| Rebuild | `docker-compose.dev.yml` Override | Multi-Stage Production Build |
| Secrets | `.env` Datei lokal | Docker Secrets oder Vault |

---

## 6. Image-Wartung

- Images regelmäßig rebuilden (min. monatlich) für Sicherheits-Patches
- `docker scan` oder Trivy für Vulnerability-Scanning
- Veraltete Images und Container aufräumen (`docker system prune`)
- Basis-Image-Versionen im CHANGELOG dokumentieren bei Updates
