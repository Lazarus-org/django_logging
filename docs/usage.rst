Usage
=====

Once ``django_logging`` is installed and added to your ``INSTALLED_APPS``, you can start using it right away. The package provides several features to customize and enhance logging in your Django project. Below is a guide on how to use the various features provided by `django_logging`.

Basic logging usage
-------------------

``dj-logging`` uses Python's standard ``logging`` API, so existing application
code does not need a package-specific logger class:

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)
    logger.debug("Debug detail")
    logger.info("Application event", extra={"job_id": 42})
    logger.warning("A recoverable issue occurred")
    logger.error("An operation failed")

Routing depends on ``DJANGO_LOGGING["LOGGING_SETUP_MODE"]`` and your existing
Django logging configuration. In the default ``additive`` mode, package-owned
file handlers are attached alongside existing root handlers, but existing
logger levels, filters and ``propagate=False`` routes remain in control. Records
must reach root and pass its effective level to be handled by the package's root
route. The ``django_logging`` namespace has its own package handlers. See
:doc:`settings` for the differences between ``additive``, ``isolated`` and
``replace_root``.

Context manager
---------------

``config_setup()`` temporarily installs the package's handlers on the
``django_logging`` logger namespace only. It does not replace root logging or
redirect unrelated application loggers. Automatic initialization must be
explicitly disabled before using it:

.. code-block:: python

    import logging
    from django_logging.utils.context_manager import config_setup

    with config_setup():
        logging.getLogger("django_logging.example").info("Inside package setup")

This changes process-global package logger state for the duration of the block.
Use it for controlled startup or standalone tooling, not as a request-scoped
configuration mechanism or where other threads may log under ``django_logging``.
The prior package logger configuration is restored when the block exits. If a
managed ``dj-logging`` configuration is already active, ``config_setup()`` raises
``RuntimeError`` rather than replacing it.

To use it, set:

.. code-block:: python

    DJANGO_LOGGING = {"AUTO_INITIALIZATION_ENABLE": False}

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

Execution tracker
-----------------

The ``execution_tracker`` decorator logs function execution time and can
optionally count synchronous Django debug queries.

.. code-block:: python

    import logging
    from django_logging.decorators import execution_tracker


    @execution_tracker(
        logging_level=logging.INFO,
        log_queries=True,
        query_threshold=10,
        query_exceed_warning=True,
    )
    def load_dashboard():
        # Perform synchronous application/database work.
        ...

Arguments:

* ``logging_level``: logging level for the completion metric; default
  ``logging.INFO``.
* ``log_queries``: whether to count synchronous queries when Django's debug
  query history is available; default ``False``.
* ``query_threshold``: optional non-negative threshold for query counts.
* ``query_exceed_warning``: emit a warning when the threshold is exceeded;
  default ``False``.

The decorator no longer clears Django's existing SQL query history. Query counts
are best-effort because Django's query history can be bounded and may be shared
with other work. If ``log_queries=True`` while ``DEBUG=False``, query counts are
not available and a warning is emitted. Asynchronous functions are timed through
their awaited completion, but ``log_queries=True`` is rejected for async functions
because a synchronous connection's history cannot reliably count queries across
async execution contexts.

Request logging middleware
--------------------------

``django_logging.middleware.RequestLogMiddleware`` supports synchronous and
asynchronous Django request handling. Enable it through the normal middleware
setting:

.. code-block:: python

    MIDDLEWARE = [
        # ...
        "django_logging.middleware.RequestLogMiddleware",
        # ...
    ]

By default, the middleware emits one INFO completion event with the request
method, bounded path, request ID, already-resolved user ID (or ``Anonymous``),
status code, content type and response-object latency in milliseconds. It does
not resolve a lazy session user solely for logging and does not read ordinary
response bodies. The completion duration ends when the response object is
returned; it does not measure the full time taken to consume a streaming body.

Request IDs are exposed as ``request.request_id`` and included in logging
context. A valid incoming ``X-Request-ID`` may be reused; values must be short
ASCII identifiers containing letters, digits, ``-``, ``_`` or ``.``. Invalid
values are replaced with a generated UUID. Request context is scoped and restored
on exceptions/cancellation, and is re-established for each stream iteration.

All request-specific options are nested inside the existing ``DJANGO_LOGGING``
setting. See the :ref:`request-logging` reference for the complete list. For
example, to enable query-value diagnostics while excluding authentication paths:

.. code-block:: python

    DJANGO_LOGGING = {
        "REQUEST_LOGGING": {
            "LOG_QUERY_PARAMS": True,
            "EXCLUDED_PATH_PREFIXES": ["/auth", "/admin"],
            "MAX_QUERY_BYTES": 4096,
        },
    }

