# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib._objects**
"""

import pluginlib._objects as objects

from tests import TestCase, mock


# pylint: disable=protected-access


class TestBlacklistEntry(TestCase):
    """Tests for BlacklistEntry class"""

    def test_empty(self):
        """Some value must be supplied or all plugins would be blacklisted"""
        with self.assertRaises(AttributeError):
            objects.BlacklistEntry()
        with self.assertRaises(AttributeError):
            objects.BlacklistEntry(operator='>')

    def test_ver_op(self):
        """Operator and version can be swapped"""
        entry = objects.BlacklistEntry('parser', 'json', '1.0', '>=')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '>=')

    def test_op_ver(self):
        """Operator and version can be swapped"""
        entry = objects.BlacklistEntry('parser', 'json', '>=', '1.0')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '>=')

    def test_op_none(self):
        """Operator is required when version is supplied"""
        with self.assertRaises(AttributeError):
            objects.BlacklistEntry('parser', 'json', '>=')
        entry = objects.BlacklistEntry('parser', 'json')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, None)
        self.assertEqual(entry.operator, '==')

    def test_no_op(self):
        """Operator defaults to '=='"""
        entry = objects.BlacklistEntry('parser', 'json', '1.0')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '==')

    def test_op_bad(self):
        """Operators must be in '=', '==', '!=', '<', '<=', '>', '>='"""
        with self.assertRaises(AttributeError):
            objects.BlacklistEntry('parser', 'json', '1.0', '%')

    def test_ver_bad(self):
        """Version is not a string"""
        with self.assertRaises(TypeError):
            objects.BlacklistEntry('parser', 'json', 1.0)

    def test_repr(self):
        """Ensure repr displays properly"""
        entry = objects.BlacklistEntry('parser', 'json', '1.0', '>=')
        self.assertEqual(repr(entry), "BlacklistEntry('parser', 'json', '>=', '1.0')")


class TestGroupDict(TestCase):
    """Tests for GroupDict dictionary subclass"""

    def setUp(self):
        """Create sample dictionary"""
        self.mock_type_parser = mock.Mock()
        self.mock_type_parser._filter.return_value = 'parsertype'
        self.mock_type_engine = mock.Mock()
        self.mock_type_engine._filter.return_value = 'enginetype'
        self.mock_type_empty = mock.Mock()
        self.mock_type_empty._filter.return_value = {}

        self.expected = {'parser': 'parsertype', 'engine': 'enginetype', 'empty': {}}
        self.gdict = objects.GroupDict({'parser': self.mock_type_parser,
                                        'engine': self.mock_type_engine,
                                        'empty': self.mock_type_empty})

    def test_no_blacklist(self):
        """Skip all blacklist logic"""
        self.assertEqual(self.gdict._filter(), self.expected)
        self.mock_type_parser._filter.assert_called_with(None, newest_only=False)
        self.mock_type_engine._filter.assert_called_with(None, newest_only=False)
        self.mock_type_empty._filter.assert_called_with(None, newest_only=False)

        self.assertEqual(self.gdict._filter([]), self.expected)
        self.mock_type_parser._filter.assert_called_with(None, newest_only=False)
        self.mock_type_engine._filter.assert_called_with(None, newest_only=False)
        self.mock_type_empty._filter.assert_called_with(None, newest_only=False)

    def test_blacklist_by_type(self):
        """Entire type is blacklisted, so it should be empty"""
        blacklist = [objects.BlacklistEntry('parser')]
        self.expected['parser'] = {}
        self.assertEqual(self.gdict._filter(blacklist), self.expected)
        self.mock_type_parser._filter.assert_not_called()
        self.mock_type_engine._filter.assert_called_with([], newest_only=False)
        self.mock_type_empty._filter.assert_called_with([], newest_only=False)

    def test_blacklist_by_type_name(self):
        """A type and specific name is blacklisted, so blacklist is passed to child for type"""
        blacklist = [objects.BlacklistEntry('parser', 'json')]
        self.assertEqual(self.gdict._filter(blacklist), self.expected)
        self.mock_type_parser._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_type_engine._filter.assert_called_with([], newest_only=False)
        self.mock_type_empty._filter.assert_called_with([], newest_only=False)

    def test_blacklist_by_name(self):
        """A name is blacklisted in all types, so all children are passed the blacklist"""
        blacklist = [objects.BlacklistEntry(None, 'json')]
        self.assertEqual(self.gdict._filter(blacklist), self.expected)
        self.mock_type_parser._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_type_engine._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_type_empty._filter.assert_called_with(blacklist, newest_only=False)

    def test_empty(self):
        """Unless the entire type is blacklisted, an empty return value is still included"""
        blacklist = [objects.BlacklistEntry('empty', 'json')]
        self.assertEqual(self.gdict._filter(blacklist), self.expected)
        self.mock_type_parser._filter.assert_called_with([], newest_only=False)
        self.mock_type_engine._filter.assert_called_with([], newest_only=False)
        self.mock_type_empty._filter.assert_called_with(blacklist, newest_only=False)

    def test_type_filter(self):
        """Types not in list should be ignored"""
        del self.expected['engine']
        self.assertEqual(self.gdict._filter(type_filter=('parser', 'empty')), self.expected)

    def test_type(self):
        """Get a specific type"""
        self.assertEqual(self.gdict._filter(type='engine'), 'enginetype')
        self.mock_type_engine._filter.assert_called_with(None, newest_only=False, type='engine')
        self.assertIsNone(self.gdict._filter(type='penguin'))

    def test_type_and_type_filter(self):
        """Type filter still affects calls for specific types"""
        self.assertEqual(self.gdict._filter(type_filter=('parser', 'empty'), type='engine'), None)
        self.mock_type_engine._filter.assert_not_called()
        self.mock_type_parser._filter.assert_not_called()
        self.mock_type_empty._filter.assert_not_called()

        self.assertEqual(self.gdict._filter(type_filter=('engine', 'empty'), type='engine'),
                         'enginetype')
        self.mock_type_engine._filter.assert_called_with(None, newest_only=False, type='engine')
        self.mock_type_parser._filter.assert_not_called()
        self.mock_type_empty._filter.assert_not_called()


class TestTypeDict(TestCase):
    """Tests for GroupDict dictionary subclass"""

    def setUp(self):
        """Create sample dictionary"""
        self.mock_plugin_json = mock.Mock()
        self.mock_plugin_json._filter.return_value = 'jsonplugin'
        self.mock_plugin_xml = mock.Mock()
        self.mock_plugin_xml._filter.return_value = 'xmlplugin'
        self.expected = {'json': 'jsonplugin', 'xml': 'xmlplugin'}
        self.tdict = objects.TypeDict('parser', {'json': self.mock_plugin_json,
                                                 'xml': self.mock_plugin_xml})

    def test_parent(self):
        """Ensure parent attribute is set"""
        self.assertEqual('parser', self.tdict._parent)

    def test_no_blacklist(self):
        """Skip all blacklist logic"""
        self.assertEqual(self.tdict._filter(), self.expected)
        self.mock_plugin_json._filter.assert_called_with(None, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with(None, newest_only=False)

        self.assertEqual(self.tdict._filter([]), self.expected)
        self.mock_plugin_json._filter.assert_called_with(None, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with(None, newest_only=False)

    def test_blacklist_by_name(self):
        """Entire name is blacklisted, so it's not called or included"""
        blacklist = [objects.BlacklistEntry(None, 'json')]
        del self.expected['json']
        self.assertEqual(self.tdict._filter(blacklist), self.expected)
        self.mock_plugin_json._filter.assert_not_called()
        self.mock_plugin_xml._filter.assert_called_with([], newest_only=False)

    def test_blacklist_all(self):
        """Type is blacklisted, so all are blacklisted"""
        blacklist = [objects.BlacklistEntry('parser')]
        self.assertEqual(self.tdict._filter(blacklist), {})
        self.mock_plugin_json._filter.assert_not_called()
        self.mock_plugin_xml._filter.assert_not_called()

    def test_blacklist_by_name_version(self):
        """A name and version is blacklisted, so blacklist is passed to child for type"""
        blacklist = [objects.BlacklistEntry('parser', 'json', '1.0')]
        self.assertEqual(self.tdict._filter(blacklist), self.expected)
        self.mock_plugin_json._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with([], newest_only=False)

    def test_blacklist_by_version(self):
        """Only a version is blacklisted, so blacklist is passed to all children"""
        blacklist = [objects.BlacklistEntry(None, None, '1.0')]
        self.assertEqual(self.tdict._filter(blacklist), self.expected)
        self.mock_plugin_json._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with(blacklist, newest_only=False)

    def test_empty(self):
        """Empty values are not included"""
        mock_plugin_empty = mock.Mock()
        mock_plugin_empty._filter.return_value = None
        self.tdict['empty'] = mock_plugin_empty
        self.assertEqual(self.tdict._filter(), self.expected)
        self.tdict._filter()
        self.mock_plugin_json._filter.assert_called_with(None, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with(None, newest_only=False)
        mock_plugin_empty._filter.assert_called_with(None, newest_only=False)

        blacklist = [objects.BlacklistEntry(None, None, '1.0')]
        self.assertEqual(self.tdict._filter(blacklist), self.expected)
        self.mock_plugin_json._filter.assert_called_with(blacklist, newest_only=False)
        self.mock_plugin_xml._filter.assert_called_with(blacklist, newest_only=False)
        mock_plugin_empty._filter.assert_called_with(blacklist, newest_only=False)

    def test_type_filter(self):
        """type_filter ignored in type dict"""
        self.assertEqual(self.tdict._filter(type_filter=('engine')), self.expected)

    def test_name(self):
        """Get a specific name"""
        self.assertEqual(self.tdict._filter(name='json'), 'jsonplugin')
        self.mock_plugin_json._filter.assert_called_with(None, newest_only=False, name='json')

        self.assertIsNone(self.tdict._filter(name='pengion'))


class TestPluginDict(TestCase):
    """Tests for PluginDict dictionary subclass"""

    def setUp(self):
        self.udict = objects.PluginDict({'2.0': 'dos', '1.0': 'uno', '3.0': 'tres'})

    def test_sorted_keys(self):
        """Sorts by version and populates cache"""

        sorted_keys = ['1.0', '2.0', '3.0']
        self.assertFalse('sorted_keys' in self.udict._cache)

        self.assertEqual(self.udict._sorted_keys(), sorted_keys)
        self.assertTrue('sorted_keys' in self.udict._cache)
        self.assertEqual(self.udict._cache['sorted_keys'], sorted_keys)

        # Call again to make sure results are consistent
        self.assertEqual(self.udict._sorted_keys(), sorted_keys)
        self.assertTrue('sorted_keys' in self.udict._cache)
        self.assertEqual(self.udict._cache['sorted_keys'], sorted_keys)

        del self.udict['2.0']
        self.assertFalse('sorted_keys' in self.udict._cache)
        self.assertEqual(self.udict._sorted_keys(), ['1.0', '3.0'])
        self.assertTrue('sorted_keys' in self.udict._cache)
        self.assertEqual(self.udict._cache['sorted_keys'], ['1.0', '3.0'])

    def test_empty(self):
        """Empty dictionary will return None"""
        udict = objects.PluginDict()
        self.assertIsNone(udict._filter())
        self.assertIsNone(udict._filter(newest_only=True))
        self.assertIsNone(udict._filter('FakeBlackList'))
        self.assertIsNone(udict._filter('FakeBlackList', newest_only=True))

    def test_no_blacklist(self):
        """Return newest without filtering"""
        self.assertEqual(self.udict._filter(newest_only=True), 'tres')

    def test_empty_blacklist(self):
        """Same as no blacklist"""
        self.assertEqual(self.udict._filter([]), self.udict)
        self.assertEqual(self.udict._filter([], newest_only=True), 'tres')

    def test_blacklist(self):
        """Cache gets populated and results get filtered"""

        # Cache is populated and highest value is filtered
        blacklist = [objects.BlacklistEntry(None, None, '3.0')]
        self.assertFalse('blacklist' in self.udict._cache)
        self.assertEqual(self.udict._filter(blacklist, newest_only=True), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 1)
        self.assertEqual(self.udict._cache['blacklist'][('3.0', '==')], set(['3.0']))

        self.assertEqual(self.udict._filter(blacklist),
                         objects.OrderedDict([('1.0', 'uno'), ('2.0', 'dos')]))

        # Another entry is cached, result is the same
        blacklist.append(objects.BlacklistEntry(None, None, '1.0'))
        self.assertEqual(self.udict._filter(blacklist, newest_only=True), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 2)
        self.assertEqual(self.udict._cache['blacklist'][('1.0', '==')], set(['1.0']))

        self.assertEqual(self.udict._filter(blacklist),
                         objects.OrderedDict([('2.0', 'dos')]))

        # An equivalent entry is added, cache is the same
        blacklist.append(objects.BlacklistEntry(None, 'number', '3.0', '=='))
        self.assertEqual(self.udict._filter(blacklist, newest_only=True), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 2)

        self.assertEqual(self.udict._filter(blacklist),
                         objects.OrderedDict([('2.0', 'dos')]))

    def test_no_result(self):
        """Blacklist filters all"""
        blacklist = [objects.BlacklistEntry(None, None, '4.0', '<')]

        self.assertEqual(self.udict._filter(blacklist), objects.OrderedDict())
        self.assertEqual(self.udict._cache['blacklist'][('4.0', '<')], set(['1.0', '2.0', '3.0']))

        self.assertIsNone(self.udict._filter(blacklist, newest_only=True))
        self.assertEqual(self.udict._cache['blacklist'][('4.0', '<')], set(['1.0', '2.0', '3.0']))

    def test_version(self):
        """Return specific version"""
        self.assertEqual(self.udict._filter(newest_only=True, version='1.0'), 'uno')

    def test_version_blacklist(self):
        """Return specific version if not blacklisted"""
        blacklist = [objects.BlacklistEntry(None, None, '1.0')]
        self.assertEqual(self.udict._filter(blacklist, newest_only=True, version='1.0'), None)
        self.assertEqual(self.udict._filter(blacklist, newest_only=True, version='2.0'), 'dos')
