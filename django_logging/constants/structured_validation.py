"""Validation for DJANGO_LOGGING['STRUCTURED_LOGGING'].

No Django dependencies: validation is reusable at runtime and by system
checks.

"""

from django_logging.constants.structured_logging import STRUCTURED_LOGGING_DEFAULTS


def structured_logging_errors(config: object) -> list[str]:
    # Exact built-in integers reject bools and integer subclasses.
    # pylint: disable=unidiomatic-typecheck
    prefix = "DJANGO_LOGGING['STRUCTURED_LOGGING']"
    if not isinstance(config, dict):
        return [f"{prefix} must be a dictionary."]
    errors = []
    for key in config:
        if key not in STRUCTURED_LOGGING_DEFAULTS:
            errors.append(f"{prefix} contains unknown option {key!r}.")

    bounded_integers = {
        "MAX_DEPTH": (1, 32),
        "MAX_ITEMS": (1, 1000),
        "MAX_STRING_LENGTH": (1, 1_048_576),
        "MAX_EVENT_BYTES": (96, 1_048_576),
        "MAX_EXCEPTION_FRAMES": (1, 128),
    }
    for key, (minimum, maximum) in bounded_integers.items():
        value = config.get(key, STRUCTURED_LOGGING_DEFAULTS[key])
        if type(value) is not int or not minimum <= value <= maximum:
            errors.append(
                f"{prefix}['{key}'] must be an integer between {minimum} and {maximum}."
            )

    for key in ("INCLUDE_EXTRA", "JSON_COMPACT", "XML_PRETTY"):
        value = config.get(key, STRUCTURED_LOGGING_DEFAULTS[key])
        if not isinstance(value, bool):
            errors.append(f"{prefix}['{key}'] must be a boolean.")
    mode = config.get("EXCEPTION_MODE", STRUCTURED_LOGGING_DEFAULTS["EXCEPTION_MODE"])
    if mode not in ("traceback", "type", "omit"):
        errors.append(
            f"{prefix}['EXCEPTION_MODE'] must be 'traceback', 'type', or 'omit'."
        )
    fields = config.get("REDACT_FIELDS", ())
    if not isinstance(fields, (list, tuple, set, frozenset)) or any(
        not isinstance(item, str) or not item.strip() or len(item) > 256
        for item in fields
    ):
        errors.append(
            f"{prefix}['REDACT_FIELDS'] must be a collection of non-empty strings up to 256 characters."
        )
    return errors


def resolve_structured_logging(config: object = None) -> dict:
    user = {} if config is None else config
    errors = structured_logging_errors(user)
    if errors:
        raise ValueError("; ".join(errors))
    return {**STRUCTURED_LOGGING_DEFAULTS, **user}
