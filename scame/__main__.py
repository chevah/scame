import os
import re
import sys
from optparse import OptionParser

from scame.__version__ import VERSION
from scame.formatcheck import (
    DEFAULT_MAX_LENGTH,
    Language,
    Reporter,
    ScameOptions,
    UniversalChecker,
    )


def parse_command_line(args):
    """
    Return the `options` based on the command line arguments.
    """
    usage = "usage: %prog [options] path1 path2"
    parser = OptionParser(
        usage=usage,
        version=VERSION,
        )
    parser.add_option(
        "-q", "--quiet", action="store_false", dest="verbose",
        help="Show errors only.")
    parser.add_option(
        "-a", "--align-closing", dest="hang_closing", action="store_false",
        help="Align the closing bracket with the matching opening.")
    parser.add_option(
        "-m", "--max-length", dest="max_line_length", type="int",
        help="Set the max line length (default %s)" % DEFAULT_MAX_LENGTH)
    parser.add_option(
        "--max-complexity", dest="max_complexity", type="int",
        help="Set the max complexity (default -1 - disabled)"
        )
    parser.set_defaults(
        hang_closing=True,
        max_line_length=DEFAULT_MAX_LENGTH,
        max_complexity=-1,
        )

    (command_options, sources) = parser.parse_args(args=args)

    # Create options based on parsed command line.
    options = ScameOptions()
    options.max_line_length = command_options.max_line_length
    options.mccabe['max_complexity'] = command_options.max_complexity
    options.pycodestyle['hang_closing'] = command_options.hang_closing
    options.scope['include'] = sources

    return options


def _get_all_files(options, dir_path):
    """
    Generated all the files in the dir_path tree (recursive),
    """
    regex_exclude = [
        re.compile(expression) for expression in options.scope['exclude']]

    def is_excepted_file(file_name):
        for expresion in regex_exclude:
            if expresion.match(file_name):
                return True
        return False

    for root, _, filenames in os.walk(dir_path):
        for name in filenames:
            target = os.path.join(root, name)
            if is_excepted_file(target):
                continue
            yield target


def check_sources(options, reporter=None):
    """
    Run checker on all the sources using `options` and sending results to
    `reporter`.
    """
    if reporter is None:
        reporter = Reporter(Reporter.CONSOLE)
    reporter.call_count = 0

    for source in options.scope['include']:
        file_path = os.path.normpath(source)

        if os.path.isdir(source):
            paths = _get_all_files(options, file_path)
        else:
            paths = [file_path]

        for file_path in paths:

            if not Language.is_editable(file_path):
                continue

            language = Language.get_language(file_path)
            with open(file_path, 'rt') as file_:
                text = file_.read()

            checker = UniversalChecker(
                file_path, text, language, reporter, options=options)
            checker.check()

    return reporter.call_count


def main(args=None):
    """
    Execute the checker.
    """
    if args is None:
        args = sys.argv[1:]

    options = parse_command_line(args=args)

    if len(options.scope['include']) == 0:
        sys.stderr.write("Expected file paths.\n")
        sys.exit(1)



    reporter = Reporter(Reporter.CONSOLE)
    reporter.error_only = not options.verbose
    return check_sources(options, reporter)


if __name__ == "__main__":
    main()
