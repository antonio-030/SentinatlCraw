# ADR-001: NemoClaw als Agent-Runtime

> Status: Akzeptiert
> Datum: 2026-04-04 (aktualisiert nach Recherche)
> Autor: Jaciel Antonio Acea Ruiz

## Kontext

SentinelClaw braucht eine Runtime-Umgebung die KI-Agenten sicher ausführt. Der Agent muss Pentest-Tools steuern können, dabei aber streng isoliert sein. Es darf kein unkontrollierter Zugriff auf das Host-System oder das Internet möglich sein.

### Anforderungen an die Runtime
- Sandbox-Isolation für Tool-Ausführung (nmap, nuclei, metasploit, etc.)
- Policy-basierte Netzwerkkontrolle (nur autorisierte Ziele erreichbar)
- Multi-Agent-Orchestrierung (Orchestrator → Sub-Agenten)
- MCP-Kompatibilität (Tools als MCP-Server)
- LLM-Provider-Routing (Claude, Azure OpenAI, Ollama)
- Self-hosted, keine Cloud-Abhängigkeit

## Entscheidung

**NemoClaw** (NVIDIA, Open Source, angekündigt GTC 2026) als Agent-Runtime.

### Was NemoClaw ist

NemoClaw ist NVIDIAs Enterprise-Distribution von OpenClaw — vergleichbar mit dem Verhältnis Red Hat Enterprise Linux zu Fedora. Es bündelt drei Kernkomponenten:

```
┌─────────────────────────────────────────────────────────────┐
│  NemoClaw                                                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OpenClaw                                           │   │
│  │  Agent-Runtime + Multi-Agent-Orchestrierung         │   │
│  │  MCP-Integration + Tool-Abstraktion                 │   │
│  │  GitHub: NVIDIA/OpenClaw (vormals: Community-Projekt)│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  OpenShell                                          │   │
│  │  Kernel-Level Sandbox-Isolation                     │   │
│  │  • Landlock LSM (Dateisystem-Policies)              │   │
│  │  • Seccomp BPF (Syscall-Filter)                     │   │
│  │  • Deklarative YAML-Policies                        │   │
│  │  • Privacy-Router (Inference-Routing)               │   │
│  │  GitHub: NVIDIA/OpenShell                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Nemotron (optional)                                │   │
│  │  NVIDIA's eigene LLM-Modelle                        │   │
│  │  → Wir nutzen stattdessen: Claude / Azure / Ollama  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Quellen:                                                   │
│  GitHub: github.com/NVIDIA/NemoClaw                         │
│  Docs:   docs.nvidia.com/nemoclaw/latest/                   │
│  Blog:   developer.nvidia.com/blog/openshell                │
└─────────────────────────────────────────────────────────────┘
```

### Wie SentinelClaw auf NemoClaw mappt

| SentinelClaw-Komponente | NemoClaw-Komponente | Funktion |
|---|---|---|
| Orchestrator-Agent | OpenClaw Agent Runtime | Multi-Agent-Koordination |
| Recon-Agent, Exploit-Agent | OpenClaw Sub-Agents | Spezialisierte Task-Ausführung |
| MCP-Server (Tool-Abstraktion) | OpenClaw MCP-Integration | Tools als MCP-Server exponieren |
| Sandbox-Container | **OpenShell** | Kernel-Level-Isolation (besser als nur Docker) |
| Netzwerk-Policies | OpenShell YAML-Policies | Deklarative Netzwerk-Regeln |
| LLM-Provider-Routing | OpenShell Privacy-Router | Inference an Claude/Azure/Ollama routen |
| Kill Switch | OpenShell + SentinelClaw-Erweiterung | Wir erweitern OpenShell um unseren 4-Pfad-Kill |

### OpenShell-Isolation: Besser als reines Docker

```
Reine Docker-Isolation:
  Container → Namespace-Isolation → Host-Kernel
  Problem: Container-Ausbrüche sind möglich

OpenShell-Isolation (was wir nutzen):
  Agent → OpenShell Sandbox → Landlock + Seccomp → Host-Kernel
  Vorteil: Selbst bei Container-Ausbruch greifen Kernel-Policies
  
  Deklarative Policy (YAML):
    filesystem:
      allow_read:  ["/opt/tools/nmap", "/opt/tools/nuclei"]
      allow_write: ["/tmp/scan-results"]
      deny_all:    true   # Alles andere verboten
    
    network:
      allow_outbound:
        - "10.10.10.0/24:*"    # Nur Scan-Ziele
        - "localhost:8080"      # MCP-Server
      deny_all: true            # Kein Internet, kein Host
    
    process:
      allowed_binaries: ["nmap", "nuclei", "sqlmap"]
      max_pids: 100
      max_memory: "2G"
```

