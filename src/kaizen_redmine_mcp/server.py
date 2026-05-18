from __future__ import annotations

import logging

from fastmcp import FastMCP

from .tools.enums import (
    list_custom_fields,
    list_issue_statuses,
    list_priorities,
    list_time_entry_activities,
    list_trackers,
    list_users,
    list_versions,
)
from .tools.time_entries import (
    delete_time_entry,
    get_time_entry,
    list_time_entries,
    log_time,
    update_time_entry,
)
from .tools.issues import create_issue, get_issue, list_issues, search_issues, update_issue
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
mcp.tool()(search_issues)
mcp.tool()(get_issue)
mcp.tool()(list_trackers)
mcp.tool()(list_issue_statuses)
mcp.tool()(list_priorities)
mcp.tool()(list_versions)
mcp.tool()(list_users)
mcp.tool()(list_time_entry_activities)
mcp.tool()(list_custom_fields)

# -- Write tools (honoured or blocked based on read-only flag inside each function) --
mcp.tool()(create_project)
mcp.tool()(create_issue)
mcp.tool()(update_issue)
mcp.tool()(log_time)
mcp.tool()(list_time_entries)
mcp.tool()(get_time_entry)
mcp.tool()(update_time_entry)
mcp.tool()(delete_time_entry)
