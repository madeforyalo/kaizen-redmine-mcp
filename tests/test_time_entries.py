from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

BASE = "https://redmine.test"

ENTRY_FIXTURE = {
    "id": 5,
    "project": {"id": 1, "name": "Alpha"},
    "issue": {"id": 10},
    "user": {"id": 42, "name": "Bot User"},
    "activity": {"id": 9, "name": "Development"},
    "hours": 2.5,
    "comments": "Implemented login fix",
    "spent_on": "2024-06-01",
    "created_on": "2024-06-01T10:00:00Z",
}


# ---------------------------------------------------------------------------
# list_time_entry_activities
# ---------------------------------------------------------------------------


def test_list_time_entry_activities(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/enumerations/time_entry_activities.json",
        json={"time_entry_activities": [
            {"id": 9, "name": "Development"},
            {"id": 10, "name": "Support"},
        ]},
    )
    from kaizen_redmine_mcp.tools.enums import list_time_entry_activities

    result = list_time_entry_activities()
    assert len(result) == 2
    assert result[0] == {"id": 9, "name": "Development"}


def test_list_time_entry_activities_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/enumerations/time_entry_activities.json", status_code=401
    )
    from kaizen_redmine_mcp.tools.enums import list_time_entry_activities

    result = list_time_entry_activities()
    assert result[0]["error"] is True


# ---------------------------------------------------------------------------
# log_time
# ---------------------------------------------------------------------------


def test_log_time(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries.json",
        method="POST",
        json={"time_entry": ENTRY_FIXTURE},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.time_entries import log_time

    result = log_time(issue_id=10, hours=2.5, activity_id=9, spent_on="2024-06-01", comments="Implemented login fix")
    assert result["id"] == 5
    assert result["hours"] == 2.5
    assert result["issue_id"] == 10

    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["time_entry"]["hours"] == 2.5
    assert body["time_entry"]["activity_id"] == 9
    assert body["time_entry"]["spent_on"] == "2024-06-01"


def test_log_time_defaults_to_today(httpx_mock: HTTPXMock) -> None:
    from datetime import date

    httpx_mock.add_response(
        url=f"{BASE}/time_entries.json",
        method="POST",
        json={"time_entry": ENTRY_FIXTURE},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.time_entries import log_time

    log_time(issue_id=10, hours=1.0, activity_id=9)
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["time_entry"]["spent_on"] == date.today().isoformat()


def test_log_time_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.time_entries import log_time

    config.read_only = True
    result = log_time(issue_id=10, hours=1.0, activity_id=9)
    assert result["error"] is True
    assert "read-only" in result["message"]


def test_log_time_422(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries.json", method="POST", status_code=422
    )
    from kaizen_redmine_mcp.tools.time_entries import log_time

    result = log_time(issue_id=99, hours=1.0, activity_id=9)
    assert result["error"] is True
    assert result["status_code"] == 422


# ---------------------------------------------------------------------------
# list_time_entries
# ---------------------------------------------------------------------------


def test_list_time_entries(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries.json?limit=25&offset=0",
        json={"total_count": 1, "offset": 0, "limit": 25, "time_entries": [ENTRY_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.time_entries import list_time_entries

    result = list_time_entries()
    assert result["total_count"] == 1
    assert result["time_entries"][0]["hours"] == 2.5


def test_list_time_entries_with_filters(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries.json?limit=10&offset=0&issue_id=10&user_id=42",
        json={"total_count": 0, "offset": 0, "limit": 10, "time_entries": []},
    )
    from kaizen_redmine_mcp.tools.time_entries import list_time_entries

    result = list_time_entries(issue_id=10, user_id=42, limit=10)
    assert result["time_entries"] == []


# ---------------------------------------------------------------------------
# get_time_entry
# ---------------------------------------------------------------------------


def test_get_time_entry(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries/5.json",
        json={"time_entry": ENTRY_FIXTURE},
    )
    from kaizen_redmine_mcp.tools.time_entries import get_time_entry

    result = get_time_entry(5)
    assert result["id"] == 5
    assert result["activity"] == {"id": 9, "name": "Development"}


def test_get_time_entry_404(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=f"{BASE}/time_entries/999.json", status_code=404)
    from kaizen_redmine_mcp.tools.time_entries import get_time_entry

    result = get_time_entry(999)
    assert result["error"] is True
    assert result["status_code"] == 404


# ---------------------------------------------------------------------------
# update_time_entry
# ---------------------------------------------------------------------------


def test_update_time_entry(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries/5.json", method="PUT", status_code=200, json={}
    )
    from kaizen_redmine_mcp.tools.time_entries import update_time_entry

    result = update_time_entry(5, hours=3.0, comments="Updated")
    assert result.get("ok") is True

    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["time_entry"]["hours"] == 3.0
    assert body["time_entry"]["comments"] == "Updated"
    assert "activity_id" not in body["time_entry"]


def test_update_time_entry_no_fields() -> None:
    from kaizen_redmine_mcp.tools.time_entries import update_time_entry

    result = update_time_entry(5)
    assert result["error"] is True
    assert "No fields" in result["message"]


def test_update_time_entry_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.time_entries import update_time_entry

    config.read_only = True
    result = update_time_entry(5, hours=1.0)
    assert result["error"] is True
    assert "read-only" in result["message"]


# ---------------------------------------------------------------------------
# delete_time_entry
# ---------------------------------------------------------------------------


def test_delete_time_entry(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries/5.json", method="DELETE", status_code=200
    )
    from kaizen_redmine_mcp.tools.time_entries import delete_time_entry

    result = delete_time_entry(5)
    assert result.get("ok") is True


def test_delete_time_entry_404(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/time_entries/999.json", method="DELETE", status_code=404
    )
    from kaizen_redmine_mcp.tools.time_entries import delete_time_entry

    result = delete_time_entry(999)
    assert result["error"] is True
    assert result["status_code"] == 404


def test_delete_time_entry_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.time_entries import delete_time_entry

    config.read_only = True
    result = delete_time_entry(5)
    assert result["error"] is True
    assert "read-only" in result["message"]
