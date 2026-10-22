"""Non-destructive activation of dictConfig component definitions.

Python's dictConfig does not have an additive/non-global apply
operation. We reuse its actual component constructors, but attach only
handlers owned by this package and only change a named application
logger when explicitly asked.

"""

import logging
import logging.config
from collections.abc import Callable
from contextlib import contextmanager
from threading import RLock
from typing import Any

_LOCK = RLock()
# Original settings for logger namespaces explicitly controlled by COMPONENTS.
_CONTROLLED: dict[str, tuple[int, bool]] = {}
_CONTROLLED_FILTERS: dict[str, list[logging.Filter]] = {}
# Keep targets and other dependent handlers alive and close them on replacement.
# They may not be attached directly to any logger (e.g. MemoryHandler.target).
_ACTIVE_HANDLERS: tuple[logging.Handler, ...] = ()


def _required_components(
    config: dict, mode: str
) -> tuple[set[str], set[str], set[str]]:
    """Find the components reachable from active logger attachments.

    A declared handler is not necessarily installed. Constructing
    unattached handlers can open files or invoke arbitrary application
    factories, even though no logging event will reach them. Follow
    standard handler-to-handler references (e.g. MemoryHandler.target)
    before building anything.

    """
    selected = set(config["_dj_package_handlers"])
    if mode == "additive":
        explicit_root = set(config.get("_dj_explicit_root_handlers", ()))
        selected.update(
            name
            for name in config["root"]["handlers"]
            if name != "console" or name in explicit_root
        )

    named_filters: set[str] = set()
    for name in config.get("_dj_explicit_loggers", ()):
        spec = config["loggers"][name]
        selected.update(spec.get("handlers", ()))
        named_filters.update(spec.get("filters", ()))

    pending = list(selected)
    while pending:
        name = pending.pop()
        spec = config["handlers"][name]
        target = spec.get("target")
        if (
            isinstance(target, str)
            and target in config["handlers"]
            and target not in selected
        ):
            selected.add(target)
            pending.append(target)
        references = spec.get("handlers", ())
        if isinstance(references, (tuple, list)):
            for reference in references:
                if (
                    isinstance(reference, str)
                    and reference in config["handlers"]
                    and reference not in selected
                ):
                    selected.add(reference)
                    pending.append(reference)

    formatters = {
        config["handlers"][name]["formatter"]
        for name in selected
        if "formatter" in config["handlers"][name]
    }
    filters = named_filters | {
        filter_name
        for name in selected
        for filter_name in config["handlers"][name].get("filters", ())
    }
    return selected, formatters, filters


def _objects(
    config: dict, resolver: Callable[[str], Any], *, mode: str
) -> tuple[dict[str, logging.Handler], dict[str, logging.Filter]]:
    """Build active components without touching the application's loggers."""
    # Dependency-ordered construction shares one failure-cleanup boundary.
    # pylint: disable=too-many-branches
    active_handlers, active_formatters, active_filters = _required_components(
        config, mode
    )
    entries = {
        "version": 1,
        "formatters": {
            name: spec
            for name, spec in config["formatters"].items()
            if name in active_formatters
        },
        "filters": {
            name: spec
            for name, spec in config["filters"].items()
            if name in active_filters
        },
        "handlers": {
            name: spec
            for name, spec in config["handlers"].items()
            if name in active_handlers
        },
    }
    configurator = logging.config.DictConfigurator(entries)
    constructed: dict[str, logging.Handler] = {}
    try:
        for name in configurator.config["formatters"]:
            spec = configurator.config["formatters"][name]
            # Preserve LogManager's resolver hook while reusing the standard
            # formatter and filter constructors.
            path = spec.get("()", spec.get("class"))
            if isinstance(path, str):
                resolver(path)
            configurator.config["formatters"][name] = configurator.configure_formatter(
                spec
            )
        for name in configurator.config["filters"]:
            spec = configurator.config["filters"][name]
            factory = spec.get("()")
            if isinstance(factory, str):
                resolver(factory)
            configurator.config["filters"][name] = configurator.configure_filter(spec)
        named_filters = dict(configurator.config["filters"])
        # MemoryHandler and QueueHandler-style references require their target
        # handler to be constructed first.
        pending = dict(entries["handlers"])
        while pending:
            ready = []
            for name, spec in pending.items():
                dependencies = set()
                target = spec.get("target")
                if isinstance(target, str) and target in entries["handlers"]:
                    dependencies.add(target)
                refs = spec.get("handlers", ())
                if isinstance(refs, (list, tuple)):
                    dependencies.update(
                        v
                        for v in refs
                        if isinstance(v, str) and v in entries["handlers"]
                    )
                if dependencies <= constructed.keys():
                    ready.append(name)
            if not ready:
                raise ValueError(
                    "Handler dependency cycle or unresolved handler target"
                )
            for name in ready:
                spec = configurator.config["handlers"][name]
                path = spec.get("class", spec.get("()"))
                if isinstance(path, str):
                    resolver(path)
                handler = configurator.configure_handler(spec)
                if not isinstance(handler, logging.Handler):
                    raise TypeError(
                        f"Handler {name!r} factory did not produce a logging.Handler"
                    )
                handler.name = f"dj_logging:{name}"
                handler._dj_logging_owned = True
                constructed[name] = handler
                configurator.config["handlers"][name] = handler
                del pending[name]
        return constructed, named_filters
    except Exception:
        for handler in reversed(list(constructed.values())):
            handler.close()
        raise


