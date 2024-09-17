# Django Logging

The [`django_logging`](https://github.com/lazarus-org/django_logging) is a Django package designed to extend and enhance Python’s built-in logging capabilities. By providing customizable configurations and advanced features, it offers developers a comprehensive logging solution tailored specifically for Django applications.

![License](https://img.shields.io/github/license/lazarus-org/django_logging)
![PyPI release](https://img.shields.io/pypi/v/dj-logging)
![Documentation](https://img.shields.io/readthedocs/django-logging)
![CI Workflow](https://github.com/lazarus-org/django_logging/actions/workflows/ci.yml/badge.svg)
![Supported Python versions](https://img.shields.io/pypi/pyversions/dj-logging)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=yellow)](https://github.com/pre-commit/pre-commit)
![Supported Django versions](https://img.shields.io/pypi/djversions/dj-logging)
![Last Commit](https://img.shields.io/github/last-commit/lazarus-org/django_logging)
![Languages](https://img.shields.io/github/languages/top/lazarus-org/django_logging)
![Open Issues](https://img.shields.io/github/issues/lazarus-org/django_logging)
[![codecov](https://codecov.io/gh/ARYAN-NIKNEZHAD/django_logging/branch/main/graph/badge.svg)](https://codecov.io/gh/ARYAN-NIKNEZHAD/django_logging)
[![pylint](https://img.shields.io/badge/pylint-10/10-brightgreen?logo=python&logoColor=blue)](https://www.pylint.org/)


## Project Detail

- Language: Python > 3.8
- Framework: Django > 4.2


## Documentation

The documentation is organized into the following sections:

- [Quick Start](#quick-start)
- [Usage](#usage)
- [Settings](#settings)
- [Available Format Options](#available-format-options)
- [Required Email Settings](#required-email-settings)


## Quick Start

Getting started with `django_logging` is simple. Follow these steps to get up and running quickly:

1. **Install the Package**

first, Install `django_logging` via pip:

```shell
$ pip install dj-logging
```

2. **Add to Installed Apps**

Add `django_logging` to your `INSTALLED_APPS` in your Django settings file:

```python
INSTALLED_APPS = [
    ...
    'django_logging',
    ...
]
```


3. **Run Your Server**

Start your Django Development server to verify the installation:
```shell
python manage.py runserver
```

when the server starts, you'll see an initialization message like this in your *console*:
```shell
INFO | 'datetime' | django_logging | Logging initialized with the following configurations:
Log File levels: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].
Log files are being written to: logs.
Console output level: DEBUG.
Colorize console: True.
Log date format: %Y-%m-%d %H:%M:%S.
Email notifier enabled: False.
```
By default, django_logging will log each level to its own file:
- DEBUG : `logs/debug.log`
- INFO : `logs/info.log`
- WARNING : `logs/warning.log`
- ERROR : `logs/error.log`
- CRITICAL : `logs/critical.log`

In addition, logs will be displayed in ***colorized*** mode in the `console`, making it easier to distinguish between different log levels.

That's it! `django_logging` is ready to use. For further customization, refer to the [Settings](#settings) section


## Usage
Once `django_logging` is installed and added to your INSTALLED_APPS, you can start using it right away. The package provides several features to customize and enhance logging in your Django project. Below is a guide on how to use the various features provided by `django_logging`.

1. **Basic Logging Usage**

At its core, `django_logging` is built on top of Python’s built-in logging module. This means you can use the standard logging module to log messages across your Django project. Here’s a basic example of logging usage:
```python
import logging

logger = logging.getLogger(__name__)

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```
These logs will be handled according to the configurations set up by `django_logging`, using either the default settings or any custom settings you've provided.

2. **Request Logging Middleware**

To log the detail of each request to the server and capture information such as the request path, user, IP address, and user agent, add `django_logging.middleware.RequestLogMiddleware` to your MIDDLEWARE setting:

```python
MIDDLEWARE = [
    ...
    'django_logging.middleware.RequestLogMiddleware',
    ...
]
```

This middleware will log th request details at info level, here is an example with default format:
```shell
INFO | 'datetime' | django_logging | Request Info: (request_path: /example-path, user: example_user,
IP: 192.168.1.1, user_agent: Mozilla/5.0)

```

3. **Context Manager**

You can use the `config_setup` context manager to temporarily apply `django_logging` configurations within a specific block of code.
Example usage:
```python
from django_logging.utils.context_manager import config_setup
import logging

logger = logging.getLogger(__name__)

def foo():
  logger.info("This log will use the configuration set in the context manager!")

with config_setup():
    """ Your logging configuration changes here"""
    foo()

# the logging configuration will restore to what it was before, in here outside of with block
```
- Note: `AUTO_INITIALIZATION_ENABLE` must be set to `False` in the settings to use the context manager. If it is `True`, attempting to use the context manager will raise a `ValueError` with the message:
```
"You must set 'AUTO_INITIALIZATION_ENABLE' to False in DJANGO_LOGGING in your settings to use the context manager."
```

4. **Log and Notify Utility**

To send specific logs as email, use the `log_and_notify_admin` function. Ensure that the `ENABLE` option in `LOG_EMAIL_NOTIFIER` is set to `True` in your settings:
```python
from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
import logging

logger = logging.getLogger(__name__)

log_and_notify_admin(logger, logging.INFO, "This is a log message")
```
You can also include additional request information (`ip_address` and `browser_type`) in the email by passing an `extra` dictionary:
```python
from django_logging.utils.log_email_notifier.log_and_notify import log_and_notify_admin
import logging

logger = logging.getLogger(__name__)

def some_view(request):
    log_and_notify_admin(
        logger,
        logging.INFO,
        "This is a log message",
        extra={"request": request}
    )
```

- Note: To use the email notifier, `LOG_EMAIL_NOTIFIER["ENABLE"]` must be set to `True`. If it is not enabled, calling `log_and_notify_admin` will raise a `ValueError`:
```shell
"Email notifier is disabled. Please set the 'ENABLE' option to True in the 'LOG_EMAIL_NOTIFIER' in DJANGO_LOGGING in your settings to activate email notifications."
```

Additionally, ensure that all [Required Email Settings](#required-email-settings) are configured in your Django settings file.

5. **Send Logs Command**

To send the entire log directory to a specified email address, use the `send_logs` management command:
```shell
python manage.py send_logs example@domain.com
```
This command will attach the log directory and send a zip file to the provided email address.

6. **Execution Tracker Decorator**

The `execution_tracker` decorator is used to log the performance metrics of any function. It tracks execution time and the number of database queries for decorated function (if enabled).

Example Usage:
```python
from django_logging.decorators import execution_tracker

@execution_tracker(logging_level=logging.INFO, log_queries=True, query_threshold=10, query_exceed_warning=False)
def some_function():
    # function code
    pass
```

Arguments:

`logging_level` (`int`): The logging level at which performance details will be logged. Defaults to `logging.INFO`.

`log_queries` (`bool`): Whether to log the number of database queries for decorated function(if `DEBUG` is `True` in your settings). If `log_queries=True`, the number of queries will be included in the logs. Defaults to `False`.

`query_threshold` (`int`): If provided, the number of database queries will be checked. If the number of queries exceeded the given threshold, a warning will be logged. Defaults to `None`.

`query_exceed_warning` (`int`): Whether to log a `WARNING` message if number of queries exceeded the threshold. Defaults to `False`.

Example Log Output:
```shell
INFO | 'datetime' | execution_tracking | Performance Metrics for Function: 'some_function'
  Module: some_module
  File: /path/to/file.py, Line: 123
  Execution Time: 0 minute(s) and 0.2132 second(s)
  Database Queries: 15 queries (exceeds threshold of 10)

```
If `log_queries` is set to `True` but `DEBUG` is `False`, a WARNING will be logged:

```shell
WARNING | 'datetime' | execution_tracking | DEBUG mode is disabled, so database queries are not tracked. To include number of queries, set `DEBUG` to `True` in your django settings.
```

## Settings

By default, `django_logging` uses a built-in configuration that requires no additional setup. However, you can customize the logging settings by adding the `DJANGO_LOGGING` dictionary configuration to your Django `settings` file.

Example configuration:
```python
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
        "USE_TEMPLATE": True
    }
}
```

Here's a breakdown of the available configuration options:
- `AUTO_INITIALIZATION_ENABLE`: Accepts `bool`. Enables automatic initialization of logging configurations. Defaults to `True`.

- `INITIALIZATION_MESSAGE_ENABLE`: Accepts bool. Enables logging of the initialization message. Defaults to `True`.

- `LOG_FILE_LEVELS`: Accepts a list of valid log levels (a list of `str` where each value must be one of the valid levels). Defines the log levels for file logging. Defaults to `['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']`.

- `LOG_DIR`: Accepts `str` like `"path/to/logs"` or a path using functions like `os.path.join()`. Specifies the directory where log files will be stored. Defaults to `"logs"`.

- `LOG_FILE_FORMATS`: Accepts log levels as keys and format options as values. The format option can be an `int` chosen from predefined options or a user-defined format `str`. Defines the format for log files. Defaults to `1` for all levels.
  - **Note**: See the [Available Format Options](#available-format-options) below for available formats.

- `LOG_CONSOLE_LEVEL`: Accepts `str` that is a valid log level. Specifies the log level for console output. Defaults to `'DEBUG'`.

- `LOG_CONSOLE_FORMAT`: Accepts the same options as `LOG_FILE_FORMATS`. Defines the format for console output. Defaults to `1`.

- `LOG_CONSOLE_COLORIZE`: Accepts `bool`. Determines whether to colorize console output. Defaults to `True`.

- `LOG_DATE_FORMAT`: Accepts `str` that is a valid datetime format. Specifies the date format for log messages. Defaults to `'%Y-%m-%d %H:%M:%S'`.

- `LOG_EMAIL_NOTIFIER`: Is a dictionary where:

  - `ENABLE`: Accepts `bool`. Determines whether the email notifier is enabled. Defaults to `False`.

  - `NOTIFY_ERROR`: Accepts `bool`. Determines whether to notify on error logs. Defaults to `False`.

  - `NOTIFY_CRITICAL`: Accepts `bool`. Determines whether to notify on critical logs. Defaults to `False`.

  - `LOG_FORMAT`: Accepts the same options as other log formats (`int` or `str`). Defines the format for log messages sent via email. Defaults to `1`.

  - `USE_TEMPLATE`: Accepts `bool`. Determines whether the email includes an HTML template. Defaults to `True`.

## Available Format Options

The `django_logging` package provides predefined log format options that you can use in configuration. Below are the available format options:

```python
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
```

You can reference these formats by their corresponding integer keys in your logging configuration settings.

## Required Email Settings

To use the email notifier, the following email settings must be configured in your `settings.py`:
- `EMAIL_HOST`: The host to use for sending emails.
- `EMAIL_PORT`: The port to use for the email server.
- `EMAIL_HOST_USER`: The username to use for the email server.
- `EMAIL_HOST_PASSWORD`: The password to use for the email server.
- `EMAIL_USE_TLS`: Whether to use a TLS (secure) connection when talking to the email server.
- `DEFAULT_FROM_EMAIL`: The default email address to use for sending emails.
- `ADMIN_EMAIL`: The email address where log notifications will be sent. This is the recipient address used by the email notifier to deliver the logs.

Example Email Settings:
```python
EMAIL_HOST = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'your-email@example.com'
ADMIN_EMAIL = 'admin@example.com'
```

These settings ensure that the email notifier is correctly configured to send log notifications to the specified `ADMIN_EMAIL` address.

## Conclusion

Thank you for using `django_logging`. We hope this package enhances your Django application's logging capabilities. For more detailed documentation, customization options, and updates, please refer to the official documentation on [Read the Docs](https://django-logging.readthedocs.io/). If you have any questions or issues, feel free to open an issue on our [GitHub repository](https://github.com/lazarus-org/django_logging).

Happy logging!
