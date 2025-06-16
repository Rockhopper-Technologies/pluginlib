# Copyright 2014 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Utility Module**

This module contains generic functions for use in other modules
"""

import abc
import logging
import operator as _operator
import sys
import warnings
from functools import update_wrapper, wraps
from inspect import isclass


PY_LT_3_10 = sys.version_info[:2] < (3, 10)

# Setup logger
LOGGER = logging.getLogger('pluginlib')
LOGGER.addHandler(logging.NullHandler())

OPERATORS = {'=': _operator.eq,
             '==': _operator.eq,
             '!=': _operator.ne,
             '<': _operator.lt,
             '<=': _operator.le,
             '>': _operator.gt,
             '>=': _operator.ge}

# types.NoneType isn't available until 3.10
NoneType = type(None)


class ClassProperty:
    """
    Property decorator for class methods
    """

    def __init__(self, method):

        self.method = method
        update_wrapper(self, method)

    def __get__(self, instance, cls):
        return self.method(cls)


class Undefined:
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
        super().__init__(*args, **kwargs)
        self._cache = {}

    def __setitem__(self, key, value):
        try:
            super().__setitem__(key, value)
        finally:
            self._cache.clear()

    def __delitem__(self, key):
        try:
            super().__delitem__(key)
        finally:
            self._cache.clear()

    def clear(self):
        try:
            super().clear()
        finally:
            self._cache.clear()

    def setdefault(self, key, default=None):

        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def pop(self, *args):
        try:
            value = super().pop(*args)
        except KeyError as e:
            raise e

        self._cache.clear()
        return value

    def popitem(self):
        try:
            item = super().popitem()
        except KeyError as e:
            raise e

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
            raise AttributeError(f"'dict' object has no attribute '{name}'") from None


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
        warnings.warn(
            "abstractstaticmethod is deprecated since Python 3.3 and will be removed in future versions. "
            "Use @staticmethod combined with @abstractmethod instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(abc.abstractmethod(func))


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
        warnings.warn(
            "abstractclassmethod is deprecated since Python 3.3 and will be removed in future versions. "
            "Use @classmethod combined with @abstractmethod instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(abc.abstractmethod(func))


class abstractattribute:  # noqa: N801  # pylint: disable=invalid-name
    """
    A class to be used to identify abstract attributes

    .. code-block:: python

        @pluginlib.Parent
        class ParentClass:
            abstract_attribute = pluginlib.abstractattribute

    """
    __isabstractmethod__ = True


def abstractproperty(*args, **kwargs):
    """
    Wrapper for abstractproperty to raise deprecation warning
    """

    warnings.warn(
        "abstractproperty is deprecated since Python 3.3 and will be removed in future versions. "
        "Use @property combined with @abstractmethod instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return abc.abstractproperty(*args, **kwargs)
