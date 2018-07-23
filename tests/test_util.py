# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib._util**
"""

import sys

import pluginlib._util as util

from tests import TestCase, mock


class TestReraise(TestCase):
    """Tests for raise_with_traceback"""
    def test_raise_with_traceback(self):
        """Caught error should raise as expected"""
        try:
            raise TypeError('Not my type')
        except TypeError as e:
            tback = getattr(e, '__traceback__', sys.exc_info()[2])
            exception = AttributeError('Nah: %s' % str(e))

            with self.assertRaisesRegex(AttributeError, 'Nah: Not my type'):
                util.raise_with_traceback(exception, tback)


class TestClassProperty(TestCase):
    """Tests for ClassProperty decorator class"""

    someproperty = 'Value of a property'

    @util.ClassProperty
    def testproperty(cls):  # noqa: N805 # pylint: disable=no-self-argument
        """Example class property"""
        return cls.someproperty

    def test_class_property(self):
        """Class property should be accessible via standard dot notation"""
        self.assertEqual(self.testproperty, self.someproperty)
        self.assertEqual(self.testproperty, 'Value of a property')


class TestUndefined(TestCase):
    """Tests for Undefined class"""

    def test_str(self):
        """String representation"""
        undef = util.Undefined()
        self.assertEqual(str(undef), 'UNDEF')
        self.assertEqual(repr(undef), 'UNDEF')

    def test_str_nondefault(self):
        """String representation with non-default label"""
        undef = util.Undefined('UNSET')
        self.assertEqual(str(undef), 'UNSET')
        self.assertEqual(repr(undef), 'UNSET')

    def test_bool(self):
        """Should always be False in a Boolean test"""
        undef = util.Undefined()
        self.assertFalse(undef)


class TestAllowBareDecorator(TestCase):
    """Test allow_bare_decorator class decorator decorator"""

    # pylint: disable=no-member
    def test_allow_bare_decorator(self):
        """Decorator should work with or without parentheses"""

        @util.allow_bare_decorator
        class Decorator(object):
            """Sample decorator class"""

            def __init__(self, name=None, group=None):
                self.name = name
                self.group = group

            def __call__(self, cls):
                cls.name = self.name or cls.__name__
                cls.group = self.group or 'default'
                return cls

        @Decorator
        class Class1(object):
            """Bare decorator"""

        self.assertEqual(Class1.__name__, 'Class1')
        self.assertEqual(Class1.name, 'Class1')
        self.assertEqual(Class1.group, 'default')

        @Decorator()
        class Class2(object):
            """Decorator without arguments"""

        self.assertEqual(Class2.__name__, 'Class2')
        self.assertEqual(Class2.name, 'Class2')
        self.assertEqual(Class2.group, 'default')

        @Decorator('spam')
        class Class3(object):
            """Decorator with one argument"""

        self.assertEqual(Class3.__name__, 'Class3')
        self.assertEqual(Class3.name, 'spam')
        self.assertEqual(Class3.group, 'default')

        @Decorator('spam', 'ham')
        class Class4(object):
            """Decorator with two arguments"""

        self.assertEqual(Class4.__name__, 'Class4')
        self.assertEqual(Class4.name, 'spam')
        self.assertEqual(Class4.group, 'ham')


class TestBlacklistEntry(TestCase):
    """Tests for BlacklistEntry class"""

    def test_empty(self):
        """Some value must be supplied or all plugins would be blacklisted"""
        with self.assertRaises(AttributeError):
            util.BlacklistEntry()
        with self.assertRaises(AttributeError):
            util.BlacklistEntry(operator='>')

    def test_ver_op(self):
        """Operator and version can be swapped"""
        entry = util.BlacklistEntry('parser', 'json', '1.0', '>=')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '>=')

    def test_op_ver(self):
        """Operator and version can be swapped"""
        entry = util.BlacklistEntry('parser', 'json', '>=', '1.0')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '>=')

    def test_op_none(self):
        """Operator is required when version is supplied"""
        with self.assertRaises(AttributeError):
            util.BlacklistEntry('parser', 'json', '>=')
        entry = util.BlacklistEntry('parser', 'json')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, None)
        self.assertEqual(entry.operator, '==')

    def test_no_op(self):
        """Operator defaults to '=='"""
        entry = util.BlacklistEntry('parser', 'json', '1.0')
        self.assertEqual(entry.type, 'parser')
        self.assertEqual(entry.name, 'json')
        self.assertEqual(entry.version, '1.0')
        self.assertEqual(entry.operator, '==')

    def test_op_bad(self):
        """Operators must be in '=', '==', '!=', '<', '<=', '>', '>='"""
        with self.assertRaises(AttributeError):
            util.BlacklistEntry('parser', 'json', '1.0', '%')

    def test_ver_bad(self):
        """Version is not a string"""
        with self.assertRaises(TypeError):
            util.BlacklistEntry('parser', 'json', 1.0)

    def test_repr(self):
        """Ensure repr displays properly"""
        entry = util.BlacklistEntry('parser', 'json', '1.0', '>=')
        self.assertEqual(repr(entry), "BlacklistEntry('parser', 'json', '>=', '1.0')")


# pylint: disable=protected-access
class TestCachingDict(TestCase):
    """Tests for CachingDict dictionary subclass"""

    def setUp(self):
        """Stage dictionary and cache"""
        self.cdict = util.CachingDict()
        self.cdict['hello'] = 'world'
        self.cdict._cache['test'] = 'Testing'

    def test_init(self):
        """Standard initialization"""
        self.assertTrue(isinstance(self.cdict._cache, dict))
        self.assertTrue('test' in self.cdict._cache)
        self.cdict._cache.clear()

    def test_setitem(self):
        """Setting a value clears the cache"""
        self.cdict['Hey'] = 'Jude'

    def test_delitem(self):
        """Deleting a value clears the cache"""
        del self.cdict['hello']

    def test_clear(self):
        """Clearing the dictionary also clears the cache"""
        self.cdict.clear()

    def test_setdefault(self):
        """setdefault() only clears the cache when the key doesn't exist"""
        self.assertEqual('world', self.cdict.setdefault('hello', None))
        self.assertTrue('test' in self.cdict._cache)
        self.assertEqual('Jude', self.cdict.setdefault('Hey', 'Jude'))

    def test_pop(self):
        """pop() only clears the cache is the key exists"""
        with self.assertRaises(KeyError):
            self.cdict.pop('Hey')
        self.assertTrue('test' in self.cdict._cache)
        self.assertEqual('world', self.cdict.pop('hello'))

    def test_popitem(self):
        """"popitem() only clears the cache if the dictionary isn't empty"""
        del self.cdict['hello']
        self.cdict._cache['test'] = 'Testing'
        self.assertTrue('test' in self.cdict._cache)

        with self.assertRaises(KeyError):
            self.cdict.popitem()
        self.assertTrue('test' in self.cdict._cache)

        self.setUp()
        self.assertTrue('test' in self.cdict._cache)
        self.assertEqual(('hello', 'world'), self.cdict.popitem())

    def tearDown(self):
        """Ensure cache was cleared"""
        self.assertFalse('test' in self.cdict._cache)
        self.assertFalse(self.cdict._cache)


