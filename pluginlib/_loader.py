# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Loader Submodule**

Provides functions and classes for loading plugins
"""

from collections import Iterable
import importlib
from inspect import ismodule
import os
import pkgutil
import sys
import traceback
import warnings

from pkg_resources import iter_entry_points, EntryPoint

from pluginlib.exceptions import PluginImportError, EntryPointWarning
from pluginlib._objects import BlacklistEntry
from pluginlib._parent import get_plugins
from pluginlib._util import BASESTRING, LOGGER, NoneType, raise_with_traceback


def format_exception(etype, value, tback, limit=None):
    """
    Python 2 compatible version of traceback.format_exception
    Accepts negative limits like the Python 3 version
    """

    rtn = ['Traceback (most recent call last):\n']

    if limit is None or limit >= 0:
        rtn.extend(traceback.format_tb(tback, limit))
    else:
        rtn.extend(traceback.format_list(traceback.extract_tb(tback)[limit:]))

    rtn.extend(traceback.format_exception_only(etype, value))

    return rtn


def _import_module(name, path=None):
    """
    Args:
        name(str):
            * Full name of object
            * name can also be an EntryPoint object, name and path will be determined dynamically
        path(str): Module directory

    Returns:
        object: module object or advertised object for EntryPoint

    Loads a module using importlib catching exceptions
    If path is given, the traceback will be formatted to give more friendly and direct information
    """

    # If name is an entry point, try to parse it
    epoint = None
    if isinstance(name, EntryPoint):
        epoint = name
        name = epoint.module_name

    if path is None:
        try:
            loader = pkgutil.get_loader(name)
        except ImportError:
            pass
        else:
            if loader:
                path = os.path.dirname(loader.get_filename(name))

    LOGGER.debug('Attempting to load module %s from %s', name, path)
    try:
        if epoint:
            mod = epoint.load()
        else:
            mod = importlib.import_module(name)

    except Exception as e:  # pylint: disable=broad-except

        etype = e.__class__
        tback = getattr(e, '__traceback__', sys.exc_info()[2])

        # Create traceback starting at module for friendly output
        start = 0
        here = 0
        tb_list = traceback.extract_tb(tback)

        if path:
            for idx, entry in enumerate(tb_list):
                # Find index for traceback starting with module we tried to load
                if os.path.dirname(entry[0]) == path:
                    start = idx
                    break
                # Find index for traceback starting with this file
                elif os.path.splitext(entry[0])[0] == os.path.splitext(__file__)[0]:
                    here = idx

        if start == 0 and isinstance(e, SyntaxError):
            limit = 0
        else:
            limit = 0 - len(tb_list) + max(start, here)

        # pylint: disable=wrong-spelling-in-comment
        # friendly = ''.join(traceback.format_exception(etype, e, tback, limit))
        friendly = ''.join(format_exception(etype, e, tback, limit))

        # Format exception
        msg = 'Error while importing candidate plugin module %s from %s' % (name, path)
        exception = PluginImportError('%s: %s' % (msg, repr(e)), friendly=friendly)

        raise_with_traceback(exception, tback)

    return mod


def _recursive_import(package):
    """
    Args:
        package(py:term:`package`): Package to walk

    Import all modules from a package recursively
    """

    prefix = '%s.' % (package.__name__)

    path = getattr(package, '__path__', None)

    if path:
        for submod in pkgutil.walk_packages(path, prefix=prefix):
            _import_module(submod[1], submod[0].path)


# pylint: disable=too-many-instance-attributes,too-many-arguments
class PluginLoader(object):
    """
    Args:
        group(str): Group to retrieve plugins from
        library(str): Standard library package
        modules(list): Iterable of modules to import recursively
        paths(list): Iterable of paths to import recursively
        entry_point(str): `Entry point`_ for additional plugins
        blacklist(list): Iterable of :py:class:`BlacklistEntry` objects or tuples
        prefix_package(str): Alternative prefix for imported packages
        type_filter(list): Iterable of parent plugin types to allow

    **Interface for importing and accessing plugins**

    Plugins are loaded from sources specified at initialization when
    :py:meth:`load_modules` is called or when the :py:attr:`plugins` property is first accessed.

    ``group`` specifies the group whose members will be returned by :py:attr:`plugins`
    This corresponds directly with the ``group`` attribute for :py:func:`Parent`.
    When not specified, the default group is used.
    ``group`` should be specified if plugins for different projects could be accessed
    in an single program, such as in libraries and frameworks.

    ``library`` indicates the package of a program's standard library.
    This should be a package which is always loaded.

    ``modules`` is an iterable of optional modules to load.
    If a package is given, it will be loaded recursively.

    ``paths`` is an iterable of optional paths to find modules to load.
    The paths are searched recursively and imported under the namespace specified by
    ``prefix_package``.

    ``entry_point`` specifies an `entry point <Entry point_>`_ group to identify
    additional modules and packages which should be loaded.

    ``blacklist`` is an iterable containing :py:class:`BlacklistEntry` objects or tuples
    with arguments for new :py:class:`BlacklistEntry` objects.

    ``prefix_package`` must be the name of an existing package under which to import the paths
    specified in ``paths``. Because the package paths will be traversed recursively, this should
    be an empty path.

    ``type_filter`` limits plugins types to only those specified. A specified type is not
    guaranteed to be available.

    .. _Entry point: https://packaging.python.org/specifications/entry-points/
    """

    def __init__(self, group=None, library=None, modules=None, paths=None, entry_point=None,
                 blacklist=None, prefix_package='pluginlib.importer', type_filter=None):

        # Make sure we got iterables
        for argname, arg in (('modules', modules), ('paths', paths), ('blacklist', blacklist),
                             ('type_filter', type_filter)):
            if not isinstance(arg, (NoneType, Iterable)) or isinstance(arg, BASESTRING):
                raise TypeError("Expecting iterable for '%s', recieved %s" % (argname, type(arg)))

        # Make sure we got strings
        for argname, arg in (('library', library), ('entry_point', entry_point),
                             ('prefix_package', prefix_package)):
            if not isinstance(arg, (NoneType, BASESTRING)):
                raise TypeError("Expecting string for '%s', recieved %s" % (argname, type(arg)))

        self.group = group or '_default'
        self.library = library
        self.modules = modules or tuple()
        self.paths = paths or tuple()
        self.entry_point = entry_point
        self.prefix_package = prefix_package
        self.type_filter = type_filter
        self.loaded = False

        if blacklist:
            self.blacklist = []
            for entry in blacklist:

                if isinstance(entry, BlacklistEntry):
                    pass
                elif isinstance(entry, Iterable):
                    try:
                        entry = BlacklistEntry(*entry)
                    except (AttributeError, TypeError) as e:
                        raise AttributeError("Invalid blacklist entry '%s': %s " % (entry, e))
                else:
                    raise AttributeError("Invalid blacklist entry '%s': Not an iterable" % entry)

                self.blacklist.append(entry)

            self.blacklist = tuple(self.blacklist)

        else:
            self.blacklist = None

    def __repr__(self):

        args = []
        for attr, default in (('group', '_default'), ('library', None), ('modules', None),
                              ('paths', None), ('entry_point', None), ('blacklist', None),
                              ('prefix_package', 'pluginlib.importer'), ('type_filter', None)):

            val = getattr(self, attr)
            if default and val == default:
                continue

            if val:
                args.append('%s=%r' % (attr, val))

        return '%s(%s)' % (self.__class__.__name__, ', '.join(args))

    def load_modules(self):
        """
        Locate and import modules from locations specified during initialization.

        Locations include:
            - Program's standard library (``library``)
            - `Entry points <Entry point_>`_ (``entry_point``)
            - Specified modules (``modules``)
            - Specified paths (``paths``)

        If a malformed child plugin class is imported, a :py:exc:`PluginWarning` will be issued,
        the class is skipped, and loading operations continue.

        If an invalid `entry point <Entry point_>`_ is specified, an :py:exc:`EntryPointWarning`
        is issued and loading operations continue.
        """

        # Start with standard library
        if self.library:
            LOGGER.info('Loading plugins from standard library')
            libmod = _import_module(self.library)
            _recursive_import(libmod)

        # Get entry points
        if self.entry_point:
            LOGGER.info('Loading plugins from entry points group %s', self.entry_point)
            for epoint in iter_entry_points(group=self.entry_point):
                try:
                    mod = _import_module(epoint)
                except PluginImportError as e:
                    warnings.warn("Module %s can not be loaded for entry point %s: %s" %
                                  (epoint.module_name, epoint.name, e), EntryPointWarning)
                    continue

                # If we have a package, walk it
                if ismodule(mod):
                    _recursive_import(mod)
                else:
                    warnings.warn("Entry point '%s' is not a module or package" % epoint.name,
                                  EntryPointWarning)

        # Load auxiliary modules
        if self.modules:
            for mod in self.modules:
                LOGGER.info('Loading plugins from %s', mod)
                _recursive_import(_import_module(mod))

        # Load auxiliary paths
        if self.paths:
            auth_paths_mod = importlib.import_module(self.prefix_package)
            initial_path = auth_paths_mod.__path__[:]

            # Append each path to module path
            for path in self.paths:

                modpath = os.path.realpath(path)
                if os.path.isdir(modpath):
                    LOGGER.info('Adding %s as a plugin search path', path)
                    if modpath not in auth_paths_mod.__path__:
                        auth_paths_mod.__path__.append(modpath)

                else:
                    LOGGER.info("Configured plugin path '%s' is not a valid directory", path)

            # Walk packages
            try:
                _recursive_import(auth_paths_mod)

            finally:
                # Restore Path
                auth_paths_mod.__path__[:] = initial_path

        self.loaded = True

    @property
    def plugins(self):
        """
        Newest version of all plugins in the group filtered by ``blacklist``

        Returns:
            dict: Nested dictionary of plugins accessible through dot-notation.

        Plugins are returned in a nested dictionary, but can also be accessed through dot-notion.
        Just as when accessing an undefined dictionary key with index-notation,
        a :py:exc:`KeyError` will be raised if the plugin type or plugin does not exist.

        Parent types are always included.
        Child plugins will only be included if a valid, non-blacklisted plugin is available.
        """

        if not self.loaded:
            self.load_modules()

        # pylint: disable=protected-access
        return get_plugins()[self.group]._filter(blacklist=self.blacklist, newest_only=True,
                                                 type_filter=self.type_filter)

    @property
    def plugins_all(self):
        """
        All resulting versions of all plugins in the group filtered by ``blacklist``

        Returns:
            dict: Nested dictionary of plugins accessible through dot-notation.

        Similar to :py:attr:`plugins`, but lowest level is a regular dictionary of
        all unfiltered plugin versions for the given plugin type and name.

        Parent types are always included.
        Child plugins will only be included if at least one valid, non-blacklisted plugin
        is available.
        """

        if not self.loaded:
            self.load_modules()

        # pylint: disable=protected-access
        return get_plugins()[self.group]._filter(blacklist=self.blacklist,
                                                 type_filter=self.type_filter)

    def get_plugin(self, plugin_type, name, version=None):
        """
        Args:
            plugin_type(str): Parent type
            name(str): Plugin name
            version(str): Plugin version

        Returns:
            :py:class:`Plugin`: Plugin, or :py:data:`None` if plugin can't be found

        Retrieve a specific plugin. ``blacklist`` and ``type_filter`` still apply.

        If ``version`` is not specified, the newest available version is returned.
        """

        if not self.loaded:
            self.load_modules()

        # pylint: disable=protected-access
        return get_plugins()[self.group]._filter(blacklist=self.blacklist,
                                                 newest_only=True,
                                                 type_filter=self.type_filter,
                                                 type=plugin_type,
                                                 name=name,
                                                 version=version)
