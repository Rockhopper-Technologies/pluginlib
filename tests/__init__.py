# Copyright 2014 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Test module for pluginlib**
"""

import logging
from io import StringIO

from pluginlib._util import LOGGER


OUTPUT = StringIO()
HANDLER = logging.StreamHandler(OUTPUT)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.INFO)

__all__ = ['OUTPUT']
