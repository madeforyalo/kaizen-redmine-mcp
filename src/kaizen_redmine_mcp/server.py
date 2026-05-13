from __future__ import annotations

import logging

from fastmcp import FastMCP

from .tools.enums import list_issue_statuses, list_priorities, list_trackers
from .tools.issues import create_issue, get_issue, list_issues, update_issue
from .tools.projects import (
    create_project,
    find_project,
    get_current_user,
    get_project,
    list_projects,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("Kaizen Redmine MCP")

# -- Read tools --
mcp.tool()(get_current_user)
mcp.tool()(list_projects)
mcp.tool()(find_project)
mcp.tool()(get_project)
mcp.tool()(list_issues)
mcp.tool()(get_issue)
mcp.tool()(list_trackers)
mcp.tool()(list_issue_statuses)
mcp.tool()(list_priorities)

# -- Write tools (honoured or blocked based on read-only flag inside each function) --
mcp.tool()(create_project)
mcp.tool()(create_issue)
mcp.tool()(update_issue)
