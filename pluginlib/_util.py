# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Utility Module**

This module contains generic functions for use in other modules
"""

from abc import abstractmethod
from functools import update_wrapper, wraps
from inspect import isclass
import logging
import operator as _operator
import sys


PY26 = sys.version_info[:2] < (2, 7)
PY34 = sys.version_info[:2] < (3, 5)


# Setup logger
if PY26:  # pragma: no branch

    class NullHandler(logging.Handler):  # pragma: no cover
        """NullHandler for Python 2.6"""
        def emit(self, record):
            pass
else:
    NullHandler = logging.NullHandler


LOGGER = logging.getLogger('pluginlib')
LOGGER.addHandler(NullHandler())

OPERATORS = {'=': _operator.eq,
             '==': _operator.eq,
             '!=': _operator.ne,
             '<': _operator.lt,
             '<=': _operator.le,
             '>': _operator.gt,
             '>=': _operator.ge}


NoneType = type(None)

if sys.version_info[0] < 3:  # pragma: no branch
    BASESTRING = basestring  # pragma: no cover  # noqa: F821 # pylint: disable=undefined-variable
else:
    BASESTRING = str


def raise_with_traceback(exc, tback):  # pragma: no cover
    """
    Placeholder for version-specific implementation
    """
    raise NotImplementedError


# Attempt to make a Python 2/3 compatible way to raise with a traceback
# pylint: disable=exec-used
if sys.version_info[0] < 3:  # pragma: no branch
    exec("""def raise_with_traceback(exc, tback):  # pragma: no cover
    raise exc.__class__, exc, tback
""")
else:
    exec("""def raise_with_traceback(exc, tback):
    raise exc.with_traceback(tback) from None
""")


def raise_from_none(exc):  # pragma: no cover
    """
    Convenience function to raise from None in a Python 2/3 compatible manner
    """
    raise exc


if sys.version_info[0] >= 3:  # pragma: no branch
    exec('def raise_from_none(exc):\n    raise exc from None')  # pylint: disable=exec-used


class ClassProperty(object):
    """
    Property decorator for class methods
    """

    def __init__(self, method):

        self.method = method
        update_wrapper(self, method)

    def __get__(self, instance, cls):
        return self.method(cls)


class Undefined(object):
    """
    Class for creating unique undefined objects for value comparisons
    """

    def __init__(self, label='UNDEF'):
        self.label = label

    def __str__(self):
        return self.label

    def __repr__(self):
        return self.__str__()

    def __bool__(self):
        return False

    # For Python 2
    __nonzero__ = __bool__


def allow_bare_decorator(cls):
    """
    Wrapper for a class decorator which allows for bare decorator and argument syntax
    """

    @wraps(cls)
    def wrapper(*args, **kwargs):
        """"Wrapper for real decorator"""

        # If we weren't only passed a bare class, return class instance
        if kwargs or len(args) != 1 or not isclass(args[0]):  # pylint: disable=no-else-return
            return cls(*args, **kwargs)
        # Otherwise, pass call to instance with default values
        else:
            return cls()(args[0])

    return wrapper


class CachingDict(dict):
    """
    A subclass of :py:class:`dict` that has a private _cache attribute

    self._cache is regular dictionary which is cleared whenever the CachingDict is changed

    Nothing is actually cached. That is the responsibility of the inheriting class
    """

    def __init__(self, *args, **kwargs):
        super(CachingDict, self).__init__(*args, **kwargs)
        self._cache = {}

    def __setitem__(self, key, value):
        try:
            super(CachingDict, self).__setitem__(key, value)
        finally:
            self._cache.clear()

    def __delitem__(self, key):
        try:
            super(CachingDict, self).__delitem__(key)
        finally:
            self._cache.clear()

    def clear(self):
        try:
            super(CachingDict, self).clear()
        finally:
            self._cache.clear()

    def setdefault(self, key, default=None):

        try:
            return self[key]
        except KeyError:
            self.__setitem__(key, default)
            return default

    def pop(self, *args):
        try:
            value = super(CachingDict, self).pop(*args)
        except KeyError as e:
            raise e
        else:
            self._cache.clear()
            return value

    def popitem(self):
        try:
            item = super(CachingDict, self).popitem()
        except KeyError as e:
            raise e
        else:
            self._cache.clear()
            return item


class DictWithDotNotation(dict):
    """
    Dictionary addressable by dot notation
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise_from_none(AttributeError("'dict' object has no attribute '%s'" % name))


class abstractstaticmethod(staticmethod):  # noqa: N801  # pylint: disable=invalid-name
    """
    A decorator for abstract static methods

    Used in parent classes to identify static methods required in child plugins

    This decorator is included to support older versions of Python and
    should be considered deprecated as of Python 3.3.
    The preferred implementation is:

    .. code-block:: python

        @staticmethod
        @pluginlib.abstractmethod
        def abstract_staticmethod():
            return 'foo'
    """

    __isabstractmethod__ = True

    def __init__(self, func):
        super(abstractstaticmethod, self).__init__(abstractmethod(func))


class abstractclassmethod(classmethod):  # noqa: N801  # pylint: disable=invalid-name
    """
    A decorator for abstract class methods

    Used in parent classes to identify class methods required in child plugins

    This decorator is included to support older versions of Python and
    should be considered deprecated as of Python 3.3.
    The preferred implementation is:

    .. code-block:: python

        @classmethod
        @pluginlib.abstractmethod
        def abstract_classmethod(cls):
            return cls.foo
    """

    __isabstractmethod__ = True

    def __init__(self, func):
        super(abstractclassmethod, self).__init__(abstractmethod(func))


class abstractattribute(object):  # noqa: N801  # pylint: disable=invalid-name
    """
    A class to be used to identify abstract attributes

    .. code-block:: python

        @pluginlib.Parent
        class ParentClass(object):
            abstract_attribute = pluginlib.abstractattribute

    """
    __isabstractmethod__ = True
