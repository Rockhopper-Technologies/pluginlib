..
  Copyright 2018 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. py:currentmodule:: pluginlib

Error Handling
==============

Logging
-------

Pluginlib uses the :py:mod:`logging` module from the
`Python Standard Library <https://docs.python.org/library/>`_
for debug and info level messages.
The 'pluginlib' :py:class:`logging.Logger` instance is configured with a
:py:class:`~logging.handlers.NullHandler` so, unless logging is configured in the program,
there will be no output.

To configure basic debug logging in a program:

    .. code-block:: python

        import logging

        logging.basicConfig(level=logging.DEBUG)

    See the :py:mod:`logging` module for more information on configuring logging.


To disable all logging for Pluginlib:

    .. code-block:: python

        import logging

        logging.getLogger('pluginlib').propagate = False

To change the logging level for Pluginlib only:

    .. code-block:: python

        import logging

        logging.getLogger('pluginlib').setLevel(logging.DEBUG)

Warnings
--------

Pluginlib raises a custom :py:exc:`PluginWarning` warning for malformed plugins and a custom
:py:exc:`EntryPointWarning` warning for invalid `entry points`_.
:py:exc:`EntryPointWarning` is a subclass of the builtin :py:exc:`ImportWarning`
and ignored by default in Python.

To raise an exception when a :py:exc:`PluginWarning` occurs:

    .. code-block:: python

        import warnings
        import pluginlib

        warnings.simplefilter('error', pluginlib.PluginWarning)

See the :py:mod:`warnings` module for more information on warnings.

.. _entry points: https://packaging.python.org/specifications/entry-points/

Exceptions
----------

When :py:class:`PluginLoader` encounters an error importing a module,
a :py:exc:`PluginImportError` exception will be raised.
:py:exc:`PluginImportError` is a subclass of :py:exc:`PluginlibError`.

When possible, :py:attr:`PluginImportError.friendly` is populated with a formatted exception
truncated to limit the output to the relevant part of the traceback.

To use friendly output for import errors:

    .. code-block:: python

        import sys
        import pluginlib

        loader = pluginlib.PluginLoader(modules=['sample_plugins'])

        try:
            plugins = loader.plugins
        except pluginlib.PluginImportError as e:
            if e.friendly:
                sys.exit(e.friendly)
            else:
                raise
