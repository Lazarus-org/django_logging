from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoLoggingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_logging"
    verbose_name = _("Django Logging")

    def ready(self) -> None:
        """This method is called when the Django application is ready.

        The `ready` method is used to perform application-specific
        startup tasks. In this case, it performs the following actions:

        1. Imports necessary modules for checks, configuration retrieval,
           and logging setup.
        2. Retrieves the logging configuration from settings using `get_config`.
        3. Sets up the logging configuration using the retrieved configs.

        This ensures that the logging configuration is correctly set up
        when the application starts.

        """
        from django_logging.settings import checks
        from django_logging.utils.get_conf import get_config
        from django_logging.utils.set_conf import set_config

        conf = get_config()

        # Set the logging configuration
        set_config(**conf)
