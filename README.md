# Django Logging

Welcome to django_logging Documentation!

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
[![codecov](https://codecov.io/gh/lazarus-org/django_logging/branch/main/graph/badge.svg)](https://codecov.io/gh/lazarus-org/django_logging)
[![pylint](https://img.shields.io/badge/pylint-10/10-brightgreen?logo=python&logoColor=blue)](https://www.pylint.org/)

The [`django_logging`](https://github.com/lazarus-org/django_logging) is a powerful yet simple Django package that extends and enhances Python's built-in ``logging`` without relying on any **third-party** libraries. Our goal is to keep things straightforward while providing flexible and customizable logging solutions that are specifically designed for Django applications.

One of the key advantages of ``django_logging`` is its seamless integration. Get started with django_logging in your existing projects without refactoring any code. Even if you're already using the **default logging setup**, you can instantly upgrade to advanced features with just a simple installation. No extra changes or complicated setup required!

imagine you have a Django package that was developed a few years ago and already uses Python's built-in ``logging``. Refactoring the entire codebase to use another logging package would be a daunting task. But with ``django_logging``, you don't have to worry about that. Simply install django_logging and enjoy all its advanced features with logging each ``LEVEL`` in separate files with three extra formats (``json``, ``xml``, ``flat``)  **without having to make any changes** to your existing code.


## Project Detail

- Language: Python >= 3.9
- Framework: Django >= 4.2


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
    # ...
    'django_logging',
    # ...
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

### Basic Logging Usage:

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

### Context Manager:

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

### Log and Notify Utility:

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

### Execution Tracker Decorator:

The `execution_tracker` decorator is used to log the performance metrics of any function. It tracks execution time and the number of database queries for decorated function (if enabled).

Example Usage:
```python
import logging
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
  Execution Time: 0.21 second(s)
  Database Queries: 15 queries (exceeds threshold of 10)

```
If `log_queries` is set to `True` but `DEBUG` is `False`, a WARNING will be logged:

```shell
WARNING | 'datetime' | execution_tracking | DEBUG mode is disabled, so database queries are not tracked. To include number of queries, set `DEBUG` to `True` in your django settings.
```

### Request Logging Middleware:

The `django_logging.middleware.RequestLogMiddleware` is a middleware that logs detailed information about each incoming request to the server. It is capable of handling both synchronous and asynchronous requests.

To enable this middleware, add it to your Django project's ``MIDDLEWARE`` setting:

```python
MIDDLEWARE = [
   #...
   'django_logging.middleware.RequestLogMiddleware',
   #...
]
```

#### Key Features

1. **Request Information Logging**:
   - Logs the following details at the start of each request:

     - Request method
     - Request path
     - Query parameters
     - Referrer (if available)

   - Example log at request start:

   ```shell
   INFO | 2024-10-03 16:29:47 | request_middleware | REQUEST STARTED:
   method=GET
   path=/admin/
   query_params=None
   referrer=http://127.0.0.1:8000/admin/login/?next=/admin/
   | {'ip_address': '127.0.0.1', 'request_id': '09580021-6bff-4b82-99b5-c52406b2cc91',
      'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
   ```
2. **Response Information Logging**:
   - Logs the following details after the request is processed:

     - User (or 'Anonymous' if not authenticated)
     - HTTP Status code
     - Content type
     - Time taken to process the request
     - Optionally logs SQL queries executed during the request (if enabled)

   - Example log at request completion:

    ```shell
    INFO | 2024-10-03 16:29:47 | request_middleware | REQUEST FINISHED:
    user=[mehrshad (ID:1)]
    status_code=200
    content_type=[text/html; charset=utf-8]
    response_time=[0.08 second(s)]
    3 SQL QUERIES EXECUTED
    Query1={'Time': 0.000(s), 'Query':
              [SELECT "django_session"."session_key", "django_session"."session_data", "django_session"."expire_date" FROM "django_session"
              WHERE ("django_session"."expire_date" > '2024-10-03 12:59:47.812918' AND "django_session"."session_key" = 'uq0nrbglazfm4cy656w3451xydfirh45') LIMIT 21]}

    Query2={'Time': 0.001(s), 'Query':
              [SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user".
              "username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user".
              "is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1 LIMIT 21]}

    | {'ip_address': '127.0.0.1', 'request_id': '09580021-6bff-4b82-99b5-c52406b2cc91',
      'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'}
    ```

3. **Request ID**:
   - A unique request ID is generated for each request (or taken from the `X-Request-ID` header if provided). This request ID is included in logs and can help with tracing specific requests.

4. **SQL Query Logging**:
   - If SQL query logging is enabled, all queries executed during the request will be logged along with their execution time.

    **Note**: to enable Query logging, you can set `LOG_SQL_QUERIES_ENABLE` to `True` in settings. for more details, refer to the [Settings](#settings).

5. **Streaming Response Support**:
   - The middleware supports both synchronous and asynchronous streaming responses, logging the start and end of the streaming process, as well as any errors during streaming.

6. **User Information**:
   - Logs the authenticated user's username and ID if available, or 'Anonymous' if the user is not authenticated.

7. **IP Address and User-Agent**:
   - The middleware logs the client's IP address and user agent for each request.


#### Context Variables Usage

We use context variables in `RequestLogMiddleware` to store the following information for each request:

- **request_id**: A unique identifier for the request.
- **ip_address**: The client’s IP address.
- **user_agent**: The client's user agent string.

These context variables can be accessed and used in other parts of the logging system or during the request processing lifecycle.

### MonitorLogSizeMiddleware

This middleware monitors the size of the log directory and checks it weekly.
It triggers the `logs_size_audit` management command to assess the total size of the log files.
If the log directory size exceeds a certain limit (`LOG_DIR_SIZE_LIMIT`), the middleware sends a warning email to the `ADMIN_EMAIL` asynchronously.

To enable this middleware, add it to your Django project's `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
   #...
   'django_logging.middleware.MonitorLogSizeMiddleware',
   #...
]
```

### Context Variable Management

`django_logging` includes a powerful `ContextVarManager` class, allowing you to manage context variables dynamically within your logging system. These variables are bound to the current context and automatically included in your log entries via the ``%(context)s`` placeholder in the log format.

#### Binding and Unbinding Context Variables

The `ContextVarManager` provides several methods to manage context variables efficiently:

**`bind(**kwargs)`**:

The `bind` method allows you to bind key-value pairs as context variables that will be available during the current context. These variables can be used to add contextual information to log entries.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

# Binding context variables
manager.bind(user="test_user", request_id="abc123")

logger.info("Logging with context")
```

**Log Output**:

```shell
INFO | 2024-10-03 12:00:00 | Logging with context | {'user': 'test_user', 'request_id': 'abc123'}
```

**``unbind(key: str)``**:

The `unbind` method removes a specific context variable by its key. It effectively clears the context variable from the log entry.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

manager.unbind("user")
logger.info("Logging without the 'user' context")
```
**Log Output**:

```shell
INFO | 2024-10-03 12:05:00 | Logging without the 'user' context | {'request_id': 'abc123'}
```

#### Batch Binding and Resetting Context Variables

**`batch_bind(**kwargs)`**:

The `batch_bind` method binds multiple context variables at once and returns tokens that can be used later to reset the variables to their previous state. This is useful when you need to bind a group of variables temporarily.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

tokens = manager.batch_bind(user="admin_user", session_id="xyz789")

logger.info("Logging with batch-bound context")
```

**Log Output**:

```shell
INFO | 2024-10-03 12:10:00 | Logging with batch-bound context | {'user': 'admin_user', 'session_id': 'xyz789'}
```

**`reset(tokens: Dict[str, contextvars.Token])`**:

The `reset` method allows you to reset context variables to their previous state using tokens returned by `batch_bind`.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

manager.reset(tokens)

logger.info("Context variables have been reset")
```
**Log Output**:

```shell
INFO | 2024-10-03 12:15:00 | Context variables have been reset |
```

**`clear()`**:

The `clear` method clears all bound context variables at once, effectively removing all contextual data from the log entry.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)
manager.clear()

logger.info("All context variables cleared")
```

**Log Output**:

```shell
INFO | 2024-10-03 12:20:00 | All context variables cleared |
```

#### Retrieving and Merging Context Variables

**`get_contextvars()`**:

The `get_contextvars` method retrieves the current context variables available in the context. This method is useful for inspecting or debugging the context.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

current_context = manager.get_contextvars()
print(current_context)  # Output: {'user': 'admin_user', 'session_id': 'xyz789'}
```

**`merge_contexts(bound_context: Dict[str, Any], local_context: Dict[str, Any])`**:

The `merge_contexts` method merges two dictionaries of context variables, giving priority to the `bound_context`. This is useful when you want to combine different sources of context data.

**Example**:

```python
from django_logging.contextvar import manager

bound_context = {"user": "admin_user"}
local_context = {"request_id": "12345"}

merged_context = manager.merge_contexts(bound_context, local_context)
print(merged_context)  # Output: {'user': 'admin_user', 'request_id': '12345'}
```

**`get_merged_context(bound_logger_context: Dict[str, Any])`**:

The `get_merged_context` method combines the bound logger context with the current context variables, allowing you to retrieve a single dictionary with all the context data.

**Example**:

```python
from django_logging.contextvar import manager

bound_logger_context = {"app_name": "my_django_app"}

merged_context = manager.get_merged_context(bound_logger_context)
print(merged_context)  # Output: {'app_name': 'my_django_app', 'user': 'admin_user'}
```

#### Scoped Context Management

**`scoped_context(**kwargs)`**:

The `scoped_context` method provides a context manager to bind context variables temporarily for a specific block of code. After the block completes, the context variables are automatically unbound.

**Example**:

```python
from django_logging.contextvar import manager
import logging

logger = logging.getLogger(__name__)

with manager.scoped_context(transaction_id="txn123"):
   logger.info("Scoped context active")

logger.info("Scoped context no longer active")
```

**Log Output**:

```shell
INFO | 2024-10-03 12:30:00 | Scoped context active | {'transaction_id': 'txn123'}
INFO | 2024-10-03 12:30:10 | Scoped context no longer active |
```

### send_logs Command

This Django management command zips the log directory and emails it to a specified email address. The command is useful for retrieving logs remotely and securely, allowing administrators to receive log files via email.

#### Key Features:

- **Zips Log Directory**: Automatically compresses the log directory into a single zip file.
- **Email Log Files**: Sends the zipped log file to a specified email address.

#### How It Works:

1. **Setup Log Directory**: The command retrieves the log directory from Django settings (`DJANGO_LOGGING['LOG_DIR']`).
2. **Zip the Logs**: Compresses the entire log directory into a zip file stored in a temporary location.
3. **Email the Zip File**: Sends the zipped log file to the email address provided as an argument, attaching it to an email message.
4. **Cleanup**: After sending the email, the temporary zip file is deleted to free up disk space.

#### Command Execution:

To execute the command, use the following syntax:

```shell
python manage.py send_logs <email>
```

#### Example:

If you want to send the logs to `admin@example.com`, the command would be:
```shell
python manage.py send_logs admin@example.com
```

This will zip the log directory and send it to `admin@example.com` with the subject "Log Files".


### generate_pretty_json Command

This Django management command allows you to locate and prettify JSON log files stored in a log directory that generated by `django_logging`. It takes JSON files from the log directory, formats them into a clean, readable structure, and saves the result in the `pretty` directory.

#### Key Features:

- **Locate JSON Logs**: Automatically finds `.json` files in the `json` log directory.
- **Pretty Formatting**: Reformats the JSON logs into a valid JSON array with proper indentation, improving readability.
- **Separate Output Directory**: Saves the reformatted JSON files in a `pretty` subdirectory, preserving the original files.

#### How It Works:

1. **Setup Directories**: The command looks for a `json` subdirectory within your defined log directory. If it doesn't exist, an error is displayed.
2. **Process JSON Files**: Each `.json` file found in the directory is processed:
   - Parses multiple JSON objects within the file.
   - Reformats them as a pretty JSON array with proper indentation.
   - Saves the new, formatted JSON in the `pretty` subdirectory with the prefix `formatted_`.

#### Command Execution:

To execute the command, use the following syntax:
```shell
python manage.py generate_pretty_json
```

#### Example:

Running the command will process the following files:

- `logs/json/error.json` ➡ `logs/json/pretty/formatted_error.json`
- `logs/json/info.json` ➡ `logs/json/pretty/formatted_info.json`


### generate_pretty_xml Command

This Django management command allows you to locate and reformat XML log files stored in a log directory generated by ``django_logging``. It processes XML files by wrapping their content in a `<logs>` element and saves the reformatted files in a separate directory.

#### Key Features:

- **Locate XML Logs**: Automatically finds `.xml` files in the `xml` log directory.
- **Reformatting**: Wraps XML content in a `<logs>` element, ensuring consistency in structure.
- **Separate Output Directory**: Saves the reformatted XML files in a ``pretty`` subdirectory with the prefix ``formatted_``, preserving the original files.

#### How It Works:

1. **Setup Directories**: The command looks for an `xml` subdirectory within your defined log directory. If it doesn't exist, an error is displayed.
2. **Process XML Files**: Each `.xml` file found in the directory is processed:
   - The content of each XML file is wrapped inside a `<logs>` element.
   - The reformatted file is saved in the `pretty` subdirectory with the prefix `formatted_`.

#### Command Execution:

To execute the command, use the following syntax:
```shell
python manage.py generate_pretty_xml
```

#### Example:

Running the command will process the following files:

- `logs/xml/error.xml` ➡ `logs/xml/pretty/formatted_error.xml`
- `logs/xml/info.xml` ➡ `logs/xml/pretty/formatted_info.xml`


### logs_size_audit Command

This Django management command monitors the size of your log directory. If the total size exceeds the configured limit, the command sends a warning email notification to the admin. The size check helps maintain log storage and prevent overflow by ensuring administrators are informed when logs grow too large.

#### Key Features:

- **Log Directory Size Check**: Automatically calculates the total size of the log directory.
- **Configurable Size Limit**: Compares the total size of the log directory against a configured limit.
- **Email Notification**: Sends an email warning to the administrator when the log size exceeds the defined limit.

#### How It Works:

1. **Setup Log Directory**: The command retrieves the log directory from Django settings, specifically `DJANGO_LOGGING['LOG_DIR']` or the Default. If the directory doesn't exist, an error is logged and displayed.
2. **Calculate Directory Size**: It calculates the total size of the files in the log directory.
3. **Compare with Size Limit**: The command compares the total directory size (in MB) with the configured size limit, which can be configured as `LOG_DIR_SIZE_LIMIT` in settings.
4. **Send Warning Email**: If the directory size exceeds the configured limit, the command sends a warning email to the admin, detailing the current log size.

#### Command Execution:

To execute the command, use the following syntax:
```shell
python manage.py logs_size_audit
```

#### Example:

Running the command when the log directory exceeds the size limit will trigger an email to the administrator:

- Example log size: `1200 MB` (limit: `1024 MB`)
- An email will be sent to `ADMIN_EMAIL` configured in Django settings.


## Settings

By default, `django_logging` uses a built-in configuration that requires no additional setup. However, you can customize the logging settings by adding the `DJANGO_LOGGING` dictionary configuration to your Django `settings` file.

#### Default configuration:

```python
DJANGO_LOGGING = {
    "AUTO_INITIALIZATION_ENABLE": True,
    "INITIALIZATION_MESSAGE_ENABLE": True,
    "LOG_SQL_QUERIES_ENABLE": True,
    "LOG_FILE_LEVELS": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    "LOG_DIR": "logs",
    "LOG_DIR_SIZE_LIMIT": 1024,  # MB
    "LOG_FILE_FORMATS": {
        "DEBUG": 1,
        "INFO": 1,
        "WARNING": 1,
        "ERROR": 1,
        "CRITICAL": 1,
    },
    "LOG_FILE_FORMAT_TYPES": {
        "DEBUG": "normal",
        "INFO": "normal",
        "WARNING": "normal",
        "ERROR": "normal",
        "CRITICAL": "normal",
    },
    "EXTRA_LOG_FILES": {  # for extra formats (JSON, XML)
        "DEBUG": False,
        "INFO": False,
        "WARNING": False,
        "ERROR": False,
        "CRITICAL": False,
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
```
#### Configuration Options:

Here's a breakdown of the available configuration options:

`AUTO_INITIALIZATION_ENABLE`
----------------------------

- **Type**: `bool`
- **Description**: Enables automatic initialization of logging configurations.
- **Default**: `True`

`INITIALIZATION_MESSAGE_ENABLE`
-------------------------------

- **Type**: `bool`
- **Description**: Enables logging of the initialization message when logging starts.
- **Default**: `True`

`LOG_SQL_QUERIES_ENABLE`
------------------------

- **Type**: `bool`
- **Description**: Enables logging of SQL queries within `RequestLogMiddleware` logs. When enabled, SQL queries executed in each request will be included in the log output.
- **Default**: `False`

`LOG_FILE_LEVELS`
-----------------

- **Type**: `list[str]`
- **Description**: Specifies which log levels should be captured in log files.
- **Default**: `["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]`

`LOG_DIR`
---------

- **Type**: `str`
- **Description**: Specifies the directory where log files will be stored.
- **Default**: `"logs"`

`LOG_DIR_SIZE_LIMIT`
--------------------

- **Type**: `int`
- **Description**: Specifies the maximum allowed size of the log directory in megabytes (MB). If the directory exceeds this limit and `MonitorLogSizeMiddleware` is enabled, a warning email will be sent to the admin weekly.
- **Default**: `1024 MB` (1 GB)

`LOG_FILE_FORMATS`
------------------

- **Type**: `dict[str, int | str]`
- **Description**: Maps each log level to its corresponding log format. The format can be an `int` representing predefined formats or a custom `str` format.
- **Default**: Format `1` for all levels.
- **Note**: See the [Available Format Options](#available-format-options) below for available formats.

`LOG_FILE_FORMAT_TYPES`
-----------------------

- **Type**: `dict[str, str]`
- **Description**: Defines the format type (e.g., `normal`, `JSON`, `XML`, `FLAT`) for each log level. The keys are log levels, and the values are the format types.
    - **Format Types**:

      - ``normal``: Standard text log.
      - ``JSON``: Structured logs in JSON format.
      - ``XML``: Structured logs in XML format.
      - ``FLAT``: logs with Flat format.
      -
- **Default**: Type `normal` for all levels.

`EXTRA_LOG_FILES`
-----------------

- **Type**: `dict[str, bool]`
- **Description**: Determines whether separate log files for `JSON` or `XML` formats should be created for each log level. When set to `True` for a specific level, a dedicated directory (e.g., `logs/json` or `logs/xml`) will be created with files like `info.json` or `info.xml`. if `False`, json and xml logs will be written to `.log` files.
- **Default**: `False` for all levels.

`LOG_CONSOLE_LEVEL`
-------------------

- **Type**: `str`
- **Description**: Specifies the log level for console output.
- **Default**: `"DEBUG"`

`LOG_CONSOLE_FORMAT`
--------------------

- **Type**: `int | str`
- **Description**: Specifies the format for console logs, similar to `LOG_FILE_FORMATS`.
- **Default**: format option `1`

`LOG_CONSOLE_COLORIZE`
----------------------

- **Type**: `bool`
- **Description**: Determines whether console output should be colorized.
- **Default**: `True`

``LOG_DATE_FORMAT``
-------------------

- **Type**: ``str``
- **Description**: Specifies the date format for log messages.
- **Default**: `"%Y-%m-%d %H:%M:%S"`

`LOG_EMAIL_NOTIFIER`
--------------------

- **Type**: `dict`
- **Description**: Configures the email notifier for sending log-related alerts.

    - `ENABLE`:
      - **Type**: `bool`
      - **Description**: Enables or disables the email notifier.
      - **Default**: `False`

    - `NOTIFY_ERROR`:
      - **Type**: `bool`
      - **Description**: Sends an email notification for `ERROR` log level events.
     - **Default**: `False`

    - `NOTIFY_CRITICAL`:
      - **Type**: `bool`
      - **Description**: Sends an email notification for `CRITICAL` log level events.
      - **Default**: `False`

    - `LOG_FORMAT`:
      - **Type**: `int | str`
      - **Description**: Specifies the log format for email notifications.
      - **Default**: format option `1`

    - `USE_TEMPLATE`:
      - **Type**: `bool`
      - **Description**: Determines whether the email should include `LAZARUS` email template.


## Available Format Options

The `django_logging` package provides predefined log format options that you can use in configuration. Below are the available format options:

```python
FORMAT_OPTIONS = {
    1: "%(levelname)s | %(asctime)s | %(module)s | %(message)s | %(context)s",
    2: "%(levelname)s | %(asctime)s | %(context)s | %(message)s",
    3: "%(levelname)s | %(context)s | %(message)s",
    4: "%(context)s | %(asctime)s - %(name)s - %(levelname)s - %(message)s",
    5: "%(levelname)s | %(message)s | %(context)s | [in %(pathname)s:%(lineno)d]",
    6: "%(asctime)s | %(context)s | %(levelname)s | %(message)s",
    7: "%(levelname)s | %(asctime)s | %(context)s | in %(module)s: %(message)s",
    8: "%(levelname)s | %(context)s | %(message)s | [%(filename)s:%(lineno)d]",
    9: "[%(asctime)s] | %(levelname)s | %(context)s | in %(module)s: %(message)s",
    10: "%(asctime)s | %(processName)s | %(context)s | %(name)s | %(levelname)s | %(message)s",
    11: "%(asctime)s | %(context)s | %(threadName)s | %(name)s | %(levelname)s | %(message)s",
    12: "%(levelname)s | [%(asctime)s] | %(context)s | (%(filename)s:%(lineno)d) | %(message)s",
    13: "%(levelname)s | [%(asctime)s] | %(context)s | {%(name)s} | (%(filename)s:%(lineno)d): %(message)s",
    14: "[%(asctime)s] | %(levelname)s | %(context)s | %(name)s | %(module)s | %(message)s",
    15: "%(levelname)s | %(context)s | %(asctime)s | %(filename)s:%(lineno)d | %(message)s",
    16: "%(levelname)s | %(context)s | %(message)s | [%(asctime)s] | %(module)s",
    17: "%(levelname)s | %(context)s | [%(asctime)s] | %(process)d | %(message)s",
    18: "%(levelname)s | %(context)s | %(asctime)s | %(name)s | %(message)s",
    19: "%(levelname)s | %(asctime)s | %(context)s | %(module)s:%(lineno)d | %(message)s",
    20: "[%(asctime)s] | %(levelname)s | %(context)s | %(thread)d | %(message)s",
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
