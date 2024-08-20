from contextlib import contextmanager

from django_logging.settings.conf import LogConfig, LogManager
from django_logging.utils.get_config import get_conf
import logging


@contextmanager
def config_context() -> None:

    # Store the current logging configuration to restore it later
    original_logging_config = logging.getLogger().manager.loggerDict.copy()

    conf = get_conf()
    try:

        # Apply the new logging configuration
        log_config = LogConfig(*conf)
        log_manager = LogManager(log_config)

        log_manager.create_log_files()
        log_manager.set_conf()

        yield log_manager

    finally:
        # Revert back to the original logging configuration
        logging.getLogger().manager.loggerDict.clear()
        logging.getLogger().manager.loggerDict.update(original_logging_config)
