# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib._loader**
"""

import os
import sys
import warnings

from pkg_resources import Distribution, EntryPoint, working_set

import pluginlib._loader as loader
from pluginlib._objects import OrderedDict
from pluginlib import BlacklistEntry, PluginImportError, EntryPointWarning, PluginWarning

from tests import TestCase, OUTPUT, mock
import tests.testdata
import tests.testdata.parents

try:
    from importlib import reload
except ImportError:
    pass


DATAPATH = os.path.dirname(tests.testdata.__file__)
DIST = Distribution.from_filename(tests.testdata.__file__)
working_set.add(DIST)
DIST._ep_map = {}  # pylint: disable=protected-access


class TestPluginLoaderInit(TestCase):
    """Tests for initialization of PluginLoader"""

    def test_bad_arguments(self):
        """Error is raised when argument type is wrong"""

        # Expect iterables
        for arg in ('modules', 'paths', 'blacklist', 'type_filter'):

            with self.assertRaises(TypeError):
                loader.PluginLoader(**{arg: 'string'})

            with self.assertRaises(TypeError):
                loader.PluginLoader(**{arg: 8675309})

        # Expect strings
        for arg in ('library', 'entry_point', 'prefix_package'):

            with self.assertRaises(TypeError):
                loader.PluginLoader(**{arg: [1, 2, 3]})

            with self.assertRaises(TypeError):
                loader.PluginLoader(**{arg: 8675309})

    def test_blacklist_argument(self):
        """blacklist argument gets verified and processed in init"""

        # No blacklist
        ploader = loader.PluginLoader()
        self.assertIsNone(ploader.blacklist)

        # List of tuples and BlacklistEntry objects
        blentry = BlacklistEntry('parser', 'yaml', '2.0', '>=')
        blacklist = [blentry, ('parser', 'json'), ('parser', 'xml', '<', '1.0')]
        ploader = loader.PluginLoader(blacklist=blacklist)

        self.assertEqual(len(ploader.blacklist), 3)
        for entry in ploader.blacklist:
            self.assertIsInstance(entry, BlacklistEntry)

        self.assertIs(ploader.blacklist[0], blentry)

        self.assertEqual(ploader.blacklist[1].type, 'parser')
        self.assertEqual(ploader.blacklist[1].name, 'json')
        self.assertEqual(ploader.blacklist[1].version, None)
        self.assertEqual(ploader.blacklist[1].operator, '==')

        self.assertEqual(ploader.blacklist[2].type, 'parser')
        self.assertEqual(ploader.blacklist[2].name, 'xml')
        self.assertEqual(ploader.blacklist[2].version, '1.0')
        self.assertEqual(ploader.blacklist[2].operator, '<')

        # Entry isn't iterable
        with self.assertRaisesRegex(AttributeError, 'Invalid blacklist entry'):
            ploader = loader.PluginLoader(blacklist=[1, 2, 3])

        # Bad arguments for BlacklistEntry
        with self.assertRaisesRegex(AttributeError, 'Invalid blacklist entry'):
            ploader = loader.PluginLoader(blacklist=[(1, 2, 3)])

    def test_repr(self):
        """Only non-default settings show up in repr"""

        ploader = loader.PluginLoader(modules=['avengers.iwar', 'avengers.stark'], group='Avengers')
        output = "PluginLoader(group='Avengers', modules=['avengers.iwar', 'avengers.stark'])"
        self.assertEqual(repr(ploader), output)

        blacklist = [('parser', 'json'), ('parser', 'xml', '<', '1.0')]
        output = "PluginLoader(blacklist=(%r, %r))" % (BlacklistEntry('parser', 'json'),
                                                       BlacklistEntry('parser', 'xml', '<', '1.0'))
        ploader = loader.PluginLoader(blacklist=blacklist)
        self.assertEqual(repr(ploader), output)


def unload(module):
    """Unload a package/module and all submodules from sys.modules"""
    for mod in [mod for mod in sys.modules if mod.startswith(module)]:
        del sys.modules[mod]


# pylint: disable=protected-access,too-many-public-methods
class TestPluginLoader(TestCase):
    """Tests for PluginLoader"""

    def setUp(self):

        # Truncate log output
        OUTPUT.seek(0)
        OUTPUT.truncate(0)

    def tearDown(self):

        # Clear entry points
        DIST._ep_map.clear()

        loader.get_plugins().clear()
        unload('tests.testdata.lib')
        unload('pluginlib.importer.')
        reload(tests.testdata.parents)

    def test_load_lib(self):
        """Load modules from standard library"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.parser), 2)
        self.assertTrue('xml' in plugins.parser)
        self.assertTrue('json' in plugins.parser)
        self.assertEqual(plugins.parser.json.version, '2.0')

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('steam' in plugins.engine)
        self.assertEqual(len(plugins.hook), 2)
        self.assertTrue('right' in plugins.hook)
        self.assertTrue('left' in plugins.hook)

    def test_load_entry_points_pkg(self):
        """Load modules from entry points"""

        # Entry point is package
        epoint1 = EntryPoint.parse('hooks = tests.testdata.lib.hooks', dist=DIST)
        # Entry point is module
        epoint2 = EntryPoint.parse('parsers = tests.testdata.lib.parsers.xml', dist=DIST)

        DIST._ep_map = {'pluginlib.test.plugins': {'hooks': epoint1, 'parsers': epoint2}}

        ploader = loader.PluginLoader(group='testdata', entry_point='pluginlib.test.plugins')
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.engine), 0)

        self.assertEqual(len(plugins.hook), 2)
        self.assertTrue('right' in plugins.hook)
        self.assertTrue('left' in plugins.hook)

        self.assertEqual(len(plugins.parser), 1)
        self.assertTrue('xml' in plugins.parser)

    def test_load_entry_points_bad(self):
        """Raise warning and continue when entry point fails - bad package"""

        epoint1 = EntryPoint.parse('bad = not.a.real.module', dist=DIST)
        epoint2 = EntryPoint.parse('parsers = tests.testdata.lib.parsers.xml', dist=DIST)
        DIST._ep_map = {'pluginlib.test.plugins': {'bad': epoint1, 'parsers': epoint2}}

        ploader = loader.PluginLoader(group='testdata', entry_point='pluginlib.test.plugins')

        with warnings.catch_warnings(record=True) as e:
            warnings.simplefilter("always")
            plugins = ploader.plugins

            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, EntryPointWarning))
            self.assertRegex(str(e[-1].message), 'can not be loaded for entry point bad')

        self.assertEqual(len(plugins.parser), 1)
        self.assertTrue('xml' in plugins.parser)
        self.assertEqual(len(plugins.engine), 0)
        self.assertEqual(len(plugins.hook), 0)

    def test_load_entry_points_bad2(self):
        """Raise warning and continue when entry point fails - bad module"""

        epoint1 = EntryPoint.parse('bad = tests.testdata.lib.parsers.bad', dist=DIST)
        epoint2 = EntryPoint.parse('parsers = tests.testdata.lib.parsers.xml', dist=DIST)
        DIST._ep_map = {'pluginlib.test.plugins': {'bad': epoint1, 'parsers': epoint2}}

        ploader = loader.PluginLoader(group='testdata', entry_point='pluginlib.test.plugins')

        with warnings.catch_warnings(record=True) as e:
            warnings.simplefilter("always")
            plugins = ploader.plugins

            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, EntryPointWarning))
            self.assertRegex(str(e[-1].message), 'can not be loaded for entry point bad')

        self.assertEqual(len(plugins.parser), 1)
        self.assertTrue('xml' in plugins.parser)
        self.assertEqual(len(plugins.engine), 0)
        self.assertEqual(len(plugins.hook), 0)

    def test_load_entry_points_not_mod(self):
        """Raise warning and continue when entry point fails"""

        epoint = EntryPoint.parse('parsers = tests.testdata.lib.parsers.xml:XML', dist=DIST)
        DIST._ep_map = {'pluginlib.test.plugins': {'parsers': epoint}}

        ploader = loader.PluginLoader(group='testdata', entry_point='pluginlib.test.plugins')

        with warnings.catch_warnings(record=True) as e:
            warnings.simplefilter("always")
            plugins = ploader.plugins

            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, EntryPointWarning))
            self.assertRegex(str(e[-1].message), "Entry point 'parsers' is not a module or package")

        self.assertEqual(len(plugins.parser), 1)
        self.assertTrue('xml' in plugins.parser)
        self.assertEqual(len(plugins.engine), 0)
        self.assertEqual(len(plugins.hook), 0)

    def test_load_modules(self):
        """Load modules from modules"""
        ploader = loader.PluginLoader(group='testdata', modules=['tests.testdata.lib.parsers'])
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.engine), 0)
        self.assertEqual(len(plugins.hook), 0)

        self.assertEqual(len(plugins.parser), 2)
        self.assertTrue('xml' in plugins.parser)
        self.assertTrue('json' in plugins.parser)
        self.assertEqual(plugins.parser.json.version, '2.0')

    def test_load_paths(self):
        """Load modules from paths"""

        path = os.path.join(DATAPATH, 'lib', 'engines')
        ploader = loader.PluginLoader(group='testdata', paths=[path])
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.parser), 0)
        self.assertEqual(len(plugins.hook), 0)

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('steam' in plugins.engine)

        self.assertEqual(plugins.engine.steam.__module__, 'pluginlib.importer.engines.steam')

    def test_load_paths_bare(self):
        """Load modules from paths without init file"""

        path = os.path.join(DATAPATH, 'bare')
        ploader = loader.PluginLoader(group='testdata', paths=[path])
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.parser), 1)
        self.assertTrue('sillywalk' in plugins.parser)

        self.assertEqual(len(plugins.hook), 2)
        self.assertTrue('fish' in plugins.hook)
        self.assertTrue('grappling' in plugins.hook)

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('electric' in plugins.engine)

        self.assertEqual(plugins.engine.electric.__module__,
                         'pluginlib.importer.bare.engines.electric')

    def test_load_paths_prefix_pkg(self):
        """Load modules from paths with alternate prefix package"""

        path = os.path.join(DATAPATH, 'lib', 'engines')
        ploader = loader.PluginLoader(group='testdata', paths=[path],
                                      prefix_package='tests.testdata.importer')
        plugins = ploader.plugins

        self.assertEqual(len(plugins), 3)
        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertTrue('hook' in plugins)

        self.assertEqual(len(plugins.parser), 0)
        self.assertEqual(len(plugins.hook), 0)

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('steam' in plugins.engine)

        self.assertEqual(plugins.engine.steam.__module__, 'tests.testdata.importer.engines.steam')

    def test_type_filter(self):
        """Filter plugin types"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib',
                                      type_filter=('engine', 'parser'))
        plugins = ploader.plugins

        self.assertTrue('parser' in plugins)
        self.assertTrue('engine' in plugins)
        self.assertFalse('hook' in plugins)

    def test_load_paths_missing(self):
        """Log on invalid path"""

        path1 = os.path.join(DATAPATH, 'lib', 'engines')
        path2 = os.path.join(DATAPATH, 'NotARealPath')
        ploader = loader.PluginLoader(group='testdata', paths=[path1, path2])
        plugins = ploader.plugins

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('steam' in plugins.engine)

        self.assertRegex(OUTPUT.getvalue().splitlines()[-1], 'not a valid directory')

    def test_load_paths_duplicate(self):
        """Ignore duplicate paths"""

        path = os.path.join(DATAPATH, 'lib', 'engines')

        with warnings.catch_warnings(record=True) as e:

            warnings.simplefilter("always")
            ploader = loader.PluginLoader(group='testdata', paths=[path, path])
            plugins = ploader.plugins

            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, PluginWarning))
            self.assertRegex(str(e[-1].message), 'Duplicate plugins found')

        self.assertEqual(len(plugins.engine), 1)
        self.assertTrue('steam' in plugins.engine)

    def test_bad_import(self):
        """Syntax error in imported module"""

        ploader = loader.PluginLoader(group='testdata', modules=['tests.testdata.bad.syntax'])
        error = 'Error while importing candidate plugin module tests.testdata.bad.syntax'
        with self.assertRaisesRegex(PluginImportError, error) as e:
            ploader.plugins  # pylint: disable=pointless-statement

        self.assertRegex(e.exception.friendly, "SyntaxError: (?:invalid syntax|expected ':')")
        self.assertRegex(e.exception.friendly, 'tests.testdata.bad.syntax')
        self.assertRegex(e.exception.friendly, 'line 12')

    def test_bad_import2(self):
        """Exception raised by imported module"""

        ploader = loader.PluginLoader(group='testdata', modules=['tests.testdata.bad2'])
        error = 'Error while importing candidate plugin module tests.testdata.bad2'
        with self.assertRaisesRegex(PluginImportError, error) as e:
            ploader.plugins  # pylint: disable=pointless-statement

        self.assertRegex(e.exception.friendly, 'RuntimeError: This parrot is no more')
        self.assertRegex(e.exception.friendly, 'tests.testdata.bad2')
        self.assertRegex(e.exception.friendly, 'line 24')

    def test_bad_import_path(self):
        """Syntax error in imported module loaded by path"""

        path = os.path.join(DATAPATH, 'bad')
        ploader = loader.PluginLoader(group='testdata', paths=[path])
        error = 'Error while importing candidate plugin module pluginlib.importer.bad.syntax'
        with self.assertRaisesRegex(PluginImportError, error) as e:
            ploader.plugins  # pylint: disable=pointless-statement

        self.assertRegex(e.exception.friendly, "SyntaxError: (?:invalid syntax|expected ':')")
        self.assertRegex(e.exception.friendly, 'testdata/bad/syntax.py')
        self.assertRegex(e.exception.friendly, 'line 12')

    def test_plugins(self):
        """plugins only loads modules on the first call"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        with mock.patch.object(ploader, 'load_modules',
                               wraps=ploader.load_modules) as mock_load_modules:
            plugins1 = ploader.plugins
            self.assertEqual(mock_load_modules.call_count, 1)

            self.assertEqual(len(plugins1.parser), 2)
            self.assertTrue('xml' in plugins1.parser)
            self.assertTrue('json' in plugins1.parser)
            self.assertEqual(plugins1.parser.json.version, '2.0')

            plugins2 = ploader.plugins
            self.assertEqual(mock_load_modules.call_count, 1)

            self.assertEqual(plugins1, plugins2)

    def test_plugins_all(self):
        """plugins only loads modules on the first call"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        with mock.patch.object(ploader, 'load_modules',
                               wraps=ploader.load_modules) as mock_load_modules:
            plugins1 = ploader.plugins_all
            self.assertEqual(mock_load_modules.call_count, 1)

            self.assertEqual(len(plugins1.parser), 2)
            self.assertTrue('xml' in plugins1.parser)
            self.assertIsInstance(plugins1.parser.xml, OrderedDict)
            self.assertTrue('json' in plugins1.parser)
            self.assertIsInstance(plugins1.parser.json, OrderedDict)
            self.assertEqual(tuple(plugins1.parser.json.keys()), ('1.0', '2.0'))

            plugins2 = ploader.plugins_all
            self.assertEqual(mock_load_modules.call_count, 1)

            self.assertEqual(plugins1, plugins2)

            # Test for example in docs
            self.assertIs(tuple(plugins1.parser.json.values())[-1], plugins1.parser.json['2.0'])

    def test_blacklist(self):
        """Blacklist prevents listing plugin"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib',
                                      blacklist=[('parser', 'json', '2.0'), ('engine',)])
        plugins = ploader.plugins

        self.assertEqual(len(plugins.engine), 0)
        self.assertEqual(plugins.parser.json.version, '1.0')

    def test_get_plugin(self):
        """Retrieve specific plugin"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        with mock.patch.object(ploader, 'load_modules',
                               wraps=ploader.load_modules) as mock_load_modules:

            jsonplugin = ploader.get_plugin('parser', 'json')
            self.assertEqual(jsonplugin.name, 'json')
            self.assertEqual(jsonplugin.version, '2.0')
            self.assertEqual(mock_load_modules.call_count, 1)

            jsonplugin = ploader.get_plugin('parser', 'json', '1.0')
            self.assertEqual(jsonplugin.name, 'json')
            self.assertEqual(jsonplugin.version, '1.0')
            self.assertEqual(mock_load_modules.call_count, 1)

    def test_get_plugin_missing(self):
        """Attempt to retrieve non-existent plugin, return None"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        self.assertIsNone(ploader.get_plugin('penguin', 'json'))
        self.assertIsNone(ploader.get_plugin('parser', 'penguin'))

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib')
        self.assertIsNone(ploader.get_plugin('parser', 'json', '300.1.1'))

    def test_get_plugin_filtered(self):
        """Retrieve specific plugin if not filtered"""

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib',
                                      type_filter=('engine', 'hook'))

        self.assertIsNone(ploader.get_plugin('parser', 'json'))

        steamplugin = ploader.get_plugin('engine', 'steam')
        self.assertEqual(steamplugin.name, 'steam')

    def test_get_plugin_blacklist(self):
        """Retrieve specific plugin if not blacklisted"""

        blacklist = [('parser', 'json', '2.0'), ('parser', 'xml'), ('engine',)]

        ploader = loader.PluginLoader(group='testdata', library='tests.testdata.lib',
                                      blacklist=blacklist)

        self.assertIsNone(ploader.get_plugin('parser', 'json', '2.0'))
        self.assertIsNone(ploader.get_plugin('parser', 'xml'))
        self.assertIsNone(ploader.get_plugin('engine', 'steam'))

        jsonplugin = ploader.get_plugin('parser', 'json')
        self.assertEqual(jsonplugin.name, 'json')
        self.assertEqual(jsonplugin.version, '1.0')
