from django_logging.settings.conf import LogConfig, LogManager


def set_logging(log_levels, log_dir):
    log_config = LogConfig(log_levels, log_dir)
    log_manager = LogManager(log_config)
    log_manager.create_log_files()
    log_manager.set_conf()
