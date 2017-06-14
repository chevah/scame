'''Tests for ReStructuredTextChecker.'''

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from scame.formatcheck import ReStructuredTextChecker
from scame.tests import CheckerTestCase

# This is a valid rst content.
# This comment is here so that the content starts at line 11
# and make it easier to identify errors in tests.
# Just add 10 to the reported line number.
#
valid_rst_content = '''\
=============
First section
=============

Text *for* first **section**.


--------------------
Second emtpy section
--------------------


Third section
^^^^^^^^^^^^^

Paragrhap for
third section `with link<http://my.home>`_.

::

  Literal block1.

  Literal block paragraph.


| Line blocks are useful for addresses,
| verse, and adornment-free lists.


.. _section-permalink:

Another Section with predefined link
------------------------------------

>>> print "This is a doctest block."
... with a line continuation
This is a doctest block.

A grid table.

+------------+------------+-----------+
| Header 1   | Header 2   | Header 3  |
+============+============+===========+
| body row 1 | column 2   | column 3  |
+------------+------------+-----------+
| body row 2 | Cells may span columns.|
+------------+------------+-----------+
| body row 3 | Cells may  | - Cells   |
+------------+ span rows. | - contain |
| body row 4 |            | - blocks. |
+------------+------------+-----------+

A simple table.

=====  =====  ======
   Inputs     Output
------------  ------
  A      B    A or B
=====  =====  ======
False  False  False
True   False  True
False  True   True
True   True   True
=====  =====  ======

A transition marker is a horizontal line
of 4 or more repeated punctuation
characters.

------------

A transition should not begin or end a
section or document, nor should two
transitions be immediately adjacent.

Footnote references, like [5]_.
Note that footnotes may get
rearranged, e.g., to the bottom of
the "page".

.. [5] A numerical footnote. Note
   there's no colon after the ``]``.

External hyperlinks, like Python_.
.. _Python: http://www.python.org/

For instance:

.. image:: images/ball1.gif

The |biohazard| symbol must be used on containers used to dispose of
medical waste.

.. |biohazard| image:: biohazard.png

.. This text will not be shown
   (but, for instance, in HTML might be
   rendered as an HTML comment)
'''
# The last line from multi line string is a bit hard to visualize,
# but it is there.


