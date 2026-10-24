# @path[src/lint_path/rules.py]
# ==============================================================================
# read one .pathbase file into a contract

import hashlib
from dataclasses import dataclass, field, replace
from pathlib import Path

from .constants import (
    ALLOW,
    CONTRACT_FILE,
    FLAG_KEYS,
    MODES,
    REQUIRE,
    RULE_KEYS,
    msg,
)
from .matching import PathGlobstar, PathLiteral, PathNode, PathStar, parse_pattern
from .projection import parse_projection
from .schema import PathContract, PathContractError, PathRule

LIMIT_KEYS = ("node_max", "depth_max", "degree_max")

# ==============================================================================
# STATE
# ==============================================================================


@dataclass
class _State:
    header: dict[str, str] = field(default_factory=dict)
    rules: list[PathRule] = field(default_factory=list)
    imported: list[PathRule] = field(default_factory=list)
    imports: dict[str, str] = field(default_factory=dict)
    sources: dict[str, set[str]] = field(default_factory=dict)
    control: dict[str, str] = field(default_factory=dict)
    in_rules: bool = False


# ==============================================================================
# PARSE
# ==============================================================================


def parse_contract(
    text: str,
    path: Path,
    directory: Path,
    seen: frozenset[Path] = frozenset(),
) -> PathContract:
    state = _State()
    lines = text.splitlines()

    for number, raw in enumerate(lines, start=1):
        parse_line(state, raw.strip(), number, path, seen)

    if state.control:
        raise PathContractError(
            msg("contract.control.orphan", path=path, line=len(lines))
        )

    rules = merge_rules(state.imported, state.rules)
    check_projections(rules, state.sources, path)

    return PathContract(
        directory=str(directory),
        rules=rules,
        header=state.header,
        imports=state.imports,
    )


def check_projections(
    rules: tuple[PathRule, ...],
    sources: dict[str, set[str]],
    path: Path,
) -> None:
    names = {rule.name for rule in rules}

    for rule in rules:
        if rule.projection is None:
            continue
        available = names
        if rule.projection.source is not None:
            available = sources.get(rule.projection.source, set())
        if rule.projection.rule not in available:
            raise PathContractError(
                msg("contract.projection.missing", path=path, name=rule.projection.rule)
            )


def parse_line(
    state: _State,
    line: str,
    number: int,
    path: Path,
    seen: frozenset[Path],
) -> None:
    if not line:
        return
    if line.startswith("#"):
        parse_comment(state, line[1:].strip(), number, path, seen)
        return
    if line.startswith("/"):
        state.in_rules = True
        state.rules.append(make_rule(line, state.control, state.header, path, number))
        state.control = {}
        return
    raise PathContractError(
        msg("contract.line.unknown", path=path, line=number, text=line)
    )


def parse_comment(
    state: _State,
    body: str,
    number: int,
    path: Path,
    seen: frozenset[Path],
) -> None:
    if not body:
        return
    if body.startswith("@"):
        if body.startswith("@path["):
            return
        if state.in_rules:
            raise PathContractError(
                msg("contract.directive.late", path=path, line=number, text=body)
            )
        parse_directive(state, body, number, path, seen)
        return
    if not body.startswith("$"):
        return

    key, value = parse_key_value(body[1:], path, number)

    if key in RULE_KEYS:
        state.in_rules = True
        state.control[key] = value
    elif state.in_rules:
        raise PathContractError(
            msg("contract.key.unknown", path=path, line=number, key=key)
        )
    elif key in FLAG_KEYS:
        if key in LIMIT_KEYS:
            check_limit(key, value, path, number)
        state.header[key] = value
    else:
        raise PathContractError(
            msg("contract.key.unknown", path=path, line=number, key=key)
        )


MIN_DIRECTIVE_WORDS = 2
ALIAS_WORDS = 4