**Security defaults:** query values, JSON request bodies, JSON error response
bodies and SQL diagnostics are disabled by default regardless of Django's
``DEBUG`` setting. Sensitive field names are redacted, diagnostic data is
bounded, and excluded paths suppress value diagnostics. Field-name redaction is
best-effort; don't log secrets or enable raw SQL diagnostics on sensitive
production traffic. ``X-Forwarded-For`` is not trusted. Configure
``TRUSTED_PROXY_CIDRS`` only for proxy peer networks that overwrite
``X-Real-IP``.

Additional stream lifecycle messages are disabled by default. Set
``REQUEST_LOGGING["LOG_STREAMING_EVENTS"]`` to ``True`` to log stream start,
finish, close and cancellation events. Streaming failures are still logged when
this option is disabled.

Monitor log-size auditing
-------------------------

Prefer scheduling the management command outside HTTP request handling, for
example weekly with cron, systemd timers or an existing task scheduler:

.. code-block:: shell

    python manage.py logs_size_audit

The command checks ``LOG_DIR_SIZE_LIMIT`` and reports when the configured log
directory exceeds the threshold. ``MonitorLogSizeMiddleware`` remains available
for compatibility, but is a pass-through by default. To restore the legacy
request-time audit, both add the middleware and explicitly set
``DJANGO_LOGGING["LOG_SIZE_AUDIT_IN_REQUEST"] = True``. The triggering request
waits for the audit to finish, so this behavior is discouraged in production.

Context Variable Management
---------------------------

``django_logging`` includes a powerful ``ContextVarManager`` class, allowing you to manage context variables dynamically within your logging system. These variables are bound to the current context and automatically included in your log entries via the ``%(context)s`` placeholder in the log format.

Binding and Unbinding Context Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``ContextVarManager`` provides several methods to manage context variables efficiently:

``bind(**kwargs)``
~~~~~~~~~~~~~~~~~~

The ``bind`` method allows you to bind key-value pairs as context variables that will be available during the current context. These variables can be used to add contextual information to log entries.

**Example**:

.. code-block:: python

   from django_logging.contextvar import manager
   import logging

   logger = logging.getLogger(__name__)

   # Binding context variables
   manager.bind(user="test_user", request_id="abc123")

   logger.info("Logging with context")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:00:00 | Logging with context | {'user': 'test_user', 'request_id': 'abc123'}

``unbind(key: str)``
~~~~~~~~~~~~~~~~~~~~

The ``unbind`` method removes a specific context variable by its key. It effectively clears the context variable from the log entry.

**Example**:

.. code-block:: python

   manager.unbind("user")

   logger.info("Logging without the 'user' context")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:05:00 | Logging without the 'user' context | {'request_id': 'abc123'}

Batch Binding and Resetting Context Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``batch_bind(**kwargs)``
~~~~~~~~~~~~~~~~~~~~~~~~

The ``batch_bind`` method binds multiple context variables at once and returns tokens that can be used later to reset the variables to their previous state. This is useful when you need to bind a group of variables temporarily.

**Example**:

.. code-block:: python

   tokens = manager.batch_bind(user="admin_user", session_id="xyz789")

   logger.info("Logging with batch-bound context")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:10:00 | Logging with batch-bound context | {'user': 'admin_user', 'session_id': 'xyz789'}

``reset(tokens: Dict[str, contextvars.Token])``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``reset`` method allows you to reset context variables to their previous state using tokens returned by ``batch_bind``.

**Example**:

.. code-block:: python

   manager.reset(tokens)

   logger.info("Context variables have been reset")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:15:00 | Context variables have been reset |

``clear()``
~~~~~~~~~~~

The ``clear`` method clears all bound context variables at once, effectively removing all contextual data from the log entry.

**Example**:

.. code-block:: python

   manager.clear()

   logger.info("All context variables cleared")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:20:00 | All context variables cleared |

Retrieving and Merging Context Variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``get_contextvars()``
~~~~~~~~~~~~~~~~~~~~~

The ``get_contextvars`` method retrieves the current context variables available in the context. This method is useful for inspecting or debugging the context.

**Example**:

.. code-block:: python

   current_context = manager.get_contextvars()
   print(current_context)  # Output: {'user': 'admin_user', 'session_id': 'xyz789'}

``merge_contexts(bound_context: Dict[str, Any], local_context: Dict[str, Any])``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``merge_contexts`` method merges two dictionaries of context variables, giving priority to the ``bound_context``. This is useful when you want to combine different sources of context data.

**Example**:

