from __future__ import annotations

from typing import Any

from ..config import config
from ..redmine_client import client

_READ_ONLY_ERROR = {"error": True, "message": "Server is in read-only mode."}


def _compact_issue(i: dict[str, Any]) -> dict[str, Any]:
    def _ref(obj: Any) -> dict[str, Any] | None:
        return {"id": obj["id"], "name": obj["name"]} if obj else None

    return {
        "id": i["id"],
        "subject": i["subject"],
        "project": _ref(i.get("project")),
        "tracker": _ref(i.get("tracker")),
        "status": _ref(i.get("status")),
        "priority": _ref(i.get("priority")),
        "assigned_to": _ref(i.get("assigned_to")),
        "author": _ref(i.get("author")),
        "created_on": i.get("created_on"),
        "updated_on": i.get("updated_on"),
    }


def list_issues(
    project_id: str | int | None = None,
    status_id: str | int | None = None,
    assigned_to_id: int | None = None,
    tracker_id: int | None = None,
    priority_id: int | None = None,
    sort: str = "updated_on:desc",
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """List issues with optional filters (paginated, compact fields).

    Args:
        project_id: Filter by project (numeric ID or identifier). Omit for all projects.
        status_id: Filter by status ID, or use special values: 'open', 'closed', '*' (any).
        assigned_to_id: Filter by assignee user ID. Use 'me' for the current user.
        tracker_id: Filter by tracker ID.
        priority_id: Filter by priority ID.
        sort: Sort field and direction, e.g. 'updated_on:desc' or 'priority:asc'.
        limit: Max results per page (1–100).
        offset: Number of records to skip.

    Returns:
        {total_count, offset, limit, issues: [{id, subject, project, tracker, status,
         priority, assigned_to, author, created_on, updated_on}]}
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset, "sort": sort}
    if project_id is not None:
        params["project_id"] = project_id
    if status_id is not None:
        params["status_id"] = status_id
    if assigned_to_id is not None:
        params["assigned_to_id"] = assigned_to_id
    if tracker_id is not None:
        params["tracker_id"] = tracker_id
    if priority_id is not None:
        params["priority_id"] = priority_id

    data = client.get("/issues.json", params)
    if data.get("error"):
        return data
    return {
        "total_count": data.get("total_count", 0),
        "offset": data.get("offset", offset),
        "limit": data.get("limit", limit),
        "issues": [_compact_issue(i) for i in data.get("issues", [])],
    }


def get_issue(issue_id: int, include_journals: bool = True) -> dict[str, Any]:
    """Return full details for a single issue.

    Args:
        issue_id: Numeric ID of the issue.
        include_journals: When True, includes journals (comments/history), attachments,
            relations, children, and watchers.

    Returns:
        Full issue object from Redmine.
    """
    params: dict[str, Any] = {}
    if include_journals:
        params["include"] = "journals,attachments,relations,children,watchers"
    data = client.get(f"/issues/{issue_id}.json", params or None)
    if data.get("error"):
        return data
    return data.get("issue", data)


def create_issue(
    project_id: str | int,
    subject: str,
    description: str = "",
    tracker_id: int | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    assigned_to_id: int | None = None,
    parent_issue_id: int | None = None,
    due_date: str | None = None,
    start_date: str | None = None,
    estimated_hours: float | None = None,
    watcher_user_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Create a new issue in a Redmine project.

    Args:
        project_id: Target project (numeric ID or string identifier).
        subject: Issue title/subject.
        description: Detailed description (supports Textile/Markdown depending on Redmine config).
        tracker_id: Tracker ID (Bug, Feature, Task, etc.). Defaults to project default.
        status_id: Initial status ID. Defaults to project default.
        priority_id: Priority ID. Defaults to project default.
        assigned_to_id: User ID to assign the issue to.
        parent_issue_id: ID of parent issue (for subtasks).
        due_date: Due date in YYYY-MM-DD format.
        start_date: Start date in YYYY-MM-DD format.
        estimated_hours: Estimated effort in hours.
        watcher_user_ids: List of user IDs to add as watchers.

    Returns:
        Created issue object or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    issue: dict[str, Any] = {"project_id": project_id, "subject": subject}
    if description:
        issue["description"] = description
    for key, val in [
        ("tracker_id", tracker_id),
        ("status_id", status_id),
        ("priority_id", priority_id),
        ("assigned_to_id", assigned_to_id),
        ("parent_issue_id", parent_issue_id),
        ("due_date", due_date),
        ("start_date", start_date),
        ("estimated_hours", estimated_hours),
        ("watcher_user_ids", watcher_user_ids),
    ]:
        if val is not None:
            issue[key] = val

    data = client.post("/issues.json", {"issue": issue})
    if data.get("error"):
        return data
    return data.get("issue", data)


def update_issue(
    issue_id: int,
    subject: str | None = None,
    description: str | None = None,
    status_id: int | None = None,
    priority_id: int | None = None,
    assigned_to_id: int | None = None,
    tracker_id: int | None = None,
    done_ratio: int | None = None,
    due_date: str | None = None,
    notes: str | None = None,
    private_notes: bool = False,
) -> dict[str, Any]:
    """Update an existing issue. Only non-None fields are sent to Redmine.

    Use `notes` to add a comment to the issue journal.

    Args:
        issue_id: Numeric ID of the issue to update.
        subject: New subject/title.
        description: New description.
        status_id: New status ID.
        priority_id: New priority ID.
        assigned_to_id: New assignee user ID.
        tracker_id: New tracker ID.
        done_ratio: Completion percentage (0–100).
        due_date: New due date in YYYY-MM-DD format.
        notes: Comment to add to the issue journal.
        private_notes: When True, the note is private (visible only to project members).

    Returns:
        {ok: True} on success, or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    issue: dict[str, Any] = {}
    for key, val in [
        ("subject", subject),
        ("description", description),
        ("status_id", status_id),
        ("priority_id", priority_id),
        ("assigned_to_id", assigned_to_id),
        ("tracker_id", tracker_id),
        ("done_ratio", done_ratio),
        ("due_date", due_date),
        ("notes", notes),
    ]:
        if val is not None:
            issue[key] = val

    if notes is not None and private_notes:
        issue["private_notes"] = True

    if not issue:
        return {"error": True, "message": "No fields to update."}

    return client.put(f"/issues/{issue_id}.json", {"issue": issue})
