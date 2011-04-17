# Copyright (C) 2011 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from tempfile import NamedTemporaryFile

from pocketlint.formatcheck import PythonChecker
from pocketlint.tests import CheckerTestCase
from pocketlint.tests.test_text import TestAnyTextMixin


good_python = """\
class example:

    def __init__(self, value):
        print "Good night."
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


class TestPyflakes(CheckerTestCase):
    """Verify pyflakes integration."""

    def test_contrib_integration(self):
        from pocketlint.contrib.pyflakes.checker import messages
        self.assertTrue('pocketlint/contrib/' in messages.__file__)

    def test_code_without_issues(self):
        self.reporter.call_count = 0
        checker = PythonChecker('bogus', good_python, self.reporter)
        checker.check_flakes()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_code_with_SyntaxError(self):
        self.reporter.call_count = 0
        checker = PythonChecker(
            'bogus', bad_syntax_python, self.reporter)
        checker.check_flakes()
        expected = [(
            0, 'Could not compile; non-default argument follows '
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
        checker = PythonChecker('bogus', ugly_python, self.reporter)
        checker.check_flakes()
        self.assertEqual(
            [(3, "undefined name 'b'"),
            (3, "local variable 'a' is assigned to but never used")],
            self.reporter.messages)
        self.assertEqual(2, self.reporter.call_count)


class TestPEP8(CheckerTestCase):
    """Verify PEP8 integration."""

    def setUp(self):
        super(TestPEP8, self).setUp()
        self.file = NamedTemporaryFile(prefix='pocketlint_')

    def tearDown(self):
        self.file.close()

    def test_code_without_issues(self):
        self.file.write(good_python)
        self.file.flush()
        checker = PythonChecker(
            self.file.name, good_python, self.reporter)
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)

    def test_bad_syntax(self):
        self.file.write(bad_syntax2_python)
        self.file.flush()
        checker = PythonChecker(
            self.file.name, ugly_style_python, self.reporter)
        checker.check_pep8()
        self.assertEqual(
            [(4, 'EOF in multi-line statement')],
            self.reporter.messages)

    def test_code_with_issues(self):
        self.file.write(ugly_style_python)
        self.file.flush()
        checker = PythonChecker(
            self.file.name, ugly_style_python, self.reporter)
        checker.check_pep8()
        self.assertEqual(
            [(4, 'E222 multiple spaces after operator')],
            self.reporter.messages)

    def test_code_with_comments(self):
        self.file.write(ugly_style_lines_python)
        self.file.flush()
        checker = PythonChecker(
            self.file.name, ugly_style_lines_python, self.reporter)
        checker.check_pep8()
        self.assertEqual([], self.reporter.messages)


class TestText(CheckerTestCase, TestAnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text):
        """Used by the TestAnyTextMixin tests."""
        checker = PythonChecker(file_name, text, self.reporter)
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

    def test_code_is_utf8(self):
        utf8_python = u"a = 'this is utf-8 [\u272a]'"
        checker = PythonChecker('bogus', utf8_python, self.reporter)
        checker.is_utf8 = True
        checker.check_text()

    def test_code_ascii_is_not_is_utf8(self):
        utf8_python = u"a = 'this is utf-8 [\u272a]'"
        checker = PythonChecker('bogus', utf8_python, self.reporter)
        checker.check_text()
        self.assertEqual(
            [(1, 'Non-ascii characer at position 21.')],
            self.reporter.messages)
