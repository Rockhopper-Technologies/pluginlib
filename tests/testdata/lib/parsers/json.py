# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**JSON parser**
Test data standard library
"""

from __future__ import absolute_import
from tests.testdata.parents import Parser


class JSON(Parser):
    """Dummy JSON parser"""

    _alias_ = 'json'
    _version_ = '1.0'

    def parse(self):
        return 'json'


class JSON2(Parser):
    """Dummy JSON parser"""

    _alias_ = 'json'
    _version_ = '2.0'

    def parse(self):
        return 'json'
