#!/usr/bin/python
# Copyright (C) 2009-2012 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).
"""Check for syntax and style problems."""

from __future__ import with_statement


__metaclass__ = type


__all__ = [
    'Reporter',
    'UniversalChecker',
    ]


import _ast
import htmlentitydefs
import logging
import mimetypes
import os
import re
import subprocess
import sys

from optparse import OptionParser
from StringIO import StringIO
from tokenize import TokenError
from xml.etree import ElementTree
try:
    from xml.etree.ElementTree import ParseError
    ParseError != '# Supress redefintion warning.'
except ImportError:
    # Python 2.6 and below.
    ParseError = object()
from xml.parsers.expat import ErrorString, ExpatError

from formatdoctest import DoctestReviewer

import contrib.pep8 as pep8
from contrib.cssccc import CSSCodingConventionChecker
from contrib.pyflakes.checker import Checker as PyFlakesChecker
try:
    import cssutils
    HAS_CSSUTILS = True
except ImportError:
    HAS_CSSUTILS = False


def find_exec(names):
    """Return the name of a GI enabled JS interpreter."""
    if os.name != 'posix':
        return None

    for name in names:
        js = subprocess.Popen(
            ['which', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        js_exec, ignore = js.communicate()
        if js.returncode == 0:
            return js_exec.strip()


JS = find_exec(['gjs', 'seed'])


DEFAULT_MAX_LENGTH = 80


class PocketLintPyFlakesChecker(PyFlakesChecker):
    '''PocketLint checker for pyflakes.

    This is here to work around some of the pyflakes problems.
    '''

    def __init__(self, tree, file_name='(none)', text=None):
        self.text = text
        if self.text:
            self.text = self.text.split('\n')
        super(PocketLintPyFlakesChecker, self).__init__(
            tree=tree, file_name=file_name)

    def report(self, messageClass, *args, **kwargs):
        '''Filter some errors not used in our project.'''
        line_no = args[0] - 1

        # Ignore explicit pyflakes:ignore requests.
        if self.text and self.text[line_no].find('pyflakes:ignore') >= 0:
            return

        self.messages.append(messageClass(self.file_name, *args, **kwargs))

    def NAME(self, node):
        '''Locate name. Ignore WindowsErrors.'''
        if node.id == 'WindowsError':
            return
        return super(PocketLintPyFlakesChecker, self).NAME(node)


class Reporter:
    """Common rules for checkers."""
    CONSOLE = object()
    FILE_LINES = object()
    COLLECTOR = object()

    def __init__(self, report_type, treeview=None):
        self.report_type = report_type
        self.file_lines_view = treeview
        if self.file_lines_view is not None:
            self.treestore = self.file_lines_view.get_model()
        self.piter = None
        self._last_file_name = None
        self.call_count = 0
        self.error_only = False
        self.messages = []

    def __call__(self, line_no, message, icon=None,
                 base_dir=None, file_name=None):
        """Report a message."""
        if self.error_only and icon != 'error':
            return
        self.call_count += 1
        args = (line_no, message, icon, base_dir, file_name)
        if self.report_type == self.FILE_LINES:
            self._message_file_lines(*args)
        elif self.report_type == self.COLLECTOR:
            self._message_collector(*args)
        else:
            self._message_console(*args)

    def _message_console(self, line_no, message, icon=None,
                         base_dir=None, file_name=None):
        """Print the messages to the console."""
        self._message_console_group(base_dir, file_name)
        print '    %4s: %s' % (line_no, message)

    def _message_console_group(self, base_dir, file_name):
        """Print the file name is it has not been seen yet."""
        source = (base_dir, file_name)
        if file_name is not None and source != self._last_file_name:
            self._last_file_name = source
            print '%s' % os.path.join('./', base_dir, file_name)

    def _message_file_lines(self, line_no, message, icon=None,
                            base_dir=None, file_name=None):
        """Display the messages in the file_lines_view."""
        if self.piter is None:
            mime_type = 'gnome-mime-text'
            self.piter = self.treestore.append(
                None, (file_name, mime_type, 0, None, base_dir))
        self.treestore.append(
            self.piter, (file_name, icon, line_no, message, base_dir))

    def _message_collector(self, line_no, message, icon=None,
                         base_dir=None, file_name=None):
        self._last_file_name = (base_dir, file_name)
        self.messages.append((line_no, message))


class Language:
    """Supported Language types."""
    TEXT = object()
    PYTHON = object()
    DOCTEST = object()
    CSS = object()
    JAVASCRIPT = object()
    SH = object()
    XML = object()
    XSLT = object()
    HTML = object()
    ZPT = object()
    ZCML = object()
    DOCBOOK = object()
    LOG = object()
    SQL = object()

    XML_LIKE = (XML, XSLT, HTML, ZPT, ZCML, DOCBOOK)

    mimetypes.add_type('application/x-zope-configuation', '.zcml')
    mimetypes.add_type('application/x-zope-page-template', '.pt')
    mimetypes.add_type('text/x-python-doctest', '.doctest')
    mimetypes.add_type('text/x-twisted-application', '.tac')
    mimetypes.add_type('text/x-log', '.log')
    mime_type_language = {
        'text/x-python': PYTHON,
        'text/x-twisted-application': PYTHON,
        'text/x-python-doctest': DOCTEST,
        'text/css': CSS,
        'text/html': HTML,
        'text/plain': TEXT,
        'text/x-sql': SQL,
        'text/x-log': LOG,
        'application/javascript': JAVASCRIPT,
        'application/xml': XML,
        'application/x-sh': SH,
        'application/x-zope-configuation': ZCML,
        'application/x-zope-page-template': ZPT,
        }
    doctest_pattern = re.compile(
        r'^.*(doc|test|stories).*/.*\.(txt|doctest)$')

    @staticmethod
    def get_language(file_path):
        """Return the language for the source."""
        # Doctests can easilly be mistyped, so it must be checked first.
        if Language.doctest_pattern.match(file_path):
            return Language.DOCTEST
        mime_type, encoding = mimetypes.guess_type(file_path)
        if mime_type is None:
            # This could be a very bad guess.
            return Language.TEXT
        elif mime_type in Language.mime_type_language:
            return Language.mime_type_language[mime_type]
        elif mime_type in Language.XML_LIKE:
            return Language.XML
        elif mime_type.endswith('+xml'):
            return Language.XML
        elif 'text/' in mime_type:
            return Language.TEXT
        else:
            return None

    @staticmethod
    def is_editable(file_path):
        """ Only search mime-types that are like sources can open.

        A fuzzy match of text/ or +xml is good, but some files types are
        unknown or described as application data.
        """
        return Language.get_language(file_path) is not None


class BaseChecker:
    """Common rules for checkers.

    The Decedent must provide self.file_name and self.base_dir
    """
    def __init__(self, file_path, text, reporter=None, options=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        self.set_reporter(reporter=reporter)
        self.options = options

    def set_reporter(self, reporter=None):
        """Set the reporter for messages."""
        if reporter is None:
            reporter = Reporter(Reporter.CONSOLE)
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

    @property
    def check_length_filter(self):
        '''Default filter used by default for checking line length.'''
        if self.options:
            return self.options.max_line_length
        else:
            return DEFAULT_MAX_LENGTH


class UniversalChecker(BaseChecker):
    """Check and reformat doctests."""

    def __init__(self, file_path, text,
                 language=None, reporter=None, options=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        self.set_reporter(reporter=reporter)
        self.language = language
        self.options = options
        self.file_lines_view = None

    def check(self):
        """Check the file syntax and style."""
        if self.language is Language.PYTHON:
            checker_class = PythonChecker
        elif self.language is Language.DOCTEST:
            checker_class = DoctestReviewer
        elif self.language is Language.CSS:
            checker_class = CSSChecker
        elif self.language in Language.XML_LIKE:
            checker_class = XMLChecker
        elif self.language is Language.JAVASCRIPT:
            checker_class = JavascriptChecker
        elif self.language is Language.LOG:
            # Log files are not source, but they are often in source code
            # trees.
            pass
        else:
            checker_class = AnyTextChecker
        checker = checker_class(
            self.file_path, self.text, self._reporter, self.options)
        checker.check()


class AnyTextMixin:
    """Common checks for many checkers."""

    def check_conflicts(self, line_no, line):
        """Check that there are no merge conflict markers."""
        if line.startswith('<' * 7) or line.startswith('>' * 7):
            self.message(line_no, 'File has conflicts.', icon='errror')

    def check_length(self, line_no, line):
        """Check the length of the line."""
        max_length = self.check_length_filter
        if len(line) > max_length:
            self.message(
                line_no, 'Line exceeds %s characters.' % max_length,
                icon='info')

    def check_trailing_whitespace(self, line_no, line):
        """Check for the presence of trailing whitespace in the line."""
        if line.endswith(' '):
            self.message(
                line_no, 'Line has trailing whitespace.', icon='info')

    def check_tab(self, line_no, line):
        """Check for the presence of tabs in the line."""
        if '\t' in line:
            self.message(
                line_no, 'Line contains a tab character.', icon='info')


class AnyTextChecker(BaseChecker, AnyTextMixin):
    """Verify the text of the document."""

    def check(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)


class SQLChecker(BaseChecker, AnyTextMixin):
    """Verify SQL style."""

    def check(self):
        """Call each line_method for each line in text."""
        # Consider http://code.google.com/p/python-sqlparse/ to verify
        # keywords and reformatting.
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_trailing_whitespace(line_no, line)
            self.check_tab(line_no, line)
            self.check_conflicts(line_no, line)


class XMLChecker(BaseChecker, AnyTextMixin):
    """Check XML documents."""

    xml_decl_pattern = re.compile(r'<\?xml .*?\?>')
    xhtml_doctype = u"""
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
          "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        """

    def check(self):
        """Check the syntax of the python code."""
        if self.text == '':
            return
        parser = ElementTree.XMLParser()
        parser.entity.update(htmlentitydefs.entitydefs)
        offset = 0
        try:
            # This is a sanity check to work with the true text....
            text = unicode(self.text.decode('utf-8').encode('utf-8'))
        except UnicodeDecodeError:
            # ...but this fallback is okay since this check is about markup.
            text = self.text.decode('ascii', 'ignore').encode('utf-8')
        if text.find('<!DOCTYPE') == -1:
            # Expat requires a doctype to honour parser.entity.
            offset = 3
            match = self.xml_decl_pattern.search(text)
            if match is None:
                text = self.xhtml_doctype + text
            else:
                start, end = match.span(0)
                text = text[:start] + self.xhtml_doctype + text[end:]
        try:
            ElementTree.parse(StringIO(text), parser)
        except (ExpatError, ParseError), error:
            if hasattr(error, 'code'):
                error_message = ErrorString(error.code)
                if hasattr(error, 'position') and error.position:
                    error_lineno, error_charno = error.position
                    error_lineno = error_lineno - offset
                elif error.lineno:
                    # Python 2.6-
                    error_lineno = error.lineno - offset
                else:
                    error_lineno = 0
            else:
                error_message, location = str(error).rsplit(':')
                error_lineno = int(location.split(',')[0].split()[1]) - offset
            self.message(error_lineno, error_message, icon='error')
        self.check_text()

    def check_text(self):
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)


class CSSReporterHandler(logging.Handler):
    """A logging handler that uses the checker to report issues."""

    error_pattern = re.compile(
        r'(?P<issue>[^(]+): \((?P<text>[^,]+, [^,]+), (?P<lineno>\d+).*')
    message_pattern = re.compile(
        r'(?P<issue>[^:]+:[^:]+): (?P<text>.*) (?P<lineno>0)$')

    def __init__(self, checker):
        logging.Handler.__init__(self, logging.INFO)
        self.checker = checker

    def handleError(self, record):
        pass

    def emit(self, record):
        if record.levelname == 'ERROR':
            icon = 'error'
        else:
            icon = 'info'
        matches = self.checker.message_pattern.search(record.getMessage())
        if matches is None:
            matches = self.error_pattern.search(record.getMessage())
        try:
            line_no = matches.group('lineno')
            message = "%s: %s" % (
                matches.group('issue'), matches.group('text'))
        except AttributeError:
            line_no = 0
            message = record.getMessage()
        self.checker.message(int(line_no), message, icon=icon)


class CSSChecker(BaseChecker, AnyTextMixin):
    """Check XML documents."""

    message_pattern = re.compile(
        r'[^ ]+ (?P<issue>.*) \[(?P<lineno>\d+):\d+: (?P<text>.+)\]')

    def check(self):
        """Check the syntax of the CSS code."""
        if self.text == '':
            return

        self.check_cssutils()
        self.check_text()
        # CSS coding conventoins checks should go last since they rely
        # on previous checks.
        self.check_css_coding_conventions()

    def check_cssutils(self):
        """Check the CSS code by parsing it using CSSUtils module."""
        if not HAS_CSSUTILS:
            return
        handler = CSSReporterHandler(self)
        log = logging.getLogger('pocket-lint')
        log.addHandler(handler)
        log.propagate = False
        parser = cssutils.CSSParser(
            log=log, loglevel=logging.INFO, raiseExceptions=False)
        parser.parseString(self.text)
        log.removeHandler(handler)

    def check_text(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_tab(line_no, line)

    def check_css_coding_conventions(self):
        """Check the input using CSS Coding Convention checker."""
        CSSCodingConventionChecker(self.text, logger=self.message).check()


class PythonChecker(BaseChecker, AnyTextMixin):
    """Check python source code."""

    # This regex is taken from PEP 0263.
    encoding_pattern = re.compile("coding[:=]\s*([-\w.]+)")

    def __init__(self, file_path, text, reporter=None, options=None):
        super(PythonChecker, self).__init__(
            file_path, text, reporter, options)
        self.encoding = 'ascii'

    def check(self):
        """Check the syntax of the python code."""
        if self.text == '':
            return
        self.check_text()
        self.check_flakes()
        self.check_pep8()

    def check_flakes(self):
        """Check compilation and syntax."""
        try:
            tree = compile(
                self.text, self.file_path, "exec", _ast.PyCF_ONLY_AST)
        except (SyntaxError, IndentationError), exc:
            line_no = exc.lineno or 0
            line = exc.text or ''
            explanation = 'Could not compile; %s' % exc.msg
            message = '%s: %s' % (explanation, line.strip())
            self.message(line_no, message, icon='error')
        else:
            warnings = PocketLintPyFlakesChecker(
                tree, file_name=self.file_path, text=self.text)
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
            original_max_line_length = pep8.MAX_LINE_LENGTH
            pep8.MAX_LINE_LENGTH = self.check_length_filter
            pep8.process_options([self.file_path])
            try:
                pep8.Checker(self.file_path).check_all()
            except TokenError, er:
                message, location = er.args
                self.message(location[0], message, icon='error')
            except IndentationError, er:
                message, location = er.args
                message = "%s: %s" % (message, location[3].strip())
                self.message(location[1], message, icon='error')
        finally:
            pep8.MAX_LINE_LENGTH = original_max_line_length
            pep8.Checker.report_error = original_report_error

    def check_text(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            if line_no in (1, 2):
                match = self.encoding_pattern.search(line)
                if match:
                    self.encoding = match.group(1).lower()
            self.check_pdb(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_ascii(line_no, line)

    def check_pdb(self, line_no, line):
        """Check the length of the line."""
        pdb_call = 'pdb.' + 'set_trace'
        if pdb_call in line:
            self.message(
                line_no, 'Line contains a call to pdb.', icon='error')

    @property
    def check_length_filter(self):
        # The pep8 lib counts from 0.
        if self.options:
            return self.options.max_line_length - 1
        else:
            return pep8.MAX_LINE_LENGTH

    def check_ascii(self, line_no, line):
        """Check that the line is ascii."""
        if self.encoding != 'ascii':
            return
        try:
            line.encode('ascii')
        except UnicodeEncodeError, error:
            self.message(
                line_no, 'Non-ascii characer at position %s.' % error.end,
                icon='error')


class JavascriptChecker(BaseChecker, AnyTextMixin):
    """Check python source code."""

    HERE = os.path.dirname(__file__)
    FULLJSLINT = os.path.join(HERE, 'contrib/fulljslint.js')
    JSREPORTER = os.path.join(HERE, 'jsreporter.js')

    def check(self):
        """Check the syntax of the javascript code."""
        if JS is None or self.text == '':
            return
        args = [JS, self.JSREPORTER, self.FULLJSLINT, self.file_path]
        jslint = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        issues, errors = jslint.communicate()
        issues = issues.strip()
        if issues:
            for issue in issues.splitlines():
                line_no, char_no_, message = issue.split('::')
                line_no = int(line_no)
                line_no -= 1
                self.message(line_no, message, icon='error')
        self.check_text()

    def check_debugger(self, line_no, line):
        """Check the length of the line."""
        debugger_call = 'debugger;'
        if debugger_call in line:
            self.message(
                line_no, 'Line contains a call to debugger.', icon='error')

    def check_text(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_debugger(line_no, line)
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_tab(line_no, line)


def get_option_parser():
    """Return the option parser for this program."""
    usage = "usage: %prog [options] file1 file2"
    parser = OptionParser(usage=usage)
    parser.add_option(
        "-v", "--verbose", action="store_true", dest="verbose",
        help="show errors and warngings.")
    parser.add_option(
        "-q", "--quiet", action="store_false", dest="verbose",
        help="Show errors only.")
    parser.add_option(
        "-f", "--format", dest="do_format", action="store_true",
        help="Reformat the doctest.")
    parser.add_option(
        "-i", "--interactive", dest="is_interactive", action="store_true",
        help="Approve each change.")
    parser.add_option(
        "-m", "--max-length", dest="max_line_length", type="int",
        help="Set the max line length (default %s)" % DEFAULT_MAX_LENGTH)
    parser.set_defaults(
        verbose=True,
        do_format=False,
        is_interactive=False,
        max_line_length=DEFAULT_MAX_LENGTH,
        )
    return parser


def check_sources(sources, options, reporter=None):
    if reporter is None:
        reporter = Reporter(Reporter.CONSOLE)
    reporter.call_count = 0
    for source in sources:
        file_path = os.path.normpath(source)
        if os.path.isdir(source) or not Language.is_editable(source):
            continue
        language = Language.get_language(file_path)
        with open(file_path) as file_:
            text = file_.read()
        if language is Language.DOCTEST and options.do_format:
            formatter = DoctestReviewer(text, file_path, reporter)
            formatter.format_and_save(options.is_interactive)
        checker = UniversalChecker(
            file_path, text, language, reporter, options=options)
        checker.check()
    return reporter.call_count


def main(argv=None):
    """Run the command line operations."""
    if argv is None:
        argv = sys.argv
    parser = get_option_parser()
    (options, sources) = parser.parse_args(args=argv[1:])
    # Handle standard args.
    if len(sources) == 0:
        parser.error("Expected file paths.")
    reporter = Reporter(Reporter.CONSOLE)
    reporter.error_only = not options.verbose
    return check_sources(sources, options, reporter)


if __name__ == '__main__':
    sys.exit(main())
