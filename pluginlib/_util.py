# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Utility Module**

This module contains generic functions for use in other modules
"""

from abc import abstractmethod
from collections import namedtuple
from functools import update_wrapper, wraps
from inspect import isclass
import logging
import operator as _operator
import sys

from pkg_resources import parse_version


# Setup logger
if sys.version_info[:2] < (2, 7):  # pragma: no branch

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


Result = namedtuple('Result', ('valid', 'message', 'errorcode'))
NoneType = type(None)

if sys.version_info[0] < 3:  # pragma: no branch
    BASESTRING = basestring  # pragma: no cover  # noqa: F821 # pylint: disable=undefined-variable
else:
    BASESTRING = str


# Attempt to make a Python 2/3 compatible way to raise with a traceback
# pylint: disable=exec-used
if sys.version_info[0] < 3:  # pragma: no branch
    exec("""def raise_with_traceback(exc, tback):  # pragma: no cover
    raise exc.__class__, exc, tback
""")
# pylint: enable=exec-used
else:
    def raise_with_traceback(exc, tback):
        """
        Python 3 compatible raise statement
        """
        raise exc.with_traceback(tback)


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


class BlacklistEntry(object):
    """
    Args:
        plugin_type(str): Parent type
        name(str): Plugin name
        version(str): Plugin version
        operator(str): Comparison operator ('=', '==', '!=', '<', '<=', '>', '>=')

    **Container for blacklist entry**

    If ``operator`` is :py:data:`None` or not specified, it defaults to '=='.

    One of ``plugin_type``, ``name``, or ``version`` must be specified.
    If any are unspecified or :py:data:`None`, they are treated as a wildcard.

    In order to be more compatible with parsed text,
    the order of ``operator`` and ``version`` can be swapped. The following are equivalent:

    .. code-block:: python

        BlacklistEntry('parser', 'json', '1.0', '>=')

    .. code-block:: python

            BlacklistEntry('parser', 'json', '>=', '1.0')

    ``version`` is evaluated using :py:func:`pkg_resources.parse_version`
    and should conform to `PEP 440`_

    .. _PEP 440: https://www.python.org/dev/peps/pep-0440/
    """

    __slots__ = ('type', 'name', 'version', 'operator')

    def __init__(self, plugin_type=None, name=None, version=None, operator=None):

        if plugin_type is name is version is None:
            raise AttributeError('plugin_type, name, or version must be specified')

        self.type = plugin_type
        self.name = name
        if version in OPERATORS:

            self.operator = version
            self.version = operator

            if self.version is None:
                raise AttributeError('version must be specifed when operator is specified')

        else:
            self.version = version
            self.operator = operator

        if self.version is not None and not isinstance(self.version, BASESTRING):
            raise TypeError('version must be a string, recieved %s' % type(self.version).__name__)

        if self.operator is None:
            self.operator = '=='
        elif self.operator not in OPERATORS:
            raise AttributeError("Unsupported operator '%s'" % self.operator)

    def __repr__(self):

        attrs = (self.type, self.name, self.operator, self.version)
        return '%s(%s)' % (self.__class__.__name__, ', '.join([repr(attr) for attr in attrs]))


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
            raise AttributeError("'dict' object has no attribute '%s'" % name)


class GroupDict(DictWithDotNotation):
    """
    Container for a plugin group
    """

    _skip_empty = False
    _bl_compare_attr = 'type'
    _bl_skip_attrs = ('name', 'version')
    _bl_empty = DictWithDotNotation

    def _newest(self, blacklist=None):
        """
        Args:
            blacklist(tuple): Iterable of of BlacklistEntry objects

        Returns nested dictionary of plugins with only the newest version of each plugin

        If a blacklist is supplied, plugins are evaluated against the blacklist entries
        """

        plugins = DictWithDotNotation()

        if blacklist:
            # Assume blacklist is correct format since it is checked by PluginLoader

            for key, val in self.items():

                plugin_blacklist = []
                skip = False

                for entry in blacklist:
                    if getattr(entry, self._bl_compare_attr) not in (key, None):
                        continue
                    if all(getattr(entry, attr) is None for attr in self._bl_skip_attrs):
                        if not self._skip_empty:
                            plugins[key] = self._bl_empty()
                        skip = True
                        break

                    plugin_blacklist.append(entry)

                if not skip:
                    result = val._newest(plugin_blacklist)  # pylint: disable=protected-access
                    if result or not self._skip_empty:
                        plugins[key] = result

        else:

            for key, val in self.items():
                result = val._newest()  # pylint: disable=protected-access
                if result or not self._skip_empty:
                    plugins[key] = result

        return plugins


class TypeDict(GroupDict):
    """
    Container for a plugin type
    """

    _skip_empty = True
    _bl_compare_attr = 'name'
    _bl_skip_attrs = ('version',)
    _bl_empty = None  # Not callable, but never called since _skip_empty is True

    def __init__(self, parent, *args, **kwargs):
        super(TypeDict, self).__init__(*args, **kwargs)
        self._parent = parent


class PluginDict(CachingDict):
    """
    Dictionary with properties for retrieving plugins
    """

    def _sorted_keys(self):
        """
        Return list of keys sorted by version

        Sorting is done based on :py:func:`pkg_resources.parse_version`
        """

        try:
            keys = self._cache['sorted_keys']
        except KeyError:
            keys = self._cache['sorted_keys'] = sorted(self.keys(), key=parse_version)

        return keys

    def _process_blacklist(self, blacklist):
        """
        Process blacklist into set of excluded versions
        """

        # Assume blacklist is correct format since it is checked by PluginLoader

        blacklist_cache = {}
        blacklist_cache_old = self._cache.get('blacklist', {})

        for entry in blacklist:

            blackkey = (entry.version, entry.operator)

            if blackkey in blacklist_cache:
                continue
            elif blackkey in blacklist_cache_old:
                blacklist_cache[blackkey] = blacklist_cache_old[blackkey]
            else:
                entry_cache = blacklist_cache[blackkey] = set()
                blackversion = parse_version(entry.version or '0')
                blackop = OPERATORS[entry.operator]

                for key in self:
                    if blackop(parse_version(key), blackversion):
                        entry_cache.add(key)

        self._cache['blacklist'] = blacklist_cache
        return set().union(*blacklist_cache.values())

    def _newest(self, blacklist=None):
        """
        Args:
            blacklist(tuple): Iterable of of BlacklistEntry objects

        Returns dictionary of plugins with only the newest version of each plugin

        If a blacklist is supplied, plugins are evaluated against the blacklist entries
        """

        rtn = None

        if self:  # Dict is not empty

            if blacklist:

                blacklist = self._process_blacklist(blacklist)

                for key in reversed(self._sorted_keys()):
                    if key not in blacklist:
                        rtn = self[key]
                        break

            else:
                rtn = self[self._sorted_keys()[-1]]

        return rtn


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
