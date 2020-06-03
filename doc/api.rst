..
  Copyright 2018 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. _API-Reference:

API Reference
=============

Classes
-------

.. py:module:: pluginlib

.. autoclass:: Plugin
    :members:
    :exclude-members: plugin_group, plugin_type

.. autoclass:: PluginLoader
    :members:

.. autoclass:: BlacklistEntry
    :members:

.. autoclass:: abstractattribute

Decorators
----------

.. autodecorator:: Parent

.. py:decorator:: abstractmethod

    Provides :py:func:`@abc.abstractmethod  <abc.abstractmethod>` decorator

    Used in parent classes to identify methods required in child plugins

.. py:decorator:: abstractproperty

    Provides :py:func:`@abc.abstractproperty  <abc.abstractproperty>` decorator

    Used in parent classes to identify properties required in child plugins

    This decorator has been deprecated since Python 3.3. The preferred implementation is:

    .. code-block:: python

        @property
        @pluginlib.abstractmethod
        def abstract_property(self):
            return self.foo

.. autodecorator:: abstractstaticmethod

.. autodecorator:: abstractclassmethod

Exceptions
----------

.. autoclass:: PluginlibError
    :members:

.. autoclass:: PluginImportError
    :members:

.. autoclass:: PluginWarning
    :members:

.. autoclass:: EntryPointWarning
    :members:
