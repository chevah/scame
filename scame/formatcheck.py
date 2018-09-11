#!/usr/bin/python
# Copyright (C) 2009-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).
"""
Check for syntax and style problems.
"""

from __future__ import (
    absolute_import,
    unicode_literals,
    with_statement,
    )


__all__ = [
    'Reporter',
    'UniversalChecker',
    ]


import _ast
try:
    from io import StringIO
except ImportError:
    # Pything 2.7 and below
    from StringIO import StringIO  # pyflakes:noqa
    IS_PY = False

try:
    from html.entities import entitydefs
except ImportError:
    from htmlentitydefs import entitydefs  # pyflakes:noqa

try:
    import json
    HAS_JSON = True
except ImportError:
    try:
        from simplejson import json  # pyflakes:noqa
        HAS_JSON = True
    except ImportError:
        HAS_JSON = False

import logging
import mimetypes
import os
import re
import subprocess
import sys
from tokenize import TokenError
from xml.etree import ElementTree

try:
    from xml.etree.ElementTree import ParseError
except ImportError:
    # Python 2.6 and below.
    ParseError = object()  # pyflakes:noqa

from xml.parsers import expat

try:
    import cssutils
    HAS_CSSUTILS = True
except ImportError:
    HAS_CSSUTILS = False

from scame.reporter import (
    css_report_handler,
    Reporter,
    )


from scame.contrib.cssccc import CSSCodingConventionChecker
from pyflakes.checker import Checker as PyFlakesChecker

try:
    import closure_linter
    # Shut up the linter.
    closure_linter
except ImportError:
    closure_linter = None

IS_PY3 = True if sys.version_info >= (3,) else False


