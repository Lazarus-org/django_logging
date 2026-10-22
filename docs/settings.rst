Settings
========

All package configuration lives in Django's ``DJANGO_LOGGING`` dictionary.
``dj-logging`` automatically initializes when ``django_logging`` is in
``INSTALLED_APPS`` unless ``AUTO_INITIALIZATION_ENABLE`` is set to ``False``.

Initialization modes
--------------------

``AUTO_INITIALIZATION_ENABLE`` defaults to ``True``. ``LOGGING_SETUP_MODE``
selects how package-owned handlers are attached:

* ``"additive"`` (default): attaches package-owned file and enabled email
  handlers to the root logger while preserving existing root handlers, the root
  level, and unrelated logger configuration. The package's own
  ``django_logging`` namespace also receives package handlers. The built-in
  console handler is not added to root automatically, avoiding a duplicate
  console stream.
* ``"isolated"``: configures the ``django_logging`` namespace only. Other
  application loggers do not automatically write to the package's files.
* ``"replace_root"``: explicitly opts into the legacy global
  ``logging.config.dictConfig`` setup. Use this only when you intend the package
  to manage the root logging configuration.

With ``"additive"``, an application record must reach the root logger to be
handled by the package's root-attached handlers. Logger levels, filters, and
``propagate=False`` routes still apply. For example, an application logger that
inherits a root ``WARNING`` level will not create an ``INFO`` record unless its
own effective level is configured accordingly. ``AUTO_INITIALIZATION_ENABLE=False``
leaves logging setup to the application or to explicit manual setup.

Default configuration
---------------------

The following shows the main options. Nested dictionaries can be omitted; their
defaults are applied by the package.

.. code-block:: python

    DJANGO_LOGGING = {
        "AUTO_INITIALIZATION_ENABLE": True,
        "LOGGING_SETUP_MODE": "additive",
        "INITIALIZATION_MESSAGE_ENABLE": True,
        "INCLUDE_LOG_iBOARD": False,
        "LOG_SQL_QUERIES_ENABLE": False,
        "LOG_SIZE_AUDIT_IN_REQUEST": False,
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
        "LOG_ROTATION": {
            "TYPE": "none",
            "MAX_BYTES": 10485760,
            "BACKUP_COUNT": 5,
            "WHEN": "midnight",
            "INTERVAL": 1,
            "COMPRESS": False,
        },
        "LOG_ROTATION_OVERRIDES": {},
        "REQUEST_LOGGING": {},
        "STRUCTURED_LOGGING": {},
        "COMPONENTS": {},
    }

Core settings
-------------

``AUTO_INITIALIZATION_ENABLE``
    Boolean, default ``True``. Enable or disable automatic initialization from
    the Django app configuration.

``LOGGING_SETUP_MODE``
    String, default ``"additive"``. Choices are ``"additive"``, ``"isolated"``
    and ``"replace_root"``. See `Initialization modes`_ above.

``INITIALIZATION_MESSAGE_ENABLE``
    Boolean, default ``True``. Emit the package's startup summary.

``LOG_DIR``
    String, default ``"logs"``. Directory where the package's log files are
    created. Ensure the process has permission to write to it.

``LOG_FILE_LEVELS``
    List of logging levels. Defaults to ``DEBUG``, ``INFO``, ``WARNING``,
    ``ERROR`` and ``CRITICAL``. Each enabled level receives a file handler.

``LOG_FILE_FORMATS``
    Mapping of level names to either one of the integer format choices listed in
    `Available format options`_ or a custom standard logging format string.

``LOG_FILE_FORMAT_TYPES``
    Mapping of levels to ``normal``, ``JSON``, ``XML`` or ``FLAT``. The default
    is ``normal`` for every level. JSON/XML/FLAT use the package's structured
    formatters and ``STRUCTURED_LOGGING`` settings.

``EXTRA_LOG_FILES``
    Mapping of levels to booleans, default ``False``. For JSON and XML levels,
    ``True`` writes to a dedicated ``logs/json`` or ``logs/xml`` subdirectory
    instead of a ``.log`` file. This option does not create a separate FLAT
    directory.

