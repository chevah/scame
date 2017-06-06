# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

import unittest
from tempfile import NamedTemporaryFile

from pocketlint.formatcheck import (
    # Imported via pocketlint to avoid duplication of conditional import.
    pep257,
    PocketLintOptions, PythonChecker,
    )
from pocketlint.tests import CheckerTestCase
from pocketlint.tests.test_text import TestAnyTextMixin


good_python = """\
class example:

    def __init__(self, value):
        len("Good night.")
"""

good_python_on_windows = """\
class example:

    def __init__(self, value):
        try:
            open("some.file", 'rt')
        except WindowsError:
            pass
"""

bad_syntax_python = """\
class Test():
    def __init__(self, default='', non_default):
        pass
"""

bad_syntax2_python = """\
class Test(
    def __init__(self, val):
        pass
"""

bad_indentation_python = """\
class Test:
    def __init__(self):
        a = 0
      b = 1
"""

ugly_python = """\
class Test:
    def __init__(self):
        a = b
"""

ugly_style_python = """\
class Test:

    def __init__(self):
        a =  "okay"
"""


ugly_style_lines_python = """\
a = 1
# Post comment.


# Pre comment.
class Test:

    # Pre comment.
    def __init__(self):
        # Inter comment.
        self.a = "okay"
"""

hanging_style_python = """\
from or import (
    environ,
    path,
    )
"""


class Bunch(object):
    """Collector of a bunch of named stuff."""
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


class TestPyflakes(CheckerTestCase):
    """Verify pyflakes integration."""

    def test_code_without_issues(self):
        self.reporter.call_count = 0
        checker = PythonChecker('bogus', good_python, self.reporter)
        checker.check_flakes()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_windows_code_without_issues(self):
        self.reporter.call_count = 0
        checker = PythonChecker(
            'bogus', good_python_on_windows, self.reporter)
        checker.check_flakes()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_code_with_SyntaxError(self):
        self.reporter.call_count = 0
        checker = PythonChecker(
            'bogus', bad_syntax_python, self.reporter)
        checker.check_flakes()
        expected = [(
            2, 'Could not compile; non-default argument follows '
               'default argument: ')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_code_with_very_bad_SyntaxError(self):
        checker = PythonChecker(
            'bogus', bad_syntax2_python, self.reporter)
        checker.check_flakes()
        expected = [(
            2, 'Could not compile; invalid syntax: def __init__(self, val):')]
        self.assertEqual(expected, self.reporter.messages)

    def test_code_with_IndentationError(self):
        checker = PythonChecker(
            'bogus', bad_indentation_python, self.reporter)
        checker.check_flakes()
        expected = [
            (4, 'Could not compile; unindent does not match any '
                'outer indentation level: b = 1')]
        self.assertEqual(expected, self.reporter.messages)

    def test_code_with_warnings(self):
        self.reporter.call_count = 0
        self.file = NamedTemporaryFile(prefix='pocketlint_', suffix='.py')
        self.write_to_file(self.file, ugly_python)
        checker = PythonChecker(self.file.name, ugly_python, self.reporter)
        checker.check_flakes()
        self.assertEqual(
            [(3, "undefined name 'b'"),
             (3, "local variable 'a' is assigned to but never used")],
            self.reporter.messages)
        self.assertEqual(2, self.reporter.call_count)

    def test_pyflakes_ignore(self):
        pyflakes_ignore = (
            'def something():\n'
            '    unused_variable = 1  # pyflakes:ignore\n')
        self.reporter.call_count = 0
        checker = PythonChecker('bogus', pyflakes_ignore, self.reporter)
        checker.check_flakes()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_pyflakes_unicode(self):
        """It handles Python non-ascii encoded files."""
        source = (
            '# -*- coding: utf-8 -*-\n'
            'variable = u"r\xe9sum\xe9"'
            )
        checker = PythonChecker('bogus', source, self.reporter)
        # This should set the correct encoding.
        checker.check_text()

        checker.check_flakes()
        self.assertEqual([], self.reporter.messages)


class TestPEP8(CheckerTestCase):
    """Verify PEP8 integration."""

    def test_code_without_issues(self):
        checker = PythonChecker(
            'file/path', good_python, self.reporter)
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)

    def test_bad_syntax(self):
        checker = PythonChecker(
            'file/path', ugly_style_python, self.reporter)
        checker.check_pep8()
        self.assertEqual(
            [(4, 'E222 multiple spaces after operator')],
            self.reporter.messages)

    def test_code_with_IndentationError(self):
        checker = PythonChecker(
            'file/path', bad_indentation_python, self.reporter)
        checker.check_pep8()
        expected = [(
            4,
            'E901 IndentationError: '
            'unindent does not match any outer indentation level')]
        self.assertEqual(expected, self.reporter.messages)
        checker.check_pep8()

    def test_code_closing_bracket(self):
        checker = PythonChecker(
            'file/path', hanging_style_python, self.reporter)
        checker.options.pep8['hang_closing'] = True
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)
        checker.options.pep8['hang_closing'] = False
        checker.check_pep8()
        self.assertEqual(
            [(4, "E123 closing bracket does not match indentation of "
                 "opening bracket's line")],
            self.reporter.messages)

    def test_code_with_issues(self):
        checker = PythonChecker(
            'file/path', ugly_style_python, self.reporter)
        checker.check_pep8()
        self.assertEqual(
            [(4, 'E222 multiple spaces after operator')],
            self.reporter.messages)

    def test_code_with_comments(self):
        checker = PythonChecker(
            'file/path', ugly_style_lines_python, self.reporter)
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)

    def test_long_length_good(self):
        long_line = '1234 56189' * 7 + '12345678' + '\n'
        checker = PythonChecker('file/path', long_line, self.reporter)
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)

    def test_long_length_bad(self):
        long_line = '1234 56189' * 8 + '\n'
        checker = PythonChecker('file/path', long_line, self.reporter)
        checker.check_pep8()
        self.assertEqual(
            [(1, 'E501 line too long (80 > 79 characters)')],
            self.reporter.messages)

    def test_long_length_options(self):
        long_line = '1234 56189' * 7 + '\n'
        options = PocketLintOptions()
        options.max_line_length = 60
        checker = PythonChecker(
            'file/path', long_line, self.reporter, options)
        checker.check_pep8()
        self.assertEqual(
            [(1, 'E501 line too long (70 > 59 characters)')],
            self.reporter.messages)


