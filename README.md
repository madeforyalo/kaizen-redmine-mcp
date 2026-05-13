# Kaizen Redmine MCP Server

A compact [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes a curated set of Redmine tools to AI clients (Claude Desktop, Cowork). Built specifically for `https://proyectos.kaizen2b.net`, it avoids the payload bloat and schema inconsistencies of community servers by returning only the fields the LLM actually needs — full details only when explicitly requested.

## Tools

| Tool | Description |
|---|---|
| `get_current_user` | Return identity of the API key owner |
| `list_projects` | Paginated compact project listing |
| `find_project` | Substring search across all projects (name or identifier) |
| `get_project` | Full project detail including trackers, categories, modules |
| `list_issues` | Paginated issue listing with optional filters |
| `get_issue` | Full issue detail including journals, attachments, relations |
| `list_trackers` | All tracker types (Bug, Feature, Task…) |
| `list_issue_statuses` | All issue statuses with `is_closed` flag |
| `list_priorities` | All priority levels |
| `create_project` | Create a new project (or subproject) |
| `create_issue` | Create a new issue with optional fields |
| `update_issue` | Update fields and/or add a journal note to an issue |

## Quick Start (Docker)

```bash
git clone https://github.com/kaizen2b/kaizen-redmine-mcp.git
cd kaizen-redmine-mcp
cp .env.example .env
# Edit .env: set REDMINE_URL and REDMINE_API_KEY
docker build -t kaizen-redmine-mcp .
docker run --env-file .env -p 127.0.0.1:8000:8000 kaizen-redmine-mcp
```

Or with Compose:

```bash
docker compose up -d
```

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `REDMINE_URL` | yes | — | Base URL of the Redmine instance (no trailing slash) |
| `REDMINE_API_KEY` | yes | — | API key for the Redmine bot user |
| `SERVER_HOST` | no | `0.0.0.0` | Bind address inside the container |
| `SERVER_PORT` | no | `8000` | Port the server listens on |
| `REDMINE_SSL_VERIFY` | no | `true` | Set `false` for self-signed certificates |
| `HTTP_TIMEOUT` | no | `30` | HTTP request timeout in seconds |
| `REDMINE_MCP_READ_ONLY` | no | `false` | When `true`, write tools return an error without touching Redmine |
| `LOG_LEVEL` | no | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## Transport

The server uses **SSE transport** (Server-Sent Events), which is the protocol expected by Claude Desktop and Cowork. It exposes two endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `GET /sse` | GET | Event stream — clients subscribe here |
| `POST /messages/` | POST | JSON-RPC messages from client to server |

> **Why not Streamable HTTP?** The newer `streamable-http` transport only accepts POST requests and returns `406 Not Acceptable` when clients connect with `Accept: text/event-stream`. SSE transport handles both directions correctly and is what Claude Desktop / Cowork expect.

## Connecting to Claude Desktop / Cowork

Add the following to your `mcp_servers` configuration (Claude Desktop `claude_desktop_config.json` or Cowork settings):

```json
{
  "mcpServers": {
    "kaizen-redmine": {
      "command": "uvx",
      "args": ["--from", "fastmcp", "fastmcp", "run", "http://127.0.0.1:8000/sse"]
    }
  }
}
```

If `uvx` is not available, use:

```json
{
  "mcpServers": {
    "kaizen-redmine": {
      "command": "python",
      "args": ["-c", "import fastmcp; fastmcp.run_client('http://127.0.0.1:8000/sse')"]
    }
  }
}
```

## Deploy on Remote Server + SSH Tunnel

On your server:

```bash
docker compose up -d   # binds only to 127.0.0.1:8000
```

On your local machine:

```bash
ssh -N -L 8000:127.0.0.1:8000 user@your-server.example.com
```

The MCP client on your machine connects to `http://127.0.0.1:8000/sse` as if the server were local. The port is never exposed to the internet.

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Read-Only Mode

Set `REDMINE_MCP_READ_ONLY=true` to block all write operations without restarting or rebuilding the container. The write tools (`create_project`, `create_issue`, `update_issue`) will return `{"error": true, "message": "Server is in read-only mode."}` immediately.

## License

MIT — see [LICENSE](LICENSE).
