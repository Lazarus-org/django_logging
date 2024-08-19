import logging

from django.conf import settings
from django.template import engines
from django.utils.timezone import now
from django_logging.utils.email.notifier import send_email_async
from django_logging.middleware import RequestLogMiddleware


class EmailHandler(logging.Handler):
    def __init__(self, include_html=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.include_html = include_html

        try:
            # Attempt to retrieve the logging settings from the Django settings
            logging_settings = settings.DJANGO_LOGGING

            self.include_html = logging_settings.get("LOG_EMAIL_NOTIFIER", {}).get("USE_TEMPLATE", include_html)

        except Exception as e:
            logging.error(f"An unexpected error occurred while initializing EmailHandler: {e}")

    def emit(self, record):
        try:
            request = getattr(record, "request", None)
            log_entry = self.format(record)

            if self.include_html:
                email_body = self.render_template(log_entry, request)
            else:
                email_body = log_entry

            subject = f"New Log Record: {record.levelname}"
            send_email_async(subject, email_body, [settings.ADMIN_EMAIL])

        except Exception as e:
            self.handleError(record)

    @staticmethod
    def render_template(log_entry, request=None, template_path="email_notifier_template.html"):
        django_engine = engines["django"]
        template = django_engine.get_template(template_path)

        # Fetch IP address and user agent using middleware methods
        ip_address = RequestLogMiddleware.get_ip_address(request) if request else "Unknown"
        user_agent = RequestLogMiddleware.get_user_agent(request) if request else "Unknown"

        context = {
            "message": log_entry,
            "time": now(),
            "browser_type": user_agent,
            "ip_address": ip_address,
        }

        return template.render(context)
