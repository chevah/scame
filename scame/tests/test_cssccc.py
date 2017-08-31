'''Test module for cssccc'''

from __future__ import (
    absolute_import,
    print_function,
    unicode_literals,
    )

from unittest import TestCase, main as unittest_main

from scame.contrib.cssccc import (
    CSSCodingConventionChecker, CSSAtRule, CSSRuleSet, CSSStatementMember)


class TestCSSCodingConventionChecker(TestCase):
    '''Test for parsing the CSS text.'''

    def test_getNextRule_start(self):
        text = 'selector{}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('selector', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

        text = '\nselector{}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\nselector', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

        text = '\n\nselector{}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\n\nselector', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

        text = 'selector\n{}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('selector\n', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

        text = 'selector, {}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('selector, ', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

    def test_getNextRule_content(self):
        text = 'selector { content; }'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual(' content; ', rule.declarations.text)
        self.assertEqual(0, rule.declarations.start_line)
        self.assertEqual(10, rule.declarations.start_character)

        text = 'selector \n{\n content; }'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\n content; ', rule.declarations.text)
        self.assertEqual(1, rule.declarations.start_line)
        self.assertEqual(1, rule.declarations.start_character)

    def test_getNextRule_continue(self):
        text = 'selector1\n { content1; }\n\nselector2\n{content2}\n'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('selector1\n ', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)
        self.assertEqual(' content1; ', rule.declarations.text)
        self.assertEqual(1, rule.declarations.start_line)
        self.assertEqual(2, rule.declarations.start_character)

        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\n\nselector2\n', rule.selector.text)
        self.assertEqual(1, rule.selector.start_line)
        self.assertEqual(14, rule.selector.start_character)
        self.assertEqual('content2', rule.declarations.text)
        self.assertEqual(4, rule.declarations.start_line)
        self.assertEqual(1, rule.declarations.start_character)

    def test_getNextRule_stop(self):
        text = 'rule1{st1\n}\n@font-face {\n src: url("u\n u"); \n }\nr2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.failUnlessRaises(StopIteration, lint.getNextRule)

    def test_getNextRule_comment_multiline(self):
        text = (
            '\n'
            '\n'
            '/* multi line\n'
            ' * comment \n'
            ' */\n'
            'selector {\n'
            'cont2;\n'
            '}')
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\n\nselector ', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

    def test_getNextRule_comment_inline(self):
        text = (
            'selector {\n'
            'so/* inline comment*/me\n'
            '}\n')
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\nsome\n', rule.declarations.text)
        self.assertEqual(0, rule.declarations.start_line)
        self.assertEqual(10, rule.declarations.start_character)

    def test_getNextRule_comment_end_of_line(self):
        text = (
            'selector {\n'
            'cont1;  /*end of line comment*/\n'
            '}')
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\ncont1;  \n', rule.declarations.text)
        self.assertEqual(0, rule.declarations.start_line)
        self.assertEqual(10, rule.declarations.start_character)

    def test_getNextRule_comment_single_line(self):
        text = (
            '\n'
            '/* single line comment */\n'
            'selector2 {\n'
            'cont1;\n'
            '}')
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.assertEqual('\nselector2 ', rule.selector.text)
        self.assertEqual(0, rule.selector.start_line)
        self.assertEqual(0, rule.selector.start_character)

    def test_get_at_import_rule(self):
        '''Test for @import url(/css/screen.css) screen, projection;'''
        text = 'rule1{st1\n}\n@import  url(somet) print, soment ;rule2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        self.assertTrue(rule.block is None)
        self.assertEqual('import', rule.identifier)
        self.assertEqual('\n@import ', rule.keyword.text)
        self.assertEqual(1, rule.keyword.start_line)
        self.assertEqual(1, rule.keyword.start_character)
        self.assertEqual(' url(somet) print, soment ', rule.text.text)
        self.assertEqual(2, rule.text.start_line)
        self.assertEqual(8, rule.text.start_character)

    def test_get_at_charset_rule(self):
        '''Test for @charset "ISO-8859-15";'''
        text = 'rule1{st1\n}\n@charset  "utf" ;rule2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        self.assertTrue(rule.block is None)
        self.assertEqual('charset', rule.identifier)
        self.assertEqual('\n@charset ', rule.keyword.text)
        self.assertEqual(1, rule.keyword.start_line)
        self.assertEqual(1, rule.keyword.start_character)
        self.assertEqual(' "utf" ', rule.text.text)
        self.assertEqual(2, rule.text.start_line)
        self.assertEqual(9, rule.text.start_character)

    def test_get_at_namespace_rule(self):
        '''Test for @namespace  foo  "http://foo" ;'''
        text = 'rule1{st1\n}@namespace  foo  "http://foo" ;rule2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        self.assertTrue(rule.block is None)
        self.assertEqual('namespace', rule.identifier)
        self.assertEqual('@namespace ', rule.keyword.text)
        self.assertEqual(1, rule.keyword.start_line)
        self.assertEqual(1, rule.keyword.start_character)
        self.assertEqual(' foo  "http://foo" ', rule.text.text)
        self.assertEqual(1, rule.text.start_line)
        self.assertEqual(12, rule.text.start_character)

    def test_get_at_page_rule(self):
        '''Test for @page

        @page :left {
          margin-left: 5cm; /* left pages only */
        }
        '''
        text = 'rule1{st1\n}\n@page :left {\n  mar; /*com*/\n }\nrule2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        self.assertTrue(rule.text is None)
        self.assertEqual('page', rule.identifier)
        self.assertEqual('\n@page :left ', rule.keyword.text)
        self.assertEqual(1, rule.keyword.start_line)
        self.assertEqual(1, rule.keyword.start_character)
        self.assertEqual('\n  mar; \n ', rule.block.text)
        self.assertEqual(2, rule.block.start_line)
        self.assertEqual(13, rule.block.start_character)

    def test_get_at_font_face_rule(self):
        '''Test for @font-face

        @font-face {
          font-family: "Example Font";
          src: url("http://www.example.com
              /fonts/example");
        }
        '''
        text = 'rule1{st1\n}\n@font-face {\n src: url("u\n u"); \n }\nr2{st2}'
        lint = CSSCodingConventionChecker(text)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSAtRule.type)
        self.assertTrue(rule.text is None)
        self.assertEqual('font-face', rule.identifier)
        self.assertEqual('\n@font-face ', rule.keyword.text)
        self.assertEqual(1, rule.keyword.start_line)
        self.assertEqual(1, rule.keyword.start_character)
        self.assertEqual('\n src: url("u\n u"); \n ', rule.block.text)
        self.assertEqual(2, rule.block.start_line)
        self.assertEqual(12, rule.block.start_character)
        rule = lint.getNextRule()
        self.assertTrue(rule.type is CSSRuleSet.type)
        self.failUnlessRaises(StopIteration, lint.getNextRule)


