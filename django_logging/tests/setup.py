import django
from django.conf import settings
import string
import random


def generate_secret_key(length: int = 50) -> str:
    """
    Generates a random secret key for Django settings.

    Args:
        length (int): The length of the secret key. Default is 50 characters.

    Returns:
        str: A randomly generated secret key.
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.choice(characters) for _ in range(length))


def configure_django_settings() -> None:
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY=generate_secret_key(),  # Add a secret key for testing
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
                "django.contrib.staticfiles",
                "django_logging",
            ],
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
                "django.contrib.sessions.middleware.SessionMiddleware",
                "django.middleware.common.CommonMiddleware",
                "django.middleware.csrf.CsrfViewMiddleware",
                "django.contrib.auth.middleware.AuthenticationMiddleware",
                "django.contrib.messages.middleware.MessageMiddleware",
                "django.middleware.clickjacking.XFrameOptionsMiddleware",
            ],
            TEMPLATES=[
                {
                    "BACKEND": "django.template.backends.django.DjangoTemplates",
                    "DIRS": [],
                    "APP_DIRS": True,
                    "OPTIONS": {
                        "context_processors": [
                            "django.template.context_processors.debug",
                            "django.template.context_processors.request",
                            "django.contrib.auth.context_processors.auth",
                            "django.contrib.messages.context_processors.messages",
                        ],
                    },
                },
            ],
            DJANGO_LOGGING={
                "INCLUDE_LOG_iBOARD": True,
                "AUTO_INITIALIZATION_ENABLE": True,
                "INITIALIZATION_MESSAGE_ENABLE": True,
                "LOG_FILE_LEVELS": ["DEBUG", "INFO"],
                "LOG_DIR": "logs",
                "LOG_FILE_FORMATS": {
                    "DEBUG": 1,
                    "INFO": 1,
                },
                "LOG_FILE_FORMAT_TYPES": {
                    "DEBUG": "JSON",
                },
                "EXTRA_LOG_FILES": {
                    "DEBUG": True,
                },
                "LOG_CONSOLE_LEVEL": "DEBUG",
                "LOG_CONSOLE_FORMAT": 1,
                "LOG_CONSOLE_COLORIZE": True,
                "LOG_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
                "LOG_EMAIL_NOTIFIER": {
                    "ENABLE": False,
                    "NOTIFY_ERROR": True,
                    "NOTIFY_CRITICAL": False,
                    "LOG_FORMAT": True,
                    "USE_TEMPLATE": True,
                },
            },
            EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
            EMAIL_HOST="smtp.example.com",
            EMAIL_PORT=587,
            EMAIL_USE_TLS=True,
            EMAIL_HOST_USER="example@test.com",
            EMAIL_HOST_PASSWORD="the_password",
            DEFAULT_FROM_EMAIL="example@test.com",
            ADMIN_EMAIL="admin@test.com",
            LANGUAGE_CODE="en-us",
            TIME_ZONE="UTC",
            USE_I18N=True,
            USE_TZ=True,
            ROOT_URLCONF="django_logging.urls",
            STATIC_URL="static/"
        )
        django.setup()

configure_django_settings()