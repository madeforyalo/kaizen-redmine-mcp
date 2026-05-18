from __future__ import annotations

from pytest_httpx import HTTPXMock

BASE = "https://redmine.test"


def test_list_custom_fields_filters_issue_type(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/custom_fields.json",
        json={
            "custom_fields": [
                {
                    "id": 12,
                    "name": "Tipo de tarea",
                    "customized_type": "issue",
                    "field_format": "list",
                    "possible_values": [
                        {"value": "Tarea"},
                        {"value": "Minuta"},
                        {"value": "KAI"},
                        {"value": "Presupuesto"},
                    ],
                },
                {
                    "id": 3,
                    "name": "Client code",
                    "customized_type": "project",  # should be excluded
                    "field_format": "string",
                    "possible_values": [],
                },
            ]
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_custom_fields

    result = list_custom_fields()
    assert len(result) == 1
    assert result[0]["id"] == 12
    assert result[0]["name"] == "Tipo de tarea"
    assert result[0]["possible_values"] == ["Tarea", "Minuta", "KAI", "Presupuesto"]
    assert result[0]["field_format"] == "list"


def test_list_custom_fields_free_text(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/custom_fields.json",
        json={
            "custom_fields": [
                {
                    "id": 7,
                    "name": "External ref",
                    "customized_type": "issue",
                    "field_format": "string",
                    "possible_values": [],
                }
            ]
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_custom_fields

    result = list_custom_fields()
    assert result[0]["possible_values"] == []


def test_list_custom_fields_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/custom_fields.json", status_code=403)
    from kaizen_redmine_mcp.tools.enums import list_custom_fields

    result = list_custom_fields()
    assert result[0]["error"] is True
    assert result[0]["status_code"] == 403


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


def test_list_users(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/users.json?limit=25&offset=0",
        json={
            "total_count": 2,
            "offset": 0,
            "limit": 25,
            "users": [
                {"id": 1, "login": "admin", "firstname": "Admin", "lastname": "User", "mail": "admin@k.test"},
                {"id": 2, "login": "bot", "firstname": "Bot", "lastname": "User", "mail": "bot@k.test"},
            ],
        },
    )
    from kaizen_redmine_mcp.tools.enums import list_users

    result = list_users()
    assert result["total_count"] == 2
    assert result["users"][0] == {"id": 1, "login": "admin", "firstname": "Admin", "lastname": "User"}
    assert "mail" not in result["users"][0]


def test_list_users_pagination(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/users.json?limit=1&offset=1",
        json={"total_count": 2, "offset": 1, "limit": 1, "users": [
            {"id": 2, "login": "bot", "firstname": "Bot", "lastname": "User"},
        ]},
    )
    from kaizen_redmine_mcp.tools.enums import list_users

    result = list_users(limit=1, offset=1)
    assert result["offset"] == 1
    assert len(result["users"]) == 1


def test_list_users_403(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/users.json?limit=25&offset=0", status_code=403)
    from kaizen_redmine_mcp.tools.enums import list_users

    result = list_users()
    assert result["error"] is True
    assert result["status_code"] == 403


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
