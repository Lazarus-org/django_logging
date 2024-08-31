from typing import Dict, Generator
from unittest.mock import patch

import pytest
from django.conf import settings


@pytest.fixture
def mock_settings() -> Generator[Dict, None, None]:
    """
    Fixture to mock Django settings.

    This fixture sets up mock settings for `DJANGO_LOGGING` to provide controlled values
    for testing the configuration functions. The settings are patched into the Django settings
    object during the test.

    Yields:
    -------
    dict
        A dictionary containing the mock settings used in the tests.
    """
    mock_settings = {
        "DJANGO_LOGGING": {
            "LOG_FILE_LEVELS": ["DEBUG", "INFO"],
            "LOG_DIR": "/custom/log/dir",
            "LOG_FILE_FORMATS": {
                "DEBUG": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "LOG_CONSOLE_LEVEL": "WARNING",
            "LOG_CONSOLE_FORMAT": "%(levelname)s - %(message)s",
            "LOG_CONSOLE_COLORIZE": True,
            "LOG_DATE_FORMAT": "%Y-%m-%d",
            "LOG_EMAIL_NOTIFIER": {
                "ENABLE": True,
                "NOTIFY_ERROR": True,
                "NOTIFY_CRITICAL": False,
                "LOG_FORMAT": "custom_format",
            },
        }
    }
    with patch.object(settings, "DJANGO_LOGGING", mock_settings["DJANGO_LOGGING"]):
        yield mock_settings


@pytest.fixture
def reset_settings() -> Generator[None, None, None]:
    """
    Fixture to reset Django settings after each test.

    This ensures that any modifications to the settings during a test are reverted after the test completes.

    Yields:
    -------
    None
    """
    original_settings = settings.DJANGO_LOGGING
    yield
    settings.DJANGO_LOGGING = original_settings
