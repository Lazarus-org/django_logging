Settings
========

By default, `django_logging` uses a built-in configuration that requires no additional setup. However, you can customize the logging settings by adding the ``DJANGO_LOGGING`` dictionary configuration to your Django ``settings`` file.

Default configuration
---------------------

.. code-block:: python

    DJANGO_LOGGING = {
        "AUTO_INITIALIZATION_ENABLE": True,
        "INITIALIZATION_MESSAGE_ENABLE": True,
        "INCLUDE_LOG_iBOARD": True,
        "LOG_SQL_QUERIES_ENABLE": True,
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
        "EXTRA_LOG_FILES": {  # for extra formats (JSON, XML)
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
        },
    }

Configuration Options
---------------------
Here's a breakdown of the available configuration options:

``AUTO_INITIALIZATION_ENABLE``
------------------------------

- **Type**: ``bool``
- **Description**: Enables automatic initialization of logging configurations. Defaults to ``True``.

``INITIALIZATION_MESSAGE_ENABLE``
---------------------------------

- **Type**: ``bool``
- **Description**: Enables logging of the initialization message when logging starts. Defaults to ``True``.

``INCLUDE_LOG_iBOARD``
----------------------

- **Type**: ``bool``
- **Description**: Makes LogiBoard url accessible in the project. Defaults to ``False``. for setting up the LogiBoard, please refer to the :doc:`LogiBoard Integration <log_iboard>`.


``LOG_SQL_QUERIES_ENABLE``
--------------------------

- **Type**: ``bool``
- **Description**: Enables logging of SQL queries within ``RequestLogMiddleware`` logs. Defaults to ``False``. When enabled, SQL queries executed in each request will be included in the log output.

``LOG_FILE_LEVELS``
-------------------

- **Type**: ``list[str]``
- **Description**: Specifies which log levels should be captured in log files. Defaults to ``["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]``.

``LOG_DIR``
-----------

- **Type**: ``str``
- **Description**: Specifies the directory where log files will be stored. Defaults to ``"logs"``.

``LOG_DIR_SIZE_LIMIT``
----------------------

- **Type**: ``int``
- **Description**: Specifies the maximum allowed size of the log directory in megabytes (MB). If the directory exceeds this limit and ``MonitorLogSizeMiddleware`` is enabled, a warning email will be sent to the admin weekly. Defaults to ``1024 MB`` (1 GB).

``LOG_FILE_FORMATS``
--------------------

- **Type**: ``dict[str, int | str]``
- **Description**: Maps each log level to its corresponding log format. The format can be an ``int`` representing predefined formats or a custom ``str`` format.
- **Default**: Format ``1`` for all levels.

``LOG_FILE_FORMAT_TYPES``
-------------------------

- **Type**: ``dict[str, str]``
- **Description**: Defines the format type (e.g., ``normal``, ``JSON``, ``XML``, ``FLAT``) for each log level. The keys are log levels, and the values are the format types.

    - **Format Types**:

      - ``normal``: Standard text log.
      - ``JSON``: Structured logs in JSON format.
      - ``XML``: Structured logs in XML format.
      - ``FLAT``: logs with Flat format.

``EXTRA_LOG_FILES``
-------------------

- **Type**: ``dict[str, bool]``
- **Description**: Determines whether separate log files for ``JSON`` or ``XML`` formats should be created for each log level. When set to ``True`` for a specific level, a dedicated directory (e.g., ``logs/json`` or ``logs/xml``) will be created with files like ``info.json`` or ``info.xml``. if ``False``, json and xml logs will be written to ``.log`` files.
- **Default**: ``False`` for all levels.

``LOG_CONSOLE_LEVEL``
---------------------

- **Type**: ``str``
- **Description**: Specifies the log level for console output. Defaults to ``"DEBUG"``.

``LOG_CONSOLE_FORMAT``
----------------------

- **Type**: ``int | str``
- **Description**: Specifies the format for console logs, similar to ``LOG_FILE_FORMATS``. Defaults to format ``1``.

``LOG_CONSOLE_COLORIZE``
------------------------

- **Type**: ``bool``
- **Description**: Determines whether console output should be colorized. Defaults to ``True``.

``LOG_DATE_FORMAT``
-------------------

- **Type**: ``str``
- **Description**: Specifies the date format for log messages. Defaults to ``"%Y-%m-%d %H:%M:%S"``.

``LOG_EMAIL_NOTIFIER``
----------------------

- **Type**: ``dict``
- **Description**: Configures the email notifier for sending log-related alerts.

    - ``ENABLE``:
      - **Type**: ``bool``
      - **Description**: Enables or disables the email notifier. Defaults to ``False``.

    - ``NOTIFY_ERROR``:
      - **Type**: ``bool``
      - **Description**: Sends an email notification for ``ERROR`` log level events. Defaults to ``False``.

    - ``NOTIFY_CRITICAL``:
      - **Type**: ``bool``
      - **Description**: Sends an email notification for ``CRITICAL`` log level events. Defaults to ``False``.

    - ``LOG_FORMAT``:
      - **Type**: ``int | str``
      - **Description**: Specifies the log format for email notifications. Defaults to format ``1``.

    - ``USE_TEMPLATE``:
      - **Type**: ``bool``
      - **Description**: Determines whether the email should include an HTML template. Defaults to ``True``.


.. _available_format_options:

Available Format Options
------------------------

The `django_logging` package provides predefined log format options that you can use in configuration. These options can be applied to log formats. Below are the available format options:

.. code-block:: python

    FORMAT_OPTIONS = {
        1: "%(levelname)s | %(asctime)s | %(module)s | %(message)s | %(context)s",
        2: "%(levelname)s | %(asctime)s | %(context)s | %(message)s",
        3: "%(levelname)s | %(context)s | %(message)s",
        4: "%(context)s | %(asctime)s - %(name)s - %(levelname)s - %(message)s",
        5: "%(levelname)s | %(message)s | %(context)s | [in %(pathname)s:%(lineno)d]",
        6: "%(asctime)s | %(context)s | %(levelname)s | %(message)s",
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

You can reference these formats by their corresponding **integer keys** in your logging configuration settings.


Required Email Settings
-----------------------

To use the email notifier, the following email settings must be configured in your ``settings.py``:

- ``EMAIL_HOST``: The host to use for sending emails.
- ``EMAIL_PORT``: The port to use for the email server.
- ``EMAIL_HOST_USER``: The username to use for the email server.
- ``EMAIL_HOST_PASSWORD``: The password to use for the email server.
- ``EMAIL_USE_TLS``: Whether to use a TLS (secure) connection when talking to the email server.
- ``DEFAULT_FROM_EMAIL``: The default email address to use for sending emails.
- ``ADMIN_EMAIL``: The email address where log notifications will be sent. This is the recipient address used by the email notifier to deliver the logs.

Example Email Settings
----------------------

Below is an example configuration for the email settings in your ``settings.py``:

.. code-block:: python

   EMAIL_HOST = "smtp.example.com"
   EMAIL_PORT = 587
   EMAIL_HOST_USER = "your-email@example.com"
   EMAIL_HOST_PASSWORD = "your-password"
   EMAIL_USE_TLS = True
   DEFAULT_FROM_EMAIL = "your-email@example.com"
   ADMIN_EMAIL = "admin@example.com"

These settings ensure that the email notifier is correctly configured to send log notifications to the specified ``ADMIN_EMAIL`` address.
