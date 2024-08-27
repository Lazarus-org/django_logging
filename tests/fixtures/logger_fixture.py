from logging import Logger, getLogger
from typing import Generator
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_logger() -> Generator[Logger, None, None]:
    """
    Fixture to create a mock logger for testing.

    This fixture creates a mock logger object, which is used to test logging-related
    functionality without affecting the actual logging configuration.

    Yields:
    -------
    logging.Logger
        A mock logger instance with its manager mocked.
    """
    logger = getLogger()
    with patch.object(logger, "manager", new_callable=Mock):
        yield logger
