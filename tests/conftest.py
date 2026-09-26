"""Global pytest fixtures and test setup."""

import pytest
import os

# Set testing environment variables
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SLACK_MOCK_MODE"] = "true"