class TestDictWithDotNotation(TestCase):
    """Tests for DictWithDotNotation dictionary subclass"""

    def test_getter(self):
        """Values can be retrieved by index or dot notation"""
        dotdict = util.DictWithDotNotation({'hello': 'world'})

        self.assertEqual('world', dotdict['hello'])
        self.assertEqual('world', dotdict.hello)

        with self.assertRaises(AttributeError):
            dotdict.notInDict  # pylint: disable=pointless-statement

        with self.assertRaises(KeyError):
            dotdict['notInDict']  # pylint: disable=pointless-statement


class TestGroupDict(TestCase):
    """Tests for GroupDict dictionary subclass"""

    def setUp(self):
        """Create sample dictionary"""
        self.mock_type_parser = mock.Mock()
        self.mock_type_parser._newest.return_value = 'parser'
        self.mock_type_engine = mock.Mock()
        self.mock_type_engine._newest.return_value = 'engine'
        self.mock_type_empty = mock.Mock()
        self.mock_type_empty._newest.return_value = {}

        self.expected = {'parser': 'parser', 'engine': 'engine', 'empty': {}}
        self.gdict = util.GroupDict({'parser': self.mock_type_parser,
                                     'engine': self.mock_type_engine,
                                     'empty': self.mock_type_empty})

    def test_no_blacklist(self):
        """Skip all blacklist logic"""
        self.assertEqual(self.gdict._newest(), self.expected)
        self.mock_type_parser._newest.assert_called_with()
        self.mock_type_engine._newest.assert_called_with()
        self.mock_type_empty._newest.assert_called_with()

        self.assertEqual(self.gdict._newest([]), self.expected)
        self.mock_type_parser._newest.assert_called_with()
        self.mock_type_engine._newest.assert_called_with()
        self.mock_type_empty._newest.assert_called_with()

    def test_blacklist_by_type(self):
        """Entire type is blacklisted, so it should be empty"""
        blacklist = [util.BlacklistEntry('parser')]
        self.expected['parser'] = {}
        self.assertEqual(self.gdict._newest(blacklist), self.expected)
        self.mock_type_parser._newest.assert_not_called()
        self.mock_type_engine._newest.assert_called_with([])
        self.mock_type_empty._newest.assert_called_with([])

    def test_blacklist_by_type_name(self):
        """A type and specific name is blacklisted, so blacklist is passed to child for type"""
        blacklist = [util.BlacklistEntry('parser', 'json')]
        self.assertEqual(self.gdict._newest(blacklist), self.expected)
        self.mock_type_parser._newest.ssert_called_with(blacklist)
        self.mock_type_engine._newest.assert_called_with([])
        self.mock_type_empty._newest.assert_called_with([])

    def test_blacklist_by_name(self):
        """A name is blacklisted in all types, so all children are passed the blacklist"""
        blacklist = [util.BlacklistEntry(None, 'json')]
        self.assertEqual(self.gdict._newest(blacklist), self.expected)
        self.mock_type_parser._newest.ssert_called_with(blacklist)
        self.mock_type_engine._newest.assert_called_with(blacklist)
        self.mock_type_empty._newest.assert_called_with(blacklist)

    def test_empty(self):
        """Unless the entire type is blacklisted, an empty return value is still included"""
        blacklist = [util.BlacklistEntry('empty', 'json')]
        self.assertEqual(self.gdict._newest(blacklist), self.expected)
        self.mock_type_parser._newest.ssert_called_with([])
        self.mock_type_engine._newest.assert_called_with([])
        self.mock_type_empty._newest.assert_called_with(blacklist)


