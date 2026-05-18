from __future__ import annotations

import httpx
import pytest
from pytest_httpx import HTTPXMock

BASE = "https://redmine.test"

ISSUE_FIXTURE = {
    "id": 10,
    "subject": "Fix login bug",
    "project": {"id": 1, "name": "Alpha"},
    "tracker": {"id": 1, "name": "Bug"},
    "status": {"id": 1, "name": "New"},
    "priority": {"id": 2, "name": "Normal"},
    "assigned_to": None,
    "author": {"id": 42, "name": "Bot User"},
    "created_on": "2024-01-01T00:00:00Z",
    "updated_on": "2024-01-02T00:00:00Z",
    "description": "Full description here",
}


def test_search_issues_subject_only(httpx_mock: HTTPXMock) -> None:
    """Results found via subject search; search.json returns nothing new."""
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?subject=%7Elogin&limit=25",
        json={"total_count": 1, "offset": 0, "limit": 25, "issues": [ISSUE_FIXTURE]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/search.json?q=login&issues=1&limit=25",
        json={"total_count": 0, "results": []},
    )
    from kaizen_redmine_mcp.tools.issues import search_issues

    result = search_issues("login")
    assert result["total_count"] == 1
    assert result["issues"][0]["id"] == 10
    assert "description" not in result["issues"][0]


def test_search_issues_deduplication(httpx_mock: HTTPXMock) -> None:
    """Issue found by both subject and full-text search appears only once."""
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?subject=%7Elogin&limit=25",
        json={"total_count": 1, "offset": 0, "limit": 25, "issues": [ISSUE_FIXTURE]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/search.json?q=login&issues=1&limit=25",
        json={"total_count": 1, "results": [{"id": 10, "type": "issue", "title": "Fix login bug"}]},
    )
    from kaizen_redmine_mcp.tools.issues import search_issues

    result = search_issues("login")
    assert result["total_count"] == 1  # not 2


def test_search_issues_description_hit(httpx_mock: HTTPXMock) -> None:
    """Issue found only via description (full-text search) gets batch-fetched."""
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?subject=%7Elogin&limit=25",
        json={"total_count": 0, "offset": 0, "limit": 25, "issues": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/search.json?q=login&issues=1&limit=25",
        json={"total_count": 1, "results": [{"id": 10, "type": "issue", "title": "Fix login bug"}]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?issue_id=10&limit=1",
        json={"total_count": 1, "offset": 0, "limit": 1, "issues": [ISSUE_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.issues import search_issues

    result = search_issues("login")
    assert result["total_count"] == 1
    assert result["issues"][0]["id"] == 10


def test_search_issues_with_project_and_status(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?subject=%7Ebug&limit=10&project_id=alpha&status_id=open",
        json={"total_count": 0, "offset": 0, "limit": 10, "issues": []},
    )
    httpx_mock.add_response(
        url=f"{BASE}/search.json?q=bug&issues=1&limit=10&scope=project%3Aalpha",
        json={"total_count": 0, "results": []},
    )
    from kaizen_redmine_mcp.tools.issues import search_issues

    result = search_issues("bug", project_id="alpha", status_id="open", limit=10)
    assert result["issues"] == []


def test_search_issues_subject_error_still_runs_fulltext(httpx_mock: HTTPXMock) -> None:
    """If subject search fails (e.g. 422), full-text search still runs."""
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?subject=%7Elogin&limit=25",
        status_code=422,
    )
    httpx_mock.add_response(
        url=f"{BASE}/search.json?q=login&issues=1&limit=25",
        json={"total_count": 1, "results": [{"id": 10, "type": "issue", "title": "Fix login bug"}]},
    )
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?issue_id=10&limit=1",
        json={"total_count": 1, "offset": 0, "limit": 1, "issues": [ISSUE_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.issues import search_issues

    result = search_issues("login")
    assert result["total_count"] == 1
    assert result["issues"][0]["id"] == 10


def test_list_issues(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?limit=25&offset=0&sort=updated_on%3Adesc",
        json={"total_count": 1, "offset": 0, "limit": 25, "issues": [ISSUE_FIXTURE]},
    )
    from kaizen_redmine_mcp.tools.issues import list_issues

    result = list_issues()
    assert result["total_count"] == 1
    issue = result["issues"][0]
    assert issue["id"] == 10
    assert "description" not in issue  # compact


def test_list_issues_with_filters(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json?limit=10&offset=0&sort=updated_on%3Adesc&project_id=alpha&status_id=open",
        json={"total_count": 0, "offset": 0, "limit": 10, "issues": []},
    )
    from kaizen_redmine_mcp.tools.issues import list_issues

    result = list_issues(project_id="alpha", status_id="open", limit=10)
    assert result["issues"] == []


def test_get_issue(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues/10.json?include=journals%2Cattachments%2Crelations%2Cchildren%2Cwatchers",
        json={"issue": {**ISSUE_FIXTURE, "journals": [], "attachments": []}},
    )
    from kaizen_redmine_mcp.tools.issues import get_issue

    result = get_issue(10)
    assert result["id"] == 10
    assert "journals" in result


def test_get_issue_no_journals(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues/10.json",
        json={"issue": ISSUE_FIXTURE},
    )
    from kaizen_redmine_mcp.tools.issues import get_issue

    result = get_issue(10, include_journals=False)
    assert result["id"] == 10


def test_create_issue(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 99}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="alpha", subject="Fix login bug")
    assert result["id"] == 99


def test_create_issue_with_custom_fields(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 200, "custom_fields": [{"id": 12, "name": "Tipo de tarea", "value": "Tarea"}]}},
        status_code=201,
    )
    import json
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(
        project_id="alpha",
        subject="Mi tarea",
        tracker_id=4,
        custom_fields=[{"id": 12, "value": "Tarea"}],
    )
    assert result["id"] == 200
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["issue"]["custom_fields"] == [{"id": 12, "value": "Tarea"}]


def test_create_issue_custom_fields_omitted_when_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 201}},
        status_code=201,
    )
    import json
    from kaizen_redmine_mcp.tools.issues import create_issue

    create_issue(project_id="alpha", subject="Sin custom fields")
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert "custom_fields" not in body["issue"]


