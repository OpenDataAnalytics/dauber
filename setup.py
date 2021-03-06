#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#  Copyright 2016 Kitware Inc.
#
#  Licensed under the Apache License, Version 2.0 ( the "License" );
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
###############################################################################

from setuptools import setup

setup(name='dauber',
      version='0.0.0-1',
      description='APACHE licensed project for running ansible playbooks',
      long_description="This project is an APACHE liscenced project for managing and running Ansible playbooks",
      author='Kitware Inc',
      author_email='chris.kotfila@kitware.com',
      url='http://www.kitware.com',
      packages=['dauber'],
      package_data={'dauber': ['ansible/callback_plugins/*.py']},
      test_suite="tests.test_suite",
      install_requires=[],
      license='Apache 2.0',
      zip_safe=False,
      keywords='ansible',

)
