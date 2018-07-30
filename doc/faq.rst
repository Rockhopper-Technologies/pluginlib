..
  Copyright 2018 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. py:module:: pluginlib

Frequently Asked Questions
==========================

Is this magic?
--------------

No, it's :py:term:`metaclasses <metaclass>`.


How is method checking handled differently from :py:mod:`abc`?
----------------------------------------------------------------

Pluginlib checks methods when classes are declared, not when they are initialized.


How can I check if a class is a plugin?
---------------------------------------

It's usually best to check inheritance against a specific parent.

.. code-block:: python

    issubclass(ChildPlugin, ParentPlugin)

For a more general case, use the :py:class:`Plugin` class.

.. code-block:: python

    issubclass(ChildPlugin, pluginlib.Plugin)


Why does creating a parent by subclassing another parent raise a warning?
-------------------------------------------------------------------------

A warning is raised when subclassing a plugin parent if it does not meet the
conditions of being a child plugin. Generally, it's best to avoid this
situation completely by having both plugin parent classes inherit
from a common, non-plugin, class. If it's unavoidable, set the
:py:attr:`~pluginlib.Plugin._skipload_` class attribute to :py:data:`False` to
avoid evaluating the class as a child plugin.
