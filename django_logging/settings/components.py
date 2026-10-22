"""Pure, explicit extensions to the package's dictConfig-compatible presets.

The host's ``LOGGING`` dictionary is deliberately not read or modified
here. Names are never implicitly replaced: additions, replacements and
removals are separate operations so a typo cannot silently override a
package preset.

"""

from copy import deepcopy
from typing import Any, Mapping

SECTIONS = ("formatters", "filters", "handlers", "loggers")


class ComponentConfigurationError(ValueError):
    """An invalid or ambiguous DJANGO_LOGGING['COMPONENTS'] definition."""


def _names(value: Any, location: str) -> list[str]:
    if not isinstance(value, (list, tuple)) or any(
        not isinstance(name, str) or not name for name in value
    ):
        raise ComponentConfigurationError(f"{location} must be a list of names")
    if len(value) != len(set(value)):
        raise ComponentConfigurationError(f"{location} contains duplicate names")
    return list(value)


def validate_components(extensions: Any) -> None:
    """Validate the extension's shape without importing user code."""
    # Each branch validates a distinct part of the component schema.
    # pylint: disable=too-many-branches
    if not isinstance(extensions, dict):
        raise ComponentConfigurationError("COMPONENTS must be a dictionary")
    allowed = set(SECTIONS) | {
        "replace",
        "disable",
        "root_handlers",
        "package_handlers",
    }
    if any(not isinstance(key, str) for key in extensions):
        raise ComponentConfigurationError("COMPONENTS keys must be strings")
    unknown = set(extensions) - allowed
    if unknown:
        raise ComponentConfigurationError(f"Unknown COMPONENTS keys: {sorted(unknown)}")
    for category in (*SECTIONS, "replace", "disable"):
        value = extensions.get(category, {})
        if not isinstance(value, dict):
            raise ComponentConfigurationError(
                f"COMPONENTS.{category} must be a dictionary"
            )
        if category in ("replace", "disable"):
            if any(not isinstance(key, str) for key in value):
                raise ComponentConfigurationError(
                    f"COMPONENTS.{category} section names must be strings"
                )
            if set(value) - set(SECTIONS):
                raise ComponentConfigurationError(
                    f"COMPONENTS.{category} contains an unknown section"
                )
            for section, entries in value.items():
                if category == "disable":
                    _names(entries, f"COMPONENTS.disable.{section}")
                else:
                    _validate_definitions(entries, f"COMPONENTS.replace.{section}")
        else:
            _validate_definitions(value, f"COMPONENTS.{category}")
    for group in ("root_handlers", "package_handlers"):
        _names(extensions.get(group, []), f"COMPONENTS.{group}")


def _validate_definitions(definitions: Any, location: str) -> None:
    if not isinstance(definitions, dict):
        raise ComponentConfigurationError(f"{location} must be a dictionary")
    for name, spec in definitions.items():
        if not isinstance(name, str) or not name or not isinstance(spec, dict):
            raise ComponentConfigurationError(
                f"{location} must map nonempty names to dictionaries"
            )


