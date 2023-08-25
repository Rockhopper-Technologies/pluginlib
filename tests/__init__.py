# Copyright 2014 - 2022 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib**
"""

import logging
import sys
import unittest

from pluginlib._util import LOGGER, PY2

if sys.version_info[:2] < (3, 3):
    import mock  # pylint: disable=import-error
else:
    from unittest import mock  # noqa: F401  # pylint: disable=no-name-in-module, import-error

if PY2:
    from StringIO import StringIO  # pylint: disable=import-error
else:
    from io import StringIO

OUTPUT = StringIO()
HANDLER = logging.StreamHandler(OUTPUT)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.INFO)

__all__ = ['mock', 'unittest', 'OUTPUT', 'TestCase']


class TestCase(unittest.TestCase):
    """Simple subclass of unittest.TestCase"""


# Fix deprecated methods
def assert_regex(self, text, regex, msg=None):
    """
    Wrapper for assertRegexpMatches
    """

    return self.assertRegexpMatches(text, regex, msg)


def assert_not_regex(self, text, regex, msg=None):
    """
    Wrapper for assertNotRegexpMatches
    """

    return self.assertNotRegexpMatches(text, regex, msg)


def assert_raises_regex(self, exception, regex, *args, **kwargs):
    """
    Wrapper for assertRaisesRegexp
    """

    return self.assertRaisesRegexp(exception, regex, *args, **kwargs)


if not hasattr(TestCase, 'assertRegex'):
    TestCase.assertRegex = assert_regex

if not hasattr(TestCase, 'assertNotRegex'):
    TestCase.assertNotRegex = assert_not_regex

if not hasattr(TestCase, 'assertRaisesRegex'):
    TestCase.assertRaisesRegex = assert_raises_regex