.. code-block:: python

   bound_context = {"user": "admin_user"}
   local_context = {"request_id": "12345"}

   merged_context = manager.merge_contexts(bound_context, local_context)
   print(merged_context)  # Output: {'user': 'admin_user', 'request_id': '12345'}

``get_merged_context(bound_logger_context: Dict[str, Any])``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``get_merged_context`` method combines the bound logger context with the current context variables, allowing you to retrieve a single dictionary with all the context data.

**Example**:

.. code-block:: python

   bound_logger_context = {"app_name": "my_django_app"}

   merged_context = manager.get_merged_context(bound_logger_context)
   print(merged_context)  # Output: {'app_name': 'my_django_app', 'user': 'admin_user'}

Scoped Context Management
^^^^^^^^^^^^^^^^^^^^^^^^^

``scoped_context(**kwargs)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``scoped_context`` method provides a context manager to bind context variables temporarily for a specific block of code. After the block completes, the context variables are automatically unbound.

**Example**:

.. code-block:: python

   with manager.scoped_context(transaction_id="txn123"):
       logger.info("Scoped context active")

   logger.info("Scoped context no longer active")

**Log Output**:

.. code-block:: text

   INFO | 2024-10-03 12:30:00 | Scoped context active | {'transaction_id': 'txn123'}
   INFO | 2024-10-03 12:30:10 | Scoped context no longer active |


send_logs Command
-----------------

This Django management command zips the log directory and emails it to a specified email address. The command is useful for retrieving logs remotely and securely, allowing administrators to receive log files via email.

Key Features
^^^^^^^^^^^^

- **Zips Log Directory**: Automatically compresses the log directory into a single zip file.
- **Email Log Files**: Sends the zipped log file to a specified email address.

How It Works
^^^^^^^^^^^^

1. **Setup Log Directory**: The command retrieves the log directory from Django settings (``DJANGO_LOGGING['LOG_DIR']``).
2. **Zip the Logs**: Compresses the entire log directory into a zip file stored in a temporary location.
3. **Email the Zip File**: Sends the zipped log file to the email address provided as an argument, attaching it to an email message.
4. **Cleanup**: After sending the email, the temporary zip file is deleted to free up disk space.

Command Execution
^^^^^^^^^^^^^^^^^

To execute the command, use the following syntax:

.. code-block:: shell

  python manage.py send_logs <email>

Example
^^^^^^^

If you want to send the logs to `admin@example.com`, the command would be:

.. code-block:: shell

  python manage.py send_logs admin@example.com

This will zip the log directory and send it to `admin@example.com` with the subject "Log Files".


generate_pretty_json Command
----------------------------

This Django management command allows you to locate and prettify JSON log files stored in a log directory that generated by ``django_logging``. It takes JSON files from the log directory, formats them into a clean, readable structure, and saves the result in the ``pretty`` directory.

Key Features
^^^^^^^^^^^^

- **Locate JSON Logs**: Automatically finds ``.json`` files in the `json` log directory.
- **Pretty Formatting**: Reformats the JSON logs into a valid JSON array with proper indentation, improving readability.
- **Separate Output Directory**: Saves the reformatted JSON files in a ``pretty`` subdirectory, preserving the original files.

How It Works
^^^^^^^^^^^^

1. **Setup Directories**: The command looks for a ``json`` subdirectory within your defined log directory. If it doesn't exist, an error is displayed.
2. **Process JSON Files**: Each `.json` file found in the directory is processed:
   - Parses multiple JSON objects within the file.
   - Reformats them as a pretty JSON array with proper indentation.
   - Saves the new, formatted JSON in the ``pretty`` subdirectory with the prefix ``formatted_``.

Command Execution
^^^^^^^^^^^^^^^^^

To execute the command, use the following syntax:

.. code-block:: bash

   python manage.py generate_pretty_json

Example
^^^^^^^

Running the command will process the following files:

- ``logs/json/error.json`` ➡ ``logs/json/pretty/formatted_error.json``
- ``logs/json/info.json`` ➡ ``logs/json/pretty/formatted_info.json``


generate_pretty_xml Command
---------------------------

This Django management command allows you to locate and reformat XML log files stored in a log directory generated by ``django_logging``. It processes XML files by wrapping their content in a `<logs>` element and saves the reformatted files in a separate directory.

Key Features
^^^^^^^^^^^^

- **Locate XML Logs**: Automatically finds ``.xml`` files in the ``xml`` log directory.
- **Reformatting**: Wraps XML content in a `<logs>` element, ensuring consistency in structure.
- **Separate Output Directory**: Saves the reformatted XML files in a ``pretty`` subdirectory with the prefix ``formatted_``, preserving the original files.

