# Copyright (C) 2009 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the GNU General Public License version 2
# (see the file COPYING).
"""Check for syntax and style problems."""

__metatype__ = type

__all__ = [
    'Reporter',
    'UniversalChecker',
    ]


import compiler
import os
from lxml import etree

from gdp.formatdoctest import DoctestReviewer

import pep8
from pyflakes.checker import Checker


class Reporter:
    """Common rules for checkers."""
    CONSOLE = object()
    FILE_LINES = object()

    def __init__(self, report_type, treeview=None):
        self.report_type = report_type
        self.file_lines_view = treeview
        self.treestore = self.file_lines_view.get_model()
        self.piter = None

    def __call__(self, line_no, message, icon=None,
                 base_dir=None, file_name=None):
        """Report a message."""
        if self.report_type == self.FILE_LINES:
            self._message_file_lines(
                line_no, message, icon=icon,
                base_dir=base_dir, file_name=file_name)
        else:
            self._message_console(
                line_no, message, icon=icon,
                base_dir=base_dir, file_name=file_name)

    def _message_console(self, line_no, message, icon=None,
                         base_dir=None, file_name=None):
        """Print the messages to the console."""
        print '%4s: %s' % line_no, message

    def _message_file_lines(self, line_no, message, icon=None,
                            base_dir=None, file_name=None):
        """Display the messages in the file_lines_view."""
        if self.piter is None:
            mime_type = 'gnome-mime-text'
            self.piter = self.treestore.append(
                None, (file_name, mime_type, 0, None, base_dir))
        self.treestore.append(
            self.piter, (file_name, icon, line_no, message, base_dir))


class BaseChecker:
    """Common rules for checkers.

    The Decedent must provide self.file_name and self.base_dir
    """

    def __init__(self, file_path, text, reporter=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        self.set_reporter(reporter=reporter)

    def set_reporter(self, reporter=None):
        """Set the reporter for messages."""
        if reporter is None:
            Reporter(Reporter.CONSOLE)
        self._reporter = reporter

    def message(self, line_no, message, icon=None,
                base_dir=None, file_name=None):
        """Report the message."""
        if base_dir is None:
            base_dir = self.base_dir
        if file_name is None:
            file_name = self.file_name
        self._reporter(
            line_no, message, icon=icon,
            base_dir=base_dir, file_name=file_name)

    def check(self):
        """Check the content."""
        raise NotImplementedError


class UniversalChecker(BaseChecker):
    """Check and reformat doctests."""

    def __init__(self, file_path, text=None, language=None, reporter=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        self.set_reporter(reporter=reporter)
        self.language = language
        self.file_lines_view = None

    def check(self):
        """Check the file syntax and style."""
        if self.language == 'python':
            PythonChecker(self.file_path, self.text, self._reporter).check()
        elif self.language == 'doctest':
            DoctestReviewer(self.text, self.file_path, self._reporter).check()
        elif self.language in ('xml', 'xslt', 'html', 'pt', 'docbook'):
            XMLChecker(self.file_path, self.text, self._reporter).check()
        else:
            AnyTextChecker(self.file_path, self.text, self._reporter).check()
        self._reporter.file_lines_view.expand_all()


class AnyTextChecker(BaseChecker):
    """Verify the text of the document."""

    def __init__(self, file_path, text, reporter=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        self.set_reporter(reporter=reporter)

    def check(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)

    def check_conflicts(self, line_no, line):
        """Check that there are no merge conflict markers."""
        if line.startswith('<<<<<<<'):
            self.message(line_no, 'File has conficts.', icon='errror')

    def check_length(self, line_no, line):
        """Check the length of the line."""
        if len(line) > 78:
            self.message(
                line_no, 'Line exceeds 78 characters.', icon='info')

    def check_trailing_whitespace(self, line_no, line):
        """Check for the presence of trailing whitespace in the line."""
        if line.endswith(' '):
            self.message(
                line_no, 'Line has trailing whitespace.', icon='info')


class XMLChecker(BaseChecker):
    """Check XML documents."""

    def check(self):
        """Check the syntax of the python code."""
        if self.text == '':
            return
        try:
            parser = etree.XMLParser(resolve_entities=False)
            root = etree.XML(self.text, parser)
        except:
            # The log is more important than the traceback.
            pass
        for error in parser.error_log:
            if error.message.startswith('Entity'):
                # XXX sinzui 2009-09-12 bug=267825, bug=410916: XMLParser
                # resolve_entities is not honoured. lxml does not support
                # loading the entities external to the document.
                continue
            self.message(error.line, error.message, icon='error')


class PythonChecker(BaseChecker):
    """Check python source code."""

    def check(self):
        """Check the syntax of the python code."""
        if self.text == '':
            return
        self.check_flakes()
        self.check_pep8()

    def check_flakes(self):
        """Check compilation and syntax."""
        try:
            tree = compiler.parse(self.text)
        except (SyntaxError, IndentationError), exc:
            (line_no, offset, line) = exc[1][1:]
            message = 'Could not compile offset %s: %s' % (
                offset, line.strip())
            self.message(line_no, message, icon='error')
        else:
            warnings = Checker(tree)
            for warning in warnings.messages:
                dummy, line_no, message = str(warning).split(':')
                self.message(int(line_no), message.strip(), icon='error')

    def check_pep8(self):
        """Check style."""
        try:
            # Monkey patch pep8 for direct access to the messages.
            original_report_error = pep8.Checker.report_error

            def pep8_report_error(ignore, line_no, offset, message, check):
                self.message(line_no, message, icon='info')

            pep8.Checker.report_error = pep8_report_error
            pep8.process_options([self.file_path])
            pep8.Checker(self.file_path).check_all()
        finally:
            Checker.report_error = original_report_error
