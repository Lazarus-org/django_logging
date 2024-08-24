from django_logging.constants.ansi_colors import LOG_LEVEL_COLORS, AnsiColors


def colorize_log_format(log_format, levelname):
    color_mapping = {
        "%(asctime)s": f"{AnsiColors.CYAN}%(asctime)s{AnsiColors.RESET}",
        "%(created)f": f"{AnsiColors.BRIGHT_BLUE}%(created)f{AnsiColors.RESET}",
        "%(relativeCreated)d": f"{AnsiColors.MAGENTA}%(relativeCreated)d{AnsiColors.RESET}",
        "%(msecs)d": f"{AnsiColors.YELLOW}%(msecs)d{AnsiColors.RESET}",
        "%(levelname)s": f"{LOG_LEVEL_COLORS.get(levelname, '')}%(levelname)s{AnsiColors.RESET}",
        "%(levelno)d": f"{AnsiColors.RED}%(levelno)d{AnsiColors.RESET}",
        "%(name)s": f"{AnsiColors.BRIGHT_MAGENTA}%(name)s{AnsiColors.RESET}",
        "%(module)s": f"{AnsiColors.BRIGHT_GREEN}%(module)s{AnsiColors.RESET}",
        "%(filename)s": f"{AnsiColors.YELLOW}%(filename)s{AnsiColors.RESET}",
        "%(pathname)s": f"{AnsiColors.CYAN}%(pathname)s{AnsiColors.RESET}",
        "%(lineno)d": f"{AnsiColors.RED}%(lineno)d{AnsiColors.RESET}",
        "%(funcName)s": f"{AnsiColors.BRIGHT_BLUE}%(funcName)s{AnsiColors.RESET}",
        "%(process)d": f"{AnsiColors.MAGENTA}%(process)d{AnsiColors.RESET}",
        "%(thread)d": f"{AnsiColors.CYAN}%(thread)d{AnsiColors.RESET}",
        "%(threadName)s": f"{AnsiColors.BRIGHT_MAGENTA}%(threadName)s{AnsiColors.RESET}",
        "%(message)s": f"{AnsiColors.GRAY}%(message)s{AnsiColors.RESET}",
    }

    for placeholder, colorized in color_mapping.items():
        log_format = log_format.replace(placeholder, colorized)

    return log_format
