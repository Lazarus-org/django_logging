"""Function execution diagnostics without disturbing existing SQL query
history."""

import inspect
import logging
import os
from functools import wraps
from time import perf_counter
from typing import Any, Callable, Optional

from django.conf import settings
from django.db import connection

from django_logging.utils.time import format_elapsed_time
from django_logging.validators.config_validators import (
    validate_boolean_setting,
    validate_integer_setting,
)

logger = logging.getLogger(__name__)


def execution_tracker(
    logging_level: int = logging.INFO,
    log_queries: bool = False,
    query_threshold: Optional[int] = None,
    query_exceed_warning: bool = False,
) -> Callable:
    """Log elapsed time and optionally count debug SQL queries for sync
    functions.

    Query counting uses the current connection's existing debug history
    and never clears it. It is therefore best-effort if Django's bounded
    query history wraps or another task concurrently shares the same
    connection.

    Asynchronous functions are timed through their *awaited* completion.
    SQL query counting for async functions is rejected at decoration
    time because Django maintains database connections per execution
    context; sampling a sync connection before/after an async coroutine
    cannot give a reliable query count across sync_to_async boundaries.

    """
    errors = []
    errors.extend(
        validate_integer_setting(logging_level, "execution_tracker.logging_level")
    )
    errors.extend(
        validate_boolean_setting(log_queries, "execution_tracker.log_queries")
    )
    if query_threshold is not None:
        errors.extend(
            validate_integer_setting(
                query_threshold, "execution_tracker.query_threshold"
            )
        )
    errors.extend(
        validate_boolean_setting(
            query_exceed_warning, "execution_tracker.query_exceed_warning"
        )
    )
    if errors:
        raise ValueError(errors[0])

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)
        if is_async and log_queries:
            raise ValueError(
                "execution_tracker.log_queries is not supported for async functions"
            )

        def log_success(elapsed: float, count: Optional[int]) -> None:
            function_name = func.__qualname__
            exceeded = (
                count is not None
                and query_threshold is not None
                and count > query_threshold
            )
            if exceeded and query_exceed_warning:
                logger.warning(
                    "Number of database queries (%s) "
                    "exceeded threshold (%s) for function '%s'",
                    count,
                    query_threshold,
                    function_name,
                )
            elif count is None and log_queries and not settings.DEBUG:
                logger.warning(
                    "DEBUG mode is disabled, so database queries are not tracked. "
                    "To include number of queries, set DEBUG to True in your django settings."
                )
            # Warnings remain independent of the optional metrics record.
            # Avoid path resolution and message/time formatting when filtered.
            if not logger.isEnabledFor(logging_level):
                return
            message = (
                f"Performance Metrics for Function: '{function_name}'\n"
                f"  Module: {func.__module__}\n"
                f"  File: {os.path.abspath(func.__code__.co_filename)}, "
                f"Line: {func.__code__.co_firstlineno}\n"
                f"  Execution Time: {format_elapsed_time(elapsed)}"
            )
            if count is not None:
                message += f"\n  Database Queries: {count} queries "
                if exceeded:
                    message += f"(exceeds threshold of ({query_threshold}))"
            logger.log(logging_level, message)

        def log_failure(exc: Exception) -> None:
            logger.error(
                "Error executing function '%s': %s",
                func.__qualname__,
                str(exc),
                exc_info=True,
            )

        if is_async:

            @wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                started = perf_counter()
                try:
                    result = await func(*args, **kwargs)
                except Exception as exc:
                    log_failure(exc)
                    raise
                log_success(perf_counter() - started, None)
                return result

            return async_wrapper

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = perf_counter()
            queries_at_start = (
                len(connection.queries_log) if log_queries and settings.DEBUG else None
            )
            try:
                result = func(*args, **kwargs)
            except Exception as exc:
                log_failure(exc)
                raise
            count = (
                max(0, len(connection.queries_log) - queries_at_start)
                if queries_at_start is not None
                else None
            )
            log_success(perf_counter() - started, count)
            return result

        return wrapper

    return decorator
