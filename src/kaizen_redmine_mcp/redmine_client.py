from __future__ import annotations

import logging
from typing import Any

import httpx

from .config import config

logger = logging.getLogger(__name__)

_ERROR_MESSAGES: dict[int, str] = {
    401: "Unauthorized — check REDMINE_API_KEY.",
    403: "Forbidden — the API key lacks permission for this action.",
    404: "Not found.",
    422: "Unprocessable entity — Redmine rejected the payload.",
}


def _error(status: int, body: str) -> dict[str, Any]:
    msg = _ERROR_MESSAGES.get(status, body[:300] if body else f"HTTP {status}")
    return {"error": True, "status_code": status, "message": msg}


class RedmineClient:
    def __init__(self) -> None:
        self._client = httpx.Client(
            base_url=config.redmine_url,
            headers={
                "X-Redmine-API-Key": config.redmine_api_key,
                "Content-Type": "application/json",
            },
            verify=config.ssl_verify,
            timeout=config.http_timeout,
        )

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            r = self._client.get(path, params=params)
            logger.debug("GET %s %s → %s", path, params, r.status_code)
            if r.status_code >= 400:
                return _error(r.status_code, r.text)
            return r.json()
        except httpx.RequestError as exc:
            return {"error": True, "status_code": 0, "message": str(exc)}

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            r = self._client.post(path, json=payload)
            logger.debug("POST %s → %s", path, r.status_code)
            if r.status_code >= 400:
                return _error(r.status_code, r.text)
            return r.json() if r.content else {}
        except httpx.RequestError as exc:
            return {"error": True, "status_code": 0, "message": str(exc)}

    def put(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            r = self._client.put(path, json=payload)
            logger.debug("PUT %s → %s", path, r.status_code)
            if r.status_code >= 400:
                return _error(r.status_code, r.text)
            return {"ok": True} if r.status_code in (200, 204) else r.json()
        except httpx.RequestError as exc:
            return {"error": True, "status_code": 0, "message": str(exc)}

    def delete(self, path: str) -> dict[str, Any]:
        try:
            r = self._client.delete(path)
            logger.debug("DELETE %s → %s", path, r.status_code)
            if r.status_code >= 400:
                return _error(r.status_code, r.text)
            return {"ok": True}
        except httpx.RequestError as exc:
            return {"error": True, "status_code": 0, "message": str(exc)}

    def close(self) -> None:
        self._client.close()


client = RedmineClient()
