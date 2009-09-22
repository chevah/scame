# Copyright (C) 2009 - Curtis Hovey <sinzui.is at verizon.net>
# This software is licensed under the GNU General Public License version 2
# (see the file COPYING)."""Text formatting features for the edit menu."""

__metaclass__ = type

__all__ = [
    'FormatPlugin',
    ]


from gettext import gettext as _

import gedit

from gdp import GDPWindow
from gdp.format import Formatter


class FormatPlugin(gedit.Plugin):
    """Plugin for formatting code."""

    action_group_name = 'GDPFormatActions'
    menu_xml = """
        <ui>
          <menubar name="MenuBar">
            <menu name='EditMenu' action='Edit'>
              <placeholder name="EditOps_3">
                  <separator />
                  <menu action="GDPFormatMenu">
                    <menuitem action="RewrapText"/>
                    <menuitem action="FixLineEnding"/>
                    <menuitem action="TabsToSpaces"/>
                    <menuitem action="QuoteLines"/>
                    <menuitem action="SortImports"/>
                    <menuitem action="SingleLine"/>
                    <menuitem action="REReplace"/>
                  </menu>
                  <separator />
              </placeholder>
            </menu>
            <menu name='ToolsMenu' action='Tools'>
              <placeholder name="ToolsOps_2">
                <separator />
                <menuitem action="CheckProblems"/>
                <menuitem action="ReformatDoctest"/>
                <separator />
              </placeholder>
            </menu>
          </menubar>
        </ui>
        """

    def actions(self, formatter):
        """Return a list of action tuples.

        (name, stock_id, label, accelerator, tooltip, callback)
        """
        return  [
            ('GDPFormatMenu', None, _('_Format'), None, None, None),
            ('RewrapText', None, _("Rewrap _text"), None,
                _("Rewrap the text to 78 characters."),
                formatter.rewrap_text),
            ('FixLineEnding', None, _("Fix _line endings"), None,
                _('Remove trailing whitespace and use newline endings.'),
                formatter.newline_ending),
            ('TabsToSpaces', None, _("Convert t_abs to spaces"), None,
                _('Convert tabs to spaces using the preferred tab size.'),
                formatter.tabs_to_spaces),
            ('QuoteLines', None, _("_Quote lines"), '<Alt>Q',
                _("Format the text as a quoted email."),
                formatter.quote_lines),
            ('SortImports', None, _("Sort _imports"), None,
                _('Sort and wrap imports.'),
                formatter.sort_imports),
            ('SingleLine', None, _("_Single line"), None,
                _("Format the text as a single line."),
                formatter.single_line),
            ('REReplace', None, _("Regular _expression line replace"), None,
                _("Reformat each line using a regular expression."),
                formatter.re_replace),
            ('ReformatDoctest', None, _("Reformat _doctest"), None,
                _("Reformat the doctest."),
                formatter.reformat_doctest),
            ('CheckProblems', None, _("C_heck syntax and style"), 'F3',
                _("Check syntax and style problems."),
                formatter.check_style),
            ]

    def __init__(self):
        """Initialize the plugin the whole Gedit application."""
        gedit.Plugin.__init__(self)
        self.windows = {}

    def activate(self, window):
        """Activate the plugin in the current top-level window.

        Add 'Format' to the edit menu and create a Formatter.
        """
        self.windows[window] = GDPWindow(window, Formatter(window), self)

    def deactivate(self, window):
        """Deactivate the plugin in the current top-level window."""
        self.windows[window].deactivate()
        del self.windows[window]

    def update_ui(self, window):
        """Toggle the plugin's sensativity in the top-level window.

        This plugin is always active.
        """
        gdp_window = self.windows[window]
        gdp_window.disconnect_signal(
            gdp_window.document, 'syntax-error-python')
        gdp_window.document = gdp_window.controller.active_document
        gdp_window.connect_signal(
            gdp_window.document, 'syntax-error-python',
            gdp_window.controller.check_style)
