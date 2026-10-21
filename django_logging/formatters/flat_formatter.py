"""Unambiguous single-line key/value formatter."""

import json
from logging import LogRecord

from django_logging.formatters.base import BaseStructuredFormatter


def _flat_value(value: object) -> str:
    if isinstance(value, str):
        # Keep existing field='value' presentation while escaping separators,
        # quotes and all control characters; never emit literal line breaks.
        return json.dumps(value, ensure_ascii=True)[1:-1].replace("'", "\\'")
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


class FLATFormatter(BaseStructuredFormatter):
    def format(self, record: LogRecord) -> str:
        event = self._event(record)
        result = " ".join(
            f"{key}='{_flat_value(value)}'" for key, value in event.items()
        )
        if len(result.encode("utf-8")) > self.options["MAX_EVENT_BYTES"]:
            return "message='[log event omitted: too large]'"
        return result
