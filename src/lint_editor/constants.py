# @path[src/lint_editor/constants.py]

PROGRAM = "lint-editor"

# git reads at most this many bytes to decide whether a file is binary
BINARY_SNIFF_BYTES = 8000

# editorconfig values this hook can verify
INDENT_STYLES = {"space", "tab"}
BOOLEAN_TRUE = "true"

# messages, printed as "{path}: {message}"
MESSAGE_NO_RULES = "no .editorconfig rule matches this file"
MESSAGE_NOT_DECLARED = "non-text file without a .gitattributes declaration"
MESSAGE_CHARSET = "content does not match charset {value}"
MESSAGE_END_OF_LINE = "line ending does not match {value}"
MESSAGE_FINAL_NEWLINE = "file does not end with a newline"
MESSAGE_TRAILING_WHITESPACE = "line {line} has trailing whitespace"
MESSAGE_INDENT_STYLE = "line {line} does not use {value} indentation"
MESSAGE_LINE_LENGTH = "line {line} exceeds max_line_length {value}"
