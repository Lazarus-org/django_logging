from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoLoggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_logging"
    verbose_name = _("Django Logging")

    def ready(self) -> None:
        from django_logging.settings import checks
        from django_logging.utils.get_conf import get_config
        from django_logging.utils.set_conf import set_config

        conf = get_config()

        # Set the logging configuration
        set_config(**conf)
