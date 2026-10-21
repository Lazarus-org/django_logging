"""Compact, structured JSON logging for line-oriented collectors."""

import json
from logging import LogRecord

from django_logging.formatters.base import BaseStructuredFormatter


class JSONFormatter(BaseStructuredFormatter):
    """Serialize typed context/extra fields without altering the log message.

    No attempt is made to infer key=value fields from free-form
    messages.

    """

    def format(self, record: LogRecord) -> str:
        data = self._event(record)
        options = {"ensure_ascii": False, "allow_nan": False}
        if self.options["JSON_COMPACT"]:
            options["separators"] = (",", ":")
        else:
            options["indent"] = 2
        result = json.dumps(data, **options)
        if len(result.encode("utf-8")) > self.options["MAX_EVENT_BYTES"]:
            # Never partially cut a JSON object or emit oversized diagnostics.
            result = json.dumps(
                {"message": "[log event omitted: too large]"}, separators=(",", ":")
            )
        return result
