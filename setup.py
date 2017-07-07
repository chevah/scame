#!/usr/bin/python

from __future__ import (
    absolute_import,
    print_function,
)

import subprocess

from distutils.core import (
    Command,
    setup,
)
from distutils.command.sdist import sdist
import unittest


class SignedSDistCommand(sdist):
    """Sign the source archive with a detached signature."""

    description = "Sign the source archive after it is generated."

    def run(self):
        sdist.run(self)
        gpg_args = [
            'gpg', '--armor', '--sign', '--detach-sig', self.archive_files[0]]
        gpg = subprocess.Popen(
            gpg_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gpg.communicate()


class Check(Command):
    description = "Run unit tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def get_command_name(self):
        pass

    def run(self):
        test_loader = unittest.defaultTestLoader
        suite = unittest.TestSuite()
        for test_module in test_loader.discover('pocketlint'):
            suite.addTest(test_module)
        unittest.TextTestRunner(verbosity=1).run(suite)

setup(
    name="pocketlint",
    description="Pocket-lint a composite linter and style checker.",
    version="1.4.4.c13",
    maintainer="Curtis C. Hovey",
    maintainer_email="sinzui.is@gmail.com",
    url="https://launchpad.net/pocket-lint",
    packages=[
        'pocketlint', 'pocketlint/contrib'],
    package_dir={
        'pocketlint': 'pocketlint',
        'pocketlint/contrib': 'pocketlint/contrib'},
    package_data={
        'pocketlint': ['jsreporter.js'],
        'pocketlint/contrib': ['fulljslint.js']},
    requires=['pyflakes (>=7.3)', 'pep8 (>=1.4.6)'],
    scripts=['scripts/pocketlint'],
    cmdclass={
        'check': Check,
        'signed_sdist': SignedSDistCommand,
    })
