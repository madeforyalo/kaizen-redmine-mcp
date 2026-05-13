from __future__ import annotations

from pytest_httpx import HTTPXMock

BASE = "https://redmine.test"


def test_list_trackers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/trackers.json",
        json={"trackers": [{"id": 1, "name": "Bug"}, {"id": 2, "name": "Feature"}]},
    )
    from kaizen_redmine_mcp.tools.enums import list_trackers

    result = list_trackers()
    assert len(result) == 2
    assert result[0] == {"id": 1, "name": "Bug"}


def test_list_issue_statuses(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issue_statuses.json",
        json={
            "issue_statuses": [
                {"id": 1, "name": "New", "is_closed": False},
                {"id": 5, "name": "Closed", "is_closed": True},
            ]
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_issue_statuses

    result = list_issue_statuses()
    assert len(result) == 2
    closed = next(s for s in result if s["name"] == "Closed")
    assert closed["is_closed"] is True


def test_list_priorities(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/enumerations/issue_priorities.json",
        json={
            "issue_priorities": [
                {"id": 1, "name": "Low"},
                {"id": 2, "name": "Normal"},
                {"id": 3, "name": "High"},
            ]
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_priorities

    result = list_priorities()
    assert len(result) == 3
    assert result[2]["name"] == "High"


def test_list_versions(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects/alpha/versions.json",
        json={
            "versions": [
                {"id": 1, "name": "v1.0", "status": "open", "due_date": "2024-06-30"},
                {"id": 2, "name": "Backlog", "status": "open", "due_date": None},
                {"id": 3, "name": "v0.9", "status": "closed", "due_date": "2024-01-01"},
            ]
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_versions

    result = list_versions("alpha")
    assert len(result) == 3
    assert result[0] == {"id": 1, "name": "v1.0", "status": "open", "due_date": "2024-06-30"}
    assert result[2]["status"] == "closed"


def test_list_versions_numeric_id(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/projects/42/versions.json",
        json={"versions": [{"id": 7, "name": "Sprint 1", "status": "open", "due_date": None}]},
    )
    from kaizen_redmine_mcp.tools.enums import list_versions

    result = list_versions(42)
    assert result[0]["id"] == 7


def test_list_versions_404(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/projects/missing/versions.json", status_code=404)
    from kaizen_redmine_mcp.tools.enums import list_versions

    result = list_versions("missing")
    assert result[0]["error"] is True
    assert result[0]["status_code"] == 404


def test_list_trackers_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/trackers.json", status_code=401)
    from kaizen_redmine_mcp.tools.enums import list_trackers

    result = list_trackers()
    assert result[0]["error"] is True
    assert result[0]["status_code"] == 401
