# @path[src/lint_commit/constants.py]
# ==============================================================================
# fixed values and every message the tool can print

# ==============================================================================
# NAMES
# ==============================================================================

PROGRAM = "lint-commit"

# the configuration file is looked up next to the repository root
CONFIG_FILE = "commit-config.toml"

# ==============================================================================
# TYPES
# ==============================================================================

TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)

# ==============================================================================
# FOOTER MARKS
# ==============================================================================

BREAKING_MARK = "BREAKING-CHANGE"

# reference marks are written as REFERENCE-NAME, the name comes from config
REFERENCE_PREFIX = "REFERENCE-"

# built in reference marks, a config entry with the same name overrides one
REFERENCE_FOOTERS: dict[str, str] = {
    "LINK": r"^https?://\S+$",
    "GITHUB": r"^(#[0-9]+|[\w.-]+/[\w.-]+#[0-9]+)$",
    "GITLAB": r"^(#[0-9]+|[\w.-]+(/[\w.-]+)*#[0-9]+)$",
    "COMMIT": r"^[0-9a-f]{7,40}$",
    "FILE": r"^[\w./-]+$",
}

# ==============================================================================
# LIMITS
# ==============================================================================

# closed intervals, both bounds are accepted
DESCRIPTION_LENGTH = (32, 72)
BREAKING_LENGTH = (32, 128)
BODY_ITEMS = (5, 9)

# ==============================================================================
# EXIT CODES
# ==============================================================================

STATUS_OK = 0
STATUS_REJECTED = 1
STATUS_ERROR = 2

# ==============================================================================
# MESSAGES
# ==============================================================================

# keys read as scope.object.trait, values hold square bracketed variables
MESSAGES: dict[str, str] = {
    "cli.parser.description": "check a commit message against the configured path rules",
    "cli.config.help": "configuration file, default [{path}]",
    "cli.message.help": "commit message file, default [.git/COMMIT_EDITMSG]",
    "config.file.missing": "configuration file not found at [{path}]",
    "config.file.invalid": "[{path}] {reason}",
    "config.table.missing": "missing [{table}] table",
    "config.table.empty": "[{table}] must not be empty",
    "config.type.unknown": "unknown type [{name}], allowed types are [{allowed}]",
    "config.type.value": "type [{name}] must map to a description string",
    "config.rule.path": "rule [{pattern}] must map to a non-empty array",
    "config.rule.type": "rule [{pattern}] has unknown type [{name}]",
    "config.reference.pattern": "reference [{name}] has an invalid pattern ({reason})",
    "config.key.unexpected": "unexpected top key [{name}], top keys come before any table",
    "pattern.glob.negated": "negated pattern [{pattern}] is not supported",
    "pattern.glob.invalid": "invalid pattern [{pattern}] ({reason})",
    "git.run.failed": "cannot run git ({reason})",
    "git.read.failed": "cannot read the staged paths ({reason})",
    "message.file.failed": "cannot read the message file [{path}] ({reason})",
    "message.text.empty": "message is empty",
    "message.head.syntax": "header must follow [type(scope)!] then a colon, a space, and a description",
    "message.head.blank": "header must be followed by a blank line",
    "message.body.blank": "body must be followed by a blank line",
    "message.foot.syntax": "footer must follow [MARK] then a colon, a space, and a value, got [{line}]",
    "message.tail.content": "unexpected content after the footer section",
    "verdict.syntax.invalid": "message does not match the strict format ({reason})",
    "verdict.description.length": "description has [{count}] characters, expected [{low}] to [{high}]",
    "verdict.body.count": "body has [{count}] entries, expected [{low}] to [{high}]",
    "verdict.foot.marker": "breaking marker is [{actual}], expected [{expected}]",
    "verdict.foot.breaking": "breaking footer must appear at most once",
    "verdict.foot.length": "footer [{mark}] has [{count}] characters, expected [{low}] to [{high}]",
    "verdict.foot.mark": "unknown footer mark [{mark}], allowed marks are [{allowed}]",
    "verdict.foot.value": "footer [{mark}] value does not match its pattern",
    "verdict.path.uncovered": "no rule matches path [{path}]",
    "verdict.path.split": "allowed type set is empty, the changes span incompatible rules",
    "verdict.type.mismatch": "type [{value}] is not allowed, allowed types are [{allowed}]",
    "verdict.scope.invalid": "directory [{scope}] cannot be used as a scope",
    "verdict.scope.mismatch": "scope is [{actual}], expected [{expected}]",
}


def msg(key: str, **values: object) -> str:
    return MESSAGES[key].format(**values)
