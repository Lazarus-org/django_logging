from django_logging.settings.conf import LogConfig, LogManager

from typing import List


def set_logging(log_levels: List[str],
                log_dir: str,
                log_email_notifier_enable: bool,
                log_email_notifier_log_levels: List[str]):
    """
    Sets up the logging configuration.

    Args:
        log_levels (List[str]): A list of log levels to configure.
        log_dir (str): The directory where log files will be stored.
    """
    log_config = LogConfig(log_levels, log_dir, log_email_notifier_enable, log_email_notifier_log_levels)
    log_manager = LogManager(log_config)
    log_manager.create_log_files()
    log_manager.set_conf()
