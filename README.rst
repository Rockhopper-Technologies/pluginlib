.. start-badges

.. raw:: html

    <a href="https://repology.org/metapackage/python:pluginlib">
        <img src="https://repology.org/badge/vertical-allrepos/python:pluginlib.svg?header=" alt="Packaging status" align="right">
    </a>

| |docs| |travis| |codecov|
| |pypi| |supported-versions| |supported-implementations|

.. |docs| image:: https://img.shields.io/readthedocs/pluginlib.svg?style=plastic
    :target: https://pluginlib.readthedocs.org
    :alt: Documentation Status
.. |travis| image:: https://img.shields.io/travis/Rockhopper-Technologies/pluginlib.svg?style=plastic
    :target: https://travis-ci.org/Rockhopper-Technologies/pluginlib
    :alt: Travis-CI Build Status
.. |codecov| image:: https://img.shields.io/codecov/c/github/Rockhopper-Technologies/pluginlib.svg?style=plastic
    :target: https://codecov.io/gh/Rockhopper-Technologies/pluginlib
    :alt: Coverage Status
.. |pypi| image:: https://img.shields.io/pypi/v/pluginlib.svg?style=plastic
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pluginlib
.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pluginlib.svg?style=plastic
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pluginlib
.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pluginlib.svg?style=plastic
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pluginlib

.. end-badges

Overview
========

Pluginlib makes creating plugins for your project simple.

Step 1: Define plugin parent classes
------------------------------------

All plugins are subclasses of parent classes. To create a parent class, use the
@Parent_ decorator.

The @Parent_ decorator can take a plugin type for accessing child plugins
of the parent. If a plugin type isn't given, the class name will be used.

The @Parent_ decorator can also take a ``group`` keyword which
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

Plugins can also be blacklisted. See the Blacklists_ section for more information.

Plugins are accessible through the PluginLoader.plugins_ property,
a nested dictionary accessible through dot notation.

.. code-block:: python

    import pluginlib
    import sample

    loader = pluginlib.PluginLoader(modules=['sample_plugins'])
    plugins = loader.plugins
    parser = plugins.parser.json()
    print(parser.parse('{"json": "test"}'))

.. _Entry points: https://packaging.python.org/specifications/entry-points/

.. _PluginLoader: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.PluginLoader
.. _PluginLoader.plugins: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.PluginLoader.plugins
.. _@Parent: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.Parent
.. _\_alias\_: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.Plugin._alias_
.. _\_version\_: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.Plugin._version_
.. _\_skipload\_: http://pluginlib.readthedocs.io/en/latest/api.html#pluginlib.Plugin._skipload_

.. _Versions: http://pluginlib.readthedocs.io/en/latest/concepts.html#versions
.. _Blacklists: http://pluginlib.readthedocs.io/en/latest/concepts.html#blacklists
.. _Abstract Methods: http://pluginlib.readthedocs.io/en/latest/concepts.html#abstract-methods
.. _Conditional Loading: http://pluginlib.readthedocs.io/en/latest/concepts.html#conditional-loading
.. _Plugin Groups: http://pluginlib.readthedocs.io/en/latest/concepts.html#plugin-groups