``LOG_CONSOLE_LEVEL``
    Console handler level, default ``"DEBUG"``. The package's console handler
    belongs to the ``django_logging`` namespace by default; additive setup does
    not add another console handler to root.

``LOG_CONSOLE_FORMAT``
    Integer format choice or custom logging format string, default ``1``.

``LOG_CONSOLE_COLORIZE``
    Boolean, default ``True``. Enables the package's colored console formatter.

``LOG_DATE_FORMAT``
    Date format passed to standard logging formatters, default
    ``"%Y-%m-%d %H:%M:%S"``.

``LOG_DIR_SIZE_LIMIT``
    Integer megabyte threshold used by the ``logs_size_audit`` management
    command, default ``1024`` (1 GiB when interpreted in binary units). Schedule
    the command outside HTTP requests; see :doc:`usage`.

``LOG_SQL_QUERIES_ENABLE``
    Boolean, default ``False``. Allows ``RequestLogMiddleware`` to include
    bounded SQL diagnostics when request logging is enabled. SQL capture follows
    Django's own query-capture behavior; this option does not enable ``DEBUG``
    or force database query capture on.

``LOG_SIZE_AUDIT_IN_REQUEST``
    Boolean, default ``False``. Explicitly opts into the legacy behavior where
    ``MonitorLogSizeMiddleware`` may run the filesystem audit during a request.
    Prefer scheduling ``python manage.py logs_size_audit`` externally.

``INCLUDE_LOG_iBOARD``
    Boolean, default ``False``. Enables the optional LogiBoard URL integration;
    see :doc:`log_iboard`.

.. _structured-logging:

Structured logging
------------------

``STRUCTURED_LOGGING`` controls the JSON, XML and FLAT formatters. All options
are optional and validated; unknown keys or invalid values fail configuration
validation.

* ``REDACT_FIELDS``: extra field names to redact, case-insensitively; default
  empty. Built-in sensitive-name matching is always applied to structured
  values (for example password, token, authorization, cookie, session, API key,
  email and phone fields).
* ``MAX_DEPTH``: maximum nested collection depth; default ``8``, allowed
  ``1``–``32``.
* ``MAX_ITEMS``: maximum items per collection; default ``100``, allowed
  ``1``–``1000``.
* ``MAX_STRING_LENGTH``: maximum string length; default ``4096``, allowed
  ``1``–``1048576``.
* ``MAX_EVENT_BYTES``: maximum serialized event size; default ``65536``,
  allowed ``96``–``1048576`` bytes.
* ``MAX_EXCEPTION_FRAMES``: maximum traceback frames to include; default ``32``,
  allowed ``1``–``128``.
* ``INCLUDE_EXTRA``: include structured fields supplied through Python logging's
  ``extra={...}``; default ``True``.
* ``EXCEPTION_MODE``: ``"traceback"`` (default), ``"type"`` or ``"omit"``.
* ``JSON_COMPACT``: compact one-event-per-line JSON when ``True``; default
  ``True``.
* ``XML_PRETTY``: pretty-print XML when ``True``; default ``True``.

Example:

.. code-block:: python

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
            "EXCEPTION_MODE": "traceback",
            "JSON_COMPACT": True,
            "XML_PRETTY": True,
        },
    }

Use ``logger.info("Order processed", extra={"order_id": 42})`` to emit
structured attributes. JSON no longer parses or removes ``key=value`` fragments
from the original message. Redaction applies to structured fields, not
arbitrary secrets embedded in message strings, SQL text or tracebacks. Avoid
logging credentials and raw request data.

.. _request-logging:

Request logging
---------------

``REQUEST_LOGGING`` configures ``django_logging.middleware.RequestLogMiddleware``.
All options are optional; defaults are merged automatically. The middleware
supports sync/async views, isolates request-local state, and normally emits one
completion event at INFO level. It does not inspect ordinary response bodies.

