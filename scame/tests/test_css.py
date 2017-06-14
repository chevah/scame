# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from scame.formatcheck import (
    CSSChecker,
    HAS_CSSUTILS,
    IS_PY3,
    )
from scame.tests import CheckerTestCase
from scame.tests.test_text import AnyTextMixin


good_css = """\
body {
    font-family: Ubuntu;
    }
"""

css3 = """\
body {
    margin: 24px;
    margin: 2rem;
    }
"""

ill_formed_property = """\
body {
    font-family: Ubuntu
    color: #333;
    }
"""

invalid_value = """\
body {
    color: speckled;
    }
"""


class TestCSS(CheckerTestCase):
    """Verify CSS integration."""

    def test_good_css(self):
        checker = CSSChecker('bogus', good_css, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_css3(self):
        checker = CSSChecker('bogus', css3, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_ill_formed_property(self):
        if not HAS_CSSUTILS:
            return
        checker = CSSChecker('bogus', ill_formed_property, self.reporter)
        checker.check_cssutils()
        qualifier = '' if IS_PY3 else 'u'
        self.assertIn(
            (3, "PropertyValue: No match: 'CHAR', %s':'" % qualifier),
            self.reporter.messages)
        self.assertIn(
            (0, 'PropertyValue: Unknown syntax or no value:  '
                'Ubuntu\n    color: #333'),
            self.reporter.messages)
        self.assertIn(
            (0, 'CSSStyleDeclaration: Syntax Error in Property: '
                'font-family: Ubuntu\n    color: #333'),
            self.reporter.messages)

    def test_invalid_value(self):
        if not HAS_CSSUTILS:
            return
        checker = CSSChecker('ballyhoo', invalid_value, self.reporter)
        checker.check_cssutils()
        message = (
            'Invalid value for "CSS Level 2.1" '
            'property: speckled: color')
        self.assertEqual(1, len(self.reporter.messages))
        message = self.reporter.messages[0]
        self.assertEqual(2, message[0])
        self.assertIn('Invalid value for', message[1])
        self.assertIn('property: speckled: color', message[1])

    def test_multiple_files(self):
        # The logging and handler for each instance is added and
        # removed between each call.
        if not HAS_CSSUTILS:
            return
        self.test_ill_formed_property()
        self.reporter.messages = []
        self.test_invalid_value()


class TestText(CheckerTestCase, AnyTextMixin):
    """
    Verify text integration.
    """

    def create_and_check(self, file_name, text, options=None):
        """Used by the TestAnyTextMixin tests."""
        checker = CSSChecker(file_name, text, self.reporter, options)
        checker.check_text()
