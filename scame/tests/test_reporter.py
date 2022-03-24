# Copyright (C) 2012-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).


from scame.tests import CheckerTestCase


class ReporterTestCase(CheckerTestCase):
    def test_init(self):
        self.assertIs(self.reporter.COLLECTOR, self.reporter.report_type)

    def test_call(self):
        self.reporter(
            12, "test", icon="info", base_dir="./lib", file_name="eg.py")
        self.assertIs(1, self.reporter.call_count)
        self.assertEqual(("./lib", "eg.py"), self.reporter._last_file_name)
        self.assertEqual([(12, "test")], self.reporter.messages)

    def test_call_error_only(self):
        self.reporter.error_only = True
        self.reporter(
            12, "test", icon="info", base_dir="./lib", file_name="eg.py")
        self.assertIs(0, self.reporter.call_count)
        self.reporter(
            9, "test", icon="error", base_dir="./lib", file_name="eg.py")
        self.assertIs(1, self.reporter.call_count)