class TestTypeDict(TestCase):
    """Tests for GroupDict dictionary subclass"""

    def setUp(self):
        """Create sample dictionary"""
        self.mock_plugin_json = mock.Mock()
        self.mock_plugin_json._newest.return_value = 'json'
        self.mock_plugin_xml = mock.Mock()
        self.mock_plugin_xml._newest.return_value = 'xml'
        self.expected = {'json': 'json', 'xml': 'xml'}
        self.tdict = util.TypeDict('parser', {'json': self.mock_plugin_json,
                                              'xml': self.mock_plugin_xml})

    def test_parent(self):
        """Ensure parent attribute is set"""
        self.assertEqual('parser', self.tdict._parent)

    def test_no_blacklist(self):
        """Skip all blacklist logic"""
        self.assertEqual(self.tdict._newest(), self.expected)
        self.mock_plugin_json._newest.assert_called_with()
        self.mock_plugin_xml._newest.assert_called_with()

        self.assertEqual(self.tdict._newest([]), self.expected)
        self.mock_plugin_json._newest.assert_called_with()
        self.mock_plugin_xml._newest.assert_called_with()

    def test_blacklist_by_name(self):
        """Entire name is blacklisted, so it's not called or included"""
        blacklist = [util.BlacklistEntry(None, 'json')]
        del self.expected['json']
        self.assertEqual(self.tdict._newest(blacklist), self.expected)
        self.mock_plugin_json._newest.assert_not_called()
        self.mock_plugin_xml._newest.assert_called_with([])

    def test_blacklist_all(self):
        """Type is blacklisted, so all are blacklisted"""
        blacklist = [util.BlacklistEntry('parser')]
        self.assertEqual(self.tdict._newest(blacklist), {})
        self.mock_plugin_json._newest.assert_not_called()
        self.mock_plugin_xml._newest.assert_not_called()

    def test_blacklist_by_name_version(self):
        """A name and version is blacklisted, so blacklist is passed to child for type"""
        blacklist = [util.BlacklistEntry('parser', 'json', '1.0')]
        self.assertEqual(self.tdict._newest(blacklist), self.expected)
        self.mock_plugin_json._newest.assert_called_with(blacklist)
        self.mock_plugin_xml._newest.assert_called_with([])

    def test_blacklist_by_version(self):
        """Only a version is blacklisted, so blacklist is passed to all children"""
        blacklist = [util.BlacklistEntry(None, None, '1.0')]
        self.assertEqual(self.tdict._newest(blacklist), self.expected)
        self.mock_plugin_json._newest.assert_called_with(blacklist)
        self.mock_plugin_xml._newest.assert_called_with(blacklist)

    def test_empty(self):
        """Empty values are not included"""
        mock_plugin_empty = mock.Mock()
        mock_plugin_empty._newest.return_value = None
        self.tdict['empty'] = mock_plugin_empty
        self.assertEqual(self.tdict._newest(), self.expected)
        self.tdict._newest()
        self.mock_plugin_json._newest.assert_called_with()
        self.mock_plugin_xml._newest.assert_called_with()
        mock_plugin_empty._newest.assert_called_with()

        blacklist = [util.BlacklistEntry(None, None, '1.0')]
        self.assertEqual(self.tdict._newest(blacklist), self.expected)
        self.mock_plugin_json._newest.assert_called_with(blacklist)
        self.mock_plugin_xml._newest.assert_called_with(blacklist)
        mock_plugin_empty._newest.assert_called_with(blacklist)


