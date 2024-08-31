from typing import Generator
from unittest.mock import MagicMock

import pytest
from django.conf import settings


@pytest.fixture
def admin_email_mock_settings() -> Generator[None, None, None]:
    """
    Fixture to mock Django settings related to email notifications.

    This fixture sets up a mock ADMIN_EMAIL setting for testing and cleans up
    by deleting the setting after the test.

    Yields:
    -------
    None
    """
    settings.ADMIN_EMAIL = "admin@example.com"
    yield
    del settings.ADMIN_EMAIL


@pytest.fixture
def magic_mock_logger() -> MagicMock:
    """
    Fixture to create a mock logger object for testing.

    Returns:
    --------
    MagicMock
        A mock logger object used in the tests.
    """
    return MagicMock()
