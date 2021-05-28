# Copyright (C) 2013-2013 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the MIT license (see the file COPYING).
"""Reporting and output helpers."""

__all__ = [
    "Reporter",
]

import logging
import os
import sys


class ConsoleHandler(logging.StreamHandler):
    """A handler that logs to console."""

    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.stream = None  # Not used.

    def emit(self, record):
        self.__emit(record, sys.stdout)

    def __emit(self, record, stream):
        self.stream = stream
        logging.StreamHandler.emit(self, record)

    def flush(self):
        if not logging:
            # We are in at_exit part so nothing to do.
            return
        is_flushable = self.stream and hasattr(self.stream, "flush")
        if is_flushable and not self.stream.closed:
            logging.StreamHandler.flush(self)


logger = logging.getLogger()
logger.propagate = False
logger.addHandler(ConsoleHandler())


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

    def __call__(
        self, line_no, message, icon=None, base_dir=None, file_name=None, category=None
    ):
        """Report a message."""
        if self.error_only and icon != "error":
            return
        self.call_count += 1
        args = (line_no, message, icon, base_dir, file_name, category)
        if self.report_type == self.FILE_LINES:
            self._message_file_lines(*args)
        elif self.report_type == self.COLLECTOR:
            self._message_collector(*args)
        else:
            self._message_console(*args)

    def _message_console(
        self, line_no, message, icon=None, base_dir=None, file_name=None, category=None
    ):
        """Print the messages to the console."""
        self._message_console_group(base_dir, file_name)
        logger.error(f"    {line_no:>4}:{category}: {message}")

    def _message_console_group(self, base_dir, file_name):
        """Print the file name is it has not been seen yet."""
        source = (base_dir, file_name)
        if file_name is not None and source != self._last_file_name:
            self._last_file_name = source
            logger.error("%s" % os.path.join("./", base_dir, file_name))

    def _message_file_lines(
        self, line_no, message, icon=None, base_dir=None, file_name=None, category=None
    ):
        """Display the messages in the file_lines_view."""
        if self.piter is None:
            mime_type = "gnome-mime-text"
            self.piter = self.treestore.append(
                None, (file_name, mime_type, 0, None, base_dir)
            )
        self.treestore.append(self.piter, (file_name, icon, line_no, message, base_dir))

    def _message_collector(
        self, line_no, message, icon=None, base_dir=None, file_name=None, category=None
    ):
        self._last_file_name = (base_dir, file_name)
        self.messages.append((line_no, message))
