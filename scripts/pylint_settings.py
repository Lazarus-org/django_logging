"""Minimal Django configuration for the repository's static analysis.

Importing these settings must never create log files or configure host
logging.

"""

SECRET_KEY = "pylint-only-unused-key"
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django_logging",
]
DJANGO_LOGGING = {"AUTO_INITIALIZATION_ENABLE": False}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
