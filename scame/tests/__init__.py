# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).
import unittest

from scame.formatcheck import Reporter


class CheckerTestCase(unittest.TestCase):
    """A testcase with a TestReporter for checkers."""

    def setUp(self):
        self.reporter = Reporter(Reporter.COLLECTOR)
        self.reporter.call_count = 0

    def write_to_file(self, wfile, string):
        string = bytes(string, "utf-8")
        wfile.write(string)
        wfile.flush()


class Bunch:
    """
    A simple class to act as a dictionary.
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, missing=None):
        return self.__dict__.get(key, missing)
