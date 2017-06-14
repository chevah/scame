Scame Static Checker
====================

Scame is a fork of pocket-lint.

It continues to be a composite linter and style checker target on Python.

It has the following goals:

* Provides a consistent report of issues raised by the subordinate
  checkers.

* Alternate reports can be written to change the report, or integrate
  the report into another application.

* Read a line, file or parse AST only once and pass it to the checkers.

* Supports checking of multiple source types:

  * Python syntax and style using pycodestyle
  * Python files using pyflakes
  * Python files using bandit
  * Python files using pylint
  * XML/HTML style and entities
  * CSS style
  * JavaScript syntax and style
  * JSON data structure syntax
  * reStructured Text style
  * Plain text

* Support checking different source parts using different configurations.

* Use soft dependencies on the checker. Only import it when enabled.

* You can ignore a single line for all reports using ` # noqa` marker.

* You can ignore a single like for all reports from a cagetory using the
  `  # noqa:CATEGORY` marker.
