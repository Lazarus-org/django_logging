"""Regression tests for temporary isolated package-logger setup."""

import logging
from unittest import mock

import pytest

from django_logging.utils.context_manager import config_setup


@pytest.fixture
def saved_logging():
    root = logging.getLogger()
    package = logging.getLogger("django_logging")
    old_root = (list(root.handlers), root.level, root.propagate)
    old_package = (list(package.handlers), package.level, package.propagate)
    for handler in list(package.handlers):
        if getattr(handler, "_dj_logging_owned", False):
            package.removeHandler(handler)
    yield root, package
    for handler in list(package.handlers):
        if handler not in old_package[0]:
            package.removeHandler(handler)
            handler.close()
    for handler in old_package[0]:
        if handler not in package.handlers:
            package.addHandler(handler)
    package.setLevel(old_package[1])
    package.propagate = old_package[2]
    for handler in list(root.handlers):
        if handler not in old_root[0]:
            root.removeHandler(handler)
    for handler in old_root[0]:
        if handler not in root.handlers:
            root.addHandler(handler)
    root.setLevel(old_root[1])
    root.propagate = old_root[2]


def test_config_setup_requires_auto_init_disabled():
    with mock.patch(
        "django_logging.utils.context_manager.is_auto_initialization_enabled",
        return_value=True,
    ):
        with pytest.raises(ValueError, match="AUTO_INITIALIZATION_ENABLE"):
            with config_setup():
                pass


def test_config_setup_restores_only_package_logger(saved_logging, tmp_path):
    root, package = saved_logging
    sentinel = logging.NullHandler()
    root.addHandler(sentinel)
    pkg_sentinel = logging.NullHandler()
    package.addHandler(pkg_sentinel)
    root_before = list(root.handlers)
    package_before = list(package.handlers)
    level_before, propagate_before = package.level, package.propagate
    from django_logging.tests.settings.test_logging_isolation import config_for

    conf = config_for(tmp_path)
    with (
        mock.patch(
            "django_logging.utils.context_manager.is_auto_initialization_enabled",
            return_value=False,
        ),
        mock.patch(
            "django_logging.utils.context_manager.get_config", return_value=conf
        ),
    ):
        with config_setup() as manager:
            assert manager is not None
            assert len(package.handlers) > len(package_before)
            assert list(root.handlers) == root_before
            assert package.propagate is False
        assert list(root.handlers) == root_before
        assert list(package.handlers) == package_before
        assert package.level == level_before
        assert package.propagate == propagate_before


def test_config_setup_restores_after_error(saved_logging, tmp_path):
    root, package = saved_logging
    before = list(package.handlers), package.level, package.propagate
    from django_logging.tests.settings.test_logging_isolation import config_for

    with (
        mock.patch(
            "django_logging.utils.context_manager.is_auto_initialization_enabled",
            return_value=False,
        ),
        mock.patch(
            "django_logging.utils.context_manager.get_config",
            return_value=config_for(tmp_path),
        ),
    ):
        with pytest.raises(RuntimeError, match="simulated"):
            with config_setup():
                raise RuntimeError("simulated")
    assert (list(package.handlers), package.level, package.propagate) == before