def compile_components(presets: Mapping[str, Any], extensions: Any) -> dict:
    """Return a validated, independent logging configuration plus routing
    hints.

    Normal keys are standard dictConfig sections. Private ``_dj_*``
    metadata records explicitly requested bindings and is removed before
    dictConfig.

    """
    # Compile and validate the complete graph before activation can mutate logging.
    # pylint: disable=too-many-branches,too-many-statements
    validate_components(extensions)
    extensions = deepcopy(extensions)
    config = deepcopy(dict(presets))
    builtin_handler_names = list(config["handlers"])
    builtin_root_handlers = list(config["root"]["handlers"])
    for section in SECTIONS:
        target = config[section]
        for name, spec in extensions.get(section, {}).items():
            if name in target:
                raise ComponentConfigurationError(
                    f"COMPONENTS.{section}.{name} already exists; use replace.{section}"
                )
            target[name] = spec
        for name, spec in extensions.get("replace", {}).get(section, {}).items():
            if name not in presets[section]:
                raise ComponentConfigurationError(
                    f"COMPONENTS.replace.{section}.{name} is not a built-in preset"
                )
            target[name] = spec
        for name in extensions.get("disable", {}).get(section, []):
            if name not in target:
                raise ComponentConfigurationError(
                    f"COMPONENTS.disable.{section}.{name} does not exist"
                )
            del target[name]

    removed_handlers = set(presets["handlers"]) - set(config["handlers"])
    config["root"]["handlers"] = [
        name for name in builtin_root_handlers if name not in removed_handlers
    ]
    for logger_spec in config["loggers"].values():
        if "handlers" in logger_spec:
            logger_spec["handlers"] = [
                name for name in logger_spec["handlers"] if name not in removed_handlers
            ]

    explicit_root = extensions.get("root_handlers", [])
    explicit_package = extensions.get("package_handlers", [])
    for key, values in (
        ("root_handlers", explicit_root),
        ("package_handlers", explicit_package),
    ):
        missing = set(values) - set(config["handlers"])
        if missing:
            raise ComponentConfigurationError(
                f"COMPONENTS.{key} refers to unknown handlers: {sorted(missing)}"
            )
    config["root"]["handlers"] = list(
        dict.fromkeys(config["root"]["handlers"] + explicit_root)
    )

    # Check references before constructing objects, without importing user code.
    for name, handler in config["handlers"].items():
        if "class" not in handler and "()" not in handler:
            raise ComponentConfigurationError(
                f"Handler {name!r} requires 'class' or '()'"
            )
        if "class" in handler and "()" in handler:
            raise ComponentConfigurationError(
                f"Handler {name!r} cannot specify both 'class' and '()'"
            )
        formatter = handler.get("formatter")
        if formatter is not None and (
            not isinstance(formatter, str) or formatter not in config["formatters"]
        ):
            raise ComponentConfigurationError(
                f"Handler {name!r} refers to missing formatter {formatter!r}"
            )
        filters = _names(handler.get("filters", []), f"handler {name!r}.filters")
        missing = set(filters) - set(config["filters"])
        if missing:
            raise ComponentConfigurationError(
                f"Handler {name!r} refers to missing filters: {sorted(missing)}"
            )
    for name, logger in config["loggers"].items():
        if set(logger) - {"handlers", "filters", "level", "propagate"}:
            raise ComponentConfigurationError(
                f"Logger {name!r} contains unsupported options"
            )
        refs = _names(logger.get("handlers", []), f"logger {name!r}.handlers")
        missing = set(refs) - set(config["handlers"])
        if missing:
            raise ComponentConfigurationError(
                f"Logger {name!r} refers to missing handlers: {sorted(missing)}"
            )
        filter_refs = _names(logger.get("filters", []), f"logger {name!r}.filters")
        missing_filters = set(filter_refs) - set(config["filters"])
        if missing_filters:
            raise ComponentConfigurationError(
                f"Logger {name!r} refers to missing filters: {sorted(missing_filters)}"
            )
        if "propagate" in logger and not isinstance(logger["propagate"], bool):
            raise ComponentConfigurationError(
                f"Logger {name!r}.propagate must be boolean"
            )
    if not set(config["root"]["handlers"]) <= set(config["handlers"]):
        raise ComponentConfigurationError("Root refers to missing handlers")

    explicit_loggers = set(extensions.get("loggers", {})) | set(
        extensions.get("replace", {}).get("loggers", {})
    )
    if "django_logging" in explicit_loggers or "root" in explicit_loggers:
        raise ComponentConfigurationError(
            "Use package_handlers/root_handlers instead of overriding managed root loggers"
        )
    config["_dj_explicit_root_handlers"] = list(explicit_root)
    config["_dj_explicit_loggers"] = sorted(
        explicit_loggers - set(extensions.get("disable", {}).get("loggers", []))
    )
    config["_dj_package_handlers"] = [
        name for name in builtin_handler_names if name in config["handlers"]
    ] + [name for name in explicit_package if name not in builtin_handler_names]
    return config