def activate(
    config: dict,
    *,
    mode: str,
    resolver: Callable[[str], Any],
    close_previous: bool = True,
) -> None:
    """Atomically replace package-owned attachments; preserve host handlers.

    Named logger overrides explicitly control level/propagate, and those
    original values are restored if a later configuration no longer
    manages the logger. Legacy replace_root remains handled by
    dictConfig instead.

    """
    # Keep routing changes and rollback in one explicit logging transaction.
    # pylint: disable=too-many-branches,too-many-statements
    if mode not in ("additive", "isolated"):
        raise ValueError(f"Unsupported owned logging mode {mode!r}")
    handlers, filters = _objects(config, resolver, mode=mode)
    managed_names = config.get("_dj_explicit_loggers", [])
    with _LOCK:
        global _CONTROLLED, _ACTIVE_HANDLERS  # pylint: disable=global-statement
        root = logging.getLogger()
        package = logging.getLogger("django_logging")
        old_managed = dict(_CONTROLLED)
        old_filters = dict(_CONTROLLED_FILTERS)
        target_names = set(managed_names) | set(old_managed)
        # Also recover handlers attached in earlier checkpoints before this
        # module tracked ownership explicitly.
        owners = {root, package}
        owners.update(logging.getLogger(name) for name in target_names)
        old_handlers = {
            h
            for owner in owners
            for h in owner.handlers
            if getattr(h, "_dj_logging_owned", False)
        }
        # Include dependent handlers that are reachable through another
        # handler, but are not directly attached to any logger.
        old_to_close = tuple(dict.fromkeys((*_ACTIVE_HANDLERS, *old_handlers)))
        before = {
            owner: (
                list(owner.handlers),
                list(owner.filters),
                owner.level,
                owner.propagate,
            )
            for owner in owners
        }
        updated_originals = dict(old_managed)
        try:
            for owner in owners:
                for handler in old_handlers:
                    owner.removeHandler(handler)
            for name, (level, propagate) in old_managed.items():
                logger = logging.getLogger(name)
                logger.setLevel(level)
                logger.propagate = propagate
                for old_filter in old_filters.get(name, ()):  # only our own
                    logger.removeFilter(old_filter)
            package.setLevel(logging.DEBUG)
            package.propagate = False
            for name in config["_dj_package_handlers"]:
                package.addHandler(handlers[name])
            if mode == "additive":
                explicit_root = set(config.get("_dj_explicit_root_handlers", ()))
                for name in config["root"]["handlers"]:
                    if name != "console" or name in explicit_root:
                        root.addHandler(handlers[name])
            installed_filters = {}
            for name in managed_names:
                logger = logging.getLogger(name)
                if name not in updated_originals:
                    updated_originals[name] = (logger.level, logger.propagate)
                spec = config["loggers"][name]
                for handler_name in spec.get("handlers", ()):
                    logger.addHandler(handlers[handler_name])
                installed_filters[name] = [
                    filters[filter_name] for filter_name in spec.get("filters", ())
                ]
                for log_filter in installed_filters[name]:
                    logger.addFilter(log_filter)
                if "level" in spec:
                    logger.setLevel(spec["level"])
                if "propagate" in spec:
                    logger.propagate = spec["propagate"]
            _CONTROLLED = {name: updated_originals[name] for name in managed_names}
            _CONTROLLED_FILTERS.clear()
            _CONTROLLED_FILTERS.update(installed_filters)
            _ACTIVE_HANDLERS = tuple(handlers.values())
        except Exception:
            for owner, (
                original_handlers,
                original_filters,
                level,
                propagate,
            ) in before.items():
                for handler in list(owner.handlers):
                    owner.removeHandler(handler)
                for handler in original_handlers:
                    owner.addHandler(handler)
                for log_filter in list(owner.filters):
                    owner.removeFilter(log_filter)
                for log_filter in original_filters:
                    owner.addFilter(log_filter)
                owner.setLevel(level)
                owner.propagate = propagate
            for handler in handlers.values():
                handler.close()
            raise
        if close_previous:
            for old in reversed(old_to_close):
                old.close()


@contextmanager
def temporary_activation(config: dict, *, resolver: Callable[[str], Any]):
    """Restore the complete logger graph and ownership state after a scope.

    Keep previous handlers alive while temporary handlers are active.
    The reentrant activation lock serializes setup, teardown, and nested
    scopes.

    """
    global _CONTROLLED, _ACTIVE_HANDLERS  # pylint: disable=global-statement
    with _LOCK:
        owners = {logging.getLogger(), logging.getLogger("django_logging")}
        owners.update(
            logging.getLogger(name)
            for name in set(_CONTROLLED) | set(config.get("_dj_explicit_loggers", ()))
        )
        before = {
            owner: (
                list(owner.handlers),
                list(owner.filters),
                owner.level,
                owner.propagate,
            )
            for owner in owners
        }
        controlled = dict(_CONTROLLED)
        filters = dict(_CONTROLLED_FILTERS)
        active = _ACTIVE_HANDLERS
        try:
            activate(config, mode="isolated", resolver=resolver, close_previous=False)
            yield
        finally:
            temporary = tuple(
                handler for handler in _ACTIVE_HANDLERS if handler not in active
            )
            for owner, (handlers, original_filters, level, propagate) in before.items():
                owner.handlers[:] = handlers
                owner.filters[:] = original_filters
                owner.setLevel(level)
                owner.propagate = propagate
            _CONTROLLED = controlled
            _CONTROLLED_FILTERS.clear()
            _CONTROLLED_FILTERS.update(filters)
            _ACTIVE_HANDLERS = active
            for handler in reversed(temporary):
                handler.close()


def forget_controlled_loggers() -> None:
    """Discard additive ownership after explicit global dictConfig takeover."""
    global _CONTROLLED, _ACTIVE_HANDLERS  # pylint: disable=global-statement
    with _LOCK:
        _CONTROLLED = {}
        _CONTROLLED_FILTERS.clear()
        _ACTIVE_HANDLERS = ()
