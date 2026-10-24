# @path[tests/lint_commit/message.unit.test.py]

import pytest

from lint_commit.constants import TYPES
from lint_commit.message import MessageError, parse_message


def body(count: int) -> str:
    return "\n".join(f"- entry {index}" for index in range(count))


def test_head_without_scope() -> None:
    message = parse_message("feat: add a parser\n")
    assert message.head.type == "feat"
    assert message.head.scope is None
    assert not message.head.breaking
    assert message.head.description == "add a parser"


def test_head_with_scope_and_breaking_marker() -> None:
    message = parse_message("fix(api)!: drop the old route\n")
    assert message.head.type == "fix"
    assert message.head.scope == "api"
    assert message.head.breaking


@pytest.mark.parametrize("kind", TYPES)
def test_every_accepted_type_parses(kind: str) -> None:
    message = parse_message(f"{kind}: something\n")
    assert message.head.type == kind


def test_unknown_type_is_rejected() -> None:
    with pytest.raises(MessageError, match="header"):
        parse_message("featx: something\n")


def test_missing_space_after_colon_is_rejected() -> None:
    with pytest.raises(MessageError, match="header"):
        parse_message("feat:something\n")


def test_scope_with_underscore_is_rejected() -> None:
    with pytest.raises(MessageError, match="header"):
        parse_message("feat(api_v2): something\n")


def test_empty_message_is_rejected() -> None:
    with pytest.raises(MessageError, match="empty"):
        parse_message("")


def test_header_without_blank_line_is_rejected() -> None:
    with pytest.raises(MessageError, match="blank line"):
        parse_message("feat: something\n- entry\n")


def test_body_is_a_list_of_single_line_entries() -> None:
    text = f"feat: something\n\n{body(5)}\n"
    message = parse_message(text)
    assert message.body == tuple(f"entry {index}" for index in range(5))


def test_body_must_be_followed_by_a_blank_line_before_footer() -> None:
    text = f"feat: something\n\n{body(5)}\nBREAKING-CHANGE: detail\n"
    with pytest.raises(MessageError, match="blank line"):
        parse_message(text)


def test_footer_without_body() -> None:
    text = "feat!: something\n\nBREAKING-CHANGE: detail\n"
    message = parse_message(text)
    assert message.body == ()
    assert message.footers == (("BREAKING-CHANGE", "detail"),)


def test_multiple_footers() -> None:
    text = "feat: something\n\nBREAKING-CHANGE: detail\nREFERENCE-LINK: #12\n"
    message = parse_message(text)
    assert message.footers == (
        ("BREAKING-CHANGE", "detail"),
        ("REFERENCE-LINK", "#12"),
    )


def test_unknown_footer_mark_is_parsed() -> None:
    text = "feat: something\n\nReviewed-by: Z\n"
    message = parse_message(text)
    assert message.footers == (("Reviewed-by", "Z"),)


def test_crlf_is_accepted() -> None:
    entries = 5
    text = "feat: something\r\n\r\n" + body(entries).replace("\n", "\r\n") + "\r\n"
    message = parse_message(text)
    assert len(message.body) == entries


def test_trailing_blank_line_is_rejected_after_footer() -> None:
    text = "feat: something\n\nBREAKING-CHANGE: detail\n\n"
    with pytest.raises(MessageError, match="footer"):
        parse_message(text)
