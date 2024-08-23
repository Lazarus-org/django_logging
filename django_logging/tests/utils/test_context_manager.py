import logging
from unittest import mock
import pytest

from django_logging.utils.context_manager import (
    config_setup,
    _restore_logging_config,
)


@pytest.fixture
def mock_logger():
    """Fixture to create a mock logger for testing."""
    logger = logging.getLogger()
    with mock.patch.object(logger, "manager", new_callable=mock.Mock):
        yield logger


def test_config_setup_auto_initialization_enabled():
    """Test that ValueError is raised when auto-initialization is enabled."""
    with mock.patch(
        "django_logging.utils.context_manager.is_auto_initialization_enabled",
        return_value=True,
    ):
        with pytest.raises(ValueError) as excinfo:
            with config_setup(): ""

        assert (
            str(excinfo.value)
            == "you most set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING in your settings"
        )


def test_config_setup_applies_custom_config(mock_logger):
    """Test that the custom logging configuration is applied."""
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
                    # Assert that the custom log manager is used
                    assert log_manager is mock_log_manager

                    # Assert the log files are created and config is set
                    mock_log_manager.create_log_files.assert_called_once()
                    mock_log_manager.set_conf.assert_called_once()


def test_config_context_restores_original_config(mock_logger):
    """Test that the original logging configuration is restored after context exit."""
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
                    # Change the logger's configuration
                    mock_logger.level = logging.ERROR
                    mock_logger.handlers.append(logging.NullHandler())

                # After exiting the context, original config should be restored
                assert mock_logger.manager.loggerDict == original_config
                assert mock_logger.level == original_level
                assert mock_logger.handlers == original_handlers


def test_restore_logging_config(mock_logger):
    """Test the _restore_logging_config helper function."""
    original_config = mock_logger.manager.loggerDict
    original_level = mock_logger.level
    original_handlers = mock_logger.handlers

    _restore_logging_config(
        mock_logger, original_config, original_level, original_handlers
    )

    assert mock_logger.manager.loggerDict == original_config
    assert mock_logger.level == original_level
    assert mock_logger.handlers == original_handlers
