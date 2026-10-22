Quick start
===========

Install ``dj-logging`` from PyPI:

.. code-block:: shell

    python -m pip install dj-logging

Add ``django_logging`` to ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS = [
        # ...
        "django_logging",
    ]

Start Django normally:

.. code-block:: shell

    python manage.py runserver

By default, ``dj-logging`` automatically creates files under ``logs/`` for the
configured levels:

* ``logs/debug.log``
* ``logs/info.log``
* ``logs/warning.log``
* ``logs/error.log``
* ``logs/critical.log``

The package also configures a console handler for the ``django_logging`` logger
namespace. In the default ``additive`` mode, it does not add another console
handler to root and does not replace the application's existing root handlers or
levels. Your application's existing Django ``LOGGING`` configuration continues
to control its own console routing. Application records that reach root and pass
the applicable levels and filters can also be written to the package's level
files.

Use standard Python logging in application code:

.. code-block:: python

    import logging

    logger = logging.getLogger(__name__)
    logger.info("Application started")
    logger.warning("A recoverable problem occurred")

The optional minimal configuration below is equivalent to the default setup:

.. code-block:: python

    DJANGO_LOGGING = {
        "AUTO_INITIALIZATION_ENABLE": True,
        "LOGGING_SETUP_MODE": "additive",
    }

You can choose ``"isolated"`` to configure only the ``django_logging``
namespace, or explicitly select ``"replace_root"`` if you want the legacy
behavior that replaces the global root logging configuration. To manage all
logging yourself, set ``AUTO_INITIALIZATION_ENABLE=False`` and configure Django's
standard ``LOGGING`` setting. See :doc:`settings` and :doc:`extensibility` for
customization.
