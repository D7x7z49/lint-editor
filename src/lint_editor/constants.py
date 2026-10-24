# @path[src/lint_editor/constants.py]
# ==============================================================================
# fixed values and every message the tool can print

# ==============================================================================
# NAMES
# ==============================================================================

PROGRAM = "lint-editor"

# ==============================================================================
# LIMITS
# ==============================================================================

# git reads at most this many bytes to decide whether a file is binary
BINARY_SNIFF_BYTES = 8000

# ==============================================================================
# EDITORCONFIG VALUES
# ==============================================================================

INDENT_STYLES = {"space", "tab"}
BOOLEAN_TRUE = "true"

# ==============================================================================
# GIT ATTRIBUTES
# ==============================================================================

# ask git to resolve the two attributes that mark a path as non-text
ATTRIBUTE_COMMAND = ("git", "check-attr", "--stdin", "-z", "binary", "text")
NON_TEXT_VALUES = {b"binary": b"set", b"text": b"unset"}

# ==============================================================================
# IGNORE FILES
# ==============================================================================

IGNORE_FILE = "lint-editor.ignore"
IGNORE_DIRS = ("", "config")

# ==============================================================================
# EXIT CODES
# ==============================================================================

STATUS_OK = 0
STATUS_FINDINGS = 1
STATUS_ERROR = 2

# ==============================================================================
# MESSAGES
# ==============================================================================

# keys read as scope.object.trait, values hold square bracketed variables
MESSAGES: dict[str, str] = {
    "cli.parser.description": "check files against their editorconfig properties",
    "cli.ignore.help": "ignore file, repeatable, replaces auto discovery",
    "cli.paths.help": "paths to check",
    "check.no_rules": "no .editorconfig rule matches this file",
    "check.not_declared": "non-text file without a .gitattributes declaration",
    "check.charset": "content does not match charset [{value}]",
    "check.end_of_line": "line ending does not match [{value}]",
    "check.final_newline": "file does not end with a newline",
    "check.trailing_whitespace": "line [{line}] has trailing whitespace",
    "check.indent_style": "line [{line}] does not use [{value}] indentation",
    "check.line_length": "line [{line}] exceeds max_line_length [{value}]",
    "git.run.failed": "cannot run git ({reason})",
    "git.attributes.failed": "git check-attr failed with exit code [{code}]",
    "ignore.negated": "[{path}] line [{line}] uses a negated pattern, which is not supported",
    "path.failed": "[{path}] {reason}",
}


def msg(key: str, **values: object) -> str:
    return MESSAGES[key].format(**values)
