# @path[tests/editorconfig.unit.test.py]

from lint_editor.editorconfig import validate_property


def test_unknown_property_passes() -> None:
    assert validate_property("unknown", b"x", "y") is None


def test_charset_utf8() -> None:
    assert validate_property("charset", b"ok\n", "utf-8") is None
    assert validate_property("charset", b"\xff\xfe", "utf-8") is not None
    assert validate_property("charset", b"\xef\xbb\xbfx", "utf-8") is not None


def test_charset_utf8_bom() -> None:
    assert validate_property("charset", b"\xef\xbb\xbfx", "utf-8-bom") is None
    assert validate_property("charset", b"x", "utf-8-bom") is not None


def test_charset_utf16() -> None:
    assert validate_property("charset", "hi\n".encode("utf-16le"), "utf-16le") is None
    assert validate_property("charset", "hi\n".encode("utf-16be"), "utf-16be") is None
    assert validate_property("charset", b"\xff", "utf-16le") is not None


def test_charset_unsupported_is_skipped() -> None:
    assert validate_property("charset", b"\xff", "latin1") is None


def test_end_of_line() -> None:
    assert validate_property("end_of_line", b"a\nb\n", "lf") is None
    assert validate_property("end_of_line", b"a\r\nb\n", "lf") is not None
    assert validate_property("end_of_line", b"a\r\nb\r\n", "crlf") is None
    assert validate_property("end_of_line", b"a\nb\n", "crlf") is not None
    assert validate_property("end_of_line", b"a\rb\r", "cr") is None
    assert validate_property("end_of_line", b"a\nb", "cr") is not None


def test_insert_final_newline() -> None:
    assert validate_property("insert_final_newline", b"a\n", "true") is None
    assert validate_property("insert_final_newline", b"a", "true") is not None
    assert validate_property("insert_final_newline", b"a", "false") is None


def test_trim_trailing_whitespace() -> None:
    assert validate_property("trim_trailing_whitespace", b"a\n", "true") is None
    assert validate_property("trim_trailing_whitespace", b"a \n", "true") is not None
    assert validate_property("trim_trailing_whitespace", b"a \n", "false") is None


def test_indent_style() -> None:
    assert validate_property("indent_style", b"    a\n", "space") is None
    assert validate_property("indent_style", b"\ta\n", "space") is not None
    assert validate_property("indent_style", b"\ta\n", "tab") is None
    assert validate_property("indent_style", b"  a\n", "tab") is not None


def test_max_line_length() -> None:
    assert validate_property("max_line_length", b"abc\n", "3") is None
    assert validate_property("max_line_length", b"abcd\n", "3") is not None
    assert validate_property("max_line_length", b"abcd\n", "off") is None
    assert validate_property("max_line_length", b"abcd\n", "x") is None
    assert validate_property("max_line_length", b"abcd\n", "0") is None
