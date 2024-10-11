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

.. image:: https://img.shields.io/badge/pylint-10/10-brightgreen?logo=python&logoColor=blue
   :target: https://www.pylint.org/
   :alt: Pylint

.. image:: https://img.shields.io/pypi/pyversions/dj-logging
    :target: https://pypi.org/project/dj-logging/
    :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/djversions/dj-logging
    :target: https://pypi.org/project/dj-logging/
    :alt: Supported Django versions

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=yellow
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

.. image:: https://img.shields.io/github/issues/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging/issues
    :alt: Open Issues

.. image:: https://img.shields.io/github/last-commit/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging/commits/main
    :alt: Last Commit

.. image:: https://img.shields.io/github/languages/top/lazarus-org/django_logging
    :target: https://github.com/lazarus-org/django_logging
    :alt: Languages

.. image:: https://img.shields.io/codecov/c/github/lazarus-org/django_logging/main
   :target: https://codecov.io/gh/lazarus-org/django_logging
   :alt: Coverage



|br|

`django_logging` is a powerful yet simple Django package that extends and enhances Python's built-in ``logging`` without relying on any **third-party** libraries. Our goal is to keep things straightforward while providing flexible and customizable logging solutions that are specifically designed for Django applications.

One of the key advantages of ``django_logging`` is its seamless integration. Get started with django_logging in your existing projects without refactoring any code. Even if you're already using the **default logging setup**, you can instantly upgrade to advanced features with just a simple installation. No extra changes or complicated setup required!

imagine you have a Django package that was developed a few years ago and already uses Python's built-in ``logging``. Refactoring the entire codebase to use another logging package would be a daunting task. But with ``django_logging``, you don't have to worry about that. Simply install django_logging and enjoy all its advanced features with logging each ``LEVEL`` in separate files with three extra formats (``json``, ``xml``, ``flat``)  **without having to make any changes** to your existing code.

Supported Versions
------------------

`django_logging` supports the following combinations of Django and Python versions:

==========  ===========================
  Django      Python
==========  ===========================
4.2         3.9, 3.10, 3.11, 3.12, 3.13
5.0         3.10, 3.11, 3.12, 3.13
5.1         3.10, 3.11, 3.12, 3.13
==========  ===========================

Documentation
-------------

The documentation is organized into the following sections:

.. toctree::
   :maxdepth: 2

   quick_start
   usage
   log_iboard
   settings
   contributing
   rules

Issues
------
If you have questions or have trouble using the app please file a bug report at:

https://github.com/lazarus-org/django_logging/issues


Indices and tables
==================

* :ref:`search`
* :ref:`genindex`
* :ref:`modindex`