# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
)

from pocketlint.formatcheck import SQLChecker
from pocketlint.tests import CheckerTestCase
from pocketlint.tests.test_text import TestAnyTextMixin


class TestSQL(CheckerTestCase, TestAnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text, options=None):
        checker = SQLChecker(file_name, text, self.reporter, options)
        checker.check()

    def test_long_length(self):
        """SQL files may have long lines."""
        pass
