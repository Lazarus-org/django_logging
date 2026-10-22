"""Real LogManager + Python logging test, without Django dependency."""

import logging
import os
import sys
import tempfile
import types
from contextlib import ExitStack
from pathlib import Path

package = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(package))
django = types.ModuleType("django")
django.__path__ = []
conf = types.ModuleType("django.conf")
conf.settings = types.SimpleNamespace(DJANGO_LOGGING={})
sys.modules["django"] = django
sys.modules["django.conf"] = conf

from django_logging.settings.conf import LogConfig, LogManager


def manager(folder, components):
    return LogManager(
        LogConfig(
            log_levels=["INFO", "ERROR"],
            log_dir=str(folder),
            log_file_formats={"INFO": "%(message)s", "ERROR": "%(message)s"},
            log_file_format_types={"INFO": "NORMAL", "ERROR": "NORMAL"},
            extra_log_files={"INFO": False, "ERROR": False},
            console_level="INFO",
            console_format="%(message)s",
            colorize_console=False,
            log_date_format="%Y-%m-%d",
            log_email_notifier_enable=False,
            log_email_notifier_log_levels=[],
            log_email_notifier_log_format=1,
            components=components,
        )
    )


from django_logging.settings import activation

root = logging.getLogger()
pkg = logging.getLogger("django_logging")
app = logging.getLogger("test06.audit")
original = {o: (list(o.handlers), o.level, o.propagate) for o in (root, pkg, app)}
try:
    with tempfile.TemporaryDirectory() as td, ExitStack() as resources:
        resources.callback(logging.shutdown)
        path = Path(td)
        custom = path / "audit.log"
        spec = {
            "formatters": {"audit_format": {"format": "%(message)s|%(levelname)s"}},
            "handlers": {
                "audit_handler": {
                    "class": "logging.FileHandler",
                    "filename": str(custom),
                    "formatter": "audit_format",
                }
            },
            "loggers": {
                "test06.audit": {
                    "handlers": ["audit_handler"],
                    "level": "INFO",
                    "propagate": False,
                }
            },
            "root_handlers": ["audit_handler"],
        }
        m = manager(path, spec)
        m.create_log_files()
        c = m.build_logging_dict()
        m.set_conf("additive")
        app.info("my audit")
        assert custom.read_text().strip() == "my audit|INFO", custom.read_text()
        assert (
            len([h for h in root.handlers if h.name == "dj_logging:audit_handler"]) == 1
        )
        m.set_conf("additive")
        app.info("exactly once")
        assert custom.read_text().count("exactly once") == 1
        # Built-in JSONFormatter structured_logging options must reach constructor.
        js = manager(path, {})
        js.log_config.log_file_format_types["INFO"] = "JSON"
        js.create_log_files()
        js.set_conf("isolated")
        formatters = [h.formatter for h in pkg.handlers if h.name == "dj_logging:info"]
        assert type(formatters[0]).__name__ == "JSONFormatter", formatters
        assert hasattr(formatters[0], "options")
        # State reset when custom logger removed.
        assert app.propagate is True
        print("ACTUAL_LOGMANAGER_SMOKE_PASS")
finally:
    # Close only handlers created here; restore existing root/package/app settings.
    for owner, (previous, level, prop) in original.items():
        for handler in list(owner.handlers):
            if handler not in previous:
                owner.removeHandler(handler)
                handler.close()
        for handler in previous:
            if handler not in owner.handlers:
                owner.addHandler(handler)
        owner.setLevel(level)
        owner.propagate = prop
    activation._CONTROLLED.clear()