### Risikoeinschätzung: NemoClaw Pre-1.0

| Risiko | Schwere | Mitigation |
|---|---|---|
| API-Brüche zwischen Releases | HOCH | Abstraktions-Layer zwischen SentinelClaw und NemoClaw |
| Fehlende Features im Early Preview | MITTEL | Eigene Implementierung als Fallback (Docker + iptables) |
| Projekt wird eingestellt | NIEDRIG | OpenClaw ist Community-getrieben, NemoClaw hat NVIDIA-Backing |
| Bugs in OpenShell-Isolation | MITTEL | Zusätzlich Docker-Isolation als zweite Schicht beibehalten |
| Dokumentation unvollständig | HOCH | Quellcode lesen, Issues auf GitHub verfolgen |

### Unsere Fallback-Strategie

```
Wenn NemoClaw funktioniert (Normalfall):
  Agent → OpenClaw → OpenShell → Kernel-Isolation
  
Wenn NemoClaw Probleme macht (Fallback):
  Agent → Eigene Orchestrierung → Docker + iptables → Container-Isolation
  
Durch den Abstraktions-Layer können wir jederzeit wechseln
ohne den Rest des Codes zu ändern.
```

## Alternativen

### Alternative A: LangChain / LangGraph
- Vorteile: Größtes Ökosystem, produktionsreif, exzellente Dokumentation
- Nachteile: Keine eingebaute Sandbox, keine Netzwerk-Policies, Security komplett Eigenentwicklung
- Warum verworfen: Zu viel Security-Eigenentwicklung für ein Pentest-Tool

### Alternative B: PentAGI (direkter Konkurrent)
- Vorteile: Bereits funktionierendes KI-Pentest-Tool, MIT-Lizenz, Docker-Isolation, Ollama-Support, spezialisierte Agenten
- Nachteile: Keine Kernel-Level-Isolation (nur Docker), kein RBAC, keine Enterprise-Features (DSGVO, BSI)
- Warum nicht gewählt: Gutes Referenzprojekt, aber fehlt Enterprise-Hardening das wir brauchen
- **Beobachten als Inspiration und Benchmark**

### Alternative C: PentestAgent (GH05TCREW)
- Vorteile: Docker-isolierte Tools, MCP-Unterstützung, Multi-Agent
- Nachteile: Community-Projekt, weniger aktiv, keine Enterprise-Features
- Warum nicht gewählt: Ähnliche Gründe wie PentAGI

### Alternative D: E2B (Sandbox-only)
- Vorteile: Firecracker-MicroVMs, Start unter 200ms, Open Source
- Nachteile: Nur Sandbox — keine Agent-Runtime, kein MCP, kein Orchestrator
- Warum nicht gewählt: Könnte als Alternative zu OpenShell dienen wenn nötig
- **Merken als Fallback für Sandbox-Schicht**

### Alternative E: Eigene Runtime
- Vorteile: Volle Kontrolle
- Nachteile: Enormer Aufwand, Security-Risiken bei Eigenentwicklung
- Warum verworfen: NemoClaw löst genau das was wir selbst bauen müssten

## Konsequenzen

### Positiv
- Kernel-Level-Isolation über OpenShell (stärker als Docker allein)
- Deklarative Policies in YAML (lesbar, auditierbar, versionierbar)
- Privacy-Router für LLM-Provider-Wahl
- MCP-Kompatibilität out-of-the-box
- NVIDIA-Backing gibt Enterprise-Kunden Vertrauen
- OpenClaw-Community wächst schnell

### Negativ
- NemoClaw ist pre-1.0 (Early Preview seit 16.03.2026) — API-Brüche erwartbar
- Dokumentation noch lückenhaft
- Weniger Community-Support als LangChain
- Abhängigkeit von NVIDIA-Projekt

### Mitigation
- **Abstraktions-Layer**: `AgentRuntime`-Interface das OpenClaw wrapped — bei Brüchen nur eine Stelle ändern
- **Dual-Isolation**: OpenShell + Docker als doppelte Sicherheitsschicht
- **Fallback-Plan**: Eigene Docker+iptables-Isolation als Backup wenn OpenShell Probleme macht
- **Regelmäßige Updates**: NemoClaw-Releases verfolgen, Breaking Changes sofort einarbeiten
- **PentAGI als Benchmark**: Architektur-Entscheidungen gegen PentAGI validieren
