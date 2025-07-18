# Copyright 2018 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Pluginlib setup file**
"""
import os

from setuptools import setup, find_packages

from setup_helpers import get_version, readme

INSTALL_REQUIRE = ['packaging', 'importlib-metadata; python_version < "3.10"']
TESTS_REQUIRE = []

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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='plugin, plugins, pluginlib',
    test_loader="unittest:TestLoader",
    python_requires='>=3.6',
)