class TestCSSStatementMember(TestCase):
    '''Tests for CSSStatementMember.'''

    def test_getStartLine(self):
        statement = CSSStatementMember(0, 4, 'some')
        self.assertEqual(1, statement.getStartLine())
        statement = CSSStatementMember(3, 4, 'some')
        self.assertEqual(4, statement.getStartLine())
        statement = CSSStatementMember(3, 4, '\n\nsome')
        self.assertEqual(6, statement.getStartLine())

    def test_getStartLine_empty_selector(self):
        statement = CSSStatementMember(0, 1, '')
        self.assertEqual(1, statement.getStartLine())

    def test_getStartLine_newlines_only(self):
        statement = CSSStatementMember(0, 1, '\n')
        self.assertEqual(2, statement.getStartLine())

    def test_getStartLine_spaces_only(self):
        statement = CSSStatementMember(0, 1, ' ')
        self.assertEqual(1, statement.getStartLine())


class TestLog(object):
    '''Container for a test log.'''

    def __init__(self, line_number, code, message):
        self.line_number = line_number
        self.code = code
        self.message = message


class RuleTesterBase(TestCase):
    '''Base class for rule checkers.'''

    ignored_messaged = []

    def setUp(self):
        self.logs = []

    def log(self, line_number, code, message):
        if code in self.ignored_messaged:
            return
        self.logs.append((line_number, code, message))

    @property
    def last_log(self):
        (line_number, code, message) = self.logs.pop()
        return TestLog(line_number, code, message)


class RuleTesterConventionA(RuleTesterBase):
    '''Class for convention A.

    selector1,
    selecter2
    {
        property1: value1;
        property2: value2;
    }
    '''

    ignored_messaged = ['I013', 'I014']


