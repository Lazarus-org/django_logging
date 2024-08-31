from typing import List

from django.conf import settings
from django.core.checks import Error

from django_logging.constants.required_email_settings import (
    EMAIL_REQUIRED_SETTINGS,
    NOTIFIER_EXTRA_REQUIRED_SETTING,
)


def check_email_settings(require_admin_email: bool = True) -> List[Error]:
    """Check if all required email settings are present in the settings file.

    Returns a list of errors if any of the required email settings are
    missing.

    """
    errors: List[Error] = []
    if require_admin_email:
        EMAIL_REQUIRED_SETTINGS.append(NOTIFIER_EXTRA_REQUIRED_SETTING)

    missed_settings = [
        setting
        for setting in EMAIL_REQUIRED_SETTINGS
        if not getattr(settings, setting, None)
    ]

    if missed_settings:
        missing = ", ".join(missed_settings)
        errors.append(
            Error(
                f"Missing required email settings: {missing}",
                hint="Email settings required because you set LOG_EMAIL_NOTIFIER['ENABLE'] to True,\n"
                "Ensure all required email settings are properly configured in your settings file.",
                id="django_logging.E021",
            )
        )

    return errors
