#!/usr/bin/python
from __future__ import (
    absolute_import,
    print_function,
    )
from setuptools import find_packages, setup

with open('scame/__version__.py') as version_file:
    exec(version_file.read())


setup(
    name='scame',
    description='A composite linter and style checker.',
    version=VERSION,  # noqa:pyflakes
    maintainer='Adi Roiban',
    maintainer_email='adi.roiban@chevah.com',
    url='https://github.com/chevah/scame',
    packages=find_packages('.'),
        entry_points={
            'console_scripts': [
              'scame = scame.__main__:main',
            ],
        },

    install_requires=[
        'pyflakes',
        ],

    extras_require={
        'dev': [
            'pycodestyle',
            'bandit',
            'pylint',
            'nose',
            ],
        }

    )
