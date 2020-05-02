.. start-badges

| |docs| |travis| |codecov|
| |pypi| |supported-versions| |supported-implementations|
| |fedora| |EPEL|

.. |docs| image:: https://img.shields.io/readthedocs/pluginlib.svg?style=plastic&logo=read-the-docs
    :target: https://pluginlib.readthedocs.org
    :alt: Documentation Status
.. |travis| image:: https://img.shields.io/travis/Rockhopper-Technologies/pluginlib.svg?style=plastic&logo=travis
    :target: https://travis-ci.org/Rockhopper-Technologies/pluginlib
    :alt: Travis-CI Build Status
.. |codecov| image:: https://img.shields.io/codecov/c/github/Rockhopper-Technologies/pluginlib.svg?style=plastic&logo=codecov
    :target: https://codecov.io/gh/Rockhopper-Technologies/pluginlib
    :alt: Coverage Status

.. |pypi| image:: https://img.shields.io/pypi/v/pluginlib.svg?style=plastic&logo=pypi
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pluginlib
.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pluginlib.svg?style=plastic&logo=pypi
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pluginlib
.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pluginlib.svg?style=plastic&logo=pypi
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pluginlib

.. |fedora| image:: https://img.shields.io/badge/dynamic/json.svg?uri=https://pdc.fedoraproject.org/rest_api/v1/component-branches/?global_component=python-pluginlib;fields=name;active=true;type=rpm&query=$.results[?(@.name.startsWith(%22f%22))].name&label=Fedora&colorB=lightgray&style=plastic&logo=fedora
    :alt: Fedora version support
    :target: https://bodhi.fedoraproject.org/updates/?packages=python-pluginlib

.. |EPEL| image:: https://img.shields.io/badge/dynamic/json.svg?uri=https://pdc.fedoraproject.org/rest_api/v1/component-branches/?global_component=python-pluginlib;fields=name;active=true;type=rpm&query=$.results[?(@.name.startsWith(%22e%22))].name&label=EPEL&colorB=lightgray&style=plastic&logo=epel
    :alt: EPEL version support
    :target: https://bodhi.fedoraproject.org/updates/?packages=python-pluginlib



.. end-badges

Overview
========

Pluginlib makes creating plugins for your project simple.

Features
--------

- Plugins are validated when they are imported

- Plugins can be loaded through different mechanisms (modules, filesystem paths, `entry points`_)

- Multiple versions_ of the same plugin are supported (The newest one is used by default)

- Plugins can be `blacklisted`_ by type, name, or version

- Multiple `plugin groups`_ are supported so one program can use multiple sets of plugins that won't conflict

- Plugins support `conditional loading`_ (examples: os, version, installed software, etc)

- Once loaded, plugins can be accessed_ through dictionary or dot notation

Installation
============

PIP
---

.. code-block:: console

    $ pip install pluginlib

EL6 and EL7 (RHEL/CentOS/Scientific)
------------------------------------

(EPEL_ repositories must be configured_)

.. code-block:: console

    $ yum install python-pluginlib
    $ yum install python34-pluginlib

Fedora
------

.. code-block:: console

    $ dnf install python2-pluginlib
    $ dnf install python3-pluginlib

Usage
=====

Step 1: Define plugin parent classes
------------------------------------

All plugins are subclasses of parent classes. To create a parent class, use the
`@Parent`_ decorator.

The `@Parent`_ decorator can take a plugin type for accessing child plugins
of the parent. If a plugin type isn't given, the class name will be used.

The `@Parent`_ decorator can also take a ``group`` keyword which
restricts plugins to a specific plugin group. ``group`` should be specified if plugins for
different projects could be accessed in an single program, such as with libraries and frameworks.
For more information, see the `Plugin Groups`_ section.

Methods required in child plugins should be labeled as abstract methods.
Plugins without these methods or with parameters
that don't match, will not be loaded.
For more information, see the `Abstract Methods`_ section.

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

    `_alias_`_
        Changes the name of the plugin which defaults to the class name.

    `_version_`_
        Sets the version of the plugin. Defaults to the module ``__version__`` or ``None``
        If multiple plugins with the same type and name are loaded, the plugin with
        the highest version is used. For more information, see the Versions_ section.

    `_skipload_`_
        Specifies the plugin should not be loaded. This is useful when a plugin is a parent class
        for additional plugins or when a plugin should only be loaded under certain conditions.
        For more information see the `Conditional Loading`_ section.


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

Plugins are loaded when the module they are in is imported. PluginLoader_
will load modules from specified locations and provides access to them.

PluginLoader_ can load plugins from several locations.
    - A program's standard library
    - `Entry points`_
    - A list of modules
    - A list of filesystem paths

Plugins can also be filtered through blacklists and type filters.
See the Blacklists_ and `Type Filters`_ sections for more information.

Plugins are accessible through the PluginLoader.plugins_ property,
a nested dictionary accessible through dot notation. For other ways to access plugins,
see the `Accessing Plugins`_ section.

.. code-block:: python

    import pluginlib
    import sample

    loader = pluginlib.PluginLoader(modules=['sample_plugins'])
    plugins = loader.plugins
    parser = plugins.parser.json()
    print(parser.parse('{"json": "test"}'))

.. _Entry points: https://packaging.python.org/specifications/entry-points/

.. _PluginLoader: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.PluginLoader
.. _PluginLoader.plugins: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.PluginLoader.plugins
.. _@Parent: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.Parent
.. _\_alias\_: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.Plugin._alias_
.. _\_version\_: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.Plugin._version_
.. _\_skipload\_: http://pluginlib.readthedocs.io/en/stable/api.html#pluginlib.Plugin._skipload_

.. _Versions: http://pluginlib.readthedocs.io/en/stable/concepts.html#versions
.. _Blacklists: http://pluginlib.readthedocs.io/en/stable/concepts.html#blacklists
.. _blacklisted: http://pluginlib.readthedocs.io/en/stable/concepts.html#blacklists
.. _Type Filters: http://pluginlib.readthedocs.io/en/stable/concepts.html#type-filters
.. _Accessing Plugins: http://pluginlib.readthedocs.io/en/stable/concepts.html#accessing-plugins
.. _accessed: http://pluginlib.readthedocs.io/en/stable/concepts.html#accessing-plugins
.. _Abstract Methods: http://pluginlib.readthedocs.io/en/stable/concepts.html#abstract-methods
.. _Conditional Loading: http://pluginlib.readthedocs.io/en/stable/concepts.html#conditional-loading
.. _Plugin Groups: http://pluginlib.readthedocs.io/en/stable/concepts.html#plugin-groups

.. _EPEL: https://fedoraproject.org/wiki/EPEL
.. _configured: https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F