def parse_directive(
    state: _State,
    body: str,
    number: int,
    path: Path,
    seen: frozenset[Path],
) -> None:
    words = body[1:].split()
    if len(words) < MIN_DIRECTIVE_WORDS:
        raise PathContractError(
            msg("contract.directive.invalid", path=path, line=number, text=body)
        )

    kind, target_text = words[0], words[1]
    alias = words[3] if len(words) >= ALIAS_WORDS and words[2] == "as" else None

    if kind not in {"import", "require"}:
        raise PathContractError(
            msg("contract.directive.invalid", path=path, line=number, text=body)
        )

    target = (path.parent / target_text).resolve()
    if target.is_dir():
        target = target / CONTRACT_FILE

    if target in seen:
        raise PathContractError(
            msg("contract.import.cycle", path=path, line=number, target=target)
        )

    if not target.is_file():
        raise PathContractError(msg("contract.file.missing", path=target, line=number))

    nested = parse_contract(
        target.read_text(encoding="utf-8"),
        target,
        target.parent,
        seen | {path},
    )

    namespace = alias or nested.header.get("set_name")
    if namespace is None:
        raise PathContractError(
            msg("contract.import.name", path=path, line=number, target=target)
        )

    state.imports[namespace] = nested.directory
    state.sources[namespace] = {rule.name for rule in nested.rules}

    if kind == "import":
        state.imported.extend(replace(rule, source=namespace) for rule in nested.rules)


def parse_key_value(text: str, path: Path, number: int) -> tuple[str, str]:
    if "=" not in text:
        raise PathContractError(
            msg("contract.line.unknown", path=path, line=number, text=text)
        )
    key, value = text.split("=", 1)
    return key.strip(), value.strip()


def check_limit(key: str, value: str, path: Path, number: int) -> None:
    if value == "inf":
        return
    try:
        int(value)
    except ValueError as error:
        raise PathContractError(
            msg("contract.limit.invalid", path=path, line=number, key=key, value=value)
        ) from error


def single_segment(nodes: tuple[PathNode, ...]) -> bool:
    # a require rule needs one concrete last segment to look for
    return bool(nodes) and isinstance(nodes[-1], (PathLiteral, PathStar, PathGlobstar))


def make_rule(
    line: str,
    control: dict[str, str],
    header: dict[str, str],
    path: Path,
    number: int,
) -> PathRule:
    try:
        pattern = parse_pattern(line)
    except ValueError as error:
        raise PathContractError(
            msg("contract.pattern.invalid", path=path, line=number, reason=error)
        ) from error

    mode = control.get("mode", header.get("default_mode", ALLOW))
    if mode not in MODES:
        raise PathContractError(
            msg("contract.mode.invalid", path=path, line=number, mode=mode)
        )

    if mode == REQUIRE and not single_segment(pattern.nodes):
        raise PathContractError(msg("contract.require.last", path=path, line=number))

    name = control.get("name") or hash_name(line)
    projection = None
    if "projection" in control:
        separator = header.get("separator", "|")
        try:
            projection = parse_projection(control["projection"], separator)
        except ValueError as error:
            raise PathContractError(
                msg("contract.pattern.invalid", path=path, line=number, reason=error)
            ) from error

    return PathRule(
        name=name,
        pattern=pattern,
        mode=mode,
        projection=projection,
    )


def hash_name(pattern: str) -> str:
    # a stable fallback identity for a rule without an explicit name
    return hashlib.sha256(pattern.encode("utf-8")).hexdigest()[:7]


# ==============================================================================
# MERGE
# ==============================================================================


def merge_rules(
    imported: list[PathRule],
    local: list[PathRule],
) -> tuple[PathRule, ...]:
    # local rules replace an imported rule by name, then by set_name.name
    by_name = {rule.name: rule for rule in imported}

    for rule in local:
        if "." in rule.name:
            source, name = rule.name.split(".", 1)
            for key, value in tuple(by_name.items()):
                if value.source == source and value.name == name:
                    del by_name[key]
                    break
        else:
            by_name.pop(rule.name, None)
        by_name[rule.name] = rule

    return tuple(by_name.values())


# ==============================================================================
# LOAD
# ==============================================================================


def load_contract(path: Path) -> PathContract:
    if not path.is_file():
        raise PathContractError(msg("contract.file.missing", path=path))
    return parse_contract(path.read_text(encoding="utf-8"), path, path.parent)
