"""
Einstiegspunkt für den MCP-Server.

Starten mit: python -m src.mcp_server
"""

from src.mcp_server.server import create_mcp_server
from src.shared.config import get_settings
from src.shared.logging_setup import setup_logging


def main() -> None:
    """Startet den MCP-Server als HTTP-Service (SSE-Transport).

    Im Docker-Container muss der Server als Daemon laufen,
    nicht auf stdio warten. SSE-Transport bindet auf Port 8080.
    """
    settings = get_settings()
    setup_logging(settings.log_level)

    mcp = create_mcp_server()
    mcp.run(
        transport="sse",
        host=settings.mcp_host,
        port=settings.mcp_port,
    )


if __name__ == "__main__":
    main()
