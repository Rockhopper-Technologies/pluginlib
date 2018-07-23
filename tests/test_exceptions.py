# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib.exceptions**
"""

import warnings

from pluginlib import exceptions

from tests import TestCase


# Because we want the test names to match the class names
# pylint: disable=invalid-name
class TestExceptions(TestCase):
    """Tests for custom exceptions"""

    def setUp(self):
        self.msg = 'Just your friendly neighborhood Spiderman'

    def test_pluginlib_error(self):
        """Raises PluginlibError as expected"""
        with self.assertRaises(Exception) as e:
            raise exceptions.PluginlibError()
        self.assertIsNone(e.exception.friendly)

        with self.assertRaises(Exception) as e:
            raise exceptions.PluginlibError(friendly=self.msg)
        self.assertEqual(e.exception.friendly, self.msg)

    def test_plugin_import_error(self):
        """Raises PluginImportError as expected"""
        with self.assertRaises(exceptions.PluginlibError) as e:
            raise exceptions.PluginImportError()
        self.assertIsNone(e.exception.friendly)

        with self.assertRaises(exceptions.PluginlibError) as e:
            raise exceptions.PluginImportError(friendly=self.msg)
        self.assertEqual(e.exception.friendly, self.msg)


class TestWarnings(TestCase):
    """Tests for custom warnings"""

    def test_plugin_warning(self):
        """Warns with PluginWarning as expected"""

        with warnings.catch_warnings(record=True) as e:
            warnings.simplefilter("always")
            warnings.warn('Just a warning', exceptions.PluginWarning)
            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, exceptions.PluginWarning))
            self.assertTrue(issubclass(e[-1].category, UserWarning))
            self.assertEqual(str(e[-1].message), 'Just a warning')

    def test_entrypoint_warning(self):
        """Warns with EntryPointWarning as expected"""

        with warnings.catch_warnings(record=True) as e:
            warnings.simplefilter("always")
            warnings.warn('Just a warning', exceptions.EntryPointWarning)
            self.assertEqual(len(e), 1)
            self.assertTrue(issubclass(e[-1].category, exceptions.EntryPointWarning))
            self.assertTrue(issubclass(e[-1].category, ImportWarning))
            self.assertEqual(str(e[-1].message), 'Just a warning')
