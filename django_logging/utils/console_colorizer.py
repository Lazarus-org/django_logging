from django_logging.constants.ansi_colors import LOG_LEVEL_COLORS, AnsiColors


def colorize_log_format(log_format: str, levelname: str) -> str:
    colors = AnsiColors()
    color_mapping = {
        "%(asctime)s": f"{colors.BRIGHT_BLUE}%(asctime)s{colors.RESET}",
        "%(created)f": f"{colors.BRIGHT_BLUE}%(created)f{colors.RESET}",
        "%(relativeCreated)d": f"{colors.MAGENTA}%(relativeCreated)d{colors.RESET}",
        "%(msecs)d": f"{colors.YELLOW}%(msecs)d{colors.RESET}",
        "%(levelname)s": f"{LOG_LEVEL_COLORS.get(levelname, '')}%(levelname)s{colors.RESET}",
        "%(levelno)d": f"{colors.RED}%(levelno)d{colors.RESET}",
        "%(exc_info)s": f"{colors.RED}%(exc_info)s{colors.RESET}",
        "%(exc_text)s": f"{colors.RED}%(exc_text)s{colors.RESET}",
        "%(name)s": f"{colors.BRIGHT_MAGENTA}%(name)s{colors.RESET}",
        "%(module)s": f"{colors.PINK}%(module)s{colors.RESET}",
        "%(stack_info)s": f"{colors.YELLOW}%(stack_info)s{colors.RESET}",
        "%(filename)s": f"{colors.YELLOW}%(filename)s{colors.RESET}",
        "%(pathname)s": f"{colors.CYAN}%(pathname)s{colors.RESET}",
        "%(lineno)d": f"{colors.LIGHT_PURPLE}%(lineno)d{colors.RESET}",
        "%(funcName)s": f"{colors.BRIGHT_BLUE}%(funcName)s{colors.RESET}",
        "%(process)d": f"{colors.MAGENTA}%(process)d{colors.RESET}",
        "%(processName)s": f"{colors.MAGENTA}%(processName)s{colors.RESET}",
        "%(thread)d": f"{colors.CYAN}%(thread)d{colors.RESET}",
        "%(threadName)s": f"{colors.BRIGHT_MAGENTA}%(threadName)s{colors.RESET}",
        "%(message)s": f"{colors.ITALIC}%(message)s{colors.RESET}",
        "%(context)s": f"{colors.MAGENTA}%(context)s{colors.RESET}",
    }

    for placeholder, colorized in color_mapping.items():
        log_format = log_format.replace(placeholder, colorized)

    return log_format
