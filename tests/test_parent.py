# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib._parent**
"""

import sys
import textwrap
import warnings

from pluginlib import (abstractmethod, abstractproperty, abstractstaticmethod,
                       abstractclassmethod, abstractattribute)
import pluginlib._parent as parent

from tests import OUTPUT, TestCase, unittest


NO_ASYNC = sys.version_info[:2] < (3, 5)
PY2 = sys.version_info[0] < 3


# pylint: disable=protected-access, no-member


# This should be imported from types, but it's broken in pypy
# https://bitbucket.org/pypy/pypy/issues/2865
class Placeholder(object):
    """Placeholder to get type"""
    __slots__ = ('member',)


MemberDescriptorType = type(Placeholder.__dict__['member'])  # pylint: disable=invalid-name


class TestParent(TestCase):
    """Test Parent decorator"""

    def tearDown(self):

        # Clear plugins from module
        parent.get_plugins().clear()

    def test_parent_basic(self):
        """Basic use of Parent decorator"""

        @parent.Parent('basic')
        class Basic(object):
            """Basic document string"""

        self.assertTrue(issubclass(Basic, parent.Plugin))
        self.assertTrue(isinstance(Basic, parent.PluginType))
        self.assertTrue(Basic._parent_)
        self.assertTrue(Basic._skipload_)
        self.assertEqual(Basic.__doc__, 'Basic document string')
        self.assertEqual(Basic._type_, 'basic')
        self.assertTrue('basic' in parent.get_plugins()['_default'])

    def test_parent_no_type(self):
        """Parent type defaults to parent class name"""

        @parent.Parent()
        class Basic(object):
            """Basic document string"""

        self.assertEqual(Basic._type_, 'Basic')
        self.assertTrue('Basic' in parent.get_plugins()['_default'])

    def test_parent_bare(self):
        """Parent type defaults to parent class name"""

        @parent.Parent
        class Basic(object):
            """Basic document string"""

        self.assertEqual(Basic._type_, 'Basic')
        self.assertTrue('Basic' in parent.get_plugins()['_default'])

    def test_multiple_inheritance(self):
        """Base class is inherited from another class"""

        class Sample(object):
            """Sample Class"""

        @parent.Parent('multiple_inheritence')
        class MultiInheritance(Sample):
            """TestMultiInheritance"""

        self.assertTrue(issubclass(MultiInheritance, parent.Plugin))
        self.assertTrue(isinstance(MultiInheritance, parent.PluginType))
        self.assertTrue(issubclass(MultiInheritance, Sample))
        self.assertTrue(MultiInheritance._parent_)
        self.assertTrue(MultiInheritance._skipload_)

    def child_is_parent(self, peers=False):
        """
        A parent class is used as base class for new parent
        If peers is True, another class is created with the same alias
        """

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent"""

            def hello(self):  # pylint: disable=no-self-use
                """Hello, world!"""
                return 'world'

        if peers:

            class Child(Parent):
                """Child"""

                _alias_ = 'foo'
                _version_ = '1.0'

        @parent.Parent('child_is_parent')
        class ParentChild(Parent):
            """TestParentChild"""

            _alias_ = 'foo'

        self.assertTrue(issubclass(ParentChild, parent.Plugin))
        self.assertTrue(isinstance(ParentChild, parent.PluginType))
        self.assertTrue(issubclass(ParentChild, Parent))
        self.assertTrue(ParentChild._parent_)
        self.assertTrue(ParentChild._skipload_)
        self.assertTrue(hasattr(ParentChild, 'hello'))

        if peers:
            self.assertTrue(len(Parent._get_plugins()['foo']) == 1)
            self.assertTrue(Parent._get_plugins()['foo']['1.0'] is Child)

        else:
            self.assertFalse('foo' in Parent._get_plugins())

        class GrandChild(ParentChild):
            """GrandChild"""

        self.assertTrue(issubclass(GrandChild, Parent))
        self.assertTrue(issubclass(GrandChild, ParentChild))
        self.assertTrue(hasattr(GrandChild, 'hello'))

    def test_child_is_parent(self):
        """A parent class is used as base class for new parent"""
        self.child_is_parent(False)

    def test_child_is_parent_peers(self):
        """A parent class is used as base class for new parent, has peers"""
        self.child_is_parent(True)

    def test_slots(self):
        """slots in a parent work as expected"""

        @parent.Parent
        class WithSlots(object):
            """This class has slots"""
            __slots__ = ('ivar',)

            def __init__(self, ivar):
                self.ivar = ivar

        inst = WithSlots(1)

        self.assertTrue('ivar' in WithSlots.__dict__)
        # Usually slots are member descriptors, but in pypy they are getset descriptors
        self.assertIsInstance(WithSlots.__dict__['ivar'], MemberDescriptorType,)
        self.assertTrue(hasattr(inst, '__slots__'))
        self.assertFalse(hasattr(inst, '__dict__'))
        self.assertEqual(inst.ivar, 1)


class TestPlugin(TestCase):
    """Test Plugin mixin"""

    def setUp(self):

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent"""

            def hello(self):  # pylint: disable=no-self-use
                """Hello, world!"""
                return 'world'

        self.parent = Parent
        self.plugins = self.parent._get_plugins()

    def tearDown(self):

        # Clear plugins from module
        parent.get_plugins().clear()

    def test_plugin_type(self):
        """plugin_type property is passed from parent"""
        self.assertEqual(self.parent.plugin_type, 'test_parent')

        class Child(self.parent):
            """Child has same plugin_type"""

        self.assertEqual(Child.plugin_type, 'test_parent')

    def test_plugin_group_none(self):
        """plugin_group property is passed from parent"""
        self.assertEqual(self.parent.plugin_group, None)

        class Child(self.parent):
            """Child has same plugin_group"""

        self.assertEqual(Child.plugin_group, None)

    def test_plugin_group(self):
        """plugin_group property is passed from parent"""

        @parent.Parent('test_parent', group='A-Team')
        class Parent(object):
            """Parent"""

        self.assertEqual(Parent.plugin_group, 'A-Team')

        class Child(Parent):
            """Child has same plugin_group"""

        self.assertEqual(Child.plugin_group, 'A-Team')

    def test_alias_none(self):
        """name attribute is class name"""

        class Child(self.parent):
            """No alias"""

        self.assertTrue(issubclass(Child, self.parent))
        self.assertEqual(Child.name, 'Child')
        self.assertIs(self.plugins['Child']['0'], Child)

    def test_alias(self):
        """name attribute is _alias_"""

        class Child(self.parent):
            """With alias"""
            _alias_ = 'voldemort'

        self.assertTrue(issubclass(Child, self.parent))
        self.assertEqual(Child.name, 'voldemort')
        self.assertIs(self.plugins['voldemort']['0'], Child)
        self.assertFalse('Child' in self.plugins)

    def test_version_none(self):
        """version attribute is _version_, module __version__ or None"""

        class Child(self.parent):
            """No version"""
            _alias_ = 'the_boy_who_lived'

        self.assertEqual(Child.version, None)
        self.assertIs(self.plugins['the_boy_who_lived']['0'], Child)

    def test_version_class(self):
        """version attribute is _version_"""

        class Child(self.parent):
            """With version"""
            _version_ = '1.0.1'
            _alias_ = 'the_boy_who_lived'

        self.assertEqual(Child.version, '1.0.1')
        self.assertIs(self.plugins['the_boy_who_lived']['1.0.1'], Child)

    def test_version_module(self):
        """version attribute is _version_, module __version__ or None"""

        sys.modules[__name__].__version__ = '2.0.0'

        class Child(self.parent):
            """Module version"""
            _alias_ = 'the_boy_who_lived'

        self.assertEqual(Child.version, '2.0.0')
        self.assertIs(self.plugins['the_boy_who_lived']['2.0.0'], Child)

        delattr(sys.modules[__name__], '__version__')

    def test_skipload(self):
        """Child not loaded when _skipload_ is True"""

        class Child(self.parent):  # pylint: disable=unused-variable
            """_skipload_ is True"""
            _skipload_ = True

        self.assertFalse('Child' in self.plugins)


# pylint: disable=too-many-public-methods
class TestPluginType(TestCase):
    """Test PluginType metaclass"""

    def setUp(self):

        # Truncate log output
        OUTPUT.seek(0)
        OUTPUT.truncate(0)

    def tearDown(self):

        # Clear plugins from module
        parent.get_plugins().clear()

    def test_skipload_static(self):
        """Use _skipload_ static method to determine if plugin should be used"""

        skip = False

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with callable _skipload_"""

        plugins = Parent._get_plugins()

        class Child1(Parent):
            """Child succeeds"""

            @staticmethod
            def _skipload_():
                """Don't skip"""
                return skip

        self.assertIs(plugins['Child1']['0'], Child1)
        self.assertEqual(OUTPUT.getvalue(), '')

        skip = True, 'This parrot is no more!'

        class Child2(Parent):  # pylint: disable=unused-variable
            """Child fails"""

            @staticmethod
            def _skipload_():
                """Skip"""
                return skip

        self.assertFalse('Child2' in plugins)
        self.assertRegex(OUTPUT.getvalue(), 'This parrot is no more!')

    def test_skipload_class(self):
        """Use _skipload_ class method to determine if plugin should be used"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with callable _skipload_"""

        plugins = Parent._get_plugins()

        class Child1(Parent):
            """Child succeeds"""

            skip = False

            @classmethod
            def _skipload_(cls):
                """Don't skip"""
                return cls.skip

        self.assertIs(plugins['Child1']['0'], Child1)
        self.assertEqual(OUTPUT.getvalue(), '')

        class Child2(Parent):  # pylint: disable=unused-variable
            """Child fails"""

            skip = True, 'He has ceased to be!'

            @classmethod
            def _skipload_(cls):
                """Don't skip"""
                return cls.skip

        self.assertFalse('Child2' in plugins)
        self.assertRegex(OUTPUT.getvalue(), 'He has ceased to be!')

    def test_abstract_method(self):
        """Method required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract class method"""

            @abstractmethod
            def abstract(self):
                """Abstract method"""

        self.missing(Parent, 'Does not contain required method')
        self.meth(Parent)
        self.static(Parent, 'Does not contain required method')
        self.klass(Parent, 'Does not contain required method')
        self.prop(Parent, 'Does not contain required method')
        self.attr(Parent, 'Does not contain required method')
        self.coroutine(Parent)
        self.type_hints_1(Parent)
        self.type_hints_2(Parent)

    def test_multiple_methods(self):
        """Method required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract class method"""

            @abstractmethod
            def abstract2(self):
                """Abstract method"""

            @abstractmethod
            def abstract(self):
                """Abstract method"""

        self.meth(Parent, 'Does not contain required method')
        self.multiple(Parent)

    def test_abs_method_argspec(self):
        """Method argument spec must match"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract class method"""

            @abstractmethod
            def abstract(self, some_arg):
                """Abstract method with another argument"""

        self.meth(Parent, 'Argument spec does not match parent for method')

    def test_abstract_staticmethod(self):
        """Static method required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract static method"""

            @abstractstaticmethod
            def abstract():
                """Abstract static method"""

        self.missing(Parent, 'Does not contain required static method')
        self.meth(Parent, 'Does not contain required static method')
        self.static(Parent)
        self.klass(Parent, 'Does not contain required static method')
        self.prop(Parent, 'Does not contain required static method')
        self.attr(Parent, 'Does not contain required static method')

    def test_abs_static_meth_argspec(self):
        """Static method argument spec must match"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract static method"""

            @abstractstaticmethod
            def abstract(some_arg):
                """Abstract static method with another argument"""

        self.static(Parent, 'Argument spec does not match parent for method')

    def test_abstract_classmethod(self):
        """Class method required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract class method"""

            @abstractclassmethod
            def abstract(cls):  # noqa: N805
                """Abstract class method"""

        self.missing(Parent, 'Does not contain required class method')
        self.meth(Parent, 'Does not contain required class method')
        self.static(Parent, 'Does not contain required class method')
        self.klass(Parent)
        self.prop(Parent, 'Does not contain required class method')
        self.attr(Parent, 'Does not contain required class method')

    def test_abs_class_meth_argspec(self):
        """Class method argument spec must match"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract class method"""

            @abstractclassmethod
            def abstract(cls, some_arg):  # noqa: N805
                """Abstract class method with another argument"""

        self.klass(Parent, 'Argument spec does not match parent for method')

    def test_abstract_property(self):
        """Property required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract property"""

            @abstractproperty
            def abstract(self):
                """Abstract property"""

        self.missing(Parent, 'Does not contain required property')
        self.meth(Parent, 'Does not contain required property')
        self.static(Parent, 'Does not contain required property')
        self.klass(Parent, 'Does not contain required property')
        self.prop(Parent)
        self.attr(Parent, 'Does not contain required property')

    def test_abstract_attribute(self):
        """Attribute required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract attribute"""

            abstract = abstractattribute

        self.missing(Parent, 'Does not contain required attribute')
        self.meth(Parent)
        self.static(Parent)
        self.klass(Parent)
        self.prop(Parent)
        self.attr(Parent)

    @unittest.skipIf(NO_ASYNC, 'Requires Python 3.5+')
    def test_abstract_coroutine(self):
        """Attribute required in subclass"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with abstract coroutine"""

            class_definition = textwrap.dedent('''\
            @abstractmethod
            async def abstract(self):
                """Abstract coroutine method"""
            ''')

            local_rtn = {}
            exec(class_definition, globals(), local_rtn)  # pylint: disable=exec-used
            abstract = local_rtn['abstract']

        self.missing(Parent, 'Does not contain required method')
        self.meth(Parent, 'Does not contain required coroutine method')
        self.static(Parent, 'Does not contain required method')
        self.klass(Parent, 'Does not contain required method')
        self.prop(Parent, 'Does not contain required method')
        self.attr(Parent, 'Does not contain required method')
        self.coroutine(Parent)

    @unittest.skipIf(PY2, 'Requires Python 3+')
    def test_type_annotations(self):
        """If parent and child have annotations they must match"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent with typed method"""

            class_definition = textwrap.dedent('''\
            @abstractmethod
            def abstract(self) -> str:
                """Method with type annotations"""
            ''')

            local_rtn = {}
            exec(class_definition, globals(), local_rtn)  # pylint: disable=exec-used
            abstract = local_rtn['abstract']

        self.meth(Parent)
        self.type_hints_1(Parent)
        self.type_hints_2(Parent, 'Type annotations differ')

    def check_method(self, parent_class, error, child, e):
        """Check child methods"""

        self.assertEqual(OUTPUT.getvalue(), '')

        plugins = parent_class._get_plugins()

        if error:
            self.assertFalse(child.name in plugins)
            self.assertEqual(len(e), 1)
            self.assertRegex(str(e[-1].message), error)
        else:
            self.assertIs(plugins[child.name]['0'], child)
            self.assertEqual(len(e), 0)

    def missing(self, parent_class, error=None):
        """Test abstract method is missing"""

        with warnings.catch_warnings(record=True) as e:

            class Missing(parent_class):
                """Does not have abstract method"""

        self.check_method(parent_class, error, Missing, e)

    def meth(self, parent_class, error=None):
        """Test abstract method is a regular method"""

        with warnings.catch_warnings(record=True) as e:

            class Meth(parent_class):
                """Only has regular method"""

                def abstract(self):
                    """Regular method"""

        self.check_method(parent_class, error, Meth, e)

    def multiple(self, parent_class, error=None):
        """Test abstract method is a regular method"""

        with warnings.catch_warnings(record=True) as e:

            class Meth(parent_class):
                """Only has regular method"""

                def abstract(self):
                    """Regular method"""

                def abstract2(self):
                    """Regular method"""

        self.check_method(parent_class, error, Meth, e)

    def static(self, parent_class, error=None):
        """Test abstract method is a static method"""

        with warnings.catch_warnings(record=True) as e:

            class Static(parent_class):
                """Only has static method"""

                @staticmethod
                def abstract():
                    """Static method"""

        self.check_method(parent_class, error, Static, e)

    def klass(self, parent_class, error=None):
        """Test abstract method is a class method"""

        with warnings.catch_warnings(record=True) as e:

            class Klass(parent_class):
                """Only has class method"""

                @classmethod
                def abstract(cls):
                    """Class method"""

        self.check_method(parent_class, error, Klass, e)

    def prop(self, parent_class, error=None):
        """Test abstract method is a property"""

        with warnings.catch_warnings(record=True) as e:

            class Prop(parent_class):
                """Only has property"""

                @property
                def abstract(self):
                    """Property"""

                @abstract.setter
                def abstract(self, value):
                    pass

                @abstract.deleter
                def abstract(self):
                    pass

        self.check_method(parent_class, error, Prop, e)

    def attr(self, parent_class, error=None):
        """Test abstract attribute"""

        with warnings.catch_warnings(record=True) as e:

            class Attr(parent_class):
                """Only has property"""
                abstract = 'No one expects the abstract attribute'

        self.check_method(parent_class, error, Attr, e)

    def coroutine(self, parent_class, error=None):
        """Test abstract coroutine method"""

        if NO_ASYNC:
            return

        with warnings.catch_warnings(record=True) as e:

            class_definition = textwrap.dedent('''\
            class Coroutine(parent_class):
                """Only has coroutine method"""
                async def abstract(self):
                    """Coroutine method"""
            ''')

            local_rtn = {'parent_class': parent_class}
            exec(class_definition, globals(), local_rtn)  # pylint: disable=exec-used
            Coroutine = local_rtn['Coroutine']  # pylint: disable=invalid-name

        self.check_method(parent_class, error, Coroutine, e)

    def type_hints_1(self, parent_class, error=None):
        """Test abstract method has type annotations"""

        if PY2:
            return

        with warnings.catch_warnings(record=True) as e:

            class_definition = textwrap.dedent('''\
            class TypeHints1(parent_class):
                """Has type annotations"""

                def abstract(self) -> str:
                    """Method with type annotations"""
            ''')

            local_rtn = {'parent_class': parent_class}
            exec(class_definition, globals(), local_rtn)  # pylint: disable=exec-used
            TypeHints1 = local_rtn['TypeHints1']  # pylint: disable=invalid-name

        self.check_method(parent_class, error, TypeHints1, e)

    def type_hints_2(self, parent_class, error=None):
        """Test abstract method has type annotations"""

        if PY2:
            return

        with warnings.catch_warnings(record=True) as e:

            class_definition = textwrap.dedent('''\
            class TypeHints2(parent_class):
                """Has type annotations"""

                def abstract(self) -> int:
                    """Method with type annotations"""
            ''')

            local_rtn = {'parent_class': parent_class}
            exec(class_definition, globals(), local_rtn)  # pylint: disable=exec-used
            TypeHints2 = local_rtn['TypeHints2']  # pylint: disable=invalid-name

        self.check_method(parent_class, error, TypeHints2, e)

    def test_duplicate_parents(self):
        """Parents with the same plugin type should raise an error"""

        @parent.Parent('test_parent')
        class Parent1(object):  # pylint: disable=unused-variable
            """First Parent"""

        with self.assertRaisesRegex(ValueError, "parent must be unique"):

            @parent.Parent('test_parent')
            class Parent2(object):  # pylint: disable=unused-variable
                """Second Parent"""

    def test_duplicate_versions(self):
        """Duplicate versions throw warning and are ignored"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent"""

        plugins = Parent._get_plugins()

        with warnings.catch_warnings(record=True) as e:

            class Child1(Parent):
                """First Child"""
                _alias_ = 'child'

        self.assertEqual(len(plugins['child']), 1)
        self.assertIs(plugins['child']['0'], Child1)
        self.assertEqual(len(e), 0)

        with warnings.catch_warnings(record=True) as e:

            class Child2(Parent):  # pylint: disable=unused-variable
                """Duplicate Child"""
                _alias_ = 'child'

        self.assertEqual(len(plugins['child']), 1)
        self.assertIs(plugins['child']['0'], Child1)
        self.assertEqual(len(e), 1)
        self.assertRegex(str(e[-1].message), 'Duplicate plugins found')

        with warnings.catch_warnings(record=True) as e:

            class Child3(Parent):
                """Child with a different version"""
                _alias_ = 'child'
                _version_ = '1.0'

        self.assertEqual(len(plugins['child']), 2)
        self.assertIs(plugins['child']['0'], Child1)
        self.assertIs(plugins['child']['1.0'], Child3)
        self.assertEqual(len(e), 0)

    def test_unknown_parent(self):
        """Raise an exception if parent is an unknown type"""

        @parent.Parent('test_parent')
        class Parent(object):
            """Parent"""

        # Clear registry
        parent.get_plugins().clear()

        with self.assertRaisesRegex(ValueError, "Unknown parent type"):

            class Child1(Parent):  # pylint: disable=unused-variable
                """Child"""
                _alias_ = 'child'
