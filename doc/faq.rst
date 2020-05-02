..
  Copyright 2018 - 2020 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/pluginlib

.. py:currentmodule:: pluginlib

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


Why does calling :py:func:`super` with no arguments in a parent class raise a :py:exc:`TypeError`?
--------------------------------------------------------------------------------------------------

This is a side-effect of :py:term:`metaclasses <metaclass>`. Take the following example:

.. code-block:: pycon
  :emphasize-lines: 10, 21

  >>> import pluginlib
  >>>
  >>> class Plugin():
  ...     def __init__(self):
  ...         pass
  ...
  >>> @pluginlib.Parent('collector')
  ... class Collector(Plugin):
  ...     def __init__(self):
  ...         super().__init__()
  ...
  >>> class Child(Collector):
  ...     def __init__(self):
  ...         super().__init__()
  ...
  >>> Child()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "<stdin>", line 3, in __init__
    File "<stdin>", line 4, in __init__
  TypeError: super(type, obj): obj must be an instance or subtype of type

We get this error when :py:func:`super` is called with no arguments in ``Collector`` because the
type of ``Collector`` is ``PluginType``, not ``Plugin``.

.. code-block:: pycon

  >>> type(Collector)
  <class 'pluginlib._parent.PluginType'>

:py:func:`super` will use this type for the first argument if one is not supplied.
To work around this, we simply have to supply arguments to :py:func:`super`.
As you can see, this is only required in parent classes.

.. code-block:: pycon
  :emphasize-lines: 10, 14

  >>> import pluginlib
  >>>
  >>> class Plugin():
  ...     def __init__(self):
  ...         pass
  ...
  >>> @pluginlib.Parent('collector')
  ... class Collector(Plugin):
  ...     def __init__(self):
  ...         super(Collector, self).__init__()
  ...
  >>> class Child(Collector):
  ...     def __init__(self):
  ...         super().__init__()
  ...
  >>> Child()
  <__main__.Child object at 0x7f5786e8d490>


Why am I getting ``TypeError: metaclass conflict``?
---------------------------------------------------

This happens when a parent class inherits from a class derived from a :py:term:`metaclass`.
This is **not** supported. Here is an example that illustrates the behavior.

.. code-block:: python

  import pluginlib

  class Meta(type):
      pass

  class ClassFromMeta(metaclass=Meta):
      pass

  @pluginlib.Parent('widget')
  class Widget(ClassFromMeta):
      pass

This will raise the following error.

.. code-block:: python

  TypeError: metaclass conflict: the metaclass of a derived class must be a (non-strict) subclass of the metaclasses of all its bases

An alternative is to make an instance of the class an attribute of the parent class.

.. code-block:: python

  @pluginlib.Parent('widget')
  class Widget():
      def __init__(self):
          self._widget = ClassFromMeta()

If desired, :py:meth:`~object.__getattr__` can be used to provide pass-through access.

.. code-block:: python

  @pluginlib.Parent('widget')
  class Widget():
      def __init__(self):
          self._widget = ClassFromMeta()

  def __getattr__(self, attr):
      return getattr(self._widget, attr)