def find_exec(names):
    """Return the name of a GI enabled JS interpreter."""
    if os.name != 'posix':
        return None

    for name in names:
        js = subprocess.Popen(
            ['which', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        js_exec, ignore = js.communicate()
        if js.returncode == 0:
            return js_exec.decode('utf-8').strip()


JS = find_exec(['gjs', 'seed'])


DEFAULT_MAX_LENGTH = 80


if IS_PY3:
    def u(string):
        if isinstance(string, str):
            return string
        else:
            return str(string.decode('utf-8', 'ignore'))

    unicode = object()
else:
    def u(string):  # pyflakes:noqa
        if isinstance(string, unicode):
            return string
        try:
            # This is a sanity check to work with the true text...
            return string.decode('utf-8')
        except UnicodeDecodeError:
            # ...but this fallback is okay since this comtemt.
            return string.decode('utf-8', 'ignore')


class PocketLintPyFlakesChecker(PyFlakesChecker):
    '''PocketLint checker for pyflakes.

    This is here to work around some of the pyflakes problems.
    '''

    def __init__(self, tree, file_path='(none)', text=None):
        self.text = text
        if self.text:
            self.text = self.text.split('\n')
        super(PocketLintPyFlakesChecker, self).__init__(
            tree=tree, filename=file_path)

    @property
    def file_path(self):
        '''Alias for consistency with the rest of pocketlint.'''
        return self.filename

    def report(self, messageClass, *args, **kwargs):
        '''Filter some errors not used in our project.'''
        self.messages.append(messageClass(self.file_path, *args, **kwargs))

    def NAME(self, node):
        '''Locate name. Ignore WindowsErrors.'''
        if node.id == 'WindowsError':
            return
        return super(PocketLintPyFlakesChecker, self).NAME(node)


class Language(object):
    """Supported Language types."""
    TEXT = object()
    PYTHON = object()
    CSS = object()
    JAVASCRIPT = object()
    JSON = object()
    SH = object()
    XML = object()
    XSLT = object()
    HTML = object()
    ZPT = object()
    ZCML = object()
    DOCBOOK = object()
    LOG = object()
    SQL = object()
    RESTRUCTUREDTEXT = object()

    XML_LIKE = (XML, XSLT, HTML, ZPT, ZCML, DOCBOOK)

    # Sorted after extension.
    mimetypes.add_type('text/plain', '.bat')
    mimetypes.add_type('text/css', '.css')
    mimetypes.add_type('text/html', '.html')
    mimetypes.add_type('image/x-icon', '.ico')
    mimetypes.add_type('text/plain', '.ini')
    mimetypes.add_type('application/javascript', '.js')
    mimetypes.add_type('application/json', '.json')
    mimetypes.add_type('text/x-log', '.log')
    mimetypes.add_type('application/x-zope-page-template', '.pt')
    mimetypes.add_type('text/x-python', '.py')
    mimetypes.add_type('text/x-rst', '.rst')
    mimetypes.add_type('text/x-sh', '.sh')
    mimetypes.add_type('text/x-sql', '.sql')
    mimetypes.add_type('text/x-twisted-application', '.tac')
    mimetypes.add_type('text/plain', '.txt')
    mimetypes.add_type('application/x-zope-configuation', '.zcml')

    # Sorted after content type.
    mime_type_language = {
        'application/javascript': JAVASCRIPT,
        'application/json': JSON,
        'application/xml': XML,
        'application/x-sh': SH,
        'application/x-zope-configuration': ZCML,
        'application/x-zope-page-template': ZPT,
        'text/css': CSS,
        'text/html': HTML,
        'text/plain': TEXT,
        'text/x-log': LOG,
        'text/x-python': PYTHON,
        'text/x-rst': RESTRUCTUREDTEXT,
        'text/x-sql': SQL,
        'text/x-twisted-application': PYTHON,
        }

    @staticmethod
    def get_language(file_path):
        """Return the language for the source."""
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


class ScameOptions(object):
    """
    Default options used by `scame`.

    The configuration options are accessed via a `get` method with takes a
    path as argument so you can have different options based on different
    paths.
    """

    def __init__(self):
        self._max_line_length = 0

        self.verbose = True
        self.diff_branch = None

        self.regex_line = []

        self.scope = {
            # Paths to be included in the report.
            'include': [],
            # List of regex for paths to be excluded.
            'exclude': [],
            }

        self.pyflakes = {
            'enabled': True,
            }

        self.mccabe = {
            'enabled': False,
            'max_complexity': -1
            }

        self.chevah_js_linter = {
            # Disabled by default, since jslint is the default linter.
            'enabled': False,
            # List of errors to ignore.
            # Ex 110 is line to long which is already provided by pocket-lint.
            'ignore': [110],
            # Extra flags to pass to linter.
            'flags': []
            }

        # See pycodestyle.StyleGuide for available options.
        self.pycodestyle = {
            'enabled': False,  # Removed when passed to pycodestyle.
            'max_line_length': 78,
            'hang_closing': False,
            }

        # See bandit.cli.main profile usage.
        # See bandit -h for the list of available tests.
        self.bandit = {
            'enabled': False,
            # -t TESTS, --tests TESTS
            'include': [],
            # -s SKIPS, --skip SKIPS
            'exclude': [],
            }
        # See pylint.lint.PyLinter.make_options
        self.pylint = {
            # Removed when passed to pylint.
            'enabled': False,
            # --rcfile=<file>
            'rcfile': None,
            # --py3k
            'py3k': False,
            # -e <msg ids>, --enable=<msg ids>
            # Ignored when rcfile is used.
            'enable': [],
            # -d <msg ids>, --disable=<msg ids>
            # Ignored when rcfile is used.
            'disable': [],
            }

    def get(self, option, path=None):
        """
        Return the value of "option" configuration.
        """
        return getattr(self, option)

    @property
    def max_line_length(self):
        return self._max_line_length

    @max_line_length.setter
    def max_line_length(self, value):
        self._max_line_length = value
        self.pycodestyle['max_line_length'] = value - 1


class BaseChecker(object):
    """Common rules for checkers.

    The Decedent must provide self.file_name and self.base_dir
    """
    # Marker use to signal that errors should be ignored.
    _IGNORE_MARKER = '  # noqa'
    REENCODE = True

    def __init__(self, file_path, text, reporter=None, options=None):
        self.file_path = file_path
        self.base_dir = os.path.dirname(file_path)
        self.file_name = os.path.basename(file_path)
        self.text = text
        if self.REENCODE:
            self.text = u(text)
        self._lines = self.text.split('\n')
        self.set_reporter(reporter=reporter)

        if not options:
            options = ScameOptions()
        self.options = options

    def set_reporter(self, reporter=None):
        """Set the reporter for messages."""
        if reporter is None:
            reporter = Reporter(Reporter.CONSOLE)
        self._reporter = reporter

    def message(
        self, line_no, message, icon=None,
        base_dir=None, file_name=None, category=None,
        code=None,
            ):
        """
        Report the message.
        """
        if base_dir is None:
            base_dir = self.base_dir
        if file_name is None:
            file_name = self.file_name

        if self._isExceptedLine(self._lines[line_no - 1], category, code):
            return

        self._reporter(
            line_no, message,
            icon=icon,
            base_dir=base_dir,
            file_name=file_name,
            category=category,
            )

    def _isExceptedLine(self, line, category, code):
        """
        Return `True` if line should be excepted.

        Any error can be excepted using the MARKER in the line.
        A category can be ignored using MARKER:CATEGORY
        A code from a category can be ignored using MARKER:CATEGORY=ID1,ID
        """
        if self._IGNORE_MARKER not in line:
            # Not an excepted line.
            return False

        comment = line

        if comment.find(self._IGNORE_MARKER + ':') == -1:
            # We have a generic exception.
            return True

        if not category:
            # This is a tagged exception but the checker has not advertised
            # a category.
            return False

        if comment.find('%s:%s' % (self._IGNORE_MARKER, category)) == -1:
            # Not this category.
            return False
        else:
            # We have a tagged exception
            return True

    def check(self):
        """Check the content."""
        raise NotImplementedError

    @property
    def check_length_filter(self):
        '''Default filter used by default for checking line length.'''
        max_line_length = self.options.get('max_line_length', self.file_path)
        if max_line_length:
            return max_line_length
        else:
            return DEFAULT_MAX_LENGTH


class UniversalChecker(BaseChecker):
    """Check and reformat source files."""

    def __init__(self, file_path, text,
                 language=None, reporter=None, options=None):
        super(UniversalChecker, self).__init__(
            file_path=file_path,
            text=text,
            reporter=reporter,
            options=options,
            )
        self.language = language
        self.file_lines_view = None

    def check(self):
        """Check the file syntax and style."""
        if self.language is Language.PYTHON:
            checker_class = PythonChecker
        elif self.language is Language.CSS:
            checker_class = CSSChecker
        elif self.language in Language.XML_LIKE:
            checker_class = XMLChecker
        elif self.language is Language.JAVASCRIPT:
            checker_class = JavascriptChecker
        elif self.language is Language.JSON:
            checker_class = JSONChecker
        elif self.language is Language.RESTRUCTUREDTEXT:
            checker_class = ReStructuredTextChecker
        elif self.language is Language.LOG:
            # Log files are not source, but they are often in source code
            # trees.
            return
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
            # Ignore if line is long due to an URL.
            if 'http://' in line or 'https://' in line:
                return
            self.message(
                line_no, 'Line exceeds %s characters.' % max_length,
                category='text',
                icon='info',
                )

    def check_trailing_whitespace(self, line_no, line):
        """Check for the presence of trailing whitespace in the line."""
        if line.endswith(' '):
            self.message(
                line_no,
                'Line has trailing whitespace.',
                category='text',
                icon='info',
                )

    def check_tab(self, line_no, line):
        """Check for the presence of tabs in the line."""
        if '\t' in line:
            self.message(
                line_no,
                'Line contains a tab character.',
                category='text',
                icon='info',
                )

    def check_windows_endlines(self):
        """Check that file does not contains Windows newlines."""
        if self.text.find('\r\n') != -1:
            self.message(
                0,
                'File contains Windows new lines.',
                category='text',
                icon='info',
                )

    def check_empty_last_line(self, total_lines):
        """Check the files ends with an one empty line.

        This will avoid merge conflicts.
        """
        if self.text[-1] != '\n' or self.text[-2:] == '\n\n':
            self.message(
                total_lines,
                'File does not ends with an empty line.',
                category='text',
                icon='info',
                )

    def check_regex_line(self, line_no, line):
        """
        Check that line does not match the regular expression.

        This can be used for custom checks.
        """
        regex_line = self.options.get('regex_line', self.file_path)
        for pattern, message in regex_line:
            if re.search(pattern, line):
                self.message(
                    line_no,
                    'Line contains flagged text. %s' % (message),
                    icon='info',
                    category='regex',
                    )


class AnyTextChecker(BaseChecker, AnyTextMixin):
    """Verify the text of the document."""

    def check(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_regex_line(line_no, line)

        self.check_windows_endlines()


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
            self.check_regex_line(line_no, line)

        self.check_windows_endlines()


class FastTreeBuilder(ElementTree.TreeBuilder):

    def _flush(self):
        if self._data:
            if self._last is not None:
                # Ensure all text is ascii; the data is never written back.
                text = ''.join([b for b in str(self._data) if ord(b) < 128])
                if self._tail:
                    assert self._last.tail is None, "internal error (tail)"
                    self._last.tail = text
                else:
                    assert self._last.text is None, "internal error (text)"
                    self._last.text = text
            self._data = []


class FastParser(object):
    """A simple and pure-python parser that checks well-formedness.

    This parser works in py 2 and 3. It handles entities and ignores
    namespaces. This parser works with python ElementTree.
    """

    def __init__(self, html=0, target=None, encoding=None):
        parser = expat.ParserCreate(encoding, None)
        target = FastTreeBuilder()
        self.parser = parser
        self.target = target
        self._error = expat.error
        self._names = {}  # Name memo cache
        parser.DefaultHandlerExpand = self._default
        parser.StartElementHandler = target.start
        parser.EndElementHandler = target.end
        parser.CharacterDataHandler = target.data
        parser.buffer_text = 1
        # Py3, but not Py2.
        # parser.ordered_attributes = 1
        # parser.specified_attributes = 1
        self._doctype = None
        self.entity = dict(entitydefs)
        self.version = "Expat %d.%d.%d" % expat.version_info

    def _default(self, text):
        prefix = text[:1]
        if prefix == "&":
            # Deal with undefined entities.
            data_handler = self.target.data
            try:
                data_handler(self.entity[text[1:-1]])
            except KeyError:
                err = expat.error(
                    "undefined entity %s: line %d, column %d" %
                    (text, self.parser.ErrorLineNumber,
                     self.parser.ErrorColumnNumber))
                err.code = 11  # XML_ERROR_UNDEFINED_ENTITY
                err.lineno = self.parser.ErrorLineNumber
                err.offset = self.parser.ErrorColumnNumber
                raise err

    def _raiseerror(self, value):
        err = ParseError(value)
        err.code = value.code
        err.position = value.lineno, value.offset
        raise err

    def feed(self, data):
        try:
            self.parser.Parse(data, 0)
        except self._error as v:
            self._raiseerror(v)

    def close(self):
        try:
            self.parser.Parse('', 1)   # End of data.
        except self._error as v:
            self._raiseerror(v)
        self.target.close()


class XMLChecker(BaseChecker, AnyTextMixin):
    """Check XML documents."""

    xml_decl_pattern = re.compile(r'<\?xml .*?\?>')
    xhtml_doctype = (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">')
    non_ns_types = (Language.ZPT, Language.ZCML)

    def check(self):
        """Check the syntax of the python code."""
        # Reconcile the text and Expat checker text requriements.
        if self.text == '':
            return
        parser = FastParser()
        offset = 0
        # The expat parser seems to be assuming ascii even when
        # XMLParser(encoding='utf-8') is used above.
        text = self.text.encode('utf-8').decode('ascii', 'ignore')
        if text.find('<!DOCTYPE') == -1:
            # Expat requires a doctype to honour parser.entity.
            offset = 1
            match = self.xml_decl_pattern.search(text)
            if match is None:
                text = self.xhtml_doctype + '\n' + text
            else:
                start, end = match.span(0)
                text = text[:start] + self.xhtml_doctype + '\n' + text[end:]
        elif text.find('<!DOCTYPE html>') != -1:
            text = text.replace('<!DOCTYPE html>', self.xhtml_doctype)
        try:
            ElementTree.parse(StringIO(text), parser)
        except (expat.ExpatError, ParseError) as error:
            if hasattr(error, 'code'):
                error_message = expat.ErrorString(error.code)
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
            self.message(
                error_lineno,
                error_message,
                category='xml',
                icon='error',
                )
        self.check_text()
        self.check_windows_endlines()

    def check_text(self):
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_regex_line(line_no, line)


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
        self.check_windows_endlines()
        # CSS coding conventoins checks should go last since they rely
        # on previous checks.
        self.check_css_coding_conventions()

    def check_cssutils(self):
        """Check the CSS code by parsing it using CSSUtils module."""
        if not HAS_CSSUTILS:
            return
        with css_report_handler(self, 'pocket-lint') as log:
            parser = cssutils.CSSParser(
                log=log, loglevel=logging.INFO, raiseExceptions=False)
            parser.parseString(self.text)

    def check_text(self):
        """Call each line_method for each line in text."""
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_regex_line(line_no, line)
            self.check_tab(line_no, line)

    def check_css_coding_conventions(self):
        """Check the input using CSS Coding Convention checker."""
        CSSCodingConventionChecker(self.text, logger=self.message).check()


class BanditPocketLintConfig(object):
    """
    A configuration with always triggers the default config.
    """
    def get_option(self, name):
        return None


class PythonChecker(BaseChecker, AnyTextMixin):
    """Check python source code."""

    REENCODE = False

    # This regex is taken from PEP 0263.
    encoding_pattern = re.compile("coding[:=]\s*([-\w.]+)")

    def __init__(self, file_path, text, reporter=None, options=None):
        super(PythonChecker, self).__init__(
            file_path, text, reporter, options)
        self.encoding = 'ascii'
        # Last compiled tree.
        self._compiled_tree = None
        # Placeholder config for bandit. Does nothing special for now.
        self._bandit_config = BanditPocketLintConfig()

    def check(self):
        """Check the syntax of the python code."""
        if self.text == '':
            return
        self.check_text()
        self.check_windows_endlines()

        try:
            # Compile the source code only once.
            self._compiled_tree = compile(
                self.text.encode(self.encoding),
                self.file_path,
                "exec",
                _ast.PyCF_ONLY_AST,
                )
        except (SyntaxError, IndentationError) as exc:
            # Failed to compile the source code.
            line_no = exc.lineno or 0
            line = exc.text or ''
            explanation = 'Could not compile; %s' % exc.msg
            message = '%s: %s' % (explanation, line.strip())
            self.message(line_no, message, icon='error')
            self._compiled_tree = None

        # pyflakes should be first as it will try to compile
        self.check_flakes()
        self.check_pycodestyle()
        self.check_bandit()
        self.check_pylint()
        self.check_complexity()

        # Reset the tree.
        self._compiled_tree = None

    def check_flakes(self):
        """Check compilation and syntax."""
        if not self._compiled_tree:
            return

        options = self.options.get('pyflakes', self.file_path)
        if not options['enabled']:
            return

        warnings = PocketLintPyFlakesChecker(
            self._compiled_tree, file_path=self.file_path, text=self.text)
        for warning in warnings.messages:
            dummy, line_no, message = str(warning).split(':')
            self.message(
                int(line_no),
                message.strip(),
                category='pyflakes',
                icon='info',
                )

    def check_pycodestyle(self):
        """Check style."""
        options = self.options.get('pycodestyle', self.file_path).copy()
        if not options['enabled']:
            return

        import pycodestyle

        class PyCodeStyleReport(pycodestyle.StandardReport):
            """
            Forward all errors to the main reporter.
            """
            def __init__(self, options, message_function):
                super(PyCodeStyleReport, self).__init__(options)
                self.message = message_function

            def error(self, line_no, offset, message, check):
                self.message(
                    line_no,
                    message,
                    category='pycodestyle',
                    icon='info',
                    )

        # Enabled is only used internally.
        del options['enabled']

        style_options = pycodestyle.StyleGuide(**options)
        pycodestyle_options = style_options.options
        pycodestyle_report = PyCodeStyleReport(
            pycodestyle_options, self.message)
        try:
            pycodestyle_checker = pycodestyle.Checker(
                filename=self.file_path,
                lines=self.text.splitlines(True),
                options=pycodestyle_options,
                report=pycodestyle_report,
                )
            pycodestyle_checker.check_all()
        except TokenError as er:
            message, location = er.args
            self.message(
                location[0], message, icon='error', category='pycodestyle')
        except IndentationError as er:
            message, location = er.args
            message = "%s: %s" % (message, location[3].strip())
            self.message(
                location[1], message, icon='error', category='pycodestyle')

    def check_complexity(self):
        """
        Check using McCabe.
        """
        options = self.options.get('mccabe', self.file_path)
        if not options['enabled']:
            return

        if not self._compiled_tree:
            # We failed to compile the tree.
            return

        from mccabe import McCabeChecker

        McCabeChecker.max_complexity = options['max_complexity']

        result = McCabeChecker(self._compiled_tree, '-').run()
        for lineno, offset, text, check in result:
            self.message(lineno, text, icon='info', category='mccabe')

    def check_bandit(self):
        """
        Check using bandit security linter.
        """
        options = self.options.get('bandit', self.file_path)
        if not options['enabled']:
            return

        if not self._compiled_tree:
            # We failed to compile the tree.
            return

        from bandit.core.node_visitor import BanditNodeVisitor
        from bandit.core.meta_ast import BanditMetaAst
        from bandit.core.metrics import Metrics
        from bandit.core.test_set import BanditTestSet

        result = BanditNodeVisitor(
            fname=self.file_path,
            metaast=BanditMetaAst(),
            testset=BanditTestSet(self._bandit_config, profile=options),
            debug=False,
            nosec_lines=(),
            metrics=Metrics(),
            )

        result.process(self._compiled_tree)

        for issue in result.tester.results:
            self.message(
                issue.lineno,
                '%s %s' % (
                    issue.test,
                    issue.text,
                    ),
                code=issue.test_id,
                icon='info',
                category='bandit',
                )

    def check_pylint(self):
        """
        Check using pylint.
        """
        options = self.options.get('pylint', self.file_path).copy()
        if not options['enabled']:
            return
        del options['enabled']

        if not self._compiled_tree:
            # We failed to compile the tree.
            return

        from pylint.lint import PyLinter, fix_import_path
        from pylint.reporters import CollectingReporter

        linter = PyLinter()
        linter.load_default_plugins()
        linter.set_reporter(CollectingReporter())

        if options['py3k']:
            linter.python3_porting_mode()
        del options['py3k']

        rcfile = options.get('rcfile', None)
        del options['rcfile']

        if rcfile:
            linter.read_config_file(config_file=rcfile)
            linter.load_config_file()
        else:
            linter.load_configuration_from_config(options)

        # PyLint does its own import and parsing, so we only pass the file
        # name and the precompiled tree.
        with fix_import_path(self.file_path):
            linter.check(self.file_path)

        for message in linter.reporter.messages:
            self.message(
                message.line,
                '%s:%s %s' % (
                    message.msg_id,
                    message.symbol,
                    message.msg,
                    ),
                code=message.msg_id,
                icon='info',
                category='pylint',
                )

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
            self.check_regex_line(line_no, line)
            self.check_ascii(line_no, line)

    def check_pdb(self, line_no, line):
        """Check for pdb breakpoints."""
        # Set trace call is split so that this file will pass the linter.
        pdb_call = 'pdb.' + 'set_trace'
        if pdb_call in line:
            self.message(
                line_no,
                'Line contains a call to pdb.',
                category='python',
                icon='error',
                )

    @property
    def check_length_filter(self):
        # The pycodestyle lib counts from 0.
        if self.options.max_line_length:
            return self.options.max_line_length - 1
        else:
            return DEFAULT_MAX_LENGTH

    def check_ascii(self, line_no, line):
        """Check that the line is ascii."""
        if self.encoding != 'ascii':
            return
        try:
            line.encode('ascii')
        except UnicodeEncodeError as error:
            self.message(
                line_no, 'Non-ascii characer at position %s.' % error.end,
                icon='error',
                )


class JavascriptChecker(BaseChecker, AnyTextMixin):
    """Check JavaScript source code."""

    def check(self):
        """Check the syntax of the JavaScript code."""
        self.check_chevah_js_linter()
        self.check_text()
        self.check_windows_endlines()

    def check_chevah_js_linter(self):
        """Check file using Chevah JS Linter."""

        options = self.options.get('chevah_js_linter', self.file_path)

        if not options['enabled']:
            return

        from closure_linter import runner
        from closure_linter.common import erroraccumulator

        import gflags as flags
        flags.FLAGS(['scame-js-linter'] + options['flags'])

        error_handler = erroraccumulator.ErrorAccumulator()
        runner.Run(self.file_path, error_handler)
        for error in error_handler.GetErrors():
            if error.code in options['ignore']:
                continue
            # Use a similar format as default Google Closure Linter formatter.
            # Line 12, E:0010: Missing semicolon at end of line
            message = 'E:%04d: %s' % (error.code, error.message)
            self.message(
                error.token.line_number,
                message,
                category='closure',
                icon='info',
                )

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
            self.check_regex_line(line_no, line)
            self.check_tab(line_no, line)


class JSONChecker(BaseChecker, AnyTextMixin):
    """Check JSON files."""

    def check(self):
        """Check JSON file using basic text checks and custom checks."""
        if not self.text:
            return

        # Line independent checks.
        for line_no, line in enumerate(self.text.splitlines()):
            line_no += 1
            self.check_trailing_whitespace(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_regex_line(line_no, line)
            self.check_tab(line_no, line)
        last_lineno = line_no
        self.check_load()
        self.check_empty_last_line(last_lineno)

    def check_length(self, line_no, line):
        """JSON files can have long lines."""
        return

    def check_load(self):
        """Check that JSON can be deserialized/loaded."""
        if not HAS_JSON:
            return
        try:
            json.loads(self.text)
        except ValueError as error:
            line_number = 0
            message = str(error)
            match = re.search(r"(.*): line (\d+)", message)
            if match:
                try:
                    line_number = int(match.group(2))
                except Exception:
                    # If we can not find the line number,
                    # just fall back to default.
                    line_number = 0
            self.message(line_number, message, icon='error')


class ReStructuredTextChecker(BaseChecker, AnyTextMixin):
    """Check reStructuredText source code."""

    # Taken from rst documentation.
    delimiter_characters = [
        '=', '-', '`', ':', '\'', '"', '~', '^', '_', '*', '+', '#', '<', '>']

    def __init__(self, file_path, text, reporter=None, options=None):
        super(ReStructuredTextChecker, self).__init__(
            file_path, text, reporter, options)
        self.lines = self.text.splitlines()

    def message(self, *args, **kwargs):
        """
        Called to record a checker detection.
        """
        # Always use the same category.
        kwargs['category'] = 'rst'
        super(ReStructuredTextChecker, self).message(*args, **kwargs)

    def check(self):
        """Check the syntax of the reStructuredText code."""
        if not self.text:
            return

        self.check_lines()
        self.check_empty_last_line(len(self.lines))
        self.check_windows_endlines()

    def check_lines(self):
        """Call each line checker for each line in text."""
        for line_no, line in enumerate(self.lines):
            line_no += 1
            self.check_length(line_no, line)
            self.check_trailing_whitespace(line_no, line)
            self.check_tab(line_no, line)
            self.check_conflicts(line_no, line)
            self.check_regex_line(line_no, line)

            if self.isTransition(line_no - 1):
                self.check_transition(line_no - 1)
            elif self.isSectionDelimiter(line_no - 1):
                self.check_section_delimiter(line_no - 1)
            else:
                pass

    def isTransition(self, line_number):
        '''Return True if the current line is a line transition.'''
        line = self.lines[line_number]
        if len(line) < 4:
            return False

        if len(self.lines) < 3:
            return False

        succesive_characters = (
            line[0] == line[1] == line[2] == line[3] and
            line[0] in self.delimiter_characters)

        if not succesive_characters:
            return False

        emply_lines_bounded = (
            self.lines[line_number - 1] == '' and
            self.lines[line_number + 1] == '')

        if not emply_lines_bounded:
            return False

        return True

    def check_transition(self, line_number):
        '''Transitions should be delimited by a single empty line.'''
        if (self.lines[line_number - 2] == '' or
                self.lines[line_number + 2] == ''):
            self.message(
                line_number + 1,
                'Transition markers should be bounded by single empty lines.',
                icon='info',
                )

    def isSectionDelimiter(self, line_number):
        '''Return true if the line is a section delimiter.'''
        if len(self.lines) < 3:
            return False

        if line_number >= len(self.lines):
            return False

        line = self.lines[line_number]
        if len(line) < 3:
            return False

        if (line[0] == line[1] == line[2] and line[0] in
                self.delimiter_characters):
            if ' ' in line:
                # We have a table header.
                return False
            else:
                return True

        return False

    def check_section_delimiter(self, line_number):
        """Checks for section delimiter.

        These checkes are designed for sections delimited by top and bottom
        markers.

        =======  <- top marker
        Section  <- text_line
        =======  <- bottom marker

        If the section is delimted only by bottom marker, the section text
        is considered the top marker.

        Section  <- top marker, text_line
        =======  <- bottom marker

        If the section has a custom anchor name:

        .. _link  <- top marker

        =======
        Section   <- text_line
        =======   <- bottom marker

        or:

        .. _link  <- top marker

        Section   <- text_line
        =======   <- bottom marker

        If we have top and bottom markers, the check will be called twice (
        for each marker). In this case we will skip the tests for bottom
        marker.
        """
        human_line_number = line_number + 1
        current_line = self.lines[line_number]

        # Skip test if we have both top and bottom markers and we are
        # at the bottom marker.
        if (line_number > 1 and current_line == self.lines[line_number - 2]):
            return

        if ((line_number + 2) < len(self.lines) and
                current_line == self.lines[line_number + 2]):
            # We have both top and bottom markers and we are currently at
            # the top marker.
            top_marker = line_number
            text_line = line_number + 1
            bottom_marker = line_number + 2
        else:
            # We only have bottom marker, and are at the bottom marker.
            top_marker = line_number - 1
            text_line = line_number - 1
            bottom_marker = line_number

        # In case we have a custom anchor, the top_marker is replaced by
        # the custom anchor.
        if self._sectionHasCustomAnchor(top_marker):
            top_marker = top_marker - 2

        # Check underline length for bottom marker,
        # since top marker can be the same as text line.
        if len(self.lines[bottom_marker]) != len(self.lines[text_line]):
            self.message(
                human_line_number,
                'Section marker has wrong length.',
                icon='error',
                )

        if not self._haveGoodSpacingBeforeSection(top_marker):
            self.message(
                human_line_number,
                'Section should be divided by 2 empty lines.',
                icon='info')

        if not self._haveGoodSpacingAfterSection(bottom_marker):
            self.message(
                human_line_number,
                'Section title should be followed by 1 empty line.',
                icon='info')

    def _sectionHasCustomAnchor(self, top_marker):
        if (top_marker - 2) < 0:
            return False

        if self.lines[top_marker - 2].startswith('.. _'):
            return True

        return False

    def _haveGoodSpacingBeforeSection(self, top_marker):
        '''Return True if we have good spacing before the section.'''
        if top_marker > 0:
            if self.lines[top_marker - 1] != '':
                return False

        # If we are on the second line, there is no space for 2 empty lines
        # before.
        if top_marker == 1:
            return False

        if top_marker > 1:
            if self.lines[top_marker - 2] != '':
                return False

        if top_marker > 2:
            if self.lines[top_marker - 3] == '':
                return False

        return True

    def _haveGoodSpacingAfterSection(self, bottom_marker):
        '''Return True if we have good spacing after the section.'''
        lines_count = len(self.lines)

        if bottom_marker < lines_count - 1:
            if self.lines[bottom_marker + 1] != '':
                return False

        if bottom_marker < lines_count - 2:
            if self.lines[bottom_marker + 2] == '':
                # If the section is followed by 2 empty spaces and then
                # followed by a section delimiter, the section delimiter
                # rules will take priority
                if self.isSectionDelimiter(bottom_marker + 3):
                    return True
                if self.isSectionDelimiter(bottom_marker + 4):
                    return True
                return False

        return True
