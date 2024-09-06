Usage
=====

Once ``django_logging`` is installed and added to your ``INSTALLED_APPS``, you can start using it right away. The package provides several features to customize and enhance logging in your Django project. Below is a guide on how to use the various features provided by `django_logging`.

Basic Logging Usage
-------------------

   At its core, `django_logging` is built on top of Python’s built-in logging module. This means you can use the standard logging module to log messages across your Django project. Here’s a basic example of logging usage:

   .. code-block:: python

      import logging

      logger = logging.getLogger(__name__)

      logger.debug("This is a debug message")
      logger.info("This is an info message")
      logger.warning("This is a warning message")
      logger.error("This is an error message")
      logger.critical("This is a critical message")

   These logs will be handled according to the configurations set up by `django_logging`, using either the default settings or any custom settings you've provided.

Request Logging Middleware
--------------------------

   To capture and log information of each request to the server, such as the ``request path``, ``user``, ``IP address`` and ``user agent``, add ``django_logging.middleware.RequestLogMiddleware`` to your ``MIDDLEWARE`` setting:

   .. code-block::

      MIDDLEWARE = [
          ...
          'django_logging.middleware.RequestLogMiddleware',
          ...
      ]

   This middleware will log the request details at ``INFO`` level, here is an example with default format:

   .. code-block:: text

      INFO | 'datetime' | django_logging | Request Info: (request_path: /example-path, user: example_user,
      IP: 192.168.1.1, user_agent: Mozilla/5.0)

Context Manager
---------------
   You can use the ``config_setup`` context manager to temporarily apply `django_logging` configurations within a specific block of code.

   Example usage:

   .. code-block:: python

      from django_logging.utils.context_manager import config_setup
      import logging

      logger = logging.getLogger(__name__)


      def foo():
          logger.info("This log will use the configuration set in the context manager!")


      with config_setup():
          """Your logging configuration changes here"""
          foo()


   Note: ``AUTO_INITIALIZATION_ENABLE`` must be set to ``False`` in the settings to use the context manager. If it is ``True``, attempting to use the context manager will raise a ``ValueError`` with the message:

   .. code-block:: text

      "You must set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING in your settings to use the context manager."

Log and Notify Utility
----------------------

   To send specific logs as email, use the ``log_and_notify_admin`` function. Ensure that the ``ENABLE`` option in ``LOG_EMAIL_NOTIFIER`` is set to ``True`` in your settings:

   .. code-block:: python

      from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
      import logging

      logger = logging.getLogger(__name__)

      log_and_notify_admin(logger, logging.INFO, "This is a log message")

   You can also include additional request information (``ip_address`` and ``browser_type``) in the email by passing an ``extra`` dictionary:

   .. code-block:: python

      from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
      import logging

      logger = logging.getLogger(__name__)


      def some_view(request):
          log_and_notify_admin(
              logger, logging.INFO, "This is a log message", extra={"request": request}
          )

   Note: To use the email notifier, ``LOG_EMAIL_NOTIFIER["ENABLE"]`` must be set to ``True``. If it is not, calling ``log_and_notify_admin`` will raise a ``ValueError``:

   .. code-block:: text

      "Email notifier is disabled. Please set the 'ENABLE' option to True in the 'LOG_EMAIL_NOTIFIER' in DJANGO_LOGGING in your settings to activate email notifications."

   Additionally, ensure that all required email settings are configured in your Django settings file.
    - **Note**: For more detailed configuration options, refer to the :doc:`Settings <settings>`.

Send Logs Command
-----------------

   To send the entire log directory to a specified email address, use the ``send_logs`` management command:

   .. code-block:: shell

      python manage.py send_logs example@domain.com

   This command will attach the log directory and send a zip file to the provided email address.


