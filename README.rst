Scame Static Checker
====================

Scame is a fork of pocket-lint by Curtis Hovey
https://launchpad.net/pocket-lint

This is MIT / X / Expat Licence

There is now a different pocketlint on GitHub, but that is a different
project.. and that is GPL.

It continues to be a composite linter and style checker target on Python.

It has the following goals:

* Provides a consistent report of issues raised by the subordinate
  checkers.

* Alternate reports can be written to change the report, or integrate
  the report into another application.

* Read a line, file or parse AST only once and pass it to the checkers.

* Supports checking of multiple source types:

  * Python files using pyflakes
  * XML/HTML style and entities
  * JSON data structure syntax
  * reStructured Text style
  * Plain text

* Support checking different source parts using different configurations.

* Use soft dependencies on the checker. Only import it when enabled.

* You can ignore a single line for all reports using ` # noqa` marker.

* You can ignore a single like for all reports from a category using the
  `  # noqa:CATEGORY` marker.

* For CSS and JS is better to use node.js based tools as they are the future.


Installing, tests, and coverage
-------------------------------

Check the Makefile for tips.
