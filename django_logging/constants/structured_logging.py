"""Options shared by the existing JSON, XML, and FLAT formatters."""

STRUCTURED_LOGGING_DEFAULTS = {
    "REDACT_FIELDS": (),
    "MAX_DEPTH": 8,
    "MAX_ITEMS": 100,
    "MAX_STRING_LENGTH": 4096,
    "MAX_EVENT_BYTES": 65536,
    "MAX_EXCEPTION_FRAMES": 32,
    "INCLUDE_EXTRA": True,
    "EXCEPTION_MODE": "traceback",  # traceback | type | omit
    "JSON_COMPACT": True,
    "XML_PRETTY": True,
}
