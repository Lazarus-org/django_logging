from django.apps import AppConfig
from django.conf import settings
from django.utils.translation import gettext_lazy as _

import os


class DjangoLoggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_logging"
    verbose_name = _("Django Logging")

    def ready(self):
        from django_logging.utils.setup_conf import set_logging

        log_settings = getattr(settings, "DJANGO_LOGGING", {})
        log_levels = log_settings.get(
            "LOG_FILE_LEVELS", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        log_dir = log_settings.get("LOG_DIR", os.path.join(os.getcwd(), "logs"))
        log_email_notifier = log_settings.get("LOG_EMAIL_NOTIFIER", {})
        log_email_notifier_enable = log_email_notifier.get("ENABLE", False)
        log_email_notifier_log_levels = [
            "ERROR" if log_email_notifier.get("NOTIFY_ERROR", False) else None,
            "CRITICAL" if log_email_notifier.get("NOTIFY_CRITICAL", False) else None,
        ]

        # Set the logging configuration
        set_logging(log_levels, log_dir, log_email_notifier_enable, log_email_notifier_log_levels)