How It Works
^^^^^^^^^^^^

1. **Setup Directories**: The command looks for an ``xml`` subdirectory within your defined log directory. If it doesn't exist, an error is displayed.
2. **Process XML Files**: Each `.xml` file found in the directory is processed:
   - The content of each XML file is wrapped inside a `<logs>` element.
   - The reformatted file is saved in the ``pretty`` subdirectory with the prefix ``formatted_``.

Command Execution
^^^^^^^^^^^^^^^^^

To execute the command, use the following syntax:

.. code-block:: bash

   python manage.py generate_pretty_xml

Example
^^^^^^^

Running the command will process the following files:

- ``logs/xml/error.xml`` ➡ ``logs/xml/pretty/formatted_error.xml``
- ``logs/xml/info.xml`` ➡ ``logs/xml/pretty/formatted_info.xml``


logs_size_audit Command
--------------------------

This Django management command monitors the size of your log directory. If the total size exceeds the configured limit, the command sends a warning email notification to the admin. It also prints a per-category breakdown showing the size of active, rotated, compressed, and archived files separately.

Key Features
^^^^^^^^^^^^

- **Log Directory Size Check**: Calculates the total size of the log directory.
- **Per-Category Breakdown**: Separates file sizes into four buckets: active log files, rotated backups, gzip-compressed files, and archived bundles.
- **Configurable Size Limit**: Compares the total size against ``LOG_DIR_SIZE_LIMIT`` in settings.
- **Email Notification**: Sends a warning email to the administrator when the limit is exceeded, including the full breakdown in the email body.

How It Works
^^^^^^^^^^^^

1. **Setup Log Directory**: Retrieves the log directory from ``DJANGO_LOGGING['LOG_DIR']``. If the directory doesn't exist, an error is displayed.
2. **Categorize Files**: Classifies each file as active (``<level>.log``), rotated (``<level>.log.N``, etc.), compressed (``.gz``), or archived (inside ``archive/``).
3. **Compare with Size Limit**: Compares the total size in MB with ``LOG_DIR_SIZE_LIMIT``.
4. **Send Warning Email**: If the limit is exceeded, sends a warning email to ``ADMIN_EMAIL`` that includes the full breakdown.

Command Execution
^^^^^^^^^^^^^^^^^

To execute the command, use the following syntax:

.. code-block:: shell

   python manage.py logs_size_audit

Example
^^^^^^^

Running the command produces a size breakdown:

.. code-block:: text

   Log directory size breakdown:
     active          5 file(s)       0.42 MB
     rotated        12 file(s)      18.30 MB
     compressed      8 file(s)       4.10 MB
     archived        3 file(s)       2.00 MB
     TOTAL                          24.82 MB

If the total exceeds ``LOG_DIR_SIZE_LIMIT``, an email is sent to ``ADMIN_EMAIL`` configured in Django settings.

rotate_logs Command
-------------------

This management command manually triggers an immediate rollover on all active rotating log handlers. It is useful in deployment scripts to start fresh log files right after a release, while safely preserving old log content in numbered backup files.

Key Features
^^^^^^^^^^^^

- **Immediate rollover**: calls ``doRollover()`` on every live ``RotatingFileHandler`` or ``TimedRotatingFileHandler`` found across all active loggers.
- **Graceful skip**: plain ``FileHandler`` instances (when ``LOG_ROTATION TYPE`` is ``"none"``) are reported as skipped rather than causing an error.
- **Multi-handler support**: rotates all qualifying handlers in a single pass, regardless of which logger they are attached to.

How It Works
^^^^^^^^^^^^

1. Iterates over the root logger and all named loggers.
2. For each handler that is a ``RotatingFileHandler`` or ``TimedRotatingFileHandler``, acquires the handler lock, calls ``doRollover()``, and releases the lock.
3. Reports rotated file paths and skipped plain handlers to stdout.

Command Execution
^^^^^^^^^^^^^^^^^

.. code-block:: shell

   python manage.py rotate_logs

Example Output
^^^^^^^^^^^^^^

When rotation succeeds:

.. code-block:: text

   Rotated 5 handler(s):
     /var/log/myapp/debug.log
     /var/log/myapp/info.log
     ...

When no rotating handlers are configured:

.. code-block:: text

   No rotating handlers found. Set LOG_ROTATION TYPE to 'size' or 'time' to enable rotation.


archive_logs Command
--------------------

This management command moves rotated log files into a timestamped subdirectory under ``logs/archive/``. Active ``<level>.log`` files are never touched. Optionally, individual files can be gzip-compressed before moving, and the entire archive directory can be bundled into a single ``tar.gz`` or ``zip`` file.

