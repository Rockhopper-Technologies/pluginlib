# Copyright 2014 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Electric engine**
Test data standard library
"""

from __future__ import absolute_import
from tests.testdata.parents import Engine


class Electric(Engine):
    """Dummy electric engine"""

    _alias_ = 'electric'

    def start(self):
        return 'beep'
