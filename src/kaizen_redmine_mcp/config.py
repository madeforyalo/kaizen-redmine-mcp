from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        logger.error("Required environment variable %s is not set. Aborting.", name)
        sys.exit(1)
    return value


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw not in ("0", "false", "no", "off")


class Config:
    redmine_url: str
    redmine_api_key: str
    server_host: str
    server_port: int
    ssl_verify: bool
    http_timeout: float
    read_only: bool
    log_level: str

    def __init__(self) -> None:
        self.redmine_url = _require("REDMINE_URL").rstrip("/")
        self.redmine_api_key = _require("REDMINE_API_KEY")
        self.server_host = os.environ.get("SERVER_HOST", "0.0.0.0")
        self.server_port = int(os.environ.get("SERVER_PORT", "8000"))
        self.ssl_verify = _bool_env("REDMINE_SSL_VERIFY", True)
        self.http_timeout = float(os.environ.get("HTTP_TIMEOUT", "30"))
        self.read_only = _bool_env("REDMINE_MCP_READ_ONLY", False)
        self.log_level = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


config = Config()
setup_logging(config.log_level)
