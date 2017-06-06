# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from scame.__main__ import parse_command_line
from scame.formatcheck import AnyTextChecker
from scame.tests import Bunch, CheckerTestCase


class AnyTextMixin(object):
    """
    A mixin that provides common text tests.
    """

    def create_and_check(self, file_name, text, options=None):
        raise NotImplementedError()

    def test_without_conflicts(self):
        self.create_and_check('bogus', '<<<<<< look')
        self.assertEqual([], self.reporter.messages)

    def test_with_conflicts(self):
        self.create_and_check('bogus', '<<<<<<' + '<')
        self.assertEqual(
            [(1, 'File has conflicts.')], self.reporter.messages)

    def test_length_okay(self):
        self.create_and_check('bogus', 'short line')
        self.assertEqual([], self.reporter.messages)

    def test_long_length(self):
        long_line = '1234 56189' * 9
        self.create_and_check('bogus', long_line)
        self.assertEqual(
            [(1, 'Line exceeds 80 characters.')],
            self.reporter.messages)

    def test_long_length_http_exception(self):
        """
        Long line with http or https links are ignored.
        """
        long_line = '1234 http://some.url 56189' * 9
        self.create_and_check('bogus', long_line)
        self.assertEqual([], self.reporter.messages)

        long_line = '1234 https://some.url 56189' * 9
        self.create_and_check('bogus', long_line)
        self.assertEqual([], self.reporter.messages)

    def test_no_trailing_whitespace(self):
        self.create_and_check('bogus', 'no trailing white-space')
        self.assertEqual([], self.reporter.messages)

    def test_trailing_whitespace(self):
        self.create_and_check('bogus', 'trailing white-space ')
        self.assertEqual(
            [(1, 'Line has trailing whitespace.')],
            self.reporter.messages)

    def test_without_tabs(self):
        self.create_and_check('bogus', '    without tabs')
        self.assertEqual([], self.reporter.messages)

    def test_with_tabs(self):
        self.create_and_check('bogus', '\twith tabs')
        self.assertEqual(
            [(1, 'Line contains a tab character.')],
            self.reporter.messages)

    def test_regex_line(self):
        """
        A list of regex and corresponding error messages can be passed to
        check each line.
        """
        options = Bunch(
            max_line_length=80,
            hang_closing=True,
            regex_line=[
                ('.*marker.*', 'Explanation.'),
                ('.*sign.*', 'Message.'),
                ],
            )

        self.create_and_check(
            'bogus',
            'with marker here\n other sign here', options)

        self.assertEqual([
            (1, 'Line contains flagged text. Explanation.'),
            (2, 'Line contains flagged text. Message.'),
            ],
            self.reporter.messages,
            )


class TestText(CheckerTestCase, AnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text, options=None):
        checker = AnyTextChecker(
            file_name, text, self.reporter, options)
        checker.check()

    def test_reencode_ascii(self):
        """Bytes strings are rencoded to get unicode"""
        ascii_line = b"this will be unicode"
        checker = AnyTextChecker('bogus', ascii_line, self.reporter)
        self.assertEqual("this will be unicode", checker.text)

    def test_reencode_utf8(self):
        """UTF-8 Bytes strings are rencoded to get unicode"""
        ascii_line = b"this will be unicode \xe2"
        checker = AnyTextChecker('bogus', ascii_line, self.reporter)
        self.assertEqual("this will be unicode ", checker.text)

    def test_with_tabs(self):
        """Text files may contain tabs."""
        pass

    def test_long_length_options(self):
        long_line = '1234 56189' * 5
        options = parse_command_line(['-m', '49'])
        self.create_and_check('bogus', long_line, options=options)
        self.assertEqual(
            [(1, 'Line exceeds 49 characters.')],
            self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_windows_newlines(self):
        """Files with Windows newlines are reported with errors."""
        content = '\r\nbla\r\nbla\r\n'
        checker = AnyTextChecker(
            'bogus', content, self.reporter)
        checker.check()
        self.assertEqual(
            [(0, 'File contains Windows new lines.')],
            self.reporter.messages)

    def test_no_empty_last_line(self):
        """
        An error is reported if file does not end with a new lines.
        """
        content = (
            'Some first line\n'
            'the second and last line without newline')
        checker = AnyTextChecker('bogus', content, self.reporter)
        checker.check_empty_last_line(2)
        expected = [(
            2, 'File does not ends with an empty line.')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_multiple_empty_last_lines(self):
        """An error is reported if file ends with multiple new lines."""
        content = (
            'Some first line\n'
            'the second and last\n'
            '\n')
        checker = AnyTextChecker('bogus', content, self.reporter)
        checker.check_empty_last_line(3)
        expected = [(
            3, 'File does not ends with an empty line.')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_single_last_line_no_newline(self):
        """An error is reported if file contains a single newline."""
        content = (
            'the second and last line without newline')
        checker = AnyTextChecker('bogus', content, self.reporter)
        checker.check_empty_last_line(2)
        expected = [(
            2, 'File does not ends with an empty line.')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)
