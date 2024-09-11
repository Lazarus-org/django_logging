import logging
import os
import time
from functools import wraps
from typing import Callable, Optional

from django.conf import settings
from django.db import connection

from django_logging.validators.config_validators import (
    validate_boolean_setting,
    validate_integer_setting,
)

logger = logging.getLogger(__name__)


# pylint: disable=too-many-locals
def execution_tracker(
    logging_level: int = logging.INFO,
    log_queries: bool = False,
    query_threshold: Optional[int] = None,
    query_exceed_warning: bool = False,
) -> Callable:
    """Decorator to log execution time, number of database queries, and
    arguments for a function, along with detailed function information (module,
    file, and line number).

    This decorator allows you to track the performance of a function by logging its execution time,
    the number of database queries made (if DEBUG is True and log_queries is enabled), and function
    arguments. It also logs a warning if the number of queries exceeds the specified threshold.

    Args:
        logging_level (int): The logging level at which to log the performance details (default is logging.INFO).
        log_queries (bool): Whether to log database queries. If set to True, and DEBUG is True, the number of
                            queries will be included in the logs (default is False).
        query_threshold (Optional[int]): Optional threshold for the number of database queries. If exceeded,
                                         a warning will be logged (default is None).
        query_exceed_warning (bool): Whether to log a warning message if number of queries exceeded the threshold.

    Returns:
        Callable: A decorator that logs performance details.

    Raises:
        ValueError: If any of the provided settings (logging_level, query_threshold, or log_queries) are invalid.

    """
    errors = []
    errors.extend(
        validate_integer_setting(logging_level, "execution_tracker.logging_level")
    )
    errors.extend(
        validate_boolean_setting(log_queries, "execution_tracker.log_queries")
    )
    if query_threshold:
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
        raise ValueError(errors[0])  # raises the first error to be fixed

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Check if DEBUG is True and log_queries is enabled; if not, ignore query tracking
            if settings.DEBUG and log_queries:
                connection.queries_log.clear()

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Calculate execution time
                elapsed_time = time.time() - start_time
                minutes, seconds = divmod(elapsed_time, 60)

                # Get detailed function information
                module_name = func.__module__
                function_name = func.__qualname__
                file_path = os.path.abspath(func.__code__.co_filename)
                line_number = func.__code__.co_firstlineno

                time_message = f"{minutes} minute(s) and {seconds:.4f} second(s)"
                log_message = (
                    f"Performance Metrics for Function: '{function_name}'\n"
                    f"  Module: {module_name}\n"
                    f"  File: {file_path}, Line: {line_number}\n"
                    f"  Execution Time: {time_message}"
                )

                # If log_queries is enabled and DEBUG is True, include number of queries
                if settings.DEBUG and log_queries:
                    num_queries = len(connection.queries_log)
                    log_message += f"\n  Database Queries: {num_queries} queries "

                    # Log query threshold warning separately, if applicable
                    if query_threshold and num_queries > query_threshold:
                        log_message += f"(exceeds threshold of ({query_threshold}))"
                        if query_exceed_warning:
                            logger.warning(
                                "Number of database queries (%s) "
                                "exceeded threshold (%s) for function '%s'",
                                num_queries,
                                query_threshold,
                                function_name,
                            )
                elif log_queries and not settings.DEBUG:
                    logger.warning(
                        "DEBUG mode is disabled, so database queries are not tracked. "
                        "To include number of queries, set DEBUG to True in your django settings."
                    )

                # Log the performance metrics
                logger.log(logging_level, log_message)

                return result

            except Exception as e:
                logger.error(
                    "Error executing function '%s': %s",
                    func.__qualname__,
                    str(e),
                    exc_info=True,
                )
                raise

        return wrapper

    return decorator
