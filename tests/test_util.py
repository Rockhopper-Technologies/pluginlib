# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib._util**
"""

import sys

import pluginlib._util as util

from tests import TestCase


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


class TestCachingDict(TestCase):
    """Tests for CachingDict dictionary subclass"""
    # pylint: disable=protected-access

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
