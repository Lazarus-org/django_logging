import logging
from unittest import mock
import pytest

from django_logging.utils.context_manager import (
    config_setup,
    _restore_logging_config,
)


@pytest.fixture
def mock_logger():
    """
    Fixture to create a mock logger for testing.

    This fixture creates a mock logger object, which is used to test logging-related
    functionality without affecting the actual logging configuration.

    Yields:
    -------
    logging.Logger
        A mock logger instance with its manager mocked.
    """
    logger = logging.getLogger()
    with mock.patch.object(logger, "manager", new_callable=mock.Mock):
        yield logger


def test_config_setup_auto_initialization_enabled():
    """
    Test that ValueError is raised when auto-initialization is enabled.

    This test verifies that if auto-initialization is enabled in the configuration,
    the `config_setup` context manager raises a ValueError with the appropriate message.

    Asserts:
    -------
    - A ValueError is raised with the message indicating that `AUTO_INITIALIZATION_ENABLE`
      must be set to False.
    """
    with mock.patch(
        "django_logging.utils.context_manager.is_auto_initialization_enabled",
        return_value=True,
    ):
        with pytest.raises(ValueError) as excinfo:
            with config_setup():
                """"""

        assert (
            str(excinfo.value)
            == "you most set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING in your settings"
        )


def test_config_setup_applies_custom_config(mock_logger):
    """
    Test that the custom logging configuration is applied.

    This test checks that when auto-initialization is disabled, the `config_setup` context manager
    correctly applies custom logging configurations obtained from `get_config`. It verifies that
    the `LogManager` is used, and its methods for creating log files and setting the configuration
    are called.

    Mocks:
    ------
    - `django_logging.utils.context_manager.is_auto_initialization_enabled` to simulate disabled auto-initialization.
    - `django_logging.utils.context_manager.get_config` to provide custom configuration values.
    - `django_logging.utils.context_manager.LogManager` to check interaction with the log manager.

    Asserts:
    -------
    - The `LogManager` instance returned by `config_setup` matches the mocked instance.
    - The `create_log_files` and `set_conf` methods of the `LogManager` are called.
    """
    with mock.patch(
        "django_logging.utils.context_manager.is_auto_initialization_enabled",
        return_value=False,
    ):
        with mock.patch(
            "django_logging.utils.context_manager.get_config",
            return_value=(
                ["INFO"],
                "/tmp/logs",
                {"INFO": 1},
                "DEBUG",
                2,
                False,
                "",
                False,
                [],
                1,
            ),
        ):
            with mock.patch(
                "django_logging.utils.context_manager.LogManager"
            ) as MockLogManager:
                mock_log_manager = MockLogManager.return_value

                with config_setup() as log_manager:
                    assert log_manager is mock_log_manager
                    mock_log_manager.create_log_files.assert_called_once()
                    mock_log_manager.set_conf.assert_called_once()


def test_config_context_restores_original_config(mock_logger):
    """
    Test that the original logging configuration is restored after context exit.

    This test verifies that the `config_setup` context manager correctly restores the original
    logging configuration after exiting the context. It checks that the logger's original settings
    (config, level, handlers) are restored as they were before the context was entered.

    Mocks:
    ------
    - `django_logging.utils.context_manager.is_auto_initialization_enabled` to simulate disabled auto-initialization.
    - `django_logging.utils.context_manager.get_config` to provide custom configuration values.
    - `django_logging.utils.context_manager.LogManager` to avoid actual log manager interaction.

    Asserts:
    -------
    - The logger's configuration, level, and handlers are restored to their original state.
    """
    original_config = mock_logger.manager.loggerDict
    original_level = mock_logger.level
    original_handlers = mock_logger.handlers

    with mock.patch(
        "django_logging.utils.context_manager.is_auto_initialization_enabled",
        return_value=False,
    ):
        with mock.patch(
            "django_logging.utils.context_manager.get_config",
            return_value=(
                ["INFO"],
                "/tmp/logs",
                {"INFO": 1},
                "DEBUG",
                2,
                False,
                "",
                False,
                [],
                1,
            ),
        ):
            with mock.patch("django_logging.utils.context_manager.LogManager"):
                with config_setup():
                    mock_logger.level = logging.ERROR
                    mock_logger.handlers.append(logging.NullHandler())

                assert mock_logger.manager.loggerDict == original_config
                assert mock_logger.level == original_level
                assert mock_logger.handlers == original_handlers


def test_restore_logging_config(mock_logger):
    """
    Test the _restore_logging_config helper function.

    This test checks that the `_restore_logging_config` function correctly restores the logger's
    original configuration, level, and handlers. It verifies that after calling `_restore_logging_config`,
    the logger is returned to its initial state.

    Asserts:
    -------
    - The logger's configuration, level, and handlers match the original values provided to the function.
    """
    original_config = mock_logger.manager.loggerDict
    original_level = mock_logger.level
    original_handlers = mock_logger.handlers

    _restore_logging_config(
        mock_logger, original_config, original_level, original_handlers
    )

    assert mock_logger.manager.loggerDict == original_config
    assert mock_logger.level == original_level
    assert mock_logger.handlers == original_handlers
