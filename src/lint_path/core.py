# @path[src/lint_path/core.py]
# ==============================================================================
# locate a contract, judge one path, and audit a tree

import subprocess
from pathlib import Path as FsPath

from pathspec import GitIgnoreSpec

from .constants import CONTRACT_FILE, REQUIRE, msg
from .matching import (
    PathGlobstar,
    PathLiteral,
    PathNode,
    PathPattern,
    PathStar,
    match_pattern,
)
from .projection import apply_mapping
from .rules import load_contract
from .schema import PathContract, PathFinding, PathRule, PathVerdict

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules"}

# ==============================================================================
# PATHS
# ==============================================================================


def load_ignore_spec(root: FsPath) -> GitIgnoreSpec | None:
    path = root / ".gitignore"
    if not path.is_file():
        return None
    return GitIgnoreSpec.from_lines(path.read_text(encoding="utf-8").splitlines())


def visible_tree(root: FsPath) -> set[FsPath] | None:
    # paths git would show, minus ignored paths
    spec = load_ignore_spec(root)
    try:
        result = subprocess.run(
            (
                "git",
                "-C",
                str(root),
                "ls-files",
                "-z",
                "--cached",
                "--others",
                "--exclude-standard",
            ),
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    visible: set[FsPath] = set()
    for name in result.stdout.split("\0"):
        if not name:
            continue
        if spec is not None and spec.match_file(name):
            continue
        current = root / name
        while current != root and root in current.parents:
            visible.add(current)
            current = current.parent
    return visible


def visible_children(directory: FsPath, visible: set[FsPath] | None) -> list[FsPath]:
    result: list[FsPath] = []

    for child in sorted(directory.iterdir()):
        if child.name in SKIP_DIRS or child.name == CONTRACT_FILE:
            continue
        if visible is not None and child not in visible:
            continue
        result.append(child)

    return result


def find_contracts(root: FsPath, visible: set[FsPath] | None = None) -> list[FsPath]:
    return sorted(
        path
        for path in root.rglob(CONTRACT_FILE)
        if not any(part in SKIP_DIRS for part in path.parts)
        and (visible is None or path in visible)
    )


def walk_tree(directory: FsPath, visible: set[FsPath] | None = None) -> list[FsPath]:
    nodes: list[FsPath] = []

    for child in visible_children(directory, visible):
        nodes.append(child)
        if child.is_dir() and not (child / CONTRACT_FILE).is_file():
            nodes.extend(walk_tree(child, visible))

    return nodes


# ==============================================================================
# LOCATE
# ==============================================================================


def locate(
    fs_path: FsPath,
    root: FsPath,
    cache: dict[FsPath, PathContract],
) -> PathContract | None:
    current = fs_path.parent

    while True:
        if current in cache:
            return cache[current]

        candidate = current / CONTRACT_FILE
        if candidate.is_file():
            contract = load_contract(candidate)
            cache[current] = contract
            return contract

        if current in (root, current.parent):
            return None
        current = current.parent


# ==============================================================================
# INDEX
# ==============================================================================


class ProjectionIndex:
    # one run parses each source contract and source tree once

    def __init__(self, visible: set[FsPath] | None = None) -> None:
        self._visible = visible
        self._contracts: dict[str, PathContract] = {}
        self._trees: dict[str, dict[str, bool]] = {}
        self._rules: dict[str, dict[str, PathRule]] = {}

    def contract(self, directory: str) -> PathContract:
        if directory not in self._contracts:
            self._contracts[directory] = load_contract(
                FsPath(directory) / CONTRACT_FILE
            )
        return self._contracts[directory]

    def tree(self, directory: str) -> dict[str, bool]:
        if directory not in self._trees:
            base = FsPath(directory)
            self._trees[directory] = {
                node.relative_to(base).as_posix(): node.is_dir()
                for node in walk_tree(base, self._visible)
            }
        return self._trees[directory]

    def rule(self, directory: str, name: str) -> PathRule | None:
        if directory not in self._rules:
            self._rules[directory] = {
                rule.name: rule for rule in self.contract(directory).rules
            }
        return self._rules[directory].get(name)


# ==============================================================================
# JUDGE
# ==============================================================================


def judge(
    contract: PathContract,
    fs_path: FsPath,
    index: ProjectionIndex | None = None,
) -> PathVerdict:
    if index is None:
        index = ProjectionIndex()
    directory = FsPath(contract.directory)

    try:
        relative = fs_path.relative_to(directory)
    except ValueError:
        return PathVerdict(allowed=False, reason=msg("path.missing"))

    segments = relative.parts
    is_dir = fs_path.is_dir()

    for rule in contract.rules:
        if match_pattern(rule.pattern, segments, is_dir=is_dir) and projection_ok(
            rule, relative.as_posix(), contract, index
        ):
            return PathVerdict(allowed=True, rule=rule)

    return PathVerdict(allowed=False, reason=msg("path.missing"))


def projection_ok(
    rule: PathRule,
    relative: str,
    contract: PathContract,
    index: ProjectionIndex,
) -> bool:
    if rule.projection is None:
        return True

    source_dir = contract.directory
    if rule.projection.source is not None:
        found = contract.imports.get(rule.projection.source)
        if found is None:
            return False
        source_dir = found

    source_rule = index.rule(source_dir, rule.projection.rule)
    if source_rule is None:
        return False

    image = apply_mapping(rule.projection, "/" + relative).lstrip("/")
    is_dir = index.tree(source_dir).get(image)
    if is_dir is None:
        return False

    return match_pattern(source_rule.pattern, tuple(image.split("/")), is_dir=is_dir)


def gate(fs_path: FsPath, root: FsPath) -> PathVerdict:
    if fs_path.name == CONTRACT_FILE:
        return PathVerdict(allowed=True)

    cache: dict[FsPath, PathContract] = {}
    index = ProjectionIndex(visible_tree(root))
    current = fs_path

    while True:
        contract = locate(current, root, cache)
        if contract is not None:
            verdict = judge(contract, current, index)
            if not verdict.allowed:
                return verdict

        if current == root:
            return PathVerdict(allowed=True)
        parent = current.parent
        if parent == current:
            return PathVerdict(allowed=True)
        current = parent


# ==============================================================================
# AUDIT
# ==============================================================================


def audit(root: FsPath, domain: FsPath | None = None) -> list[PathFinding]:
    if domain is not None:
        visible = None
        base = domain.parent
        paths = [
            path
            for path in find_contracts(base)
            if path == domain or base in path.parents
        ]
    else:
        visible = visible_tree(root)
        paths = find_contracts(root, visible)

    contracts = [load_contract(path) for path in paths]
    findings: list[PathFinding] = []
    index = ProjectionIndex(visible)

    for contract in contracts:
        directory = FsPath(contract.directory)
        nodes = walk_tree(directory, visible)

        findings.extend(check_capacity(contract, directory, nodes, visible))

        for node in nodes:
            verdict = judge(contract, node, index)
            if not verdict.allowed:
                findings.append(
                    PathFinding(
                        path=str(node),
                        domain=contract.directory,
                        rule=verdict.rule,
                        reason=verdict.reason or "",
                    )
                )

        for rule in contract.rules:
            if rule.mode != REQUIRE:
                continue
            if not obligation_satisfied(rule, directory, nodes, visible):
                findings.append(
                    PathFinding(
                        path=None,
                        domain=contract.directory,
                        rule=rule,
                        reason=msg("domain.obligation", rule=rule.name),
                    )
                )

    return findings


def check_capacity(
    contract: PathContract,
    directory: FsPath,
    nodes: list[FsPath],
    visible: set[FsPath] | None = None,
) -> list[PathFinding]:
    findings: list[PathFinding] = []

    node_max = capacity_limit(contract.header, "node_max")
    depth_max = capacity_limit(contract.header, "depth_max")
    degree_max = capacity_limit(contract.header, "degree_max")

    if node_max is not None and len(nodes) > node_max:
        findings.append(
            PathFinding(
                path=None,
                domain=contract.directory,
                rule=None,
                reason=msg("domain.capacity.node", count=len(nodes), max=node_max),
            )
        )

    for node in nodes:
        relative = node.relative_to(directory)
        depth = len(relative.parts)

        if depth_max is not None and depth > depth_max:
            findings.append(
                PathFinding(
                    path=str(node),
                    domain=contract.directory,
                    rule=None,
                    reason=msg("domain.capacity.depth", depth=depth, max=depth_max),
                )
            )

        if degree_max is not None and node.is_dir():
            degree = len(visible_children(node, visible))
            if degree > degree_max:
                findings.append(
                    PathFinding(
                        path=str(node),
                        domain=contract.directory,
                        rule=None,
                        reason=msg(
                            "domain.capacity.degree", degree=degree, max=degree_max
                        ),
                    )
                )

    return findings


def capacity_limit(header: dict[str, str], key: str) -> int | None:
    value = header.get(key)
    if value is None or value == "inf":
        return None
    return int(value)


def obligation_satisfied(
    rule: PathRule,
    directory: FsPath,
    nodes: list[FsPath],
    visible: set[FsPath] | None = None,
) -> bool:
    # every sibling matched by the parent part must carry the last part
    if rule.pattern.is_dir:
        return any(
            match_pattern(rule.pattern, node.relative_to(directory).parts, is_dir=True)
            for node in nodes
        )

    parent = PathPattern(rule.pattern.nodes[:-1], is_dir=True)
    last = rule.pattern.nodes[-1]

    if not parent.nodes:
        return any(
            match_last_segment(last, child.name)
            for child in visible_children(directory, visible)
        )

    for node in nodes:
        if not node.is_dir():
            continue
        if not match_pattern(parent, node.relative_to(directory).parts, is_dir=True):
            continue
        if not any(
            match_last_segment(last, child.name)
            for child in visible_children(node, visible)
        ):
            return False

    return True


def match_last_segment(node: PathNode, name: str) -> bool:
    if isinstance(node, PathGlobstar):
        return True
    if isinstance(node, PathStar):
        return bool(name)
    if isinstance(node, PathLiteral):
        return bool(node.regex.fullmatch(name))
    return False
