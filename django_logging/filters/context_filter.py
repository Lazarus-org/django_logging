from logging import Filter, LogRecord
from typing import Any, Dict

from django_logging.contextvar import manager


class ContextVarFilter(Filter):
    """A logging filter that merges context variables into the log record.

    This filter retrieves the current context variables, combines them with any existing
    bound logger context, and adds the merged context to the log record's 'context' attribute.

    Attributes:
        N/A

    Methods:
        filter(record: LogRecord) -> bool:
            Merges context variables into the log record before formatting.

    """

    def filter(self, record: LogRecord) -> bool:
        """Merge context variables into the log record.

        Args:
            record (LogRecord): The logging record to be processed.

        Returns:
            bool: Always returns True to allow the record to be logged.

        This method checks if the log record already has a 'context' attribute. It then merges
        the current context variables (retrieved via `contextvar.get_merged_context`) into the log record.

        """
        bound_logger_context: Dict[str, Any] = getattr(record, "context", {})

        # Merge the context variables and set them in the record
        record.context = manager.get_merged_context(bound_logger_context) or ""

        return True