class TestPluginDict(TestCase):
    """Tests for PluginDict dictionary subclass"""

    def setUp(self):
        self.udict = util.PluginDict({'2.0': 'dos', '1.0': 'uno', '3.0': 'tres'})

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
        udict = util.PluginDict()
        self.assertIsNone(udict._newest())
        self.assertIsNone(udict._newest('FakeBlackList'))

    def test_no_blacklist(self):
        """Return newest without filtering"""
        self.assertEqual(self.udict._newest(), 'tres')

    def test_empty_blacklist(self):
        """Same as no blacklist"""
        self.assertEqual(self.udict._newest([]), 'tres')

    def test_blacklist(self):
        """Cache gets populated and results get filtered"""

        # Cache is populated and highest value is filtered
        blacklist = [util.BlacklistEntry(None, None, '3.0')]
        self.assertFalse('blacklist' in self.udict._cache)
        self.assertEqual(self.udict._newest(blacklist), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 1)
        self.assertEqual(self.udict._cache['blacklist'][('3.0', '==')], set(['3.0']))

        # Another entry is cached, result is the same
        blacklist.append(util.BlacklistEntry(None, None, '1.0'))
        self.assertEqual(self.udict._newest(blacklist), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 2)
        self.assertEqual(self.udict._cache['blacklist'][('1.0', '==')], set(['1.0']))

        # An equivalent entry is added, cache is the same
        blacklist.append(util.BlacklistEntry(None, 'number', '3.0', '=='))
        self.assertEqual(self.udict._newest(blacklist), 'dos')
        self.assertEqual(len(self.udict._cache['blacklist']), 2)

    def test_no_result(self):
        """Blacklist filters all"""
        blacklist = [util.BlacklistEntry(None, None, '4.0', '<')]
        self.assertIsNone(self.udict._newest(blacklist))
        self.assertEqual(self.udict._cache['blacklist'][('4.0', '<')], set(['1.0', '2.0', '3.0']))


class TestClassAbstractStaticMethod(TestCase):
    """Tests for abstractstaticmethod decorator class"""

    def test_abstractstaticmethod(self):
        """Creates a static method marked as an abstract method"""

        def func():
            """Dummy function"""
            return True

        meth = util.abstractstaticmethod(func)
        self.assertIsInstance(meth, staticmethod)
        self.assertTrue(getattr(meth, '__isabstractmethod__', False))
        if sys.version_info[:2] >= (2, 7):
            self.assertTrue(getattr(meth.__func__, '__isabstractmethod__', False))
        else:
            self.assertTrue(getattr(meth.__get__(True), '__isabstractmethod__', False))


class TestClassAbstractClassMethod(TestCase):
    """Tests for abstractclassmethod decorator class"""

    def test_abstractclassmethod(self):
        """Creates a class method marked as an abstract method"""

        def func():
            """Dummy function"""
            return True

        meth = util.abstractclassmethod(func)
        self.assertIsInstance(meth, classmethod)
        self.assertTrue(getattr(meth, '__isabstractmethod__', False))
        if sys.version_info[:2] >= (2, 7):
            self.assertTrue(getattr(meth.__func__, '__isabstractmethod__', False))
        else:
            self.assertTrue(getattr(meth.__get__(True).__func__, '__isabstractmethod__', False))
