# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Parent Submodule**

Provides plugin bases class and Parent decorator
"""

import inspect
import sys
import warnings

from pluginlib.exceptions import PluginWarning
from pluginlib._objects import GroupDict, TypeDict, PluginDict
from pluginlib._util import (allow_bare_decorator, ClassProperty, DictWithDotNotation,
                             LOGGER, Result, Undefined)

DEFAULT = '_default'
UNDEFINED = Undefined()

isfunction = inspect.isfunction  # pylint: disable=invalid-name
getfullargspec = getattr(inspect,  # pylint: disable=invalid-name
                         'getfullargspec', getattr(inspect, 'getargspec'))

try:
    STR = unicode

except NameError:
    STR = str

PY26 = sys.version_info[:2] < (2, 7)

# pylint: disable=protected-access


def _check_methods(cls, subclass):  # pylint: disable=too-many-branches
    """
    Args:
        cls(:py:class:`Plugin`): Parent class
        subclass(:py:class:`Plugin`): Subclass to evaluate

    Returns:
        Result: Named tuple

    Validate abstract methods are defined in subclass
    For error codes see _inspect_class
    """

    for meth, methobj in cls.__abstractmethods__.items():

        # Need to get attribute from dictionary for instance tests to work
        for base in subclass.__mro__:  # pragma: no branch
            if meth in base.__dict__:
                submethobj = base.__dict__[meth]
                break

        # If we found our abstract method, we didn't find anything
        if submethobj is methobj:
            submethobj = UNDEFINED

        # Determine if we have the right method type
        result = None
        bad_arg_spec = 'Argument spec does not match parent for method %s'

        # pylint: disable=deprecated-method
        if isinstance(methobj, property):
            if submethobj is UNDEFINED or not isinstance(submethobj, property):
                result = Result(False, 'Does not contain required property (%s)' % meth, 210)

        elif isinstance(methobj, staticmethod):
            if submethobj is UNDEFINED or not isinstance(submethobj, staticmethod):
                result = Result(False, 'Does not contain required static method (%s)' % meth, 211)
            elif PY26:  # pragma: no cover
                if getfullargspec(methobj.__get__(True)) != \
                   getfullargspec(submethobj.__get__(True)):
                    result = Result(False, bad_arg_spec % meth, 220)
            elif getfullargspec(methobj.__func__) != getfullargspec(submethobj.__func__):
                result = Result(False, bad_arg_spec % meth, 220)

        elif isinstance(methobj, classmethod):
            if submethobj is UNDEFINED or not isinstance(submethobj, classmethod):
                result = Result(False, 'Does not contain required class method (%s)' % meth, 212)
            elif PY26:  # pragma: no cover
                if getfullargspec(methobj.__get__(True).__func__) != \
                   getfullargspec(submethobj.__get__(True).__func__):
                    result = Result(False, bad_arg_spec % meth, 220)
            elif getfullargspec(methobj.__func__) != getfullargspec(submethobj.__func__):
                result = Result(False, bad_arg_spec % meth, 220)

        elif isfunction(methobj):
            if submethobj is UNDEFINED or not isfunction(submethobj):
                result = Result(False, 'Does not contain required method (%s)' % meth, 213)
            elif getfullargspec(methobj) != getfullargspec(submethobj):
                result = Result(False, bad_arg_spec % meth, 220)

        # If it's not a type we're specifically checking, just check for existence
        elif submethobj is UNDEFINED:
            result = Result(False, 'Does not contain required attribute (%s)' % meth, 214)

        if result:
            return result

    return Result(True, None, 0)


def _inspect_class(cls, subclass):
    """
    Args:
        cls(:py:class:`Plugin`): Parent class
        subclass(:py:class:`Plugin`): Subclass to evaluate

    Returns:
        Result: Named tuple

    Inspect subclass for inclusion

    Values for errorcode:

        * 0: No error

        Error codes between 0 and 100 are not intended for import

        * 50 Skipload flag is True

        Error codes between 99 and 200 are excluded from import

        * 156: Skipload call returned True

        Error codes 200 and above are malformed classes

        * 210: Missing abstract property
        * 211: Missing abstract static method
        * 212: Missing abstract class method
        * 213: Missing abstract method
        * 214: Missing abstract attribute
        * 220: Argument spec does not match
    """

    if callable(subclass._skipload_):

        result = subclass._skipload_()

        if isinstance(result, tuple):
            skip, msg = result
        else:
            skip, msg = result, None

        if skip:
            return Result(False, msg, 156)

    elif subclass._skipload_:
        return Result(False, 'Skipload flag is True', 50)

    return _check_methods(cls, subclass)


class PluginType(type):
    """
    Metaclass for plugins
    """

    __plugins = DictWithDotNotation([(DEFAULT, GroupDict())])

    # pylint: disable=bad-mcs-classmethod-argument
    def __new__(cls, name, bases, namespace, **kwargs):

        # Make sure '_parent_', '_skipload_' are set explicitly or ignore
        for attr in ('_parent_', '_skipload_'):
            if attr not in namespace:
                namespace[attr] = False

        new = super(PluginType, cls).__new__(cls, name, bases, namespace, **kwargs)

        # Determine group
        group = cls.__plugins.setdefault(new._group_ if new._group_ else DEFAULT, GroupDict())

        if new._type_ in group:
            if new._parent_:
                raise ValueError('parent must be unique: %s' % new._type_)

            plugindict = group[new._type_].get(new.name, UNDEFINED)
            version = STR(new.version or 0)

            # Check for duplicates. Warn and ignore
            if plugindict and version in plugindict:

                existing = plugindict[version]
                warnings.warn("Duplicate plugins found for %s: %s.%s and %s.%s" %
                              (new, new.__module__, new.__name__,
                               existing.__module__, existing.__name__),
                              PluginWarning, stacklevel=2)

            else:
                result = _inspect_class(group[new._type_]._parent, new)

                if result.valid:
                    group[new._type_].setdefault(new.name, PluginDict())[version] = new

                else:
                    skipmsg = u'Skipping %s class %s.%s: Reason: %s'
                    args = (new, new.__module__, new.__name__, result.message)

                    if result.errorcode < 100:
                        LOGGER.debug(skipmsg, *args)
                    elif result.errorcode < 200:
                        LOGGER.info(skipmsg, *args)
                    else:
                        warnings.warn(skipmsg % args, PluginWarning, stacklevel=2)

        elif new._parent_:
            group[new._type_] = TypeDict(new)

            new.__abstractmethods__ = dict()

            # Get abstract methods by walking the MRO
            for base in reversed(new.__mro__):
                for meth, methobj in base.__dict__.items():
                    if getattr(methobj, '__isabstractmethod__', False):
                        new.__abstractmethods__[meth] = methobj

        else:
            raise ValueError('Unknown parent type: %s' % new._type_)

        return new

    def _get_plugins(cls):

        return cls.__plugins[cls._group_ if cls._group_ else DEFAULT][cls._type_]


class Plugin(object):
    """
    **Mixin class for plugins.
    All parents and child plugins will inherit from this class automatically.**

    **Class Attributes**

        *The following attributes can be set as class attributes in subclasses*

        .. autoattribute:: _alias_
        .. autoattribute:: _skipload_
        .. autoattribute:: _version_

    **Class Properties**

        .. autoattribute:: version
            :annotation:

            :py:class:`str` -- Returns :attr:`_version_` if set,
            otherwise falls back to module ``__version__`` or :py:data:`None`

        .. autoattribute:: name
            :annotation:

            :py:class:`str` -- :attr:`_alias_` if set or falls back to class name
    """

    __slots__ = ()

    _alias_ = None
    """:py:class:`str` -- Friendly name to refer to plugin.
       Accessed through :attr:`~Plugin.name` property."""
    _skipload_ = False
    """:py:class:`bool` -- When True, plugin is not loaded.
       Can also be a static or class method that returns a tuple ``(bool, message)``"""
    _version_ = None
    """:py:class:`str` -- Plugin version. Should adhere to `PEP 440`_.
       Accessed through :attr:`~Plugin.version` property.

       .. _PEP 440: https://www.python.org/dev/peps/pep-0440/"""

    @ClassProperty
    def version(cls):  # noqa: N805  # pylint: disable=no-self-argument
        """
        :py:class:Returns `str` -- Returns :attr:`_version_` if set,
        otherwise falls back to module `__version__` or None
        """
        return cls._version_ or getattr(sys.modules.get(cls.__module__, None),
                                        '__version__', None)

    @ClassProperty
    def name(cls):  # noqa: N805  # pylint: disable=no-self-argument
        """
        :py:class:`str` -- :attr:`_alias_` if set or falls back to class name
        """

        return cls._alias_ or cls.__name__  # pylint: disable=no-member


