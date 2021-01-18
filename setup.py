# Copyright 2018 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib setup file**
"""
import os
import sys

from setuptools import setup, find_packages

from setup_helpers import get_version, readme

INSTALL_REQUIRE = ['setuptools']
TESTS_REQUIRE = []

if sys.version_info[:2] < (3, 3):

    # Include unittest.mock from 3.3+
    TESTS_REQUIRE.append('mock')

if sys.version_info[:2] < (2, 7):

    # Include OrderedDict from 2.7+
    INSTALL_REQUIRE.append('ordereddict')
    # Include unittest features from 2.7+
    TESTS_REQUIRE.append('unittest2')

setup(
    name='pluginlib',
    version=get_version(os.path.join('pluginlib', '__init__.py')),
    description='A framework for creating and importing plugins',
    long_description=readme('README.rst'),
    url='https://github.com/Rockhopper-Technologies/pluginlib',
    license='MPLv2.0',
    author='Avram Lubkin',
    author_email='avylove@rockhopper.net',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=INSTALL_REQUIRE,
    tests_require=TESTS_REQUIRE,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='plugin, plugins, pluginlib',
    test_loader="unittest:TestLoader"
)
