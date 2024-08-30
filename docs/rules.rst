Roles
=====

The `django_logging` package provides several logging roles to cater to different logging needs and contexts. These roles define specific behaviors and configurations, making it easier to manage logging in a Django application.

Available Roles
---------------

1. **Basic Logger Role**

   The Basic Logger Role is designed for standard logging use cases. It handles logging messages of different severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) and outputs them to both the console and log files, depending on the settings.

   **Key Features:**
   - Supports all standard logging levels.
   - Configurable to write logs to a file, the console, or both.
   - Can be integrated easily across different modules in your Django project.

2. **Request Logging Role**

   The Request Logging Role is specifically designed to log HTTP request details. This role captures information such as the request path, user, IP address, and user agent.

   **Key Features:**
   - Logs details of incoming requests.
   - Can be customized to include additional request metadata.
   - Useful for monitoring and debugging purposes.

   **Example Configuration:**

   .. code-block:: python

      MIDDLEWARE = [
          ...
          'django_logging.middleware.RequestLogMiddleware',
          ...
      ]

3. **Email Notifier Role**

   The Email Notifier Role enables sending logs via email. This is particularly useful for critical errors that require immediate attention.

   **Key Features:**
   - Sends log messages via email to designated recipients.
   - Supports customizable log levels for triggering email notifications.
   - Requires proper email configuration in the Django settings.

   **Example Usage:**

   .. code-block:: python

      from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
      import logging

      logger = logging.getLogger(__name__)

      log_and_notify_admin(logger, logging.CRITICAL, "Critical error occurred!")

   **Note:** To use this role, ensure that `LOG_EMAIL_NOTIFIER` is enabled and properly configured.

4. **Context Manager Role**

   The Context Manager Role provides a way to temporarily apply different logging configurations within a specific block of code. This is useful when you need to adjust logging behavior for certain operations without affecting the global configuration.

   **Key Features:**
   - Allows temporary configuration changes within a context.
   - Automatically reverts to the original configuration after exiting the context.
   - Useful for testing or handling specific scenarios where different logging behavior is required.

   **Example Usage:**

   .. code-block:: python

      from django_logging.utils.context_manager import config_setup
      import logging

      logger = logging.getLogger(__name__)

      with config_setup():
          logger.info("This log uses temporary configurations")


