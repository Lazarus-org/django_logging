Extensible components
=====================

``dj-logging`` provides convenient built-in presets, but you are not limited to
the built-in handlers, formatters, filters or logger routes. Configure extensions
inside the existing ``DJANGO_LOGGING["COMPONENTS"]`` dictionary. Definitions use
Python's standard ``logging.config.dictConfig`` component conventions where
supported by each component type.

The package remains plug-and-play when ``COMPONENTS`` is omitted. You do not need
to fork ``dj-logging`` or wait for a release to use a custom logging component.

Add a custom handler and logger
-------------------------------

This example adds a rotating audit file without changing the built-in handlers:

.. code-block:: python

    DJANGO_LOGGING = {
        "COMPONENTS": {
            "formatters": {
                "audit": {
                    "format": "%(asctime)s %(levelname)s %(message)s",
                },
            },
            "handlers": {
                "audit_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": "logs/audit.log",
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

Then use the standard logging API:

.. code-block:: python

    import logging

    audit_logger = logging.getLogger("myapp.audit")
    audit_logger.info("Shipment delivered")

The directory for a custom file handler must exist before the handler is
constructed. The example uses ``logs/``, which the default package setup creates;
for a different directory, create it in your deployment setup.

Component sections
------------------

``COMPONENTS`` accepts the following top-level keys:

``formatters``
    Add named formatter definitions. A formatter can use ``class`` or the
    standard ``()`` factory convention, with constructor arguments supported by
    Python's logging configurator.

``filters``
    Add named filters using a dotted class path or ``()`` factory. Handler and
    explicitly configured logger definitions can refer to these filters by name.

``handlers``
    Add named handlers. Use standard handler options such as ``class``,
    ``level``, ``formatter``, ``filters`` and handler-specific keyword arguments.
    Standard handler-to-handler references such as ``target`` are followed when
    building the active component graph.

``loggers``
    Explicitly configure an application logger by name. The names ``root`` and
    ``django_logging`` are reserved; use ``root_handlers`` and
    ``package_handlers`` for those destinations. Supported keys are
    ``handlers``, ``filters``, ``level`` and ``propagate``. Explicit logger
    configuration can change that logger's level and propagation; the package
    records the prior values and restores them when the managed route is removed.

``root_handlers``
    List handlers to attach to root in ``additive`` mode. The built-in console
    handler is not attached to root automatically; listing ``"console"`` here
    explicitly opts into that route and can duplicate an existing application
    console handler.

``package_handlers``
    List handlers to attach to the ``django_logging`` logger namespace. This
    works with ``additive`` and ``isolated`` modes.

Replace or disable built-in presets
-----------------------------------

Adding a component never silently overwrites a built-in name. Use ``replace``
to replace a built-in preset, or ``disable`` to remove a named component:

.. code-block:: python

    DJANGO_LOGGING = {
        "COMPONENTS": {
            "replace": {
                "handlers": {
                    "info": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "filename": "logs/info.log",
                        "maxBytes": 10_485_760,
                        "backupCount": 5,
                        "formatter": "info",
                        "level": "INFO",
                        "filters": ["info", "context_var_filter"],
                    },
                },
            },
            "disable": {
                "handlers": ["debug"],
            },
        },
    }

Replacement specs should preserve any formatter and filters the application
still needs. Disabling a filter that remains referenced by a handler or logger
will make the configuration invalid; replace or disable those references too.

Built-in handler names include the lowercase configured levels (for example
``debug``, ``info``, ``warning``, ``error`` and ``critical``), ``console``, and
optional email handlers such as ``email_error`` and ``email_critical`` when those
notifications are enabled. Formatter names include the configured lowercase
levels, ``console`` and ``email``. Filter names include lowercase severity names
and ``context_var_filter``.

Routing modes and component construction
----------------------------------------

The component graph is compiled from built-in presets and user additions before
activation:

* ``additive`` attaches package-owned file/email handlers to root alongside
  existing root handlers, and installs configured handlers in the
  ``django_logging`` namespace. It does not change the root level or rewrite
  unrelated application loggers.
* ``isolated`` installs handlers only in the ``django_logging`` namespace.
* ``replace_root`` uses the global standard logging configuration mechanism and
  should be selected only when root configuration replacement is intentional.

In ``additive`` and ``isolated`` modes, only handlers reachable from active
routes are instantiated. Handler dependencies (for example a ``MemoryHandler``
target) and their formatter/filter dependencies are included. An unattached
component does not open files or run a factory in these modes. ``replace_root``
uses global ``dictConfig`` behavior and may instantiate all declared handlers.

The schema and component references are checked during Django system checks.
Import-path and constructor failures can still occur when the component is
actually activated. Activation constructs the new owned components before
replacing existing package-owned attachments; unrelated application handlers
are preserved in ``additive`` and ``isolated`` modes.

Custom classes and factories are executable Python code. Only configure
components from trusted application code; never accept component paths or
factory specifications from untrusted input.

Rotation and deployment considerations
--------------------------------------

``LOG_ROTATION`` remains a shortcut for the package's built-in level file
handlers. Custom handlers are independent of that setting and can implement a
different rotation or delivery strategy.

Do not share Python's standard ``RotatingFileHandler`` or
``TimedRotatingFileHandler`` across multiple Gunicorn worker processes writing
to the same file. See :doc:`performance` for production performance guidance and
:doc:`settings` for the complete settings reference.
