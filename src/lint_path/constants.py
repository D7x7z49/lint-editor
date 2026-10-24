# @path[src/lint_path/constants.py]
# ==============================================================================
# fixed values and every message the tool can print

# ==============================================================================
# NAMES
# ==============================================================================

PROGRAM = "lint-path"
CONTRACT_FILE = ".pathbase"

# ==============================================================================
# MODES
# ==============================================================================

ALLOW = "allow"
REQUIRE = "require"
MODES = (ALLOW, REQUIRE)

# ==============================================================================
# KEYS
# ==============================================================================

# flags live before the first rule, controls sit next to a rule
FLAG_KEYS = (
    "node_max",
    "depth_max",
    "degree_max",
    "set_name",
    "default_mode",
    "separator",
)
RULE_KEYS = ("name", "description", "mode", "projection")

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
    "cli.parser.description": "check paths against .pathbase contracts",
    "cli.audit.help": "check every domain under the scan root",
    "cli.root.help": "limit scanning to this directory",
    "cli.domain.help": "use this .pathbase instead of discovery",
    "cli.paths.missing": "pass at least one path, or use --audit",
    "cli.format.help": "output format, text or json",
    "contract.file.missing": "no contract file at [{path}]",
    "contract.line.unknown": "[{path}:{line}] has an unknown form [{text}]",
    "contract.key.unknown": "[{path}:{line}] uses an unknown key [{key}]",
    "contract.mode.invalid": "[{path}:{line}] uses an invalid mode [{mode}]",
    "contract.limit.invalid": "[{path}:{line}] has an invalid value for {key} [{value}]",
    "contract.require.last": "[{path}:{line}] require rule must end with a single segment",
    "contract.directive.invalid": "[{path}:{line}] has an invalid directive [{text}]",
    "contract.directive.late": "[{path}:{line}] has a directive after the first rule [{text}]",
    "contract.import.cycle": "[{path}:{line}] imports [{target}] in a cycle",
    "contract.import.name": "[{path}:{line}] imports [{target}] without set_name or as",
    "contract.projection.missing": "[{path}] projection references an unknown rule [{name}]",
    "contract.control.orphan": "[{path}:{line}] has a control without a rule",
    "contract.pattern.invalid": "[{path}:{line}] has an invalid pattern ({reason})",
    "path.missing": "no rule matches this path",
    "path.capacity": "this path exceeds a capacity bound",
    "domain.obligation": "a required path is missing [{rule}]",
    "domain.capacity.depth": "depth [{depth}] exceeds depth_max [{max}]",
    "domain.capacity.degree": "degree [{degree}] exceeds degree_max [{max}]",
    "domain.capacity.node": "node count [{count}] exceeds node_max [{max}]",
    "git.failed": "cannot run git ({reason})",
}


def msg(template_key: str, **values: object) -> str:
    # fill one message template, keep the key visible when it is unknown
    template = MESSAGES.get(template_key, template_key)
    return template.format(**values)
