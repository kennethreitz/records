#!/usr/bin/env python

import os
import re
import sys

from codecs import open

from setuptools import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py register')
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload --universal')
    sys.exit()

requires = ['psycopg2', 'tablib']
version = '0.1.0'

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()
with open('HISTORY.rst', 'r', 'utf-8') as f:
    history = f.read()

setup(
    name='records',
    version=version,
    description='SQL for Humans',
    long_description=readme + '\n\n' + history,
    author='Kenneth Reitz',
    author_email='me@kennethreitz.org',
    url='https://github.com/kennethreitz/records',
    py_modules=['records'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    install_requires=requires,
    license='ISC',
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
    )
)
