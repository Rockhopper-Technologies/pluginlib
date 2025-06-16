# Copyright 2014 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib Package**

A framework for creating and importing plugins
"""

__version__ = '0.10.0'

__all__ = ['abstractmethod', 'abstractattribute', 'BlacklistEntry', 'EntryPointWarning', 'Parent',
           'Plugin', 'PluginlibError', 'PluginImportError', 'PluginLoader', 'PluginWarning']

from abc import abstractmethod

from pluginlib._parent import Parent, Plugin
from pluginlib._loader import PluginLoader
from pluginlib._objects import BlacklistEntry
from pluginlib._util import (  # noqa: F401
    abstractstaticmethod, abstractclassmethod, abstractattribute, abstractproperty
)
from pluginlib.exceptions import PluginlibError, PluginImportError, PluginWarning, EntryPointWarning
