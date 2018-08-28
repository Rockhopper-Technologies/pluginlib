..
  Copyright 2018 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. py:currentmodule:: pluginlib


Concepts
========

.. _abstract-methods:

Abstract Methods
----------------

Methods required in child plugins should be labeled as abstract methods.
Plugins without these methods or with :py:term:`parameters <parameter>`
that don’t match, will not be loaded.

Regular methods, static methods, class methods, properties, and attributes can all
be designated as abstract. The process is slightly different depending on the type and
what version of Python you are running.

Regular methods always use the :py:func:`@abstractmethod  <abstractmethod>` decorator.

.. code-block:: python

    @pluginlib.Parent('parser')
    class Parser(object):

        @pluginlib.abstractmethod
        def parse(self, string):
            pass

For Python 3.3 and above, static methods, class methods, and properties also use the
:py:func:`@abstractmethod  <abstractmethod>` decorator. Just place
:py:func:`@abstractmethod  <abstractmethod>` as the innermost decorator.

.. code-block:: python

    @pluginlib.Parent('parser')
    class Parser(object):

        @staticmethod
        @pluginlib.abstractmethod
        def abstract_staticmethod():
            return 'foo'

        @classmethod
        @pluginlib.abstractmethod
        def abstract_classmethod(cls):
            return cls.foo

        @property
        @pluginlib.abstractmethod
        def abstract_property(self):
            return self.foo

For code that must be compatible with older versions of Python, use the
:py:func:`@abstractstaticmethod  <abstractstaticmethod>`,
:py:func:`@abstractclassmethod  <abstractclassmethod>`, and
:py:func:`@abstractproperty  <abstractproperty>` decorators.

.. code-block:: python

    @pluginlib.Parent('parser')
    class Parser(object):

        @pluginlib.abstractstaticmethod
        def abstract_staticmethod():
            return 'foo'

        @pluginlib.abstractclassmethod
        def abstract_classmethod(cls):
            return cls.foo

        @pluginlib.abstractproperty
        def abstract_property(self):
            return self.foo

Abstract attributes call also be defined, but no guarantee is made as to what kind of attribute
the child plugin will have, just that the attribute is present.
Abstract attributes are defined using :py:class:`abstractattribute`.

.. code-block:: python

    @pluginlib.Parent('parser')
    class Parser(object):
        abstract_attribute = pluginlib.abstractattribute


.. _versions:

Versions
--------

Plugin versions have two uses in Pluginlib:

    1. If multiple plugins with the same type and name are loaded, the plugin with
       the highest version is used when :py:attr:`PluginLoader.plugins` is accessed.
    2. :ref:`blacklists` can filter plugins based on their version number.
    3. :py:attr:`PluginLoader.plugins_all` returns all unfiltered versions of plugins

Versions must be strings and should adhere to `PEP 440`_. Version strings are
evaluated using :py:func:`pkg_resources.parse_version`.

By default, all plugins will have a version of :py:data:`None`,
which is treated as ``'0'`` when compared against other versions.

A plugin version can be set explicitly with the
:py:attr:`~pluginlib.Plugin._version_` class attribute.

.. code-block:: python

    class NullParser(ParserParent):

        _version _ = '1.0.1'

        def parse(self, string):
            return string

If a plugin version is not explicitly set and the module it's found in
has a ``__version__`` variable, the module version is used.

.. code-block:: python

    __version__ = '1.0.1'

    class NullParser(ParserParent):

        def parse(self, string):
            return string

.. _PEP 440: https://www.python.org/dev/peps/pep-0440/


.. _conditional-loading:

Conditional Loading
-------------------

Sometimes a plugin child class is created that should not be loaded as a plugin.
Examples include plugins only intended for specific environments and plugins inherited
by additional plugins.

The :py:attr:`~pluginlib.Plugin._skipload_` attribute can be configured to prevent a
plugin from loading. :py:attr:`~pluginlib.Plugin._skipload_` can be a :py:class:`Boolean <bool>`,
:py:func:`static method <staticmethod>`, or :py:func:`class method <classmethod>`.
If :py:attr:`~pluginlib.Plugin._skipload_` is a method, it will be called with no arguments.

