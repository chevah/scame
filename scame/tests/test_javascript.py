# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).
from scame.formatcheck import JavascriptChecker
from scame.tests import CheckerTestCase
from scame.tests.test_text import AnyTextMixin


class TestText(CheckerTestCase, AnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text, options=None):
        """Used by the TestAnyTextMixin tests."""
        checker = JavascriptChecker(file_name, text, self.reporter, options)
        checker.check_text()

    def test_code_with_debugger(self):
        script = "debugger;"
        checker = JavascriptChecker("bogus", script, self.reporter)
        checker.check_text()
        self.assertEqual(
            [(1, "Line contains a call to debugger.")], self.reporter.messages
        )
