Quick Start
===========

Getting Started with `django_logging` is simple. Follow these steps to get up and running quickly:

1. **Install the Package**

   first, Install `django_logging` via pip:

.. code-block:: shell

  $ pip install dj-logging

2. **Add to Installed Apps**

   Add `django_logging` to your ``INSTALLED_APPS`` in your Django settings file:

.. code-block:: python

  INSTALLED_APPS = [
      # ...
      "django_logging",
      # ...
  ]

3. **Run Your Server**

   Start your Django Development server to verify the installation:

.. code-block:: shell

   python manage.py runserver

when the server starts, you'll see an initialization message like this in your *console*:

.. code-block:: text

  INFO | django_logging | Logging initialized with the following configurations:
  Log File levels: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].
  Log files are being written to: logs.
  Console output level: DEBUG.
  Colorize console: True.
  Log date format: %Y-%m-%d %H:%M:%S.
  Email notifier enabled: False.

By default, django_logging will log each level to its own file:

- DEBUG : ``logs/debug.log``
- INFO : ``logs/info.log``
- WARNING : ``logs/warning.log``
- ERROR : ``logs/error.log``
- CRITICAL : ``logs/critical.log``

In addition, logs will be displayed in **colorized** mode in the ``console``, making it easier to distinguish between different log levels.

That's it! `django_logging` is ready to use. For further customization, refer to the :doc:`Settings <settings>`.