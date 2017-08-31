# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from tempfile import NamedTemporaryFile
import unittest

from scame.formatcheck import (
    JavascriptChecker,
    JS
    )
from scame.tests import CheckerTestCase
from scame.tests.test_text import AnyTextMixin

try:
    import closure_linter
    # Shut up the linter.
    closure_linter
except ImportError:
    closure_linter = None


good_js = """\
var a = 1;
"""

invalid_js = """\
a = 1

"""


class TestJavascript(CheckerTestCase):
    """Verify Javascript integration."""

    def setUp(self):
        super(TestJavascript, self).setUp()
        self.file = NamedTemporaryFile(prefix='pocketlint_')

    def tearDown(self):
        self.file.close()

    def test_good_js(self):
        self.write_to_file(self.file, good_js)
        checker = JavascriptChecker(self.file.name, good_js, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_invalid_value(self):
        if JS is None:
            return
        self.write_to_file(self.file, invalid_js)
        checker = JavascriptChecker(self.file.name, invalid_js, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, "Expected ';' and instead saw '(end)'.")],
            self.reporter.messages)

    closure_linter_trigger = (
        'var test = 1+ 1;\n'
        )

    def test_closure_linter(self):
        if closure_linter is None:
            raise unittest.SkipTest('Google Closure Linter not available.')

        self.write_to_file(self.file, self.closure_linter_trigger)
        checker = JavascriptChecker(
            self.file.name, invalid_js, self.reporter)
        checker.options.closure_linter.update({
            'enabled': True,
            'ignore': [],
            })

        checker.check()

        self.assertEqual(
            [(1, u'E:0002: Missing space before "+"')],
            self.reporter.messages)

    def test_closure_linter_ignore(self):
        if closure_linter is None:
            raise unittest.SkipTest('Google Closure Linter not available.')

        self.write_to_file(self.file, self.closure_linter_trigger)
        checker = JavascriptChecker(
            self.file.name, invalid_js, self.reporter)
        checker.options.closure_linter.update({
            'enabled': True,
            'ignore': [2],
            })

        checker.check()

        self.assertEqual([], self.reporter.messages)

    def test_closure_linter_disabled(self):
        """No errors are reported when closure linter is disabled."""
        self.write_to_file(self.file, self.closure_linter_trigger)
        checker = JavascriptChecker(
            self.file.name, invalid_js, self.reporter)
        checker.options.closure_linter.update({
            'enabled': False,
            'ignore': [],
            })

        checker.check()

        self.assertEqual([], self.reporter.messages)


class TestText(CheckerTestCase, AnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text, options=None):
        """Used by the TestAnyTextMixin tests."""
        checker = JavascriptChecker(file_name, text, self.reporter, options)
        checker.check_text()

    def test_code_with_debugger(self):
        script = "debugger;"
        checker = JavascriptChecker('bogus', script, self.reporter)
        checker.check_text()
        self.assertEqual(
            [(1, 'Line contains a call to debugger.')],
            self.reporter.messages)
