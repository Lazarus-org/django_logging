from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoLoggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_logging"
    verbose_name = _("Django Logging")

    def ready(self) -> None:
        from django_logging.settings import checks
        from django_logging.utils.setup_logging import set_logging
        from django_logging.utils.get_config import get_conf
        conf = get_conf()

        # Set the logging configuration
        set_logging(*conf)
