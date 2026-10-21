"""Regressions for SQL history preservation and awaited coroutine tracking."""

import asyncio
import inspect
import logging
from unittest.mock import patch

import pytest
from django.db import connection
from django.test import override_settings

from django_logging.decorators import execution_tracker


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_execution_tracker_preserves_existing_query_history(caplog):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 100")
    before = list(connection.queries_log)
    assert before

    @execution_tracker(log_queries=True)
    def action():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 101")
        return "done"

    assert action() == "done"
    assert list(connection.queries_log)[: len(before)] == before
    assert any(
        "Database Queries: 1 queries" in record.message for record in caplog.records
    )


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_execution_tracker_query_threshold_zero_is_supported(caplog):
    @execution_tracker(log_queries=True, query_threshold=0, query_exceed_warning=True)
    def action():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    action()
    assert any("exceeded threshold (0)" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_execution_tracker_measures_awaited_work():
    entered = asyncio.Event()
    finish = asyncio.Event()

    @execution_tracker()
    async def action():
        entered.set()
        await finish.wait()
        return 42

    assert inspect.iscoroutinefunction(action)
    with patch("django_logging.decorators.execution_tracking.logger") as mocked:
        task = asyncio.create_task(action())
        await entered.wait()
        assert not task.done()
        assert not mocked.log.called
        finish.set()
        assert await task == 42
        assert mocked.log.call_count == 1
        assert "Performance Metrics" in mocked.log.call_args.args[1]


def test_async_query_counting_is_explicitly_unsupported():
    with pytest.raises(ValueError, match="async"):

        @execution_tracker(log_queries=True)
        async def action():
            return None


@pytest.mark.asyncio
async def test_async_error_preserves_original_exception():
    @execution_tracker()
    async def action():
        raise RuntimeError("test failure")

    with patch("django_logging.decorators.execution_tracking.logger") as mocked:
        with pytest.raises(RuntimeError, match="test failure"):
            await action()
        mocked.error.assert_called_once()


def test_disabled_metrics_skip_message_work_and_follow_level_changes():
    @execution_tracker()
    def action():
        return 42

    with (
        patch("django_logging.decorators.execution_tracking.logger") as log,
        patch(
            "django_logging.decorators.execution_tracking.format_elapsed_time"
        ) as format_time,
        patch("django_logging.decorators.execution_tracking.os") as operating_system,
    ):
        log.isEnabledFor.return_value = False
        assert action() == 42
        format_time.assert_not_called()
        operating_system.path.abspath.assert_not_called()
        log.log.assert_not_called()
        log.isEnabledFor.return_value = True
        assert action() == 42
        format_time.assert_called_once()
        log.log.assert_called_once()


@pytest.mark.asyncio
async def test_disabled_async_metrics_skip_message_formatting():
    @execution_tracker()
    async def action():
        return 42

    with (
        patch("django_logging.decorators.execution_tracking.logger") as log,
        patch(
            "django_logging.decorators.execution_tracking.format_elapsed_time"
        ) as format_time,
    ):
        log.isEnabledFor.return_value = False
        assert await action() == 42
        format_time.assert_not_called()
        log.log.assert_not_called()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_disabled_metrics_keep_query_threshold_warning(caplog):
    @execution_tracker(query_threshold=0, log_queries=True, query_exceed_warning=True)
    def action():
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    caplog.set_level(
        logging.WARNING, logger="django_logging.decorators.execution_tracking"
    )
    with patch(
        "django_logging.decorators.execution_tracking.format_elapsed_time"
    ) as format_time:
        action()
        format_time.assert_not_called()
    assert any("exceeded threshold (0)" in record.message for record in caplog.records)
    assert not any("Performance Metrics" in record.message for record in caplog.records)


@override_settings(DEBUG=False)
def test_disabled_metrics_keep_debug_disabled_warning():
    @execution_tracker(log_queries=True)
    def action():
        return "ok"

    with patch("django_logging.decorators.execution_tracking.logger") as log:
        log.isEnabledFor.return_value = False
        assert action() == "ok"
        log.warning.assert_called_once()
        assert "DEBUG mode is disabled" in log.warning.call_args.args[0]
        log.log.assert_not_called()
