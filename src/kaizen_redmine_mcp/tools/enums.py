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
