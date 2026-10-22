"""Explicit, process-global package logger configuration context.

Unlike the old implementation, this context never mutates root logging
or replaces logging.Manager.loggerDict. It must not be used as a
request-scoped configuration mechanism: logging is process-wide.

"""

import logging
from contextlib import contextmanager
from typing import Iterator

from django_logging.settings.activation import _LOCK, temporary_activation
from django_logging.settings.conf import LogConfig, LogManager
from django_logging.utils.get_conf import get_config, is_auto_initialization_enabled


@contextmanager
def config_setup() -> Iterator[LogManager]:
    """Temporarily install *isolated* django_logging handlers.

    The package logger's prior handlers, propagation, and level are
    restored after the block; unrelated/root logging never changes. The
    lock serializes simultaneous usages of this context manager, but
    logging by other threads can still observe the temporary package
    configuration.

    """
    if is_auto_initialization_enabled():
        raise ValueError(
            "You must set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING."
        )

    with _LOCK:
        log_manager = LogManager(LogConfig(**get_config()))
        config = log_manager.build_logging_dict()
        log_manager.create_log_files()
        with temporary_activation(config, resolver=log_manager._resolve_class):
            yield log_manager