Key Features
^^^^^^^^^^^^

- **Safe archiving**: only rotated files (``debug.log.1``, ``info.log.2024-01-15``, etc.) are moved. Active ``.log`` files remain in place.
- **``--compress``**: gzip-compresses each uncompressed rotated file before archiving (``info.log.1`` → ``info.log.1.gz``).
- **``--bundle``**: after archiving, bundles the entire timestamped directory into a single ``tar.gz`` or ``zip`` file and removes the directory.
- **``--dry-run``**: prints exactly what would happen without touching any files.
- **Re-run safe**: existing ``archive/`` subdirectories are never re-archived on subsequent runs.

How It Works
^^^^^^^^^^^^

1. Scans the log directory for files that do not match the active ``<level>.log`` naming pattern.
2. Creates ``<LOG_DIR>/archive/<YYYY-MM-DD_HHMMSS>/`` and moves the rotated files into it.
3. If ``--compress`` is set, uncompressed files are gzip-compressed during the move.
4. If ``--bundle`` is set, the timestamped directory is compressed into a single file and then deleted.

Command Execution
^^^^^^^^^^^^^^^^^

.. code-block:: shell

   # Basic — move rotated files into archive/
   python manage.py archive_logs

   # Gzip each file before moving
   python manage.py archive_logs --compress

   # Bundle archive directory into a tar.gz and remove the directory
   python manage.py archive_logs --bundle tar.gz

   # Bundle into a zip file
   python manage.py archive_logs --bundle zip

   # Compress individual files and then bundle into tar.gz
   python manage.py archive_logs --compress --bundle tar.gz

   # Preview everything without touching any files
   python manage.py archive_logs --compress --bundle tar.gz --dry-run

Arguments
^^^^^^^^^

``--compress``
  Gzip-compress each uncompressed rotated file before moving it to the archive directory. Files that are already ``.gz`` are moved as-is.

``--bundle <FORMAT>``
  After archiving, bundle the entire timestamped archive directory into a single compressed file and remove the source directory. Supported formats: ``tar.gz``, ``zip``.

``--dry-run``
  Print what would be archived and bundled without moving or creating any files.

Example Output
^^^^^^^^^^^^^^

.. code-block:: text

   Archived 3 file(s) to /var/log/myapp/archive/2024-03-15_143022:
     /var/log/myapp/archive/2024-03-15_143022/debug.log.1.gz
     /var/log/myapp/archive/2024-03-15_143022/info.log.2024-03-14.gz
     /var/log/myapp/archive/2024-03-15_143022/error.log.1.gz
   Bundled archive directory into /var/log/myapp/archive/2024-03-15_143022.tar.gz (0.04 MB) and removed the source directory.

Resulting layout after ``--bundle tar.gz``:

.. code-block:: text

   logs/
     debug.log                           ← active, untouched
     info.log                            ← active, untouched
     archive/
       2024-03-15_143022.tar.gz          ← all rotated files, bundled


Log Rotation
------------

``django_logging`` supports dynamic log file rotation through the ``LOG_ROTATION`` setting. By default no rotation is applied. Setting ``TYPE`` to ``"size"`` or ``"time"`` switches the underlying handler automatically — no other code changes are needed.

For full configuration details refer to the :doc:`Settings <settings>` documentation.

Size-based rotation example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DJANGO_LOGGING = {
       "LOG_ROTATION": {
           "TYPE": "size",
           "MAX_BYTES": 5_000_000,  # 5 MB
           "BACKUP_COUNT": 10,
           "COMPRESS": True,  # produces debug.log.1.gz, info.log.1.gz …
       },
   }

Time-based rotation example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   DJANGO_LOGGING = {
       "LOG_ROTATION": {
           "TYPE": "time",
           "WHEN": "midnight",
           "INTERVAL": 1,
           "BACKUP_COUNT": 30,
       },
   }

Per-level rotation overrides
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Use ``LOG_ROTATION_OVERRIDES`` to give individual log levels a different strategy. Only the keys you specify are changed; everything else inherits from ``LOG_ROTATION``.

.. code-block:: python

   DJANGO_LOGGING = {
       "LOG_ROTATION": {
           "TYPE": "size",
           "MAX_BYTES": 5_000_000,
           "BACKUP_COUNT": 5,
       },
       "LOG_ROTATION_OVERRIDES": {
           "ERROR": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 30},
           "CRITICAL": {"TYPE": "time", "WHEN": "midnight", "BACKUP_COUNT": 90},
       },
   }