def test_create_issue_with_category(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 100, "category": {"id": 5, "name": "Backend"}}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="alpha", subject="Backend task", category_id=5)
    assert result["id"] == 100
    request = httpx_mock.get_requests()[-1]
    import json
    body = json.loads(request.content)
    assert body["issue"]["category_id"] == 5


def test_create_issue_category_omitted_when_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 101}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="alpha", subject="No category")
    assert result["id"] == 101
    request = httpx_mock.get_requests()[-1]
    import json
    body = json.loads(request.content)
    assert "category_id" not in body["issue"]


def test_create_issue_with_fixed_version(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 102, "fixed_version": {"id": 3, "name": "v1.0"}}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="alpha", subject="v1.0 task", fixed_version_id=3)
    assert result["id"] == 102
    import json
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert body["issue"]["fixed_version_id"] == 3


def test_create_issue_fixed_version_omitted_when_none(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        json={"issue": {**ISSUE_FIXTURE, "id": 103}},
        status_code=201,
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="alpha", subject="No version")
    assert result["id"] == 103
    import json
    body = json.loads(httpx_mock.get_requests()[-1].content)
    assert "fixed_version_id" not in body["issue"]


def test_create_issue_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.issues import create_issue

    config.read_only = True
    result = create_issue(project_id="alpha", subject="Fix login bug")
    assert result["error"] is True
    assert "read-only" in result["message"]


def test_update_issue(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues/10.json",
        method="PUT",
        status_code=200,
        json={},
    )
    from kaizen_redmine_mcp.tools.issues import update_issue

    result = update_issue(10, status_id=2)
    assert result.get("ok") is True


def test_update_issue_no_fields() -> None:
    from kaizen_redmine_mcp.tools.issues import update_issue

    result = update_issue(10)
    assert result["error"] is True
    assert "No fields" in result["message"]


def test_update_issue_read_only() -> None:
    from kaizen_redmine_mcp.config import config
    from kaizen_redmine_mcp.tools.issues import update_issue

    config.read_only = True
    result = update_issue(10, status_id=2)
    assert result["error"] is True
    assert "read-only" in result["message"]


def test_update_issue_with_private_notes(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues/10.json",
        method="PUT",
        status_code=200,
        json={},
    )
    from kaizen_redmine_mcp.tools.issues import update_issue

    result = update_issue(10, notes="Internal note", private_notes=True)
    assert result.get("ok") is True
    request = httpx_mock.get_requests()[-1]
    import json
    body = json.loads(request.content)
    assert body["issue"]["private_notes"] is True


def test_get_issue_404(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues/999.json?include=journals%2Cattachments%2Crelations%2Cchildren%2Cwatchers",
        status_code=404,
    )
    from kaizen_redmine_mcp.tools.issues import get_issue

    result = get_issue(999)
    assert result["error"] is True
    assert result["status_code"] == 404


def test_create_issue_422(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=f"{BASE}/issues.json",
        method="POST",
        status_code=422,
        json={"errors": ["Project is invalid"]},
    )
    from kaizen_redmine_mcp.tools.issues import create_issue

    result = create_issue(project_id="bad", subject="x")
    assert result["error"] is True
    assert result["status_code"] == 422
