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

One of the key advantages of ``django_logging`` is its seamless integration. Get started with django_logging in your existing projects without refactoring any code. Even if you're already using the **built-in logging module**, you can instantly upgrade to advanced features with just a simple installation. No extra changes or complicated setup required!

imagine you have a Django package that was developed a few years ago and already uses Python's built-in ``logging``. Refactoring the entire codebase to use another logging package would be a daunting task. But with ``django_logging``, you don't have to worry about that. Simply install django_logging and enjoy all its advanced features with logging each ``LEVEL`` in separate files with three extra formats (``json``, ``xml``, ``flat``)  **without having to make any changes** to your existing code.


## Project Detail

- Language: Python >= 3.10
- Framework: Django 5.2 on Python 3.10–3.14; Django 6.0 and 6.1 on Python 3.12–3.14 (CI compatibility targets)


## Documentation

The documentation is organized into the following sections:

- [Quick Start](#quick-start)
- [Usage](#usage)
- [LogiBoard Integration](#logiboard-integration)
- [Settings](#settings)
- [Log Rotation](#log-rotation)
- [Custom handlers, formatters, and loggers](#custom-handlers-formatters-and-loggers)
- [Performance and production deployment](https://django-logging.readthedocs.io/en/latest/performance.html)
- [Extensible components](https://django-logging.readthedocs.io/en/latest/extensibility.html)
- [Management Commands](#management-commands)
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


3. **Choose how logging is configured**

Adding `django_logging` to `INSTALLED_APPS` automatically installs package-managed file handlers in additive mode. Existing application logging handlers and levels are preserved. For an application-managed setup, set `AUTO_INITIALIZATION_ENABLE` to `False`.

To enable dj-logging's own handlers only for the `django_logging` logger hierarchy, add:

```python
# Optional: automatic initialization is already enabled in additive mode.
DJANGO_LOGGING = {
    "AUTO_INITIALIZATION_ENABLE": True,
    "LOGGING_SETUP_MODE": "additive",
}
```

Then run your application normally:

```shell
python manage.py runserver
```

Automatic setup installs package-owned file destinations without replacing your existing root handlers or logging levels. For projects that deliberately want the older root-logger takeover behavior, choose `"LOGGING_SETUP_MODE": "replace_root"` explicitly. See [Settings](#settings) for complete configuration and migration guidance.


## Usage
Once `django_logging` is installed and added to your INSTALLED_APPS, you can start using it right away. The package provides several features to customize and enhance logging in your Django project. Below is a guide on how to use the various features provided by `django_logging`.

### Basic Logging Usage:

At its core, `django_logging` is built on top of Python's built-in logging module. This means you can use the standard logging module to log messages across your Django project. Here's a basic example of logging usage:
```python
import logging

logger = logging.getLogger(__name__)

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")
```
These records are handled by the application's standard Django `LOGGING` configuration. With explicit isolated setup, records emitted under `django_logging.*` are also handled by the package's isolated handlers. To route other application loggers into package files, use Django `LOGGING` or explicitly opt into the legacy root setup.

### Temporary package logging configuration

`config_setup()` temporarily installs the package's own handlers on the `django_logging` logger namespace. It does **not** replace the root logger and does not redirect unrelated application loggers. Disable automatic initialization before using it.

```python
import logging
from django_logging.utils.context_manager import config_setup

with config_setup():
    logging.getLogger("django_logging.example").info("Hello from the scoped setup")
```

This context changes a process-global package logger for the duration of the block; it is suitable for controlled startup or standalone tooling, **not** for request-scoped configuration or concurrent use where other threads may log under `django_logging`. It restores the previous package logger configuration after exit, even on an exception. If another dj-logging-managed configuration is already installed, `config_setup()` rejects overriding it.

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

`django_logging.middleware.RequestLogMiddleware` works with synchronous and
asynchronous Django request handlers. By default it writes **one completion
log entry at INFO level** with method, bounded path, status, content type,
response latency in milliseconds, and an already-resolved user ID (or
`Anonymous`). It does not resolve lazy Django session users to generate logs.

Enable it through Django's normal middleware setting:

```python
MIDDLEWARE = [
    # ...
    "django_logging.middleware.RequestLogMiddleware",
    # ...
]
```

The request ID is exposed as `request.request_id` and is available as the
`request_id` logging context variable. Incoming `X-Request-ID` values must
be short ASCII strings containing only letters, digits, `_`, `-`, or `.`;
other values are replaced with a generated UUID. Context is scoped to the
request and restored on exceptions or cancellations. When streaming content
is consumed after the view returns, the request's logging context is restored
for that iteration. **The completion event measures time to the response
object, not the total streaming time**. Additional streaming lifecycle events are
disabled by default and can be enabled with `REQUEST_LOGGING["LOG_STREAMING_EVENTS"]`;
stream context propagation and error logging remain active when disabled.

#### Request-specific configuration

All options live inside the existing `DJANGO_LOGGING` setting (no separate
Django settings namespace or policy module):

```python
DJANGO_LOGGING = {
    # Your existing dj-logging settings remain available.
    "LOG_SQL_QUERIES_ENABLE": False,
    "REQUEST_LOGGING": {
        "LOG_REQUEST_STARTED": False,
        "LOG_REQUEST_FINISHED": True,
        "LOG_USER_AGENT": True,
        "LOG_QUERY_PARAMS": False,
        "LOG_REQUEST_BODY": False,
        "LOG_ERROR_RESPONSE": False,
        "LOG_STREAMING_EVENTS": False,
        "EXCLUDED_PATHS": ["/auth/login"],
        "EXCLUDED_PATH_PREFIXES": ["/admin", "/auth"],
        "EXCLUDED_FIELDS": ["customer_identifier"],
        "EXCLUDED_FIELDS_BY_PATH": {"/api/search": ["custom_secret"]},
        "MAX_QUERY_BYTES": 4096,
        "MAX_BODY_BYTES": 2048,
        "MAX_ERROR_BYTES": 2048,
        "MAX_SQL_BYTES": 4096,
        "MAX_DIAGNOSTIC_DEPTH": 8,
        "TRUSTED_PROXY_CIDRS": [],
        "MAX_REQUEST_ID_LENGTH": 80,
    },
}
```

All `REQUEST_LOGGING` options are optional. Invalid or unknown options fail
Django system checks (`django_logging.E040_REQUEST_LOGGING`) and raise
`ImproperlyConfigured` if request middleware is instantiated.

`LOG_STREAMING_EVENTS` defaults to `False`. It suppresses additional stream
start/finish/close/cancellation messages; stream context propagation and streaming
error logging remain enabled.

**Privacy and performance:** Query values, JSON request bodies, JSON error
response bodies, and SQL values are disabled by default (regardless of
`settings.DEBUG`). Values are capped before parsing and after serialization.
Sensitive field names are always redacted, with extra field exclusions
configurable globally or per path. Entire excluded path families suppress all
request value diagnostics. Logging user-agent metadata is sanitized and
bounded. Regular response bodies are never accessed.

Redaction is best-effort: a secret may be sent under an unrecognized key or in
a URL path; exclude endpoints that handle credentials rather than relying on
field names. Do not enable SQL logging on production traffic that includes
sensitive query parameters. SQL diagnostics reuse the existing top-level
`LOG_SQL_QUERIES_ENABLE` flag and Django's own SQL query capture behavior;
this package does not turn `DEBUG` or database query capture on automatically.

**Trusted client IPs:** By default only `REMOTE_ADDR` is used; an arbitrary
`X-Forwarded-For` header is never trusted. If your deployment has a trusted
reverse proxy, list its *peer* network in `TRUSTED_PROXY_CIDRS`. Only then
will a syntactically valid single `X-Real-IP` value be considered. Ensure the
trusted reverse proxy strips and overwrites client-provided `X-Real-IP`.
Do not include client networks in `TRUSTED_PROXY_CIDRS`.

**Behavior changes from previous releases:** The start event is now opt-in;
query parameters and referrers are no longer logged automatically; the
completion event uses `response_time_ms` and a resolved user ID instead of
username; middleware-instance `.context` / `.initial_queries` state has been
removed; and untrusted forwarding headers no longer override `REMOTE_ADDR`.
These changes are intentional for concurrency correctness and safe defaults.

#### Context Variables Usage

We use context variables in `RequestLogMiddleware` to store the following information for each request:

- **request_id**: A unique identifier for the request.
- **ip_address**: The client’s IP address.
- **user_agent**: The client's user agent string.

These context variables can be accessed and used in other parts of the logging system or during the request processing lifecycle.

### MonitorLogSizeMiddleware

**Schedule `python manage.py logs_size_audit` outside HTTP requests** (for example weekly using cron, systemd timers, or an existing scheduler). This command checks `LOG_DIR_SIZE_LIMIT` and requests a warning email when the configured threshold is reached. It does not require installing middleware.

`MonitorLogSizeMiddleware` remains available for backward compatibility but is a **pass-through by default**. A synchronous filesystem scan/email request inside HTTP handling is undesirable on high-traffic applications.

To explicitly restore the legacy request-time behavior, configure `DJANGO_LOGGING["LOG_SIZE_AUDIT_IN_REQUEST"] = True` **and** add the middleware. It uses a cache claim to avoid concurrent scans, but the triggering request still waits for the command to finish. Prefer a shared cache backend for multi-worker deployments; local-memory caches cannot coordinate across processes.

```python
DJANGO_LOGGING = {"LOG_SIZE_AUDIT_IN_REQUEST": True}  # legacy opt-in only
```

The optional legacy middleware is installed as follows:

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

This Django management command monitors the size of your log directory. If the total size exceeds the configured limit, the command sends a warning email notification to the admin. It also prints a per-category breakdown showing the size of active, rotated, compressed, and archived files separately.

#### Key Features:

- **Log Directory Size Check**: Calculates the total size of the log directory.
- **Per-Category Breakdown**: Separates file sizes into four buckets: active log files, rotated backups, gzip-compressed files, and archived bundles.
- **Configurable Size Limit**: Compares the total size against a configured limit.
- **Email Notification**: Sends a warning email to the administrator when the limit is exceeded, including the full breakdown in the email body.

#### How It Works:

1. **Setup Log Directory**: The command retrieves the log directory from Django settings, specifically `DJANGO_LOGGING['LOG_DIR']` or the default. If the directory doesn't exist, an error is logged and displayed.
2. **Categorize Files**: Classifies each file as active (`<level>.log`), rotated (`<level>.log.N`, etc.), compressed (`.gz`), or archived (inside `archive/`).
3. **Compare with Size Limit**: Compares the total directory size (in MB) with the configured `LOG_DIR_SIZE_LIMIT`.
4. **Send Warning Email**: If the limit is exceeded, sends a warning email to the admin that includes the full per-category breakdown.

#### Command Execution:

To execute the command, use the following syntax:
```shell
python manage.py logs_size_audit
```

#### Example:

Running the command produces a size breakdown:

```
Log directory size breakdown:
  active          5 file(s)       0.42 MB
  rotated        12 file(s)      18.30 MB
  compressed      8 file(s)       4.10 MB
  archived        3 file(s)       2.00 MB
  TOTAL                          24.82 MB
```

If the total exceeds `LOG_DIR_SIZE_LIMIT`, an email is sent to `ADMIN_EMAIL` configured in Django settings.


### rotate_logs Command

This Django management command manually triggers an immediate rollover on all active rotating log handlers. It is useful in deployment scripts to start fresh log files right after a release, while safely preserving old log content in numbered backup files.

#### Key Features:

- **Immediate Rollover**: Calls `doRollover()` on every live `RotatingFileHandler` or `TimedRotatingFileHandler` found across all active loggers.
- **Graceful Skip**: Plain `FileHandler` instances (when `LOG_ROTATION TYPE` is `"none"`) are reported as skipped rather than causing an error.
- **Multi-Handler Support**: Rotates all qualifying handlers in a single pass, regardless of which logger they are attached to.

#### How It Works:

1. Iterates over the root logger and all named loggers.
2. For each handler that is a `RotatingFileHandler` or `TimedRotatingFileHandler`, acquires the handler lock, calls `doRollover()`, and releases the lock.
3. Reports rotated file paths and skipped plain handlers to stdout.

#### Command Execution:

To execute the command, use the following syntax:
```shell
python manage.py rotate_logs
```

#### Example:

When rotation succeeds:
```
Rotated 5 handler(s):
  /var/log/myapp/debug.log
  /var/log/myapp/info.log
  ...
```

When no rotating handlers are configured:
```
No rotating handlers found. Set LOG_ROTATION TYPE to 'size' or 'time' to enable rotation.
```


### archive_logs Command

This Django management command moves rotated log files into a timestamped subdirectory under `logs/archive/`. Active `<level>.log` files are never touched. Optionally, individual files can be gzip-compressed before moving, and the entire archive directory can be bundled into a single `tar.gz` or `zip` file.

#### Key Features:

- **Safe Archiving**: Only rotated files (`debug.log.1`, `info.log.2024-01-15`, etc.) are moved. Active `.log` files remain in place.
- **`--compress`**: Gzip-compresses each uncompressed rotated file before archiving (`info.log.1` → `info.log.1.gz`).
- **`--bundle`**: After archiving, bundles the entire timestamped directory into a single `tar.gz` or `zip` file and removes the directory.
- **`--dry-run`**: Prints exactly what would happen without touching any files.
- **Re-Run Safe**: Existing `archive/` subdirectories are never re-archived on subsequent runs.

#### How It Works:

1. Scans for recognized configured-level rotated filenames (`info.log.1`, `error.log.2026-10-18`, optional `.gz`, and JSON/XML counterparts). Unrelated files, symlinks and already archived paths are excluded.
2. Creates `<LOG_DIR>/archive/<YYYY-MM-DD_HHMMSS_microseconds>/` and preserves relative subdirectories to avoid filename collisions.
3. If `--compress` is set, gzips into a temporary file, atomically installs the compressed result, then removes the source. An interrupted copy leaves the original intact.
4. If `--bundle` is set, the timestamped directory is compressed into a single file and then deleted after bundling completes.

#### Command Execution:

To execute the command, use the following syntax:
```shell
# Basic — move rotated files into archive/
python manage.py archive_logs

# Gzip each file before moving
python manage.py archive_logs --compress

# Bundle the archive directory into a tar.gz and remove it
python manage.py archive_logs --bundle tar.gz

# Bundle into a zip file
python manage.py archive_logs --bundle zip

# Compress individual files and then bundle into tar.gz
python manage.py archive_logs --compress --bundle tar.gz

# Preview everything without touching any files
python manage.py archive_logs --compress --bundle tar.gz --dry-run
```

#### Arguments:

- `--compress`: Gzip-compress each uncompressed rotated file before moving it to the archive directory. Files that are already `.gz` are moved as-is.
- `--bundle <FORMAT>`: After archiving, bundle the entire timestamped archive directory into a single compressed file and remove the source directory. Supported formats: `tar.gz`, `zip`.
- `--dry-run`: Print what would be archived and bundled without moving or creating any files.

#### Example:

```
Archived 3 file(s) to /var/log/myapp/archive/2024-03-15_143022:
  /var/log/myapp/archive/2024-03-15_143022/debug.log.1.gz
  /var/log/myapp/archive/2024-03-15_143022/info.log.2024-03-14.gz
  /var/log/myapp/archive/2024-03-15_143022/error.log.1.gz
Bundled archive directory into /var/log/myapp/archive/2024-03-15_143022.tar.gz (0.04 MB) and removed the source directory.
```

Resulting layout after `--bundle tar.gz`:

```
logs/
  debug.log                          ← active, untouched
  info.log                           ← active, untouched
  archive/
    2024-03-15_143022.tar.gz         ← all rotated files, bundled and compressed
```

## LogiBoard Integration

The `LogiBoard` in the `django_logging` package provides an interface for uploading, extracting, and exploring log files that have been zipped and shared via email. This allows for easier log management.

> **Note: Superuser Access Only**
>
> Only superusers have access to the LogiBoard URL. If accessed by a non-superuser, they will get Access Denied page made by Lazarus.

### Setup Instructions

1. **Add to URLs**:
   Include the following in your URL configuration to enable access to LogiBoard:

   ```python
   from django.urls import path, include


   urlpatterns = [
       # ...
       path('django-logging/', include('django_logging.urls')),
       # ...
   ]
   ```
   LogiBoard will be accessible at the following link in your project after setting it up:
   ``/django-logging/log-iboard/``

2. **Static Files**:
   Run the following command to collect and prepare the static files necessary for LogiBoard's interface:

   ```shell
   python manage.py collectstatic
   ```
   The `collectstatic` command is required to gather and serve static assets (such as JavaScript, CSS, and images) used by LogiBoard. This ensures the front-end of the log upload and browsing interface works correctly.

3. **Enable LogiBoard**:
   In your settings file, ensure the following setting is added under ``DJANGO_LOGGING``:

   ```python
   DJANGO_LOGGING = {
       # ...
       "INCLUDE_LOG_iBOARD": True,
       # ...
   }
   ```
   This setting ensures that LogiBoard is available in your project.

### Using LogiBoard

Logiboard is designed to help administrators easily review log files that have been zipped and sent via email (generated by the ``send_logs`` management command). This is particularly useful for remotely retrieving log files from production systems or shared environments.

- **Access Logiboard**: Go to the link `/django-logging/log-iboard/` in your project to open the LogiBoard interface.
- **Upload ZIP Files**: Click the upload icon or drag and drop ZIP files into the upload area. Only ZIP files are supported for upload.
- **Explore Log Files**: After uploading, Logiboard automatically extracts the log files and displays their structure. You can browse through directories and open log files in supported formats, such as `.log`, `.txt`, `.json`, and `.xml`.
- **Upload New Files**: Once you're done reviewing, click the "Send Another" button to upload and explore more logs.

LogiBoard makes it simple to manage and review logs, ensuring you can quickly access and analyze critical log data.



## Custom handlers, formatters, and loggers

`dj-logging` is plug-and-play by default, but it does **not** restrict you to its built-in handlers, formatters, or rotation strategies. All custom components are configured under the existing `DJANGO_LOGGING["COMPONENTS"]` dictionary. The definitions follow Python's standard `logging.config.dictConfig` conventions. No fork of this package is needed.

For example, you can add an independent audit log with its own rotating file handler:

```python
DJANGO_LOGGING = {
    "COMPONENTS": {
        "formatters": {
            "audit": {"format": "%(asctime)s %(levelname)s %(message)s"},
        },
        "handlers": {
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "/var/log/myapp/audit.log",
                "maxBytes": 10_485_760,
                "backupCount": 5,
                "formatter": "audit",
                "level": "INFO",
            },
        },
        "loggers": {
            "myapp.audit": {
                "handlers": ["audit_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    },
}
```

```python
import logging
logging.getLogger("myapp.audit").info("Audit event")
```

Custom formatters, filters and handlers can use dotted class paths or standard `()` factories. Use `COMPONENTS["replace"]` to replace a named built-in preset (such as the `info` handler), or `COMPONENTS["disable"]` to remove one. Each operation must be explicit; naming collisions and unresolved references raise configuration errors. `root_handlers` adds chosen custom handlers to the additive root route, while `package_handlers` adds them to the `django_logging` namespace. Other application loggers and handlers are preserved unless explicitly opted into changes.

Declared but unattached custom components are not instantiated in `additive` or `isolated` mode; only components reachable through configured handlers and their dependencies are constructed. Dependent handlers are closed on reinitialization. An explicitly listed built-in `console` handler in `root_handlers` is installed on root as requested; this may create duplicate console output if your application already has a console handler.

Existing `LOG_ROTATION` settings continue working; they are shortcuts for the built-in file handlers, not a limit on third-party handlers. Do not share a standard `RotatingFileHandler` across multiple Gunicorn workers writing to the same file. See [Checkpoint 06 — extensible components](CHECKPOINT_06_EXTENSIBLE_COMPONENTS.md) for advanced examples, compatibility semantics, and caveats.

## Settings

`dj-logging` auto-initializes when `django_logging` is added to `INSTALLED_APPS`. By default, it adds package-owned file destinations **alongside** the handlers configured by Django. It does not change the root logger's level, replace existing handlers, or disable other loggers. You can customize the behavior with `DJANGO_LOGGING`.

#### How logging is initialized

- **Default: plug-and-play additive setup.** `AUTO_INITIALIZATION_ENABLE=True` and `LOGGING_SETUP_MODE="additive"` create the configured files, attach package-owned file/email handlers to root, and configure the `django_logging` logger. Existing root handlers and logger levels are preserved. No second root console handler is added.
- **Isolated setup.** `LOGGING_SETUP_MODE="isolated"` configures only the `django_logging` namespace; application logs do not automatically reach its files.
- **Opt out.** Set `AUTO_INITIALIZATION_ENABLE=False` to manage logging exclusively through standard Django `LOGGING` or initialize the package manually.
- **Legacy root setup (explicit opt in).** `LOGGING_SETUP_MODE="replace_root"` performs the original `dictConfig()` root replacement; select it only when you intend to delegate root logging to the package.

**Routing note:** Additive mode receives application records that reach the root logger. It respects logger levels, filters and `propagate=False` declarations: explicit app logger routes may bypass it. For example, the default Python root level is WARNING, so INFO messages from an otherwise unconfigured application logger need an appropriate level in Django's `LOGGING` settings. The `django_logging` namespace is configured to emit its own INFO request events. This is not a guarantee that every application log is collected.

**Migration from v2.1.0:** the package remains automatic by default, but root logging is no longer replaced automatically. Console output and log routing can differ because existing application handlers and levels are preserved. To retain the old global setup exactly, select `"LOGGING_SETUP_MODE": "replace_root"`. Other existing package options continue to work.

Example with explicit additive setup (optional; it is the default):

```python
DJANGO_LOGGING = {
    "AUTO_INITIALIZATION_ENABLE": True,
    "LOGGING_SETUP_MODE": "additive",
    "LOG_FILE_LEVELS": ["INFO", "ERROR"],
}
```

For package-only logging, use `isolated`. To disable setup entirely, set `AUTO_INITIALIZATION_ENABLE=False`. `django_logging.filters.ContextVarFilter` remains available for use in your own Django `LOGGING` handlers.


#### Default configuration:

```python
DJANGO_LOGGING = {
    "AUTO_INITIALIZATION_ENABLE": True,
    "LOGGING_SETUP_MODE": "additive",
    "INITIALIZATION_MESSAGE_ENABLE": True,
    "LOG_SQL_QUERIES_ENABLE": False,
    "REQUEST_LOGGING": {},  # See request middleware configuration above
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
    "EXTRA_LOG_FILES": {
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
        "MAX_CONCURRENT": 4,
        "SMTP_TIMEOUT": 10,
    },
    "LOG_SIZE_AUDIT_IN_REQUEST": False,
    # Rotation (all optional — defaults to no rotation)
    "LOG_ROTATION": {
        "TYPE": "none",
        "MAX_BYTES": 10485760,  # 10 MB
        "BACKUP_COUNT": 5,
        "WHEN": "midnight",
        "INTERVAL": 1,
        "COMPRESS": False,
    },
    "LOG_ROTATION_OVERRIDES": {},
}
```
#### Configuration Options:

Here's a breakdown of the available configuration options:

`AUTO_INITIALIZATION_ENABLE`
----------------------------

- **Type**: `bool`
- **Description**: Enables automatic initialization of logging configurations.
- **Default**: `True`

`LOGGING_SETUP_MODE`
--------------------

- **Type**: `str` (`"additive"`, `"isolated"` or `"replace_root"`)
- **Default**: `"additive"`
- **Description**: Chooses additive application logging, isolated package logging, or explicit legacy root replacement.

`INITIALIZATION_MESSAGE_ENABLE`
-------------------------------

- **Type**: `bool`
- **Description**: Enables logging of the initialization message when logging starts.
- **Default**: `True`

`INCLUDE_LOG_iBOARD`
--------------------

- **Type**: ``bool``
- **Description**: Makes LogiBoard url accessible in the project. for setting up the LogiBoard, please refer to the [LogiBoard Integration](#LogiBoard-Integration).
- **Default**: `False`

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
      - **Description**: Determines whether the email should include the packaged HTML template.

    - `MAX_CONCURRENT`:
      - **Type**: `int` (1–64)
      - **Default**: `4`
      - **Description**: Maximum in-flight SMTP notification threads **per worker process**. Additional notifications are dropped with a warning rather than queued. There is no delivery guarantee.

    - `SMTP_TIMEOUT`:
      - **Type**: `int` seconds (1–120)
      - **Default**: `10`
      - **Description**: Socket timeout for SMTP connections; failures are logged without changing application request outcomes.

`LOG_SIZE_AUDIT_IN_REQUEST`
---------------------------

- **Type**: `bool`
- **Default**: `False`
- **Description**: Opt-in legacy behavior that runs filesystem log-size audits during an HTTP request. Use a scheduler and the `logs_size_audit` management command instead.

`LOG_ROTATION`
--------------

- **Type**: `dict`
- **Description**: Controls how log files are rotated. By default no rotation is applied and a plain `FileHandler` is used. Setting `TYPE` to `"size"` or `"time"` switches the underlying handler automatically for every log level — no other code changes required.

  - `TYPE`:
    - **Type**: `str`
    - **Choices**: `"none"` | `"size"` | `"time"`
    - **Description**: Selects the rotation strategy. `"none"` uses plain `FileHandler`, `"size"` uses `RotatingFileHandler`, `"time"` uses `TimedRotatingFileHandler`, and `"external"` uses POSIX `WatchedFileHandler` (for rotation by `logrotate` or a similar external process). `COMPRESS` must be false for `"external"`.
    - **Default**: `"none"`

  - `MAX_BYTES`:
    - **Type**: `int`
    - **Description**: Maximum file size in bytes before rotation. Only used when `TYPE="size"`.
    - **Default**: `10485760` (10 MB)

  - `BACKUP_COUNT`:
    - **Type**: `int`
    - **Description**: Number of rotated backup files to keep. `0` keeps all rotated files indefinitely.
    - **Default**: `5`

  - `WHEN`:
    - **Type**: `str`
    - **Description**: Time unit for timed rotation. Only used when `TYPE="time"`. Accepted values: `"s"`, `"m"`, `"h"`, `"d"`, `"midnight"`, `"W0"`–`"W6"`.
    - **Default**: `"midnight"`

  - `INTERVAL`:
    - **Type**: `int`
    - **Description**: Number of `WHEN` units between rotations. Only used when `TYPE="time"`.
    - **Default**: `1`

  - `COMPRESS`:
    - **Type**: `bool`
    - **Description**: When `True`, each rotated file is gzip-compressed automatically (e.g. `debug.log.1.gz`). Works with both `"size"` and `"time"` rotation types.
    - **Default**: `False`

**Gunicorn / multiprocess warning:** Python's built-in size/time rotating file handlers are not safe when multiple independent worker processes rotate the same path. Use log collection through stdout/stderr in container environments, or `LOG_ROTATION={"TYPE": "external", "COMPRESS": False}` with an external rename/create rotation scheme on POSIX. `WatchedFileHandler` detects inode replacement but **does not provide inter-process record locking**. Avoid `copytruncate` if loss of logs is unacceptable. `rotate_logs` operates only on handlers in the current process; it cannot rotate other running workers' handlers. Neither SMTP notifications nor per-process counters are durable across crashes.

`LOG_ROTATION_OVERRIDES`
------------------------

- **Type**: `dict[str, dict]`
- **Description**: Per-level rotation overrides. Each key must be a valid log level (`"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`). The value is a partial `LOG_ROTATION` dict — only the keys you supply are changed; everything else is inherited from the global `LOG_ROTATION` config.
- **Default**: `{}`

### Rotation settings reference

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `TYPE` | `str` | `"none"`, `"size"`, `"time"`, or `"external"` | `"none"` |
| `MAX_BYTES` | `int` | Max file size in bytes before rotation (size only) | `10485760` |
| `BACKUP_COUNT` | `int` | Number of rotated files to keep; `0` keeps all | `5` |
| `WHEN` | `str` | Timed rotation interval unit (time only) | `"midnight"` |
| `INTERVAL` | `int` | Number of `WHEN` units between rotations (time only) | `1` |
| `COMPRESS` | `bool` | Gzip-compress each rotated file | `False` |


## Structured logging and redaction

When a file level uses `"JSON"`, `"XML"` or `"FLAT"` in `LOG_FILE_FORMAT_TYPES`,
its formatter also uses the optional `STRUCTURED_LOGGING` configuration under
**the existing `DJANGO_LOGGING` dictionary**. No additional package or service is
required. Automatic initialization stays enabled in additive mode by default.

```python
DJANGO_LOGGING = {
    "LOG_FILE_FORMAT_TYPES": {"INFO": "JSON", "ERROR": "JSON"},
    "STRUCTURED_LOGGING": {
        "REDACT_FIELDS": ["customer_reference"],
        "MAX_DEPTH": 8,
        "MAX_ITEMS": 100,
        "MAX_STRING_LENGTH": 4096,
        "MAX_EVENT_BYTES": 65536,
        "MAX_EXCEPTION_FRAMES": 32,
        "INCLUDE_EXTRA": True,
        "EXCEPTION_MODE": "traceback",  # 'traceback', 'type', 'omit'
        "JSON_COMPACT": True,
        "XML_PRETTY": True,
    },
}
```

```python
logger.info("Order processed", extra={"order_id": 42, "customer_reference": "private"})
# JSON includes: "message": "Order processed",
# "extra": {"order_id": 42, "customer_reference": "[REDACTED]"}
```

Structured JSON uses **one JSON object per line** by default, preserving the
original log message rather than extracting/removing `key=value` fragments.
Extra fields appear under `extra` and context variables under `context` when
those values are included in the format. The formatter supports standard
Python logging specifiers in `LOG_FILE_FORMATS`. XML remains pretty-printed by
default; invalid field names are represented as `<field name="...">`. FLAT
values escape newlines and quotes to keep events on one line.

Sensitive field names are redacted recursively using built-in security names
(e.g. passwords, API keys, tokens, and email) and `REDACT_FIELDS`. Values,
collection sizes, nesting depth, total event size, and traceback frame formatting
are bounded; an oversized event is replaced with a small omission marker rather
than malformed output. `MAX_EXCEPTION_FRAMES` defaults to `32` and accepts values
from `1` to `128`.
Unsupported Python objects are not stringified to avoid exposing secrets via
`__repr__` or `__str__`.

**Security limitation:** free-form log messages, SQL text, and traceback text
can contain secrets even when structured fields are redacted. Automatic
field-name redaction cannot reliably sanitize such strings. Avoid putting
credentials, bodies, tokens, personal data, or raw SQL into log messages. For
high-sensitivity deployments, set `EXCEPTION_MODE` to `"type"` or `"omit"`.

**Compatibility note:** JSON formatters no longer automatically parse
`key=value` fragments into top-level keys or remove them from messages.
Applications relying on those inferred keys must switch to `extra={...}` or
explicit context variables. Existing text formatters and standard Python
logging APIs are otherwise retained.

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

## Python and Django compatibility

The supported target matrix is Python **3.10–3.14** with Django **5.2**, and
Python **3.12–3.14** with Django **6.0 or 6.1**. Each valid combination is tested
individually using tox in GitHub Actions. Django 6.x does not support Python
3.10 or 3.11.

Developers can run one combination with, for example:

```bash
python -m pip install tox
python -m tox -e py313-django61
```

Run `python scripts/check_release_matrix.py` (Python 3.11+ with PyYAML) to
check that CI and tox declare the same supported matrix.

`execution_tracker` supports awaited async functions for elapsed-time
measurement. Query counting (`log_queries=True`) is supported only for
synchronous functions in Django `DEBUG` mode; decorating an async function
with SQL tracking enabled raises `ValueError`. It never clears accumulated
Django SQL debug history.

## Conclusion

Thank you for using `django_logging`. We hope this package enhances your Django application's logging capabilities. For more detailed documentation, customization options, and updates, please refer to the official documentation on [Read the Docs](https://django-logging.readthedocs.io/). If you have any questions or issues, feel free to open an issue on our [GitHub repository](https://github.com/lazarus-org/django_logging).

Happy logging!
