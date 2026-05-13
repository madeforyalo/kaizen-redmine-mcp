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
