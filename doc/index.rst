..
  Copyright 2018 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. toctree::
   :hidden:

   self
   concepts.rst
   error_handling.rst
   faq.rst
   api.rst

.. py:currentmodule:: pluginlib

Overview
========

Pluginlib makes creating plugins for your project simple.

Step 1: Define plugin parent classes
------------------------------------

All plugins are subclasses of parent classes. To create a parent class, use the
:py:func:`@Parent <Parent>` decorator.

The :py:func:`@Parent <Parent>` decorator can take a plugin type for accessing child plugins
of the parent. If a plugin type isn't given, the class name will be used.

The :py:func:`@Parent <Parent>` decorator can also take a ``group`` keyword which
restricts plugins to a specific plugin group. ``group`` should be specified if plugins for
different projects could be accessed in an single program, such as with libraries and frameworks.
For more information, see the :ref:`plugin-groups` section.

Methods required in child plugins should be labeled as abstract methods.
Plugins without these methods or with :py:term:`parameters <parameter>`
that don't match, will not be loaded.
For more information, see the :ref:`abstract-methods` section.

.. code-block:: python

    """
    sample.py
    """
    import pluginlib

    @pluginlib.Parent('parser')
    class Parser(object):

        @pluginlib.abstractmethod
        def parse(self, string):
            pass

Step 2: Define plugin classes
-----------------------------

To create a plugin, subclass a parent class and include any required methods.

Plugins can be customized through optional class attributes:

    :py:attr:`~pluginlib.Plugin._alias_`
        Changes the name of the plugin which defaults to the class name.

    :py:attr:`~pluginlib.Plugin._version_`
        Sets the version of the plugin. Defaults to the module ``__version__`` or :py:data:`None`.
        If multiple plugins with the same type and name are loaded, the plugin with
        the highest version is used. For more information, see the :ref:`versions` section.

    :py:attr:`~pluginlib.Plugin._skipload_`
        Specifies the plugin should not be loaded. This is useful when a plugin is a parent class
        for additional plugins or when a plugin should only be loaded under certain conditions.
        For more information see the :ref:`conditional-loading` section.

.. code-block:: python

    """
    sample_plugins.py
    """
    import json
    import sample

    class JSON(sample.Parser):

        _alias_ = 'json'

        def parse(self, string):
            return json.loads(string)

Step 3: Load plugins
--------------------

Plugins are loaded when the module they are in is imported. :py:class:`PluginLoader`
will load modules from specified locations and provides access to them.

:py:class:`PluginLoader` can load plugins from several locations.
    - A program's standard library
    - `Entry points`_
    - A list of modules
    - A list of filesystem paths

Plugins can also be filtered through blacklists and type filters.
See the :ref:`blacklists` and :ref:`type-filters` sections for more information.

Plugins are accessible through the :py:attr:`PluginLoader.plugins` property,
a nested dictionary accessible through dot notation. For other ways to access plugins,
see the :ref:`accessing-plugins` section.

.. code-block:: python

    import pluginlib
    import sample

    loader = pluginlib.PluginLoader(modules=['sample_plugins'])
    plugins = loader.plugins
    parser = plugins.parser.json()
    print(parser.parse('{"json": "test"}'))

.. _Entry points: https://packaging.python.org/specifications/entry-points/
