# Agents — Agent-Runtime und LLM-Anbindung

> Kapselt die NemoClaw/OpenShell-Runtime, LLM-Provider und Chat-Agent-Logik.

## Was macht dieses Modul?

Das Modul stellt die Verbindung zwischen SentinelClaw und der NemoClaw-Sandbox her.
Es verwaltet die SSH-Verbindung zur OpenShell-Sandbox, routet LLM-Anfragen an den
konfigurierten Provider (Claude, Azure OpenAI, Ollama) und verfolgt den Token-Verbrauch.

## Dateien

| Datei | Funktion |
|---|---|
| `nemoclaw_runtime.py` | SSH-Verbindung zur OpenShell-Sandbox, Agent-Ausführung |
| `chat_agent.py` | Chat-Agent für interaktive Web-UI-Kommunikation |
| `chat_system_prompt.py` | System-Prompt-Generierung für den Chat-Agent |
| `llm_provider.py` | Abstraktion über alle LLM-Provider |
| `claude_api_provider.py` | Claude-API-Anbindung (Standard) |
| `azure_provider.py` | Azure OpenAI-Anbindung (DSGVO-konform) |
| `ollama_provider.py` | Ollama Self-Hosted-Anbindung |
| `token_tracker.py` | Token-Budget-Tracking pro Scan (Warnung bei 80%, Stopp bei 100%) |
| `scan_executor.py` | Scan-Ausführung über die Runtime |
| `sandbox_policy.py` | Sandbox-Policy-Verwaltung |
| `sandbox_log_stream.py` | Echtzeit-Log-Streaming aus der Sandbox |
| `tool_bridge.py` | Tool-Aufrufe zwischen Agent und MCP-Server |

## Starten

Wird nicht eigenständig gestartet. Wird von `src.orchestrator` und `src.api` importiert.

## Umgebungsvariablen

| Variable | Beschreibung |
|---|---|
| `SENTINEL_LLM_PROVIDER` | LLM-Provider: `claude`, `azure`, `ollama` |
| `SENTINEL_CLAUDE_API_KEY` | API-Key für Claude |
| `SENTINEL_AZURE_ENDPOINT` | Azure OpenAI Endpoint-URL |
| `SENTINEL_AZURE_API_KEY` | Azure OpenAI API-Key |
| `SENTINEL_OLLAMA_URL` | Ollama-Server-URL |
| `SENTINEL_LLM_MAX_TOKENS_PER_SCAN` | Token-Budget pro Scan |
| `SENTINEL_OPENSHELL_GATEWAY_NAME` | Name des NemoClaw-Gateways |

## Dependencies

- `nemoclaw`, `openclaw` (Agent-Runtime)
- `anthropic` (Claude API)
- `openai` (Azure OpenAI)
- `httpx` (Ollama-Kommunikation)
