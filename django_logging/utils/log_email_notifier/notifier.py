import logging
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP
from typing import List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def send_email_async(
    subject: str,
    body: str,
    recipient_list: List[str],
    event: Optional[threading.Event] = None,
) -> None:
    def send_email() -> None:
        msg = MIMEMultipart()
        msg["From"] = settings.DEFAULT_FROM_EMAIL
        msg["To"] = ", ".join(recipient_list)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html"))

        try:
            server = SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.sendmail(
                settings.DEFAULT_FROM_EMAIL, recipient_list, msg.as_string()
            )
            server.quit()
            logger.info("Log Record has been sent to ADMIN EMAIL successfully.")

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Email Notifier failed to send Log Record: %s", e)

        finally:
            if event:
                event.set()  # set event that waits until email send. (used for Tests)

    # Start a new thread to send the email asynchronously
    email_thread = threading.Thread(target=send_email)
    email_thread.start()
