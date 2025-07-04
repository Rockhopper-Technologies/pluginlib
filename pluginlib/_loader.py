# Copyright 2014 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Loader Submodule**

Provides functions and classes for loading plugins
"""


import contextlib
import importlib
from inspect import ismodule
import os
import pkgutil
import sys
import traceback
import warnings
from collections.abc import Iterable

from pluginlib.exceptions import PluginImportError, EntryPointWarning
from pluginlib._objects import BlacklistEntry
from pluginlib._parent import get_plugins
from pluginlib._util import LOGGER, NoneType, PY_LT_3_10


if PY_LT_3_10:  # pragma: no cover
    from importlib_metadata import entry_points, EntryPoint  # pylint: disable=import-error
else:
    from importlib.metadata import entry_points, EntryPoint


def _raise_friendly_exception(exc, name, path):
    """
    Attempt to create a friendly traceback that only shows the errors
    encountered from the plugin import and not the framework
    """

    etype = exc.__class__
    tback = getattr(exc, '__traceback__', sys.exc_info()[2])

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
            if os.path.splitext(entry[0])[0] == os.path.splitext(__file__)[0]:
                here = idx

    if start == 0 and isinstance(exc, SyntaxError):
        limit = 0
    else:
        limit = 0 - len(tb_list) + max(start, here)

    friendly = ''.join(traceback.format_exception(etype, exc, tback, limit))

    # Format exception
    msg = f'Error while importing candidate plugin module {name} from {path}'
    exception = PluginImportError(f'{msg}: {repr(exc)}', friendly=friendly)

    raise exception.with_traceback(tback) from None


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
        name = epoint.module

    if path is None:
        with contextlib.suppress(ImportError):
            spec = importlib.util.find_spec(name)
            if spec:
                path = (
                    os.path.dirname(spec.origin)
                    if getattr(spec, 'origin', None)
                    else next(iter(spec.submodule_search_locations))
                )
    LOGGER.debug('Attempting to load module %s from %s', name, path)
    try:
        mod = epoint.load() if epoint else importlib.import_module(name)

    except Exception as e:  # pylint: disable=broad-except
        _raise_friendly_exception(e, name, path)

    return mod


def _recursive_import(package):
    """
    Args:
        package(py:term:`package`): Package to walk

    Import all modules from a package recursively
    """

    path = getattr(package, '__path__', None)
    if path:
        # pylint: disable=unused-variable
        for finder, name, is_pkg in pkgutil.walk_packages(path, prefix=f'{package.__name__}.'):
            _import_module(name, finder.path)


def _recursive_path_import(path, prefix_package):
    """
    Args:
        path(str): Path to walk
        prefix_package(str): Prefix to apply to found modules

    Import all modules from a path recursively

    If a python package is found, it is imported recursively,
    however, the directory walk will stop on the directory of the package
    and Python files under the package that are in directories without
    init files, will be skipped.
    """

    # Include basename of path in module prefix
    basename = os.path.basename(path.strip('/'))
    root_prefix = f'{prefix_package}.{basename}.'

    # Walk path
    for root, dirs, files in os.walk(path):
        # If root is a Python module, we won't walk any farther down it
        # find_module() seems to be recursive in Python 3
        if '__init__.py' in files:
            dirs.clear()
            if root != path:
                continue

        # Generate prefix
        if root == path:
            prefix = root_prefix
        else:
            prefix = f'{root_prefix}{os.path.relpath(root, path).replace(os.sep, ".")}.'

        # Walk root and import modules
        # pylint: disable=unused-variable
        for finder, name, is_pkg in pkgutil.walk_packages([root], prefix=prefix):
            LOGGER.debug('Attempting to load module %s from %s', name, finder.path)
            try:
                spec = finder.find_spec(name)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)

            except Exception as e:  # pylint: disable=broad-except
                _raise_friendly_exception(e, name, root)


# pylint: disable=too-many-instance-attributes,too-many-arguments
class PluginLoader:
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

    # pylint: disable-next=too-many-positional-arguments
    def __init__(self, group=None, library=None, modules=None, paths=None, entry_point=None,
                 blacklist=None, prefix_package='pluginlib.importer', type_filter=None):

        # Make sure we got iterables
        for argname, arg in (('modules', modules), ('paths', paths), ('blacklist', blacklist),
                             ('type_filter', type_filter)):
            if not isinstance(arg, (NoneType, Iterable)) or isinstance(arg, str):
                raise TypeError(f"Expecting iterable for '{argname}', received {type(arg)}")

        # Make sure we got strings
        for argname, arg in (('library', library), ('entry_point', entry_point),
                             ('prefix_package', prefix_package)):
            if not isinstance(arg, (NoneType, str)):
                raise TypeError(f"Expecting string for '{argname}', received {type(arg)}")

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
                        # pylint: disable=raise-missing-from
                        raise AttributeError(
                            "Invalid blacklist entry f'{entry}': {e} "
                        ) from e
                else:
                    raise AttributeError(f"Invalid blacklist entry '{entry}': Not an iterable")

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
                args.append(f'{attr}={val!r}')

        return f'{self.__class__.__name__}({", ".join(args)})'

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
            for epoint in entry_points(group=self.entry_point):
                try:
                    mod = _import_module(epoint)
                except PluginImportError as e:
                    warnings.warn(
                        f'Module {epoint.module} can not be loaded for entry point {epoint.name}: '
                        f'{e}',
                        EntryPointWarning
                    )
                    continue

                # If we have a package, walk it
                if ismodule(mod):
                    _recursive_import(mod)
                else:
                    warnings.warn(f"Entry point '{epoint.name}' is not a module or package",
                                  EntryPointWarning)

        # Load auxiliary modules
        if self.modules:
            for mod in self.modules:
                LOGGER.info('Loading plugins from %s', mod)
                _recursive_import(_import_module(mod))

        # Load auxiliary paths
        if self.paths:
            # Import each path recursively
            for path in self.paths:
                modpath = os.path.realpath(path)
                if os.path.isdir(modpath):
                    LOGGER.info("Recursively importing plugins from path `%s`", path)
                    _recursive_path_import(path, self.prefix_package)
                else:
                    LOGGER.info("Configured plugin path '%s' is not a valid directory", path)

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

        Similar to :py:attr:`plugins`, but lowest level is an :py:class:`~collections.OrderedDict`
        of all unfiltered plugin versions for the given plugin type and name.

        Parent types are always included.
        Child plugins will only be included if at least one valid, non-blacklisted plugin
        is available.

        The newest plugin can be retrieved by accessing the last item in the dictionary.

        .. code-block:: python

            plugins = loader.plugins_all
            tuple(plugins.parser.json.values())[-1]
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
