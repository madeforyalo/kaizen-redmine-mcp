from __future__ import annotations

from .config import config
from .server import mcp

if __name__ == "__main__":
    # SSE transport: exposes GET /sse (event stream) + POST /messages/
    # Use this instead of streamable-http for compatibility with Claude Desktop
    # and Cowork clients, which connect via SSE (Accept: text/event-stream).
    # Streamable-HTTP only accepts POST and returns 406 to SSE clients.
    mcp.run(
        transport="sse",
        host=config.server_host,
        port=config.server_port,
    )
