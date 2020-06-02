# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**XML parser**
Test data standard library
"""

from __future__ import absolute_import
from tests.testdata.parents import Parser


class XML(Parser):
    """Dummy XML parser"""

    _alias_ = 'xml'

    def parse(self):
        return 'xml'
