from __future__ import annotations

import os

import pytest

# Set required env vars before any app imports touch config
os.environ.setdefault("REDMINE_URL", "https://redmine.test")
os.environ.setdefault("REDMINE_API_KEY", "test-key-0000")
os.environ.setdefault("REDMINE_MCP_READ_ONLY", "false")


@pytest.fixture(autouse=True)
def reset_read_only():
    """Ensure read_only is False between tests unless overridden."""
    from kaizen_redmine_mcp.config import config

    original = config.read_only
    yield
    config.read_only = original