class TestCSSRuleSetSelectorChecksA(RuleTesterConventionA):
    '''Test coding conventions for selector from rule sets.'''

    def test_valid_selector(self):

        selector = CSSStatementMember(0, 0, 'something\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(0, 0, '\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(1, 0, '\n\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(2, 0, '\n\nsomething,\nsomethi\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(3, 0, '\n\nsom:some some,\n#somethi\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

    def test_I002(self):
        selector = CSSStatementMember(2, 0, '\n\n\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I002', last_log.code)
        self.assertEqual(6, last_log.line_number)

        selector = CSSStatementMember(4, 0, '\n\n\n\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I002', last_log.code)
        self.assertEqual(9, last_log.line_number)

    def test_I003(self):
        selector = CSSStatementMember(2, 0, '\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I003', last_log.code)
        self.assertEqual(4, last_log.line_number)

        selector = CSSStatementMember(2, 0, 'something\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I003', last_log.code)
        self.assertEqual(3, last_log.line_number)

    def test_I004(self):
        selector = CSSStatementMember(3, 0, '\n\nsomething, something\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I004', last_log.code)
        self.assertEqual(6, last_log.line_number)

    def test_I005(self):
        selector = CSSStatementMember(4, 0, '\nsomething,\nsomething')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I005', last_log.code)
        self.assertEqual(7, last_log.line_number)


class TestCSSRuleSetDeclarationsChecksA(RuleTesterConventionA):
    '''Test coding conventions for declarations from rule sets.'''

    def test_valid_declarations(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some: 3px;\n    other:\n        url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual([], self.logs)

    def test_I006(self):
        stmt = CSSStatementMember(
            4, 0, '\n    some: 3px;\n    other: url();')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        last_log = self.last_log
        self.assertEqual('I006', last_log.code)
        self.assertEqual(7, last_log.line_number)

        stmt = CSSStatementMember(
            4, 0, '\n    some: 3px;\n    other: url();\n ')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        last_log = self.last_log
        self.assertEqual('I006', last_log.code)
        self.assertEqual(8, last_log.line_number)

        stmt = CSSStatementMember(
            4, 0, '\n    some: 3px;\n    other: url();\n\n ')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        last_log = self.last_log
        self.assertEqual('I006', last_log.code)
        self.assertEqual(9, last_log.line_number)

    def test_I007(self):
        stmt = CSSStatementMember(
            4, 0, '\n    some: 3px; other: url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        last_log = self.last_log
        self.assertEqual('I007', last_log.code)
        self.assertEqual(6, last_log.line_number)

    def test_I008(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some: 3px;\n  other: url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I008', self.last_log.code)

        stmt = CSSStatementMember(
            0, 0, '\n    some: 3px;\n     other: url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I008', self.last_log.code)

    def test_I009(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some 3px;\n    other: url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I009', self.last_log.code)

        stmt = CSSStatementMember(
            0, 0, '\n    some: 3:px;\n    other: url();\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I009', self.last_log.code)

    def test_I010(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some : 3px;\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I010', self.last_log.code)

    def test_I011(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some:3px;\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I011', self.last_log.code)

    def test_I012(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some:  3px;\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I012', self.last_log.code)


class RuleTesterConventionB(RuleTesterBase):
    '''Class for convention B.

    selector1,
    selecter2 {
        property1: value1;
        property2: value2;
    }
    '''

    ignored_messaged = ['I005', 'I014']


class TestCSSRuleSetSelectorChecksB(RuleTesterConventionB):
    '''Test coding conventions for selector from rule sets.'''

    def test_valid_selector(self):

        selector = CSSStatementMember(0, 0, 'something ')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(0, 0, '\nsomething ')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(1, 0, '\n\nsomething ')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(2, 0, '\n\nsomething,\nsomethi ')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

        selector = CSSStatementMember(3, 0, '\n\nsom:some some,\n#somethi ')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        self.assertEqual([], self.logs)

    def test_I013(self):
        selector = CSSStatementMember(2, 0, '\n\nsomething\n')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I013', last_log.code)
        self.assertEqual(5, last_log.line_number)

    def test_I013_compressed_file(self):
        selector = CSSStatementMember(0, 0, 'something')
        rule = CSSRuleSet(selector=selector, declarations=None, log=self.log)
        rule.selector.text = ''
        rule.checkSelector()
        last_log = self.last_log
        self.assertEqual('I013', last_log.code)
        self.assertEqual(1, last_log.line_number)


class RuleTesterConventionC(RuleTesterBase):
    '''Class for convention C.

    selector1,
    selecter2 {
        property1: value1;
        property2: value2;
        }
    '''

    ignored_messaged = ['I005', 'I006']


class TestCSSRuleSetDeclarationsChecksC(RuleTesterConventionC):
    '''Test coding conventions for declarations from rule sets.'''

    def test_valid_declarations(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some: 3px;\n    other:\n        url();\n    ')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual([], self.logs)

    def test_I014(self):
        stmt = CSSStatementMember(
            0, 0, '\n    some:  3px;\n')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I014', self.last_log.code)

        stmt = CSSStatementMember(
            0, 0, '\n    some:  3px;\n   ')
        rule = CSSRuleSet(selector=None, declarations=stmt, log=self.log)
        rule.checkDeclarations()
        self.assertEqual('I014', self.last_log.code)


if __name__ == '__main__':
    unittest_main()
