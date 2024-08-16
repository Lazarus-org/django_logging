import logging
import logging.config
import os


class LogConfig:

    def __init__(
            self,
            log_levels,
            log_dir,
    ):
        self.log_levels = log_levels
        self.log_dir = log_dir


class LogManager:

    def __init__(self, log_config):

        self.log_config = log_config
        self.log_files = {}

    def create_log_files(self):

        for log_level in self.log_config.log_levels:
            log_file_path = os.path.join(
                self.log_config.log_dir, f"{log_level.lower()}.log"
            )
            os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
            if not os.path.exists(log_file_path):
                open(log_file_path, "w").close()
            self.log_files[log_level] = log_file_path

    def get_log_file(self, log_level):
        return self.log_files.get(log_level)

    def set_conf(self):

        handlers = {
            level.lower(): {
                "class": "logging.FileHandler",
                "filename": log_file,
                "formatter": "default",
                "level": level,
            }
            for level, log_file in self.log_files.items()
        }
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "console",
            "level": "DEBUG",
        }

        loggers = {
            level.lower(): {
                "level": level,
                "handlers": [level.lower()],
                "propagate": False,
            }
            for level in self.log_config.log_levels
        }

        config = {
            "version": 1,
            "handlers": handlers,
            "loggers": loggers,
            "root": {"level": "DEBUG", "handlers": list(handlers.keys())},
            "disable_existing_loggers": False,
        }

        logging.config.dictConfig(config)
