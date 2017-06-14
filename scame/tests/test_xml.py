# Copyright (C) 2011-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from scame.formatcheck import XMLChecker
from scame.tests import CheckerTestCase
from scame.tests.test_text import AnyTextMixin


good_markup = """\
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<root>
  <child>hello world</child>
</root>
"""

missing_dtd_and_xml = """\
<root>
  <child>hello&nbsp;world</child>
</root>
"""

html5_dtd_and_entity = """\
<!DOCTYPE html>
<html>
  <title>hello&nbsp;world</title>
</html>
"""

ill_formed_markup = """\
<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<root>
  <child>hello world<
</root>
"""

utf8_xml_markup = """\
\xa0<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<root>
  <child>hello world</child>
</root>
"""

utf8_html_markup = """\
\xa0<!DOCTYPE html PUBLIC
  "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
  </head>
  <body>
      <p>hello world</p>
  </body>
</html>
"""

zpt_without_namespace = """\
<metal:root>
  <p tal:condition="has_hello">hello&nbsp;world</p>
</metal:root>
"""


class TestXML(CheckerTestCase):
    """Verify XML integration."""

    def test_good_markup(self):
        checker = XMLChecker('bogus', good_markup, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_missing_dtd_and_xml(self):
        checker = XMLChecker('bogus', missing_dtd_and_xml, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_html5_dtd(self):
        checker = XMLChecker('bogus', html5_dtd_and_entity, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_zpt_without_namespace(self):
        checker = XMLChecker('bogus.pt', zpt_without_namespace, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_ill_formed_markup(self):
        checker = XMLChecker('bogus', ill_formed_markup, self.reporter)
        checker.check()
        self.assertEqual(
            [(3, 'not well-formed (invalid token)')], self.reporter.messages)

    def test_utf8_xml_markup(self):
        checker = XMLChecker('bogus', utf8_xml_markup, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)

    def test_utf8_html_markup(self):
        checker = XMLChecker('bogus', utf8_html_markup, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)


class TestText(CheckerTestCase, AnyTextMixin):
    """Verify text integration."""

    def create_and_check(self, file_name, text, options=None):
        """Used by the TestAnyTextMixin tests."""
        checker = XMLChecker(file_name, text, self.reporter, options)
        checker.check_text()

    def test_long_length(self):
        pass

    def test_with_tabs(self):
        pass