class TestReStructuredTextChecker(CheckerTestCase):
    """Verify reStructuredTextChecker checking."""

    def test_empty_file(self):
        self.reporter.call_count = 0
        content = ('')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_valid_content(self):
        self.reporter.call_count = 0
        checker = ReStructuredTextChecker(
            'bogus', valid_rst_content, self.reporter)
        checker.check()
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_no_empty_last_line(self):
        self.reporter.call_count = 0
        content = (
            'Some first line\n'
            'the second and last line witout newline')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_empty_last_line(2)
        expected = [(
            2, 'File does not ends with an empty line.')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_multiple_empty_last_lines(self):
        self.reporter.call_count = 0
        content = (
            'Some first line\n'
            'the second and last\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_empty_last_line(3)
        expected = [(
            3, 'File does not ends with an empty line.')]
        self.assertEqual(expected, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_isTransition_good(self):
        content = (
            '\n'
            '----\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isTransition(1)
        self.assertTrue(result)

    def test_isTransition_short_line(self):
        content = (
            '\n'
            '---\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isTransition(1)
        self.assertFalse(result)

    def test_isTransition_short_file(self):
        content = (
            '\n'
            '----\n'
            '')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isTransition(1)
        self.assertFalse(result)

    def test_isTransition_false(self):
        content = (
            '\n'
            '----\n'
            'some\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isTransition(1)
        self.assertFalse(result)

        content = (
            'some\n'
            '----\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isTransition(1)
        self.assertFalse(result)

    def test_check_transitions_good(self):
        content = (
            'some text\n'
            '\n'
            '----\n'
            '\n'
            'some text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_transition(2)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_transitions_bad_spacing_before(self):
        content = (
            'some text\n'
            '\n'
            '\n'
            '----\n'
            '\n'
            'some text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_transition(3)
        expect = [(
            4, 'Transition markers should be bounded by single empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_transitions_bad_spacing_after(self):
        content = (
            'some text\n'
            '\n'
            '----\n'
            '\n'
            '\n'
            'some text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_transition(2)
        expect = [(
            3, 'Transition markers should be bounded by single empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_transitions_bad_spacing_both(self):
        content = (
            'some text\n'
            '\n'
            '\n'
            '----\n'
            '\n'
            '\n'
            'some text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_transition(3)
        expect = [(
            4, 'Transition markers should be bounded by single empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_isSectionDelimiter_short_file(self):
        content = (
            'Something'
            '---------\n'
            '')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isSectionDelimiter(1)
        self.assertFalse(result)

    def test_isSectionDelimiter_short_line(self):
        content = (
            'Som'
            '---\n'
            '')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isSectionDelimiter(1)
        self.assertFalse(result)

    def test_isSectionDelimiter_table(self):
        content = (
            '---- ----'
            'Row1 Row1'
            '---- ----\n'
            '')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isSectionDelimiter(0)
        self.assertFalse(result)
        result = checker.isSectionDelimiter(2)
        self.assertFalse(result)

    def test_isSectionDelimiter_good(self):
        content = (
            'Section\n'
            '-------\n'
            'some text')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isSectionDelimiter(1)
        self.assertTrue(result)

    def test_isSectionDelimiter_good_bounded_start_of_file(self):
        content = (
            '=======\n'
            'Section\n'
            '=======\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        result = checker.isSectionDelimiter(0)
        self.assertTrue(result)
        result = checker.isSectionDelimiter(2)
        self.assertTrue(result)

    def test_check_section_delimiter_bounded(self):
        content = (
            'some text\n'
            '\n'
            '\n'
            '=======\n'
            'Section\n'
            '=======\n'
            '\n'
            'some text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(3)
        checker.check_section_delimiter(5)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_section_delimiter_bad_marker_length(self):
        content = (
            'Section\n'
            '------\n'
            '\n'
            'some text\n'
            'other text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        expect = [(2, 'Section marker has wrong length.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_delimiter_bad_length_both_markers(self):
        content = (
            '---------\n'
            'Section\n'
            '---------\n'
            '\n'
            'some text\n'
            'other text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(0)
        checker.check_section_delimiter(2)
        expect = [(1, 'Section marker has wrong length.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_before_space_good_start_both(self):
        content = (
            '-------\n'
            'Section\n'
            '-------\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(0)
        checker.check_section_delimiter(2)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_section_before_space_good_start_bottom(self):
        content = (
            'Section\n'
            '-------\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_section_before_space_bad_only_one_line_near_start(self):
        content = (
            '\n'
            'Section\n'
            '-------\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(2)
        expect = [(3, 'Section should be divided by 2 empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_before_space_bad_only_one_line(self):
        content = (
            'end of previous section.\n'
            '\n'
            'Section\n'
            '-------\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(3)
        expect = [(4, 'Section should be divided by 2 empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_before_space_multiple_empty_lines(self):
        content = (
            'end of previous section.\n'
            '\n'
            '\n'
            '\n'
            'Section\n'
            '-------\n'
            '\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(5)
        expect = [(6, 'Section should be divided by 2 empty lines.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_after_space_last_line(self):
        content = (
            'Section\n'
            '-------\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_section_after_space_bad(self):
        content = (
            'Section\n'
            '-------\n'
            'Paragraph start.\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        expect = [(2, 'Section title should be followed by 1 empty line.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_after_space_too_many_empty_lines(self):
        content = (
            'Section\n'
            '-------\n'
            '\n'
            '\n'
            'Paragraph start.\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        expect = [(2, 'Section title should be followed by 1 empty line.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(1, self.reporter.call_count)

    def test_check_section_empty_section_next_section_only_bottom(self):
        content = (
            'Emtpy Section\n'
            '=============\n'
            '\n'
            '\n'
            'Another Section\n'
            '---------------\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def test_check_section_empty_section_next_section_both_markers(self):
        content = (
            'Emtpy Section\n'
            '=============\n'
            '\n'
            '\n'
            '---------------\n'
            'Another Section\n'
            '---------------\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_section_delimiter(1)
        self.assertEqual([], self.reporter.messages)
        self.assertEqual(0, self.reporter.call_count)

    def disable_check_section_delimiter_both_markers_not_sync(self):
        # When both top and bottom markers are used, and they don't have
        # the same size, they are interpreted as separate markers.
        content = (
            '------\n'
            'Section\n'
            '--------\n'
            '\n'
            'some text\n'
            'other text\n')
        checker = ReStructuredTextChecker('bogus', content, self.reporter)
        checker.check_lines()
        expect = [
            (1, 'Section marker has wrong length.'),
            (1, 'Section title should be followed by 1 empty line.'),
            (3, 'Section marker has wrong length.')]
        self.assertEqual(expect, self.reporter.messages)
        self.assertEqual(3, self.reporter.call_count)