@unittest.skipIf(pep257 is None, 'pep257 is not available.')
class TestPEP257(CheckerTestCase):
    """Verify PEP257 integration."""

    def setUp(self):
        super(TestPEP257, self).setUp()
        self.file = NamedTemporaryFile(prefix='pocketlint_')

    def tearDown(self):
        self.file.close()

    def makeChecker(self, content, options=None):
        """Create a Python checker with file from `content`."""
        # Don't know why multi-line text is interpreted as Unicode.
        content = content.encode('utf-8')
        return PythonChecker(
            self.file.name, content, self.reporter, options=options)

    def test_code_without_issues(self):
        """No errors are reported if everything has a valid docstring."""
        checker = self.makeChecker('''
"""Module's docstring."""

class SomeClass(object):

        """Class with short docstring."""

        def method(self):
            """Method with short docstring."""

        def otherMethod(self):
            """
            Method with multi.

            Line docstring.

            """
        ''')

        checker.check_pep257()
        self.assertEqual([], self.reporter.messages)

    def test_pep8_options(self):
        """It can set PEP8 options."""
        long_line = '1234 56189' * 7 + '\n'
        checker = PythonChecker('file/path', long_line, self.reporter)
        checker.options.pep8['ignore'] = ['E501']
        checker.options.pep8['max_line_length'] = 60
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)

    pep257_without_docstrings = '''
def some_function():
    """Bad multi line without point"""
    '''

    def test_code_with_issues(self):
        """Errors are reported when docstrings are missing or in bad format.

        """
        checker = self.makeChecker(self.pep257_without_docstrings)

        checker.check_pep257()

        self.assertEqual(
            [(1, 'All modules should have docstrings.'),
             (3, 'First line should end with a period.'), ],
            self.reporter.messages,
            )

    def test_code_with_ignore(self):
        """A list with error message which should be ignored can be
        provided as `pep257_ignore` option.

        Hope that pep257 will add error codes soon.
        """
        options = Bunch(
            pep257_ignore=['First line should end with a period.'])
        checker = self.makeChecker(
            self.pep257_without_docstrings, options=options)

        checker.check_pep257()

        self.assertEqual(
            [(1, 'All modules should have docstrings.'), ],
            self.reporter.messages,
            )


class TestText(CheckerTestCase, TestAnyTextMixin):
    """Verify text integration."""

    def test_with_tabs(self):
        # pep8 checks this.
        pass

    def test_trailing_whitespace(self):
        # pep8 checks this.
        pass

    def test_long_length(self):
        # pep8 checks this.
        pass

    def create_and_check(self, file_name, text, options=None):
        """Used by the TestAnyTextMixin tests."""
        checker = PythonChecker(file_name, text, self.reporter, options)
        checker.check_text()

    def test_code_without_issues(self):
        checker = PythonChecker('bogus', good_python, self.reporter)
        checker.check_text()
        self.assertEqual([], self.reporter.messages)

    def test_code_with_pdb(self):
        pdb_python = "import pdb; pdb." + "set_trace()"
        checker = PythonChecker('bogus', pdb_python, self.reporter)
        checker.check_text()
        self.assertEqual(
            [(1, 'Line contains a call to pdb.')], self.reporter.messages)

    def _test_encoding(self, python, expected_encoding='foo-encoding'):
        checker = PythonChecker(
            'bogus', python % dict(encoding=expected_encoding), self.reporter)
        checker.check_text()
        self.assertEqual(expected_encoding, checker.encoding)

    def test_pep0263_no_encoding(self):
        self._test_encoding("# First line\n# Second line\n\n", 'ascii')

    def test_pep0263_encoding_standard_coding(self):
        self._test_encoding("# coding=%(encoding)s\n")

    def test_pep0263_encoding_standard_encoding(self):
        self._test_encoding("# encoding=%(encoding)s\n")

    def test_pep0263_encoding_emacs(self):
        self._test_encoding("# -*- coding: %(encoding)s -*-\n")

    def test_pep0263_encoding_vim(self):
        self._test_encoding("# vim: set fileencoding=%(encoding)s :\n")

    def test_pep0263_encoding_2nd_line(self):
        self._test_encoding("# First line\n# coding=%(encoding)s\n\n")

    def test_code_utf8(self):
        utf8_python = "a = 'this is utf-8 [\u272a]'"
        checker = PythonChecker('bogus', utf8_python, self.reporter)
        checker.encoding = 'utf-8'
        checker.check_text()

    def test_code_ascii_is_not_utf8(self):
        utf8_python = "a = 'this is utf-8 [\u272a]'"
        checker = PythonChecker('bogus', utf8_python, self.reporter)
        checker.check_text()
        self.assertEqual(
            [(1, 'Non-ascii characer at position 21.')],
            self.reporter.messages)
