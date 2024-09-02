from django_logging.constants.ansi_colors import LOG_LEVEL_COLORS, AnsiColors
from django_logging.constants.config_types import LogLevel


def colorize_log_format(log_format: str, levelname: str) -> str:
    colors = AnsiColors()
    color_mapping = {
        "%(asctime)s": f"{colors.CYAN}%(asctime)s{colors.RESET}",
        "%(created)f": f"{colors.BRIGHT_BLUE}%(created)f{colors.RESET}",
        "%(relativeCreated)d": f"{colors.MAGENTA}%(relativeCreated)d{colors.RESET}",
        "%(msecs)d": f"{colors.YELLOW}%(msecs)d{colors.RESET}",
        "%(levelname)s": f"{LOG_LEVEL_COLORS.get(levelname, '')}%(levelname)s{colors.RESET}",
        "%(levelno)d": f"{colors.RED}%(levelno)d{colors.RESET}",
        "%(name)s": f"{colors.BRIGHT_MAGENTA}%(name)s{colors.RESET}",
        "%(module)s": f"{colors.BRIGHT_GREEN}%(module)s{colors.RESET}",
        "%(filename)s": f"{colors.YELLOW}%(filename)s{colors.RESET}",
        "%(pathname)s": f"{colors.CYAN}%(pathname)s{colors.RESET}",
        "%(lineno)d": f"{colors.RED}%(lineno)d{colors.RESET}",
        "%(funcName)s": f"{colors.BRIGHT_BLUE}%(funcName)s{colors.RESET}",
        "%(process)d": f"{colors.MAGENTA}%(process)d{colors.RESET}",
        "%(thread)d": f"{colors.CYAN}%(thread)d{colors.RESET}",
        "%(threadName)s": f"{colors.BRIGHT_MAGENTA}%(threadName)s{colors.RESET}",
        "%(message)s": f"{colors.GRAY}%(message)s{colors.RESET}",
    }

    for placeholder, colorized in color_mapping.items():
        log_format = log_format.replace(placeholder, colorized)

    return log_format