* ``LOG_REQUEST_STARTED``: boolean, default ``False``.
* ``LOG_REQUEST_FINISHED``: boolean, default ``True``; completion event includes
  method, bounded path, already-resolved user ID (or ``Anonymous``), status,
  content type and response-object latency in milliseconds.
* ``LOG_USER_AGENT``: boolean, default ``True``; adds a sanitized, bounded user
  agent to request context.
* ``LOG_QUERY_PARAMS``: boolean, default ``False``; opt-in query-value diagnostics.
* ``LOG_REQUEST_BODY``: boolean, default ``False``; opt-in JSON request-body
  diagnostics for POST/PUT/PATCH requests with a declared bounded content length.
* ``LOG_ERROR_RESPONSE``: boolean, default ``False``; opt-in bounded JSON error
  response diagnostics for status codes >= 400.
* ``LOG_STREAMING_EVENTS``: boolean, default ``False``; controls additional
  stream started/finished/closed/cancelled messages. Context is still propagated
  during iteration, and stream errors are still logged when this is disabled.
* ``EXCLUDED_PATHS``: exact absolute paths excluded from value diagnostics.
* ``EXCLUDED_PATH_PREFIXES``: absolute path prefixes excluded from value
  diagnostics. Use these for credential-handling endpoints.
* ``EXCLUDED_FIELDS``: extra sensitive field names to redact globally.
* ``EXCLUDED_FIELDS_BY_PATH``: mapping of an exact absolute path to additional
  field names to redact on that path.
* ``MAX_QUERY_BYTES``: query-string byte limit, default ``4096``.
* ``MAX_BODY_BYTES``: request-body byte limit, default ``2048``.
* ``MAX_ERROR_BYTES``: error-response byte limit, default ``2048``.
* ``MAX_SQL_BYTES``: SQL diagnostic byte limit, default ``4096``.
* ``MAX_DIAGNOSTIC_DEPTH``: nested diagnostic depth, default ``8``, allowed
  ``1``–``32``.
* ``TRUSTED_PROXY_CIDRS``: list of trusted reverse-proxy peer CIDRs, default
  empty. Only a valid ``X-Real-IP`` is considered when ``REMOTE_ADDR`` belongs
  to one of these networks. ``X-Forwarded-For`` is never trusted by this helper.
* ``MAX_REQUEST_ID_LENGTH``: maximum accepted incoming request ID length,
  default ``80``, allowed ``1``–``128``. IDs must be ASCII alphanumeric or
  contain ``-``, ``_`` or ``.``; invalid values are replaced by a UUID.

The four byte limits accept integers from ``0`` to ``1048576``. A value of zero
effectively prevents capture for that diagnostic. Boolean options must be actual
booleans, and unknown keys fail Django system checks with
``django_logging.E040_REQUEST_LOGGING``. Invalid middleware configuration raises
``ImproperlyConfigured`` when the middleware is instantiated.

Privacy notes: query/body/error/SQL value diagnostics are disabled by default,
regardless of ``DEBUG``. Field-name redaction is best-effort; secrets can appear
under unexpected names or in path segments. Excluded paths suppress value
diagnostics but do not suppress the basic completion event. Do not enable raw SQL
diagnostics for production traffic containing sensitive query values.

Extensible components
---------------------

``COMPONENTS`` extends the built-in configuration with standard Python logging
components. See :doc:`extensibility` for the full guide.

* ``formatters``, ``filters``, ``handlers`` and ``loggers`` add named components.
* ``replace`` replaces a named built-in preset, organized by component type.
* ``disable`` removes named components, organized by component type.
* ``root_handlers`` explicitly attaches listed handlers to root in additive mode.
* ``package_handlers`` attaches listed handlers to the ``django_logging`` logger.

Additions cannot silently reuse existing names. Use ``replace`` or ``disable``
explicitly. Missing handler/formatter/filter references are configuration errors.
Unattached custom components are not instantiated in additive/isolated modes;
only components reachable from active routes and their handler dependencies are
constructed. Import or constructor errors can still occur during activation.

Rotation
--------

