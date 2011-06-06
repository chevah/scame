// Copyright (C) 2009-2010 - Curtis Hovey <sinzui.is at verizon.net>
// This software is licensed under the MIT license (see the file COPYING).

function report_implied_names() {
    // Report about implied global names.
    var implied_names = [];
    var prop;
    for (prop in JSLINT.implied) {
        if (JSLINT.implied.hasOwnProperty(prop)) {
            implied_names.push(prop);
            }
        }
    if (implied_names.length > 0) {
        implied_names.sort();
        return '0::0::Implied globals:' + implied_names.join(', ');
        }
    return '';
    }


function report_lint_errors() {
    // Report about lint errors.
    var errors = [];
    var i;
    for (i = 0; i < JSLINT.errors.length; i++) {
        var error = JSLINT.errors[i];
        if (error === null) {
            error = {
                'line': -1,
                'character': -1,
                'reason': 'JSLINT had a fatal error.'
                };
            }
        // Fix the line and character offset for editors.
        error.line += 1;
        error.character += 1;
        errors.push(
            [error.line, error.character, error.reason].join('::'));
        }
    return errors.join('\n');
    }


function lint_script(source_script) {
    // Lint the source and report errors.
    var result = JSLINT(source_script);
    if (! result) {
        var issues = [];
        errors = report_lint_errors();
        if (errors) {
            issues.push(errors);
            }
        implied = report_implied_names();
        if (implied) {
            issues.push(implied);
            }
        window.status = '::::' + issues.join('\n');
        }
    }
