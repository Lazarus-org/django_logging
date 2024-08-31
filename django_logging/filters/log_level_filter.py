import logging


class LoggingLevelFilter(logging.Filter):
    """Filters log records based on their logging level.

    This filter is used to prevent log records from being written to log
    files intended for lower log levels. For example, if we have
    separate log files for DEBUG, INFO, WARNING, and ERROR levels, this
    filter ensures that a log record with level ERROR is only written to
    the ERROR log file, and not to the DEBUG, INFO or WARNING log files.

    """

    def __init__(self, logging_level: int):
        """Initializes a LoggingLevelFilter instance.

        Args:
            logging_level: The logging level to filter on (e.g. logging.DEBUG, logging.INFO, etc.).

        Returns:
            None

        """
        super().__init__()
        self.logging_level = logging_level

    def filter(self, record: logging.LogRecord) -> bool:
        """Filters a log record based on its level.

        Args:
            record: The log record to filter.

        Returns:
            True if the log record's level matches the specified logging level, False otherwise.

        """
        return record.levelno == self.logging_level
