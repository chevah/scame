# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

import sys
import unittest

from scame.formatcheck import Reporter


class CheckerTestCase(unittest.TestCase):
    """A testcase with a TestReporter for checkers."""

    def setUp(self):
        self.reporter = Reporter(Reporter.COLLECTOR)
        self.reporter.call_count = 0

    def write_to_file(self, wfile, string):
        if sys.version_info >= (3,):
            string = bytes(string, 'utf-8')
        wfile.write(string)
        wfile.flush()


class Bunch(object):
    """
    A simple class to act as a dictionary.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
