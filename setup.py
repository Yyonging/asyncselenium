#!/usr/bin/env python

# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from distutils.command.install import INSTALL_SCHEMES
from os.path import dirname, join, abspath
from setuptools import setup
from setuptools.command.install import install


for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup_args = {
    'cmdclass': {'install': install},
    'name': 'asyncselenium',
    'version': "0.0.2",
    'license': 'Apache 2.0',
    'description': 'A async selenium package to improve performance',
    'long_description': open(join(abspath(dirname(__file__)), "README.rst")).read(),
    'url': 'https://github.com/Yyonging/asyncselenium.git',
    'classifiers': ['Development Status :: 5 - Production/Stable',
                    'Intended Audience :: Developers',
                    'License :: OSI Approved :: Apache Software License',
                    'Operating System :: POSIX',
                    'Operating System :: Microsoft :: Windows',
                    'Operating System :: MacOS :: MacOS X',
                    'Topic :: Software Development :: Testing',
                    'Topic :: Software Development :: Libraries',
                    'Programming Language :: Python :: 3.6'],
    'package_dir': {
        'asyncselenium': 'asyncselenium',
        'asyncselenium.common': 'asyncselenium/common',
        'asyncselenium.webdriver': 'asyncselenium/webdriver',
    },
    'packages': ['asyncselenium',
                 'asyncselenium.common',
                 'asyncselenium.webdriver',
                 'asyncselenium.webdriver.remote',
                 'asyncselenium.webdriver.support',
                 'asyncselenium.webdriver.chrome',
                ],
    'include_package_data': True,
    'install_requires': ['selenium', 'aiohttp'],
    'zip_safe': False
}

setup(**setup_args)
