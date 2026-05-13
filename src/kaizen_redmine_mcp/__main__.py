from __future__ import annotations

from .config import config
from .server import mcp

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=config.server_host,
        port=config.server_port,
        path="/mcp",
    )
