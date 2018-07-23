# Copyright 2014 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**pluginlib test data parents**
Parent classes for tests
"""

from pluginlib import Parent, abstractmethod


@Parent('parser', 'testdata')
class Parser(object):
    """Parser parent class"""

    @abstractmethod
    def parse(self):
        """Required method"""


@Parent('engine', 'testdata')
class Engine(object):
    """Engine parent class"""

    @abstractmethod
    def start(self):
        """Required method"""


@Parent('hook', 'testdata')
class Hook(object):
    """Hook parent class"""
