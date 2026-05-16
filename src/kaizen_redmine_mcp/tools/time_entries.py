from __future__ import annotations

from datetime import date
from typing import Any

from ..config import config
from ..redmine_client import client

_READ_ONLY_ERROR = {"error": True, "message": "Server is in read-only mode."}


def _compact_entry(e: dict[str, Any]) -> dict[str, Any]:
    def _ref(obj: Any) -> dict[str, Any] | None:
        return {"id": obj["id"], "name": obj["name"]} if obj else None

    return {
        "id": e["id"],
        "project": _ref(e.get("project")),
        "issue_id": e.get("issue", {}).get("id") if e.get("issue") else None,
        "user": _ref(e.get("user")),
        "activity": _ref(e.get("activity")),
        "hours": e.get("hours"),
        "comments": e.get("comments", ""),
        "spent_on": e.get("spent_on"),
        "created_on": e.get("created_on"),
    }


def log_time(
    issue_id: int,
    hours: float,
    activity_id: int,
    spent_on: str | None = None,
    comments: str = "",
) -> dict[str, Any]:
    """Log hours spent on an issue.

    Args:
        issue_id: ID of the issue to log time against.
        hours: Number of hours spent (decimals allowed, e.g. 1.5).
        activity_id: ID of the time entry activity (use list_time_entry_activities
            to get valid IDs — e.g. Development, Support, Meeting).
        spent_on: Date of work in YYYY-MM-DD format. Defaults to today.
        comments: Optional description of the work done.

    Returns:
        Created time entry object or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    entry: dict[str, Any] = {
        "issue_id": issue_id,
        "hours": hours,
        "activity_id": activity_id,
        "comments": comments,
        "spent_on": spent_on or date.today().isoformat(),
    }

    data = client.post("/time_entries.json", {"time_entry": entry})
    if data.get("error"):
        return data
    return _compact_entry(data.get("time_entry", data))


def list_time_entries(
    issue_id: int | None = None,
    project_id: str | int | None = None,
    user_id: int | None = None,
    spent_on: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> dict[str, Any]:
    """List time entries with optional filters (paginated).

    Args:
        issue_id: Filter by issue ID.
        project_id: Filter by project (numeric ID or identifier).
        user_id: Filter by user ID. Use 'me' for the current user.
        spent_on: Filter by exact date (YYYY-MM-DD).
        limit: Max results per page (1–100).
        offset: Number of records to skip.

    Returns:
        {total_count, offset, limit, time_entries: [{id, project, issue_id,
         user, activity, hours, comments, spent_on, created_on}]}
    """
    params: dict[str, Any] = {"limit": limit, "offset": offset}
    if issue_id is not None:
        params["issue_id"] = issue_id
    if project_id is not None:
        params["project_id"] = project_id
    if user_id is not None:
        params["user_id"] = user_id
    if spent_on is not None:
        params["spent_on"] = spent_on

    data = client.get("/time_entries.json", params)
    if data.get("error"):
        return data
    return {
        "total_count": data.get("total_count", 0),
        "offset": data.get("offset", offset),
        "limit": data.get("limit", limit),
        "time_entries": [_compact_entry(e) for e in data.get("time_entries", [])],
    }


def get_time_entry(time_entry_id: int) -> dict[str, Any]:
    """Return full details for a single time entry.

    Args:
        time_entry_id: Numeric ID of the time entry.

    Returns:
        Time entry object or error dict.
    """
    data = client.get(f"/time_entries/{time_entry_id}.json")
    if data.get("error"):
        return data
    return _compact_entry(data.get("time_entry", data))


def update_time_entry(
    time_entry_id: int,
    hours: float | None = None,
    activity_id: int | None = None,
    spent_on: str | None = None,
    comments: str | None = None,
) -> dict[str, Any]:
    """Update an existing time entry. Only non-None fields are sent to Redmine.

    Args:
        time_entry_id: Numeric ID of the time entry to update.
        hours: New number of hours.
        activity_id: New activity ID.
        spent_on: New date in YYYY-MM-DD format.
        comments: New comment text.

    Returns:
        {ok: True} on success, or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    entry: dict[str, Any] = {}
    for key, val in [
        ("hours", hours),
        ("activity_id", activity_id),
        ("spent_on", spent_on),
        ("comments", comments),
    ]:
        if val is not None:
            entry[key] = val

    if not entry:
        return {"error": True, "message": "No fields to update."}

    return client.put(f"/time_entries/{time_entry_id}.json", {"time_entry": entry})


def delete_time_entry(time_entry_id: int) -> dict[str, Any]:
    """Delete a time entry permanently.

    Args:
        time_entry_id: Numeric ID of the time entry to delete.

    Returns:
        {ok: True} on success, or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    return client.delete(f"/time_entries/{time_entry_id}.json")
