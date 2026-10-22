Performance and production deployment
=====================================

``dj-logging`` is built on Python's standard logging API. The cost of logging
still depends on the number of emitted records, active filters, formatter type,
handler destination, payload size, and deployment topology. Measure the complete
application workload before changing defaults based on a microbenchmark.

Keep the request hot path lightweight
-------------------------------------

* The request middleware normally emits one completion event; request-start
  logging is opt-in.
* Query parameters, JSON request bodies, JSON error bodies, and SQL diagnostics
  are disabled by default. Do not enable them merely because Django ``DEBUG`` is
  true.
* ``REQUEST_LOGGING.LOG_STREAMING_EVENTS`` defaults to ``False``. Stream context
  is still restored while chunks are consumed and streaming errors are still
  logged; only the extra stream lifecycle events are suppressed.
* Log-size auditing should be scheduled with
  ``python manage.py logs_size_audit`` rather than performed during a request.
  ``MonitorLogSizeMiddleware`` is a pass-through unless
  ``LOG_SIZE_AUDIT_IN_REQUEST=True`` is explicitly configured.
* Avoid constructing expensive log messages when the level is disabled. Prefer
  parameterized logging such as ``logger.debug("Fetched item %s", item_id)``
  over eager string formatting.
* ``execution_tracker`` skips path resolution and metrics-message formatting
  when its configured level is disabled. Query-threshold warnings and the
  warning about disabled Django query tracking remain independent of that
  level. Enabling metrics again takes effect on the next call.

Structured formatter cost
-------------------------

JSON and FLAT are generally suitable for line-oriented collection pipelines.
XML is supported for integrations that need it, but nested XML generation is
usually more expensive. The structured formatters enforce limits during
sanitization and serialization.

XML text sanitization uses a compiled character filter to remove XML 1.0-invalid
characters without rebuilding every valid character in a Python loop. Allowed
Unicode characters, tabs, newlines, and carriage returns retain their values;
escaping remains the XML serializer's responsibility.

``STRUCTURED_LOGGING`` controls the resource limits:

* ``MAX_DEPTH`` limits nested structures.
* ``MAX_ITEMS`` limits each collection.
* ``MAX_STRING_LENGTH`` limits individual strings.
* ``MAX_EVENT_BYTES`` caps the final event and is applied alongside the earlier
  traversal budget.
* ``MAX_EXCEPTION_FRAMES`` bounds traceback frame formatting.
* ``INCLUDE_EXTRA=False`` avoids serializing arbitrary ``extra`` fields when an
  application doesn't need them.
* ``JSON_COMPACT=True`` emits one compact JSON event per line. Set
  ``XML_PRETTY=False`` to avoid indentation when compact XML is preferred.

Limits reduce worst-case work but do not make logging free. Avoid putting very
large objects, request bodies, raw SQL, or credentials into log records.

Handler I/O, rotation and compression
-------------------------------------

File handlers write synchronously on the thread emitting the log record. The
choice of handler has an overhead trade-off:

* ``FileHandler`` avoids rotation checks.
* ``RotatingFileHandler`` checks file size and can perform rollover during an
  emit.
* ``TimedRotatingFileHandler`` checks the rotation schedule during an emit.
* ``WatchedFileHandler`` checks for external file replacement and is useful with
  POSIX rename/create rotation tools.
* The package's compressed rotating handlers gzip rotated files synchronously.
  A large rollover can block the request-serving worker that triggered it.

Rotation is disabled by default. For container deployments, collecting stdout
and stderr is often easier to operate than coordinating files across workers.
If external rotation is used, configure ``LOG_ROTATION`` with
``TYPE="external"`` and ``COMPRESS=False`` and ensure the external tool uses a
rename/create strategy appropriate for ``WatchedFileHandler``.

**Multiprocess warning:** Standard size/time rotating handlers do not provide
safe coordination when independent Gunicorn workers rotate the same file.
``WatchedFileHandler`` detects inode replacement but does not lock records across
processes. External rotation also does not itself guarantee atomic multiprocess
writes. Validate the chosen output strategy under the actual deployment.

Email and background work
-------------------------

The built-in email notifier has a bounded number of concurrent SMTP attempts per
process, configured with ``LOG_EMAIL_NOTIFIER.MAX_CONCURRENT``. When capacity is
exhausted, additional notifications are dropped with a warning rather than
queued. A finite ``SMTP_TIMEOUT`` prevents indefinite socket waits. This is
best-effort notification, not a durable alert queue.

The package does not enable a generic asynchronous logging queue by default.
Applications can supply a custom handler through :doc:`extensibility`; any
queue-based handler should define its capacity, backpressure/drop policy,
shutdown behavior, and process-fork handling explicitly.

Run the included microbenchmarks
--------------------------------

The repository contains a reproducible microbenchmark script:

.. code-block:: shell

    python scripts/benchmark_performance.py --iterations 10000 --repeats 5

The script measures selected Python-level operations; it is not a substitute for
end-to-end Django, WSGI/ASGI, database, or Gunicorn load tests. Record the Python
version, operating system, storage type, log volume, payload shape, and worker
configuration when comparing results. Benchmark the actual production handler
configuration before claiming a throughput improvement.

The measurements include XML text filtering and execution tracking with metrics
both enabled and disabled. When Django is available, the standalone script
configures minimal settings with automatic logging initialization disabled.
