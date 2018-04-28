#!/usr/bin/env python

import io
import os
import sys
from codecs import open
from shutil import rmtree

from setuptools import setup, Command

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = '\n' + f.read()


class PublishCommand(Command):
    """Support setup.py publish."""

    description = 'Build and publish the package.'
    user_options = []

    @staticmethod
    def status(s):
        """Prints things in bold."""
        print('\033[1m{}\033[0m'.format(s))

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status('Removing previous builds...')
            rmtree(os.path.join(here, 'dist'))
        except FileNotFoundError:
            pass

        self.status('Building Source and Wheel (universal) distribution...')
        os.system('{} setup.py sdist bdist_wheel --universal'.format(sys.executable))

        self.status('Uploading the package to PyPi via Twine...')
        os.system('twine upload dist/*')

        sys.exit()

requires = ['SQLAlchemy;python_version>="3.0"',
            'SQLAlchemy<1.1;python_version<"3.0"',
            'openpyxl<2.5.0', # temporary fix to issue #142
            'tablib>=0.11.4',
            'docopt']
version = '0.5.3'


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
        'pg': ['psycopg2'],
        'redshift': ['sqlalchemy-redshift', 'psycopg2']
        # TODO: Add the rest.
    },
    license='ISC',
    zip_safe=False,
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ),
    cmdclass={
        'publish': PublishCommand,
    }
)
