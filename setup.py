#!/usr/bin/env python

import os
import sys
from codecs import open

from setuptools import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py register')
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload --universal')
    sys.exit()

requires = ['SQLAlchemy', 'tablib', 'docopt']
version = '0.5.2'


def read(f):
    return open(f, encoding='utf-8').read()

setup(
    name='records',
    version=version,
    description='SQL for Humans',
    long_description=read('README.rst') + '\n\n' + read('HISTORY.rst'),
    author='Kenneth Reitz',
    author_email='me@kennethreitz.org',
    url='https://github.com/kennethreitz/records',
    py_modules=['records'],
    package_data={'': ['LICENSE']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['records=records:cli'],
    },
    install_requires=requires,
    extras_require={
        'pandas': ['tablib[pandas]'],
    },
    license='ISC',
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
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
