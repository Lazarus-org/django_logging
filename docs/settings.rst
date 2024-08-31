Settings
========

By default, `django_logging` uses a built-in configuration that requires no additional setup. However, you can customize the logging settings by adding the `DJANGO_LOGGING` dictionary configuration to your Django `settings` file.

Example configuration:

   .. code-block:: python

      DJANGO_LOGGING = {
          "AUTO_INITIALIZATION_ENABLE": True,
          "INITIALIZATION_MESSAGE_ENABLE": True,
          "LOG_FILE_LEVELS": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
          "LOG_DIR": "logs",
          "LOG_FILE_FORMATS": {
              "DEBUG": 1,
              "INFO": 1,
              "WARNING": 1,
              "ERROR": 1,
              "CRITICAL": 1,
          },
          "LOG_CONSOLE_LEVEL": "DEBUG",
          "LOG_CONSOLE_FORMAT": 1,
          "LOG_CONSOLE_COLORIZE": True,
          "LOG_DATE_FORMAT": "%Y-%m-%d %H:%M:%S",
          "LOG_EMAIL_NOTIFIER": {
              "ENABLE": False,
              "NOTIFY_ERROR": False,
              "NOTIFY_CRITICAL": False,
              "LOG_FORMAT": 1,
              "USE_TEMPLATE": True,
          },
      }


Here's a breakdown of the available configuration options:

- **AUTO_INITIALIZATION_ENABLE**: Accepts `bool`. Enables automatic initialization of logging configurations. Defaults to `True`.

- **INITIALIZATION_MESSAGE_ENABLE**: Accepts `bool`. Enables logging of the initialization message. Defaults to `True`.

- **LOG_FILE_LEVELS**: Accepts a list of valid log levels (a list of `str` where each value must be one of the valid levels). Defines the log levels for file logging. Defaults to `['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']`.

- **LOG_DIR**: Accepts `str` like `"path/to/logs"` or a path using functions like `os.path.join()`. Specifies the directory where log files will be stored.  Defaults to `"logs"`.

- **LOG_FILE_FORMATS**: Accepts log levels as keys and format options as values. The format option can be an `int` chosen from predefined options or a user-defined format `str`. Defines the format for log files. Defaults to `1` for all levels.

 - **Note**:See the **Available Format Options** below for available formats.

- **LOG_CONSOLE_LEVEL**: Accepts `str` that is a valid log level. Specifies the log level for console output. Defaults to `'DEBUG'`,

- **LOG_CONSOLE_FORMAT**: Accepts the same options as `LOG_FILE_FORMATS`. Defines the format for console output. Defaults to `1`.

- **LOG_CONSOLE_COLORIZE**: Accepts `bool`. Determines whether to colorize console output. Defaults to `True`.

- **LOG_DATE_FORMAT**: Accepts `str` that is a valid datetime format. Specifies the date format for log messages. Defaults to `'%Y-%m-%d %H:%M:%S'`.

- **LOG_EMAIL_NOTIFIER**: Is a dictionary where:

 - **ENABLE**: Accepts `bool`. Determines whether the email notifier is enabled. Defaults to `False`.

 - **NOTIFY_ERROR**: Accepts `bool`. Determines whether to notify on error logs. Defaults to `False`.

 - **NOTIFY_CRITICAL**: Accepts `bool`. Determines whether to notify on critical logs. Defaults to `False`.

 - **LOG_FORMAT**: Accepts the same options as other log formats (`int` or `str`). Defines the format for log messages sent via email.  Defaults to `1`.

 - **USE_TEMPLATE**: Accepts `bool`. Determines whether the email includes an HTML template.  Defaults to `True`.


Available Format Options
=========================

The `django_logging` package provides predefined log format options that you can use in configuration. These options can be applied to log formats. Below are the available format options:

.. code-block:: python

    FORMAT_OPTIONS = {
        1: "%(levelname)s | %(asctime)s | %(module)s | %(message)s",
        2: "%(levelname)s | %(asctime)s | %(message)s",
        3: "%(levelname)s | %(message)s",
        4: "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        5: "%(levelname)s | %(message)s | [in %(pathname)s:%(lineno)d]",
        6: "%(asctime)s | %(levelname)s | %(message)s",
        7: "%(levelname)s | %(asctime)s | in %(module)s: %(message)s",
        8: "%(levelname)s | %(message)s | [%(filename)s:%(lineno)d]",
        9: "[%(asctime)s] | %(levelname)s | in %(module)s: %(message)s",
        10: "%(asctime)s | %(processName)s | %(name)s | %(levelname)s | %(message)s",
        11: "%(asctime)s | %(threadName)s | %(name)s | %(levelname)s | %(message)s",
        12: "%(levelname)s | [%(asctime)s] | (%(filename)s:%(lineno)d) | %(message)s",
        13: "%(levelname)s | [%(asctime)s] | {%(name)s} | (%(filename)s:%(lineno)d): %(message)s",
    }

You can reference these formats by their corresponding integer keys in your logging configuration settings.


Required Email Settings
-----------------------

To use the email notifier, the following email settings must be configured in your `settings.py`:

- **`EMAIL_HOST`**: The host to use for sending emails.
- **`EMAIL_PORT`**: The port to use for the email server.
- **`EMAIL_HOST_USER`**: The username to use for the email server.
- **`EMAIL_HOST_PASSWORD`**: The password to use for the email server.
- **`EMAIL_USE_TLS`**: Whether to use a TLS (secure) connection when talking to the email server.
- **`DEFAULT_FROM_EMAIL`**: The default email address to use for sending emails.
- **`ADMIN_EMAIL`**: The email address where log notifications will be sent. This is the recipient address used by the email notifier to deliver the logs.

Example Email Settings
----------------------

Below is an example configuration for the email settings in your `settings.py`:

.. code-block:: python

   EMAIL_HOST = "smtp.example.com"
   EMAIL_PORT = 587
   EMAIL_HOST_USER = "your-email@example.com"
   EMAIL_HOST_PASSWORD = "your-password"
   EMAIL_USE_TLS = True
   DEFAULT_FROM_EMAIL = "your-email@example.com"
   ADMIN_EMAIL = "admin@example.com"

These settings ensure that the email notifier is correctly configured to send log notifications to the specified `ADMIN_EMAIL` address.