``LOG_ROTATION`` configures the built-in per-level file handlers. It does not
restrict the handler types available through ``COMPONENTS``.

* ``TYPE``: ``"none"`` (default), ``"size"``, ``"time"`` or ``"external"``.
* ``MAX_BYTES``: positive integer, default ``10485760`` (10 MiB); used for
  size-based rotation.
* ``BACKUP_COUNT``: non-negative integer, default ``5``; zero keeps all backups.
* ``WHEN``: timed rotation unit, default ``"midnight"``; accepted values are
  ``"s"``, ``"m"``, ``"h"``, ``"d"``, ``"midnight"`` and ``"W0"``–``"W6"``.
* ``INTERVAL``: positive integer, default ``1``.
* ``COMPRESS``: boolean, default ``False``. When enabled for size/time rotation,
  rotated files are gzip-compressed synchronously in the emitting process.

``TYPE="external"`` uses POSIX ``WatchedFileHandler`` for an external rename/create
rotator such as logrotate. ``COMPRESS`` must be ``False`` in this mode; let the
external rotator handle compression. ``LOG_ROTATION_OVERRIDES`` maps individual
levels to partial rotation dictionaries that override the global settings.

**Gunicorn warning:** Standard size/time rotating handlers are not safe when
multiple independent worker processes rotate the same file. ``WatchedFileHandler``
detects file replacement but does not provide inter-process record locking. For
multiprocess/container deployments, consider stdout/stderr collection or a
carefully configured external rotator. The ``rotate_logs`` command operates on
handlers in the current process only.

.. _email-notifications:

Email notifications
-------------------

``LOG_EMAIL_NOTIFIER`` defaults to disabled. Options:

* ``ENABLE``: boolean, default ``False``.
* ``NOTIFY_ERROR``: boolean, default ``False``; enable the ERROR email handler.
* ``NOTIFY_CRITICAL``: boolean, default ``False``; enable the CRITICAL email handler.
* ``LOG_FORMAT``: integer format choice or custom format string, default ``1``.
* ``USE_TEMPLATE``: boolean, default ``True``.
* ``MAX_CONCURRENT``: integer ``1``–``64``, default ``4``; maximum in-flight SMTP
  notification threads per process. Notifications over capacity are dropped
  with a warning, not queued; delivery is not guaranteed.
* ``SMTP_TIMEOUT``: integer seconds ``1``–``120``, default ``10``.

When email notifications are enabled, configure Django's ``EMAIL_HOST``,
``EMAIL_PORT``, ``EMAIL_HOST_USER``, ``EMAIL_HOST_PASSWORD``, ``EMAIL_USE_TLS``,
``DEFAULT_FROM_EMAIL`` and the package's ``ADMIN_EMAIL`` recipient setting.

Available format options
------------------------

The integer values for ``LOG_FILE_FORMATS``, ``LOG_CONSOLE_FORMAT`` and
``LOG_EMAIL_NOTIFIER["LOG_FORMAT"]`` refer to the following format strings.

.. code-block:: python

    FORMAT_OPTIONS = {
        1: "%(levelname)s | %(asctime)s | %(module)s | %(message)s | %(context)s",
        2: "%(levelname)s | %(asctime)s | %(context)s | %(message)s | %(exc_text)s",
        3: "%(levelname)s | %(context)s | %(message)s | %(stack_info)s",
        4: "%(context)s | %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        5: "%(levelname)s | %(message)s | %(context)s | [in %(pathname)s:%(lineno)d]",
        6: "%(asctime)s | %(context)s | %(levelname)s | %(message)s | %(exc_info)s",
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

Required Django email settings
------------------------------

For the built-in email notifier, configure ``EMAIL_HOST``, ``EMAIL_PORT``,
``EMAIL_HOST_USER``, ``EMAIL_HOST_PASSWORD``, ``EMAIL_USE_TLS`` and
``DEFAULT_FROM_EMAIL``. The package also reads ``ADMIN_EMAIL`` as the recipient.
Use environment variables or a secrets manager for credentials; do not commit
SMTP passwords to source control.
