"""
Tests for JSON files.
"""

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from scame.formatcheck import IS_PY3, JSONChecker
from scame.tests import CheckerTestCase


class TestJSON(CheckerTestCase):
    """Verify JSON validation."""

    def test_empty_file(self):
        """No errors are be reported for empty files."""
        self.reporter.call_count = 0
        content = ''
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_long_line(self):
        """No errors are be reported for long lines."""
        self.reporter.call_count = 0
        content = '{"1": "' + 'a' * 100 + '"}\n'
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_trailing_spaces(self):
        """Short test to check that trailing spaces are caught."""
        self.reporter.call_count = 0
        content = '{} \n'
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual(
            [(1, 'Line has trailing whitespace.')],
            self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_conflict_markups(self):
        """Short test to check that merge conflicts are caught."""
        self.reporter.call_count = 0
        content = '{}\n>>>>>>>\n'
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual(
            (2, 'File has conflicts.'),
            self.reporter.messages[0])

    def test_tabs(self):
        """Short test to check that tab characters are caught."""
        self.reporter.call_count = 0
        content = '\t{}\n'
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual(
            [(1, 'Line contains a tab character.')],
            self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_unable_to_compile(self):
        """Line number '0' is reported if JSON can not be compiled at all."""
        content = '\n\nno-json-object\n'
        checker = JSONChecker('bogus', content, self.reporter)

        checker.check()

        self.assertEqual(1, self.reporter.call_count)
        self.assertIn(
            self.reporter.messages[0],
            [(0, 'No JSON object could be decoded'),
             (3, 'Expecting value: line 3 column 1 (char 2)')])

    def test_compile_error_with_line(self):
        """The line number raised by JSON module is used."""
        content = '{\n1: "something"}\n'
        checker = JSONChecker('bogus', content, self.reporter)
        checker.check()

        if IS_PY3:
            self.assertEqual(
                [(2, 'Expecting property name enclosed in double quotes: '
                     'line 2 column 1 (char 2)')],
                self.reporter.messages)
        else:
            self.assertEqual(
                [(2, 'Expecting property name: line 2 column 1 (char 2)')],
                self.reporter.messages)

        self.assertEqual(1, self.reporter.call_count)

    def test_compile_error_on_multiple_line(self):
        """The first line number is used when the error is multiple lines."""
        content = '{}\n}\n}\n'
        checker = JSONChecker('bogus', content, self.reporter)
        checker.check()

        self.assertEqual(
            [(2,
             'Extra data: line 2 column 1 - line 4 column 1 (char 3 - 7)')],
            self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)
