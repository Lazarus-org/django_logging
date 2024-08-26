import pytest

from django_logging.handlers import EmailHandler


@pytest.fixture
def email_handler() -> EmailHandler:
    """
    Fixture to create an EmailHandler instance.

    Returns:
    -------
    EmailHandler
        An instance of the EmailHandler class.
    """
    return EmailHandler()
