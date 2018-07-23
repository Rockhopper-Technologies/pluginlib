# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Bad Module that will raise syntax error when imported
"""


def func1():
    """Raises an exception"""
    raise RuntimeError('This parrot is no more')


def func2():
    """Calls function 1"""
    func1()


def func3():
    """Calls function 2"""
    func2()


func3()