.. note::
    :py:attr:`~pluginlib.Plugin._skipload_` can not be inherited and must be declared directly
    in the plugin class it applies to.

:py:attr:`~pluginlib.Plugin._skipload_` as an attribute:

.. code-block:: python

    class ParserPlugin(ParserParent):

        _skipload_ = True


:py:attr:`~pluginlib.Plugin._skipload_` as a static method:

.. code-block:: python

    import platform

    class ParserPlugin(ParserParent):

        @staticmethod
        def _skipload_():

            if platform.system() != 'Linux':
                return True, "Only supported on Linux"
            return False

:py:attr:`~pluginlib.Plugin._skipload_` as a class method:

.. code-block:: python

    import sys

    class ParserPlugin(ParserParent):

        minimum_python = (3,4)

        @classmethod
        def _skipload_(cls):
            if sys.version_info[:2] < cls.minimum_python
                return True, "Not supported on this version of Python"
            return False


.. _blacklists:

Blacklists
----------

:py:class:`PluginLoader` allows blacklisting plugins based on the plugin type, name, or version.
Blacklists are implemented with the ``blacklist`` argument.

The ``blacklist`` argument to :py:class:`PluginLoader` must an iterable containing
either :py:class:`BlacklistEntry` instances or tuples of arguments for creating
:py:class:`BlacklistEntry` instances.

The following are equivalent:

.. code-block:: python

    PluginLoader(blacklist=[BlacklistEntry('parser', 'json')])

.. code-block:: python

    PluginLoader(blacklist=[('parser', 'json')])

For information about blacklist entries, see :py:class:`BlacklistEntry` in the :ref:`API-Reference`.


.. _plugin-groups:

Plugin Groups
-------------

By default, Pluginlib places all plugins in a single group. This may not be desired
in all cases, such as when created libraries and frameworks. For these use cases,
a group should be specified for the :py:func:`@Parent <Parent>` decorator and when
creating a :py:class:`PluginLoader` instance. Only plugins with a matching group
will be available from the :py:class:`PluginLoader` instance.

.. code-block:: python

    @pluginlib.Parent('parser', group='my_framework')
    class Parser(object):

        @pluginlib.abstractmethod
        def parse(self, string):
            pass

.. code-block:: python

    loader = pluginlib.PluginLoader(modules=['sample_plugins'], group='my_framework')


.. _type-filters:

Type Filters
------------

By default, :py:class:`PluginLoader` will provide plugins for all parent plugins in the same
plugin group. To limit plugins to specific types, use the ``type_filter`` keyword.

.. code-block:: python

    loader = PluginLoader(library='myapp.lib')
    print(loader.plugins.keys())
    # ['parser', 'engine', 'hook', 'action']

    loader = PluginLoader(library='myapp.lib', type_filter=('parser', 'engine'))
    print(loader.plugins.keys())
    # ['parser', 'engine']



.. _accessing-plugins:

Accessing Plugins
-----------------

Plugins are accessed through :py:class:`PluginLoader` properties and methods. In all cases,
plugins that are filtered out through :ref:`blacklists <blacklists>` or
:ref:`type filters <type-filters>` will not be returned.

Plugins are filtered each time these methods are called, so it is recommended to save the result
to a variable.

:py:attr:`PluginLoader.plugins`
    This property returns the newest version of each available plugin.

:py:attr:`PluginLoader.plugins_all`
    This property returns all versions of each available plugin.

:py:meth:`PluginLoader.get_plugin`
    This method returns a specific plugin or :py:data:`None` if unavailable.

.. code-block:: python

    loader = PluginLoader(library='myapp.lib')

    plugins = loader.plugins
    # {'parser': {'json': <class 'myapp.lib.JSONv2'>}}

    plugins_all = loader.plugins_all
    # {'parser': {'json': {'1.0': <class 'myapp.lib.JSONv1'>,
    #                      '2.0': <class 'myapp.lib.JSONv2'>}}}

    json_parser = loader.get_plugin('parser', 'json')
    # <class 'myapp.lib.JSONv2'>

    json_parser = loader.get_plugin('parser', 'json', '1.0')
    # <class 'myapp.lib.JSONv1'>

    json_parser = loader.get_plugin('parser', 'json', '4.0')
    # None
