# Copyright (C) 2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    with_statement,
)

from tempfile import NamedTemporaryFile

from pocketlint.formatdoctest import DoctestReviewer
from pocketlint.tests import CheckerTestCase


good_doctest = """\
Example doctest
==============

You can work with file paths using os.path

    >>> import os.path
    >>> os.path.join('.', 'pocketlint', 'formatcheck.py')
    ./pocketlint/formatcheck.py
"""

malformed_doctest = """\
You can work with file paths using os.path
    >>> import os.path
    >>> os.path.join('.', 'pocketlint', 'formatcheck.py')
Narrative without WANT section.
"""

source_comments_doctest = """\
eg
    >>> # one
    >>> a = (
    ... # two
    ... 1)
"""


class TestDoctest(CheckerTestCase):
    """Verify doctest checking."""

    def setUp(self):
        super(TestDoctest, self).setUp()
        self.file = NamedTemporaryFile(prefix='pocketlint_')

    def tearDown(self):
        self.file.close()

    def test_init_with_options(self):
        self.write_to_file(self.file, good_doctest)
        checker = DoctestReviewer(
            self.file.name, good_doctest, self.reporter, None)
        self.assertEqual(self.file.name, checker.file_path)
        self.assertEqual(good_doctest, checker.doctest)
        self.assertIs(None, checker.options)

    def test_doctest_without_issues(self):
        self.write_to_file(self.file, good_doctest)
        checker = DoctestReviewer(
            self.file.name, good_doctest, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_doctest_with_source_comments(self):
        self.write_to_file(self.file, source_comments_doctest)
        checker = DoctestReviewer(
            self.file.name, source_comments_doctest, self.reporter)
        checker.check_source_comments()
        self.assertEqual([
            (2, 'Comment belongs in narrative.'),
            (4, 'Comment belongs in narrative.')], self.reporter.messages)

    def test_doctest_malformed_doctest(self):
        self.write_to_file(self.file, malformed_doctest)
        checker = DoctestReviewer(
            self.file.name, malformed_doctest, self.reporter)
        checker.check()
        expected = (
            "line 4 of the docstring for %s has inconsistent leading "
            "whitespace: 'Narrative without WANT section.'" % self.file.name)
        self.assertEqual(
            [(0, expected)], self.reporter.messages)

    def test_doctest_with_globs(self):
        # Doctest runners often setup global identifiers that are not python
        # execution issues
        doctest = "    >>> ping('text')\n    pong text"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_doctest_with_python_compilation_error(self):
        doctest = "    >>> if (True\n    pong text"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, 'Could not compile:\n    if (True')],
            self.reporter.messages)

    def test_moin_header(self):
        doctest = "= Heading =\n\nnarrative"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, 'narrative uses a moin header.')],
            self.reporter.messages)

    def test_fix_moin_header_1(self):
        doctest = "= Heading =\n\nnarrative"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual(
            "Heading\n=======\n\nnarrative", text)

    def test_fix_moin_header_2(self):
        doctest = "== Heading ==\n\nnarrative"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual(
            "Heading\n-------\n\nnarrative", text)

    def test_fix_moin_header_3(self):
        doctest = "=== Heading ===\n\nnarrative"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual(
            "Heading\n.......\n\nnarrative", text)

    def test_bad_indentation(self):
        doctest = "narrative\n>>> len('done')\n"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(2, 'source has bad indentation.')],
            self.reporter.messages)

    def test_fix_bad_indentation(self):
        doctest = "narrative\n>>> len('done')\n"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual(
            "narrative\n\n    >>> len('done')\n\n", text)

    def test_fix_bad_indentation_with_source_and_want(self):
        doctest = "narrative\n\n>>> len(\n...     'done')"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual(
            "narrative\n\n    >>> len(\n    ...     'done')\n\n", text)

    def test_trailing_whitespace(self):
        doctest = "narrative  \n    >>> len('done')\n"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, 'narrative has trailing whitespace.')],
            self.reporter.messages)

    def test_fix_trailing_whitespace(self):
        doctest = "narrative  \n    >>> len('done') \n"
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        self.assertEqual("narrative\n\n    >>> len('done')\n\n", text)

    def test_long_line_source_and_want(self):
        doctest = (
            "    >>> very_very_very_very_very.long_long_long_long("
            "method_method_method_method,\n"
            "    ...   call_call_call_call_call_call_call_call_call_call,"
            "bad_bad_bad_bad_bad)\n")
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, 'source exceeds 78 characters.'),
             (2, 'source exceeds 78 characters.')],
            self.reporter.messages)

    def test_long_line_narrative(self):
        doctest = (
            "narrative is a line that exceeds 78 characters which causes "
            "scrolling in consoles and wraps poorly in email\n")
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.check()
        self.assertEqual(
            [(1, 'narrative exceeds 78 characters.')],
            self.reporter.messages)

    def test_fix_long_line(self):
        doctest = (
            "narrative is a line that exceeds 78 characters which causes "
            "scrolling in consoles and wraps poorly in email\n"
            "  * item")
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        text = checker.format()
        expected = (
            "narrative is a line that exceeds 78 characters which causes "
            "scrolling in\nconsoles and wraps poorly in email\n\n"
            "  * item\n\n")
        self.assertEqual(expected, text)

    def test_format_and_save(self):
        doctest = (
            "narrative is a line that exceeds 78 characters which causes "
            "scrolling in consoles and wraps poorly in email\n"
            "  * item\n\n"
            "    >>> very_very_very_very_very.long_long_long_long("
            "method_method_method_method)\n"
            "    True\n\n")
        self.write_to_file(self.file, doctest)
        checker = DoctestReviewer(
            self.file.name, doctest, self.reporter)
        checker.format_and_save()
        expected = (
            "narrative is a line that exceeds 78 characters which causes "
            "scrolling in\nconsoles and wraps poorly in email\n\n"
            "  * item\n\n"
            "    >>> very_very_very_very_very.long_long_long_long("
            "method_method_method_method)\n"
            "    True\n\n\n")
        self.file.seek(0)
        text = self.file.read().decode('utf-8')
        self.assertEqual(expected, text)
        self.assertEqual(expected, checker.doctest)
        # Source code issues cannot be fixed by the formatter.
        checker.check()
        self.assertEqual(
            [(6, 'source exceeds 78 characters.')],
            self.reporter.messages)
