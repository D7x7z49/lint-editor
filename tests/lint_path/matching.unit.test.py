# @path[tests/lint_path/matching.unit.test.py]

from lint_path.matching import match_pattern, parse_pattern


def check(pattern: str, path: str, *, is_dir: bool = False) -> bool:
    segments = tuple(part for part in path.split("/") if part)
    return match_pattern(parse_pattern(pattern), segments, is_dir=is_dir)


def test_root() -> None:
    assert check("/", "", is_dir=True)


def test_literal_file() -> None:
    assert check("/a", "a")
    assert not check("/a", "b")


def test_literal_dir() -> None:
    assert check("/a/", "a", is_dir=True)
    assert not check("/a/", "a")


def test_star_matches_one_segment() -> None:
    assert check("/a/*", "a/b")
    assert not check("/a/*", "a/b/c")


def test_globstar_matches_zero_or_more() -> None:
    assert check("/a/**", "a")
    assert check("/a/**", "a/b/c")


def test_class() -> None:
    assert check("/[a-z][a-z0-9_]*", "hello")
    assert not check("/[a-z][a-z0-9_]*", "Hello")


def test_alternation() -> None:
    assert check("/{spec,test}", "spec")
    assert check("/{spec,test}", "test")
    assert not check("/{spec,test}", "other")


def test_escape() -> None:
    assert check(r"/a\.b", "a.b")
    assert not check(r"/a\.b", "axb")


def test_group_repeat() -> None:
    assert check("/(a/b){2}", "a/b/a/b")
    assert check("/(a/b){2,3}", "a/b/a/b/a/b")
    assert not check("/(a/b){2}", "a/b/a/b/a/b")


def test_group_with_globstar() -> None:
    assert check("/(a/**/b){2}", "a/x/b/a/b")
