Welcome to django_logging Documentation!
========================================

.. |br| raw:: html

   <br />

.. image:: https://img.shields.io/github/license/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging/blob/main/LICENSE
    :alt: License

.. image:: https://img.shields.io/pypi/v/dj-logging
    :target: https://pypi.org/project/dj-logging/
    :alt: PyPI release

.. image:: https://img.shields.io/readthedocs/django-logging
    :target: https://django-logging.readthedocs.io/en/latest/
    :alt: Documentation

.. image:: https://img.shields.io/pypi/pyversions/dj-logging
    :target: https://pypi.org/project/dj-logging/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/djversions/dj-logging
    :target: https://pypi.org/project/dj-logging/
    :alt: Supported Django versions

.. image:: https://img.shields.io/github/issues/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging/issues
    :alt: Open Issues

.. image:: https://img.shields.io/github/last-commit/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging/commits/main
    :alt: Last Commit

``dj-logging`` extends Python's built-in ``logging`` for Django applications. It
provides plug-and-play file logging, request correlation, structured JSON/XML/FLAT
formatters, optional email notifications, rotation helpers, and an extensible
configuration layer for custom handlers, formatters, filters and logger routes.

The package automatically initializes when ``django_logging`` is included in
``INSTALLED_APPS``. The default ``additive`` mode preserves existing root
handlers and logger levels; it does not silently replace a project's complete
logging setup. See :doc:`quick_start` to begin, :doc:`settings` for all options,
and :doc:`extensibility` to add custom logging components.

Supported versions
------------------

The package metadata declares the following Python/Django combinations. Actual
compatibility should be confirmed by the project's CI matrix before a release.

.. list-table:: Supported version targets
   :header-rows: 1
   :widths: 20 80

   * - Django
     - Python
   * - 5.2
     - 3.10, 3.11, 3.12, 3.13, 3.14
   * - 6.0
     - 3.12, 3.13, 3.14
   * - 6.1
     - 3.12, 3.13, 3.14

Documentation
-------------

.. toctree::
   :maxdepth: 2

   quick_start
   usage
   settings
   extensibility
   performance
   log_iboard
   contributing
   rules

Issues
------

For questions or bug reports, visit:

https://github.com/lazarus-org/django_logging/issues

Indices and tables
==================

* :ref:`search`
* :ref:`genindex`
* :ref:`modindex`
