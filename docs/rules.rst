Feature guide
=============

This page summarizes the main parts of ``dj-logging``. For full configuration
syntax, defaults and caveats, follow the linked reference pages.

Basic logging
-------------

Use the standard Python logging API throughout the application:

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Job accepted", extra={"job_id": 123})

The handler routing depends on ``DJANGO_LOGGING["LOGGING_SETUP_MODE"]`` and the
application's existing logger levels and propagation. See :doc:`settings`.

Request logging
---------------

Add ``django_logging.middleware.RequestLogMiddleware`` to Django's
``MIDDLEWARE`` to enable request correlation and bounded completion logs. Query
values, request bodies, error response bodies and SQL diagnostics are opt-in.
See the :ref:`request-logging` section in :doc:`settings` for the options and
security limitations.

Email notifications
-------------------

The built-in email handler is disabled by default. Configure
``LOG_EMAIL_NOTIFIER`` and Django's email settings before enabling it. Delivery
uses a bounded number of concurrent per-process attempts; excess notifications
may be dropped instead of queued. See :ref:`email-notifications` in :doc:`settings`.

Context variables
-----------------

``ContextVarManager`` supports binding context values to the current execution
context. ``ContextVarFilter`` merges them into the ``context`` record attribute,
which can be rendered with ``%(context)s`` in a standard logging format. Use
``scoped_context()`` or the tokens returned by ``batch_bind()``/``reset()`` to
restore prior values safely. See :doc:`usage`.

Execution tracking
------------------

``django_logging.decorators.execution_tracker`` measures sync function duration
and can optionally count synchronous Django debug queries. It does not clear
existing query history. Async functions are timed through awaited completion;
SQL query counting is rejected for async functions because the synchronous
connection history cannot reliably represent async database activity. See
:doc:`usage`.

Custom components
-----------------

Use ``DJANGO_LOGGING["COMPONENTS"]`` to add, replace or disable handlers,
formatters, filters and named logger routes without modifying the package. See
:doc:`extensibility`.

Production performance
----------------------

Structured payload limits, synchronous file I/O, compression, and multiprocess
rotation all affect runtime behavior. See :doc:`performance` before choosing a
handler strategy for high-volume or Gunicorn deployments.
