scame-0.5.1 - 2019/05/25
========================

* Fix git diff linter for moved files.


scame-0.5.0 - 2018/09/11
========================

* Switch from deprecated Google Closure Linter to Chevah JS Linter.
* Allow passing full command line arguments to chevah js linter.


scame-0.4.2 - 2017/10/29
========================

* Break progress at 72.


scame-0.4.1 - 2017/10/29
========================

* Force flush the output on progress.


scame-0.4.0 - 2017/10/29
========================

* Add command line to show progress.
  This helps CI system to know that task is running.


scame-0.3.3 - 2017/06/14
========================

* Fix check_source with not used with command line input.


scame-0.3.2 - 2017/06/14
========================

* Add exclude option for command line.
* Add option to enable pycodestyle checks from command line.
* Add option to enable bandit checks from command line.
* Add option to run only files changed since a base branch.


scame-0.3.1 - 2017/06/14
========================

* Fix scan_source.


scame-0.3.0 - 2017/06/14
========================

* Add version to the command line options.
* Fix previous bad release.


scame-0.2.0 - 2017/06/06
========================

* In ScameOptions pass the full path, not just the file name.


scame-0.1.0 - 2017/06/06
========================

* Initial rename from pocket-lint
* Add the changes from the Chevah's pocket-lint fork
* There is a dedicated `options` configuration.
* check_sources can now do recursive checks and exclude based on regex
* Add checker for bandit
* Add checker for pylint
* Remove checker for Go
* Remove checker and formatter for Python doctests.
* Remove jslint checker.


pocket-lint-0.3: The first release
==================================

Fixed rules to ensure Zope zcml and pt are recongnised as XML.


pocket-lint-0.1: The first release
==================================

Pocket-lint a composite linter and style checker. It has several notable
features:

    * Provides a consistent report of issues raised by the subordinate
      checkers.
    * Alternate Reports can be written to change the report, or integrate
      the report into another application.
    * Supports checking of multiple source types:
      * Python syntax and style
      * Python doctest style
      * XML/HTML style and entities
      * CSS style
      * JavaScript syntax and style
      * Plain text
    * Supports reporting:
      * Python doctests
      * CSS
      * XML/HTML
