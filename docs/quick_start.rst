Quick Start
===========

Getting Started with `django_logging` is simple. Follow these steps to get up and running quickly:

1. **Installation**

   Install `django_logging` via pip:

   .. code-block:: shell

      $ pip install django_logging

2. **Add to Installed Apps**

   Add `django_logging` to your `INSTALLED_APPS` in your Django settings file:

   .. code-block:: python

      INSTALLED_APPS = [
          ...
          'django_logging',
          ...
      ]

3. **Default Configuration**

   By default, `django_logging` is configured to use its built-in settings. You do not need to configure anything manually unless you want to customize the behavior. The default settings will automatically handle logging with predefined formats and options.

4. **Verify Installation**

   To ensure everything is set up correctly, run your Django development server:

    .. code-block:: shell

      python manage.py runserver

   By default, `django_logging` will log an initialization message to the console that looks like this:

    .. code-block:: text

      INFO | django_logging | Logging initialized with the following configurations:
      Log File levels: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].
      Log files are being written to: logs.
      Console output level: DEBUG.
      Colorize console: True.
      Log date format: %Y-%m-%d %H:%M:%S.
      Email notifier enabled: False.


That's it! `django_logging` is ready to use with default settings. For further customization, refer to the [Settings](settings.rst) section.