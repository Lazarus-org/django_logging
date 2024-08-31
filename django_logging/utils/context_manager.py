from contextlib import contextmanager
from logging import Logger, PlaceHolder, getLogger
from typing import Dict, Iterator, Union

from django_logging.settings.conf import LogConfig, LogManager
from django_logging.utils.get_conf import get_config, is_auto_initialization_enabled


@contextmanager
def config_setup() -> Iterator[LogManager]:
    """Context manager to temporarily apply a custom logging configuration.

    Raises:
        ValueError: If 'AUTO_INITIALIZATION_ENABLE' in DJNAGO_LOGGING is set to True.

    Yields:
        LogManager: The log manager instance with the custom configuration.

    """
    if is_auto_initialization_enabled():
        raise ValueError(
            "you most set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING in your settings"
        )

    logger = getLogger()
    original_config = logger.manager.loggerDict.copy()
    original_level = logger.level
    original_handlers = logger.handlers.copy()

    try:
        conf = get_config()
        log_config = LogConfig(**conf)
        log_manager = LogManager(log_config)
        log_manager.create_log_files()
        log_manager.set_conf()

        yield log_manager
    finally:
        _restore_logging_config(
            logger, original_config, original_level, original_handlers
        )


def _restore_logging_config(
    logger: Logger,
    original_config: Dict[str, Union[Logger, PlaceHolder]],
    original_level: int,
    original_handlers: list,
) -> None:
    """Restore the original logging configuration.

    Args:
        logger (Logger): The root logger instance.
        original_config (Dict[str, Logger | PlaceHolder]): The original logger dictionary.
        original_level (int): The original root logger level.
        original_handlers (list): The original root logger handlers.

    """
    logger.manager.loggerDict.clear()
    logger.manager.loggerDict.update(original_config)
    logger.level = original_level
    logger.handlers.clear()
    logger.handlers.extend(original_handlers)