@allow_bare_decorator
class Parent(object):
    """
    Args:
        plugin_type(str): Plugin type
        group(str): Group to store plugins

    **Class Decorator for plugin parents**

    ``plugin_type`` determines under what attribute child plugins will be accessed in
    :py:attr:`PluginLoader.plugins`.
    When not specified, the class name is used.

    ``group`` specifies the parent and all child plugins are members of
    the specified plugin group. A :py:attr:`PluginLoader` instance only accesses the
    plugins group specified when it was initialized.
    When not specified, the default group is used.
    ``group`` should be specified if plugins for different projects could be accessed
    in an single program, such as in libraries and frameworks.
    """

    __slots__ = 'plugin_type', 'group'

    def __init__(self, plugin_type=None, group=None):
        self.plugin_type = plugin_type
        self.group = group

    def __call__(self, cls):

        # In case we're inheriting another parent, clean registry
        if isinstance(cls, PluginType):
            plugins = cls._get_plugins().get(cls.name, {})
            remove = []

            for pver, pcls in plugins.items():
                if cls is pcls:
                    remove.append(pver)

            if plugins and len(remove) == len(plugins):
                del cls._get_plugins()[cls.name]

            else:
                for key in remove:
                    del plugins[key]

        dict_ = cls.__dict__.copy()
        dict_.pop('__dict__', None)
        dict_.pop('__weakref__', None)

        # Clean out slot members
        for member in dict_.get('__slots__', ()):
            dict_.pop(member, None)

        # Set type
        dict_['_type_'] = self.plugin_type or cls.__name__
        dict_['_group_'] = self.group

        # Mark as parents
        for attr in ('_parent_', '_skipload_'):
            dict_[attr] = True

        # Reorder bases so any overrides are hit first in the MRO
        bases = [base for base in cls.__bases__ if base not in (object, Plugin)]
        bases.append(Plugin)
        bases = tuple(bases)

        return PluginType(cls.__name__, bases, dict_)


def get_plugins():
    """
    Convenience method for accessing all imported plugins
    """

    return PluginType._PluginType__plugins
