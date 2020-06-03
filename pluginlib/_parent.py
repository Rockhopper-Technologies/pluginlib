# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

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
                             LOGGER, PY26, Undefined)

try:
    from asyncio import iscoroutinefunction
except ImportError:  # pragma: no cover
    iscoroutinefunction = lambda func: False  # noqa: E731


DEFAULT = '_default'
UNDEFINED = Undefined()

isfunction = inspect.isfunction  # pylint: disable=invalid-name
getfullargspec = getattr(inspect,  # pylint: disable=invalid-name
                         'getfullargspec', getattr(inspect, 'getargspec'))

try:
    STR = unicode

except NameError:
    STR = str


class ClassInspector(object):
    """
    Args:
        cls(:py:class:`Plugin`): Parent class
        subclass(:py:class:`Plugin`): Subclass to evaluate

    Inspects subclass for inclusion
    After initialization, the following attributes are set:

    errorcode
        A code corresponding to the error condition

    message
        Error message

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
        * 215: Missing abstract coroutine
        * 216: Type annotations differ
        * 220: Argument spec does not match
    """

    def __init__(self, cls, subclass):

        self.message = None
        self.errorcode = 0
        self.cls = cls
        self.subclass = subclass

        self._check_skipload()
        if not self.errorcode:
            self._check_methods()

    def __bool__(self):
        return self.errorcode == 0

    # Python 2 equivalent
    __nonzero__ = __bool__

    def _check_skipload(self):
        """
        Determine if subclass should be skipped
        _skipload_ is either a Boolean or callable that returns a Boolean
        """

        # pylint: disable=protected-access
        if callable(self.subclass._skipload_):

            result = self.subclass._skipload_()

            if isinstance(result, tuple):
                skip, self.message = result
            else:
                skip = result

            if skip:
                self.errorcode = 156

        elif self.subclass._skipload_:
            self.errorcode = 50
            self.message = 'Skipload flag is True'

    def _check_methods(self):
        """
        Validate abstract methods are defined in subclass
        """

        for name, method in self.cls.__abstractmethods__.items():

            if self.errorcode:
                break

            # Need to get attribute from dictionary for instance tests to work
            for base in self.subclass.__mro__:  # pragma: no branch
                if name in base.__dict__:
                    submethod = base.__dict__[name]
                    break

            # If we found our abstract method, we didn't find anything
            if submethod is method:
                submethod = UNDEFINED

            if isinstance(method, property):
                self._check_property(name, submethod)
            elif isinstance(method, staticmethod):
                self._check_static_method(name, method, submethod)
            elif isinstance(method, classmethod):
                self._check_class_method(name, method, submethod)
            elif isfunction(method):
                self._check_generic_method(name, method, submethod)

            # If it's not a type we're specifically checking, just check for existence
            elif submethod is UNDEFINED:
                self.errorcode = 214
                self.message = 'Does not contain required attribute (%s)' % name

            if not self.errorcode:
                self._check_coroutine_method(name, method, submethod)

            if not self.errorcode:
                self._check_annotations(name, method, submethod)

    def _check_property(self, name, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        Check for class properties
        """

        if submethod is UNDEFINED or not isinstance(submethod, property):
            self.errorcode = 210
            self.message = 'Does not contain required property (%s)' % name

    def _check_static_method(self, name, method, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        Check for static methods
        """

        if submethod is UNDEFINED or not isinstance(submethod, staticmethod):
            self.errorcode = 211
            self.message = 'Does not contain required static method (%s)' % name
        elif PY26:  # pragma: no cover
            self._compare_argspec(name, getfullargspec(method.__get__(True)),
                                  getfullargspec(submethod.__get__(True)))
        else:
            self._compare_argspec(name, getfullargspec(method.__func__),
                                  getfullargspec(submethod.__func__))

    def _check_class_method(self, name, method, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        Check for class methods
        """

        if submethod is UNDEFINED or not isinstance(submethod, classmethod):
            self.errorcode = 212
            self.message = 'Does not contain required class method (%s)' % name
        elif PY26:  # pragma: no cover
            self._compare_argspec(name, getfullargspec(method.__get__(True).__func__),
                                  getfullargspec(submethod.__get__(True).__func__))
        else:
            self._compare_argspec(name, getfullargspec(method.__func__),
                                  getfullargspec(submethod.__func__))

    def _check_generic_method(self, name, method, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        Check for generic methods
        """

        if submethod is UNDEFINED or not isfunction(submethod):
            self.errorcode = 213
            self.message = 'Does not contain required method (%s)' % name
        else:
            self._compare_argspec(name, getfullargspec(method), getfullargspec(submethod))

    def _check_coroutine_method(self, name, method, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        If abstract is a coroutine method, child should be too
        """

        if iscoroutinefunction(method) and not iscoroutinefunction(submethod):
            self.errorcode = 215
            self.message = 'Does not contain required coroutine method (%s)' % name

    def _check_annotations(self, name, method, submethod):
        """
        Args:
            name(str): Method name
            method(:py:class:`function`): Abstract method object
            submethod(:py:class:`function`): Subclass method object

        If abstract has type annotations and the child has type annotations, they should match
        """

        meth_annotations = getattr(method, '__annotations__', {})
        if meth_annotations:
            submeth_annotations = getattr(submethod, '__annotations__', {})
            if submeth_annotations and meth_annotations != submeth_annotations:
                self.errorcode = 216
                self.message = 'Type annotations differ for (%s)' % name

    def _compare_argspec(self, name, spec_1, spec_2):
        """
        Args:
            name(str): Method name
            spec_1(:py:class:`inspect.FullArgSpec`): Argument spec
            spec_2(:py:class:`inspect.FullArgSpec`): Argument spec

        Compares two argspecs skipping type annotations
        """

        spec_1_dict = spec_1._asdict()
        spec_2_dict = spec_2._asdict()

        matches = True

        for key, val in spec_1_dict.items():
            # Annotations are checked separately
            if key == 'annotations':
                continue
            if spec_2_dict[key] != val:
                matches = False
                break

        if not matches:
            self.errorcode = 220
            self.message = 'Argument spec does not match parent for method %s' % name


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
                result = ClassInspector(group[new._type_]._parent, new)

                if result:
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
                for method_name, method in base.__dict__.items():
                    if getattr(method, '__isabstractmethod__', False):
                        new.__abstractmethods__[method_name] = method

        else:
            raise ValueError('Unknown parent type: %s' % new._type_)

        return new

    def _get_plugins(cls):
        """
        Return registered plugins
        """

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

        .. autoattribute:: name
            :annotation:

            :py:class:`str` -- :attr:`_alias_` if set or falls back to class name

        .. autoattribute:: plugin_group

        .. autoattribute:: plugin_type

        .. autoattribute:: version
            :annotation:

            :py:class:`str` -- Returns :attr:`_version_` if set,
            otherwise falls back to module ``__version__`` or :py:data:`None`

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

    @ClassProperty
    def plugin_type(cls):  # noqa: N805  # pylint: disable=no-self-argument
        """
        :py:class:`str` -- ``plugin_type`` of :py:class:`~pluginlib.Parent` class
        """

        return cls._type_  # pylint: disable=no-member

    @ClassProperty
    def plugin_group(cls):  # noqa: N805  # pylint: disable=no-self-argument
        """
        :py:class:`str` -- ``group`` of :py:class:`~pluginlib.Parent` class
        """

        return cls._group_  # pylint: disable=no-member


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

    # pylint: disable=protected-access
    return PluginType._PluginType__plugins
