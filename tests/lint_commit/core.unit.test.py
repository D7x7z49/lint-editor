# @path[tests/lint_commit/core.unit.test.py]

from lint_commit.core import derive_scope


def test_single_path_uses_its_parent() -> None:
    assert derive_scope(["src/api/parser.py"]) == "api"


def test_shared_parent() -> None:
    assert derive_scope(["src/api/a.py", "src/api/b.py"]) == "api"


def test_different_tops_have_no_scope() -> None:
    assert derive_scope(["src/a.py", "docs/b.md"]) is None


def test_root_files_have_no_scope() -> None:
    assert derive_scope(["a.py", "b.py"]) is None


def test_empty_list_has_no_scope() -> None:
    assert derive_scope([]) is None


def test_deeper_common_parent() -> None:
    assert derive_scope(["src/api/v1/a.py", "src/api/v1/b.py"]) == "v1"


def test_common_parent_stops_at_the_first_difference() -> None:
    assert derive_scope(["src/api/a.py", "src/ui/b.py"]) == "src"
