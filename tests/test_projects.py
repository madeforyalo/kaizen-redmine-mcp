from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

BASE = "https://redmine.test"

PROJECT_FIXTURE = {
    "id": 1,
    "name": "Alpha",
    "identifier": "alpha",
    "description": "Alpha project",
    "parent": None,
}


def test_get_current_user(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/users/current.json",
        json={
            "user": {
                "id": 42,
                "login": "bot",
                "firstname": "Bot",
                "lastname": "User",
                "mail": "bot@kaizen.test",
                "admin": False,
            }
        },
    )
    from kaizen_redmine_mcp.tools.projects import get_current_user

    result = get_current_user()
    assert result["id"] == 42
    assert result["login"] == "bot"
    assert "mail" in result


def test_list_projects(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects.json?limit=25&offset=0",
        json={"total_count": 1, "offset": 0, "limit": 25, "projects": [PROJECT_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.projects import list_projects

    result = list_projects()
    assert result["total_count"] == 1
    assert result["projects"][0]["identifier"] == "alpha"
    assert "description" not in result["projects"][0]  # compact — no description


def test_get_project(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects/alpha.json?include=trackers%2Cissue_categories%2Cenabled_modules",
        json={"project": {**PROJECT_FIXTURE, "trackers": [], "enabled_modules": []}},
    )
    from kaizen_redmine_mcp.tools.projects import get_project

    result = get_project("alpha")
    assert result["identifier"] == "alpha"
    assert "trackers" in result


def test_find_project_single_page(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects.json?limit=100&offset=0",
        json={"total_count": 1, "offset": 0, "limit": 100, "projects": [PROJECT_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.projects import find_project

    results = find_project("alph")
    assert len(results) == 1
    assert results[0]["identifier"] == "alpha"
    assert len(results[0]["description"]) <= 200


def test_find_project_pagination(httpx_mock: HTTPXMock) -> None:
    """find_project should iterate pages until it collects enough matches."""
    page1 = [
        {"id": i, "name": f"Other {i}", "identifier": f"other-{i}", "description": "", "parent": None}
        for i in range(1, 101)
    ]
    page2 = [
        {"id": 200, "name": "Kaizen Main", "identifier": "kaizen-main", "description": "Main project", "parent": None}
    ]
    httpx_mock.add_response(
        url=f"{BASE}/projects.json?limit=100&offset=0",
        json={"total_count": 101, "offset": 0, "limit": 100, "projects": page1},
    )
    httpx_mock.add_response(
        url=f"{BASE}/projects.json?limit=100&offset=100",
        json={"total_count": 101, "offset": 100, "limit": 100, "projects": page2},
    )
    from kaizen_redmine_mcp.tools.projects import find_project

    results = find_project("kaizen")
    assert len(results) == 1
    assert results[0]["identifier"] == "kaizen-main"


def test_create_project(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects.json",
        method="POST",
        json={"project": {**PROJECT_FIXTURE, "id": 99}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.projects import create_project

    result = create_project("Alpha", "alpha")
    assert result["id"] == 99


def test_create_project_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.projects import create_project

    config.read_only = True
    result = create_project("Alpha", "alpha")
    assert result["error"] is True
    assert "read-only" in result["message"]


def test_get_project_404(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects/missing.json?include=trackers%2Cissue_categories%2Cenabled_modules",
        status_code=404,
    )
    from kaizen_redmine_mcp.tools.projects import get_project

    result = get_project("missing")
    assert result["error"] is True
    assert result["status_code"] == 404


def test_create_project_422(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects.json",
        method="POST",
        status_code=422,
        json={"errors": ["Identifier has already been taken"]},
    )
    from kaizen_redmine_mcp.tools.projects import create_project

    result = create_project("Alpha", "alpha")
    assert result["error"] is True
    assert result["status_code"] == 422


def test_get_current_user_401(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/users/current.json", status_code=401)
    from kaizen_redmine_mcp.tools.projects import get_current_user

    result = get_current_user()
    assert result["error"] is True
    assert result["status_code"] == 401
