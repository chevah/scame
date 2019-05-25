import os
import re
import subprocess
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
        "--progress", action="store_true", dest="progress",
        help="Show a dot for each processed file.")

    parser.add_option(
        "--pycodestyle", dest="pycodestyle", action="store_true",
        help="Enable pycodestyle checks.")
    parser.add_option(
        "-a", "--align-closing", dest="hang_closing", action="store_false",
        help="Align the closing bracket with the matching opening.")

    parser.add_option(
        "--bandit", dest="bandit", action="store_true",
        help="Enable bandit checks.")

    parser.add_option(
        "--diff-branch", dest="diff_branch",
        help="Name of the branch to use as base for changed files.")
    parser.add_option(
        "--exclude", dest="exclude",
        help="Comma separated list of regex paths to exclude.")

    parser.add_option(
        "-m", "--max-length", dest="max_line_length", type="int",
        help="Set the max line length (default %s)" % DEFAULT_MAX_LENGTH)
    parser.add_option(
        "--max-complexity", dest="max_complexity", type="int",
        help="Set the max complexity (default -1 - disabled)"
        )
    parser.set_defaults(
        verbose=True,
        hang_closing=True,
        max_line_length=DEFAULT_MAX_LENGTH,
        max_complexity=-1,
        diff_branch=None,
        exclude='',
        pycodestyle=False,
        bandit=False,
        )

    (command_options, sources) = parser.parse_args(args=args)

    # Create options based on parsed command line.
    options = ScameOptions()
    options.verbose = command_options.verbose
    options.progress = command_options.progress
    options.max_line_length = command_options.max_line_length
    options.mccabe['max_complexity'] = command_options.max_complexity
    options.bandit['enabled'] = command_options.bandit
    options.pycodestyle['enabled'] = command_options.pycodestyle
    options.pycodestyle['hang_closing'] = command_options.hang_closing
    options.diff_branch = command_options.diff_branch

    exclude = []
    for part in command_options.exclude.split(','):
        part = part.strip()
        if not part:
            continue
        exclude.append(part)

    options.scope['include'] = sources
    options.scope['exclude'] = exclude

    return options


def _get_all_files(dir_path):
    """
    Generated all the files in the dir_path tree (recursive),
    """
    for root, _, filenames in os.walk(dir_path):
        for name in filenames:
            target = os.path.join(root, name)
            yield target


def _execute(
        command, input_text=None, output=None,
        ignore_errors=False, verbose=False,
        extra_environment=None,
        ):
    """
    Returns (exit_code, stdoutdata)
    """
    if verbose:
        print('Calling: %s' % command)

    if output is None:
        output = subprocess.PIPE

    if extra_environment is not None:
        execute_environment = os.environ.copy()
        execute_environment.update(extra_environment)
    else:
        execute_environment = None

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=output,
            env=execute_environment,
            )
    except OSError, error:
        if error.errno == 2:
            print('Failed to execute: %s' % ' '.join(command))
            print('Missing command: %s' % command[0])
            sys.exit(1)
        else:
            raise

    try:
        (stdoutdata, stderrdata) = process.communicate(input_text)
    except KeyboardInterrupt:
        # Don't print stack trace on keyboard interrupt.
        # Just exit.
        os._exit(1)

    exit_code = process.returncode
    if exit_code != 0:
        if verbose:
            print('Failed to execute %s\n%s' % (command, stderrdata))
        if not ignore_errors:
            sys.exit(exit_code)

    return (exit_code, stdoutdata)


def _git_diff_files(ref='master'):
    """
    Return a list of (action, filename) that have changed in
    comparison with `ref`.
    """
    result = []
    command = ['git', 'diff', '--name-status', '%s' % (ref)]
    exit_code, output = _execute(command)
    if exit_code != 0:
        print('Failed to diff files.')
        sys.exit(1)

    for line in output.splitlines():
        parts = line.split('\t')
        action = parts[0]
        name = parts[-1]
        action = action.lower()
        result.append((action, name))

    return result


def check_sources(options, reporter=None):
    """
    Run checker on all the sources using `options` and sending results to
    `reporter`.
    """
    if reporter is None:
        reporter = Reporter(Reporter.CONSOLE)
    reporter.call_count = 0

    if options.diff_branch:
        # We ignore the passed sources, and get the files from the VCS.
        sources = []
        for change in _git_diff_files(ref=options.diff_branch):
            # Filter deleted changes since we can not lint then.
            if change[0] == 'd':
                continue
            sources.append(change[1])
    else:
        # We don't have explicit sources, so we use the one from the
        # configuration
        sources = options.scope['include']

    regex_exclude = [
        re.compile(expression) for expression in options.scope['exclude']]

    def is_excepted_file(file_name):
        for expresion in regex_exclude:
            if expresion.match(file_name):
                return True

        if options.scope['include']:
            included = False
            for include in options.scope['include']:
                if file_name.startswith(include):
                    included = True
                    break
            if not included:
                return True

        return False

    count = 0
    for source in sources:
        file_path = os.path.normpath(source)

        if os.path.isdir(source):
            paths = _get_all_files(file_path)
        else:
            paths = [file_path]

        for file_path in paths:
            if is_excepted_file(file_path):
                continue

            if not Language.is_editable(file_path):
                continue

            language = Language.get_language(file_path)
            with open(file_path, 'rt') as file_:
                text = file_.read()

            count += 1
            if options.progress:
                sys.stdout.write('.')
                if count % 72 == 0:
                    sys.stdout.write('\n')
                if count % 5 == 0:
                    sys.stdout.flush()

            checker = UniversalChecker(
                file_path, text, language, reporter, options=options)
            checker.check()

    sys.stdout.flush()
    return reporter.call_count


def main(args=None):
    """
    Execute the checker.
    """
    if args is None:
        args = sys.argv[1:]

    options = parse_command_line(args=args)

    if not options.scope['include'] and not options.diff_branch:
        sys.stderr.write("Expected file paths or branch diff reference.\n")
        sys.exit(1)

    reporter = Reporter(Reporter.CONSOLE)
    reporter.error_only = not options.verbose
    return check_sources(options, reporter)


if __name__ == "__main__":
    main()
