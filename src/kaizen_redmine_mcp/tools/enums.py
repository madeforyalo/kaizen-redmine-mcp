from __future__ import annotations

from typing import Any

from ..redmine_client import client


def list_trackers() -> list[dict[str, Any]]:
    """Return all issue trackers defined in Redmine.

    Returns:
        List of {id, name} dicts.
    """
    data = client.get("/trackers.json")
    if data.get("error"):
        return [data]
    return [{"id": t["id"], "name": t["name"]} for t in data.get("trackers", [])]


def list_issue_statuses() -> list[dict[str, Any]]:
    """Return all issue statuses defined in Redmine.

    Returns:
        List of {id, name, is_closed} dicts.
    """
    data = client.get("/issue_statuses.json")
    if data.get("error"):
        return [data]
    return [
        {"id": s["id"], "name": s["name"], "is_closed": s.get("is_closed", False)}
        for s in data.get("issue_statuses", [])
    ]


def list_priorities() -> list[dict[str, Any]]:
    """Return all issue priority levels defined in Redmine.

    Returns:
        List of {id, name} dicts.
    """
    data = client.get("/enumerations/issue_priorities.json")
    if data.get("error"):
        return [data]
    return [
        {"id": p["id"], "name": p["name"]}
        for p in data.get("issue_priorities", [])
    ]


def list_time_entry_activities() -> list[dict[str, Any]]:
    """Return all time entry activity types defined in Redmine.

    Use the returned IDs as the activity_id parameter when calling log_time
    or update_time_entry. Common activities: Development, Support, Meeting,
    Design, Testing.

    Returns:
        List of {id, name} dicts.
    """
    data = client.get("/enumerations/time_entry_activities.json")
    if data.get("error"):
        return [data]
    return [
        {"id": a["id"], "name": a["name"]}
        for a in data.get("time_entry_activities", [])
    ]


def list_users(limit: int = 25, offset: int = 0) -> dict[str, Any]:
    """Return a paginated list of Redmine users.

    Requires the API key to belong to an administrator account — Redmine
    returns 403 for non-admin keys.

    Args:
        limit: Max results per page (1–100).
        offset: Number of records to skip.

    Returns:
        {total_count, offset, limit, users: [{id, login, firstname, lastname}]}
    """
    data = client.get("/users.json", {"limit": limit, "offset": offset})
    if data.get("error"):
        return data
    return {
        "total_count": data.get("total_count", 0),
        "offset": data.get("offset", offset),
        "limit": data.get("limit", limit),
        "users": [
            {
                "id": u["id"],
                "login": u["login"],
                "firstname": u["firstname"],
                "lastname": u["lastname"],
            }
            for u in data.get("users", [])
        ],
    }


def list_versions(project_id: str | int) -> list[dict[str, Any]]:
    """Return all versions (sprints / milestones) defined in a project.

    Use this before calling create_issue with fixed_version_id to obtain valid
    version IDs that belong to the target project — Redmine rejects IDs from
    other projects with a 422 error.

    Args:
        project_id: Numeric ID or string identifier of the project.

    Returns:
        List of {id, name, status, due_date} dicts. status is one of
        'open', 'locked', or 'closed'.
    """
    data = client.get(f"/projects/{project_id}/versions.json")
    if data.get("error"):
        return [data]
    return [
        {
            "id": v["id"],
            "name": v["name"],
            "status": v.get("status", "open"),
            "due_date": v.get("due_date"),
        }
        for v in data.get("versions", [])
    ]
