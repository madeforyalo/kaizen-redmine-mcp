from __future__ import annotations

from typing import Any

from ..config import config
from ..redmine_client import client

_READ_ONLY_ERROR = {"error": True, "message": "Server is in read-only mode."}


def get_current_user() -> dict[str, Any]:
    """Return info about the user who owns the current API key.

    Returns:
        {id, login, firstname, lastname, mail, admin}
    """
    data = client.get("/users/current.json")
    if data.get("error"):
        return data
    u = data["user"]
    return {
        "id": u["id"],
        "login": u["login"],
        "firstname": u["firstname"],
        "lastname": u["lastname"],
        "mail": u["mail"],
        "admin": u.get("admin", False),
    }


def _compact_project(p: dict[str, Any]) -> dict[str, Any]:
    parent = p.get("parent")
    return {
        "id": p["id"],
        "name": p["name"],
        "identifier": p["identifier"],
        "parent_id": parent["id"] if parent else None,
    }


def list_projects(limit: int = 25, offset: int = 0) -> dict[str, Any]:
    """List Redmine projects (paginated, compact fields only).

    Args:
        limit: Max results per page (1–100).
        offset: Number of records to skip.

    Returns:
        {total_count, offset, limit, projects: [{id, name, identifier, parent_id}]}
    """
    data = client.get("/projects.json", {"limit": limit, "offset": offset})
    if data.get("error"):
        return data
    return {
        "total_count": data.get("total_count", 0),
        "offset": data.get("offset", offset),
        "limit": data.get("limit", limit),
        "projects": [_compact_project(p) for p in data.get("projects", [])],
    }


def find_project(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search projects by substring in name or identifier (case-insensitive).

    Iterates pages until enough matches are found or all projects are scanned.

    Args:
        query: Substring to search for in project name or identifier.
        limit: Maximum number of results to return.

    Returns:
        List of {id, name, identifier, description} with description truncated to 200 chars.
    """
    q = query.lower()
    results: list[dict[str, Any]] = []
    offset = 0
    page_size = 100

    while True:
        data = client.get("/projects.json", {"limit": page_size, "offset": offset})
        if data.get("error"):
            return [data]
        projects = data.get("projects", [])
        if not projects:
            break
        for p in projects:
            if q in p["name"].lower() or q in p["identifier"].lower():
                parent = p.get("parent")
                results.append(
                    {
                        "id": p["id"],
                        "name": p["name"],
                        "identifier": p["identifier"],
                        "parent_id": parent["id"] if parent else None,
                        "description": (p.get("description") or "")[:200],
                    }
                )
                if len(results) >= limit:
                    return results
        total = data.get("total_count", 0)
        offset += page_size
        if offset >= total:
            break

    return results


def get_project(project_id: str | int) -> dict[str, Any]:
    """Return full details for a single project including trackers, categories, and modules.

    Args:
        project_id: Numeric ID or string identifier of the project.

    Returns:
        Full project object from Redmine including trackers, issue_categories, enabled_modules.
    """
    data = client.get(
        f"/projects/{project_id}.json",
        {"include": "trackers,issue_categories,enabled_modules"},
    )
    if data.get("error"):
        return data
    return data.get("project", data)


def create_project(
    name: str,
    identifier: str,
    description: str = "",
    parent_id: int | None = None,
    is_public: bool = False,
    inherit_members: bool = True,
) -> dict[str, Any]:
    """Create a new Redmine project.

    Args:
        name: Display name of the project.
        identifier: URL-safe unique identifier (lowercase letters, numbers, hyphens).
        description: Optional project description.
        parent_id: Numeric ID of parent project (for subprojects).
        is_public: Whether the project is publicly visible.
        inherit_members: Inherit members from parent project (only applies when parent_id is set).

    Returns:
        Created project object or error dict.
    """
    if config.read_only:
        return _READ_ONLY_ERROR

    payload: dict[str, Any] = {
        "name": name,
        "identifier": identifier,
        "description": description,
        "is_public": is_public,
    }
    if parent_id is not None:
        payload["parent_id"] = parent_id
        payload["inherit_members"] = inherit_members

    data = client.post("/projects.json", {"project": payload})
    if data.get("error"):
        return data
    return data.get("project", data)
