from django_logging.settings.conf import LogConfig, LogManager

from typing import List, Optional, Union, Dict


def set_logging(
        log_levels: List[str],
        log_dir: str,
        log_file_formats: Dict[str, Union[int, str]],
        console_level: str,
        console_format: Optional[Union[int, str]],
        colorize_console: bool,
        log_date_format: str,
        log_email_notifier_enable: bool,
        log_email_notifier_log_levels: List[str],
        log_email_notifier_log_format: Union[int, str]
):
    """
    Sets up the logging configuration.

    Args:
        log_levels (List[str]): A list of log levels to configure.
        log_dir (str): The directory where log files will be stored.
    """
    log_config = LogConfig(
        log_levels,
        log_dir,
        log_file_formats,
        console_level,
        console_format,
        colorize_console,
        log_date_format,
        log_email_notifier_enable,
        log_email_notifier_log_levels,
        log_email_notifier_log_format
    )
    log_manager = LogManager(log_config)
    log_manager.create_log_files()
    log_manager.set_conf()
