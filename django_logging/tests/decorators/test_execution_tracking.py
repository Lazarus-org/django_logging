import sys

import pytest
import logging
import time
from django.conf import settings
from django.db import connection

from django_logging.decorators import execution_tracker
from django_logging.tests.constants import PYTHON_VERSION, PYTHON_VERSION_REASON

pytestmark = [
    pytest.mark.decorators,
    pytest.mark.decorators_execution_tracking,
    pytest.mark.skipif(sys.version_info < PYTHON_VERSION, reason=PYTHON_VERSION_REASON),
]


@pytest.mark.django_db
class TestExecutionTracker:
    """
    Test suite for the `execution_tracker` decorator.
    """

    @execution_tracker(logging_level=logging.INFO)
    def sample_function(self, duration: float) -> str:
        """
        A sample function to test the performance logger decorator.

        Args:
        ----
            duration (float): The time in seconds for which the function will sleep.

        Returns:
        -------
            str: A success message after the function sleeps.
        """
        time.sleep(duration)
        return "Function executed"

    def test_execution_tracker_raises_error_on_invalid_attribute(self) -> None:
        """
        Test that the `execution_tracker` raises a ValueError when an invalid logging level and
         query threshold is provided.

        Asserts:
        -------
            - A `ValueError` is raised when an invalid logging level is passed.
        """
        with pytest.raises(ValueError, match="execution_tracker.logging_level"):

            @execution_tracker(logging_level="invalid", query_threshold="invalid")  # type: ignore
            def sample_function():
                pass

    def test_execution_tracker_raises_error_on_invalid_log_queries(self) -> None:
        """
        Test that the `execution_tracker` raises a ValueError when an invalid log_queries value is provided.

        Asserts:
        -------
            - A `ValueError` is raised when an invalid log_queries value is passed.
        """
        with pytest.raises(ValueError, match="execution_tracker.log_queries"):

            @execution_tracker(log_queries="invalid")  # type: ignore
            def sample_function():
                pass

    def test_execution_tracker_execution_time(self) -> None:
        """
        Test that the `execution_tracker` decorator correctly logs execution time.

        Asserts:
        -------
            - The decorated function logs its execution time and runs successfully.
        """
        start_time = time.time()
        result = self.sample_function(0.2)
        elapsed_time = time.time() - start_time

        assert (
            result == "Function executed"
        ), "The function did not return the expected message."
        assert elapsed_time >= 0.2, "The execution time was shorter than expected."

    def test_execution_tracker_logs_queries(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Test that the `execution_tracker` logs database queries when `log_queries` is enabled.

        Asserts:
        -------
            - The log contains information about the number of database queries when `log_queries` is enabled.
        """
        settings.DEBUG = True  # Simulate a DEBUG environment
        caplog.clear()

        @execution_tracker(logging_level=logging.INFO, log_queries=True)
        def sample_db_function():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return "DB function executed"

        sample_db_function()

        assert any(
            "Database Queries:" in record.message for record in caplog.records
        ), "Expected database queries to be logged."

    def test_execution_tracker_query_threshold_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Test that the `execution_tracker` logs a warning if the number of queries exceeds the query threshold.

        Asserts:
        -------
            - A warning is logged when the query count exceeds the specified threshold.
        """
        settings.DEBUG = True
        caplog.clear()

        @execution_tracker(
            logging_level=logging.INFO,
            log_queries=True,
            query_threshold=1,
            query_exceed_warning=True,
        )
        def sample_db_threshold_function():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.execute("SELECT 2")
            return "DB function executed"

        sample_db_threshold_function()

        assert any(
            "exceeded threshold" in record.message for record in caplog.records
        ), "Expected a warning for exceeding query threshold."

    def test_execution_tracker_logs_queries_debug_false(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Test that the `execution_tracker` logs a warning when `log_queries` is enabled
        but `DEBUG` is set to False.

        Asserts:
        -------
            - A warning is logged indicating that database queries are not tracked
              because `DEBUG` is set to False.
        """
        settings.DEBUG = False  # Simulate a production environment where DEBUG is False
        caplog.clear()

        @execution_tracker(logging_level=logging.INFO, log_queries=True)
        def sample_db_function():
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return "DB function executed"

        sample_db_function()

        assert any(
            "DEBUG mode is disabled, so database queries are not tracked"
            in record.message
            for record in caplog.records
        ), "Expected a warning about disabled query logging when DEBUG is False."

    def test_execution_tracker_error_handling(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """
        Test that the `execution_tracker` correctly logs errors when an exception is raised.

        Asserts:
        -------
            - The log contains an error message when the decorated function raises an exception.
        """

        @execution_tracker(logging_level=logging.ERROR)
        def sample_error_function():
            raise ValueError("Sample error")

        with pytest.raises(ValueError, match="Sample error"):
            sample_error_function()

        assert any(
            "Error executing function" in record.message for record in caplog.records
        ), "Expected an error message in the logs when an exception is raised."
