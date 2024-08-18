class AnsiColors:
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    RED_BACKGROUND = "\033[1;41m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    GRAY = "\033[0;37m"
    WHITE = "\033[0;38m"
    RESET = "\033[0m"
    BRIGHT_BLACK = "\033[0;90m"
    BRIGHT_RED = "\033[0;91m"
    BRIGHT_GREEN = "\033[0;92m"
    BRIGHT_YELLOW = "\033[0;93m"
    BRIGHT_BLUE = "\033[0;94m"
    BRIGHT_MAGENTA = "\033[0;95m"
    BRIGHT_CYAN = "\033[0;96m"
    BRIGHT_WHITE = "\033[0;97m"
    BLACK_BACKGROUND = "\033[40m"
    RED_BACKGROUND = "\033[41m"
    GREEN_BACKGROUND = "\033[42m"
    YELLOW_BACKGROUND = "\033[43m"
    BLUE_BACKGROUND = "\033[44m"
    MAGENTA_BACKGROUND = "\033[45m"
    CYAN_BACKGROUND = "\033[46m"
    WHITE_BACKGROUND = "\033[47m"


# Mapping log levels to ANSI colors
LOG_LEVEL_COLORS = {
    "DEBUG": AnsiColors.BLUE,
    "INFO": AnsiColors.GREEN,
    "WARNING": AnsiColors.YELLOW,
    "ERROR": AnsiColors.RED,
    "CRITICAL": AnsiColors.RED_BACKGROUND,
}
