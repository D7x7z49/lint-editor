<!-- @path[README.md] -->
# lint-editor

[![ci](https://github.com/D7x7z49/lint-editor/actions/workflows/ci.yml/badge.svg)](https://github.com/D7x7z49/lint-editor/actions/workflows/ci.yml)

a pre-commit hook that enforces [EditorConfig](https://editorconfig.org) rules on text files and requires an explicit declaration for non-text files.

## why

language formatters cover their own language. the rest of the repository, such as docs, config, and data, has no shared rule. two kinds of noise slip through:

- a non-text file arrives unannounced, and it may carry a secret
- a text file drifts from the conventions, and its diff stops being readable

this hook closes the gap with two contracts already in the repository:

- `.editorconfig` states the text rules, so every text file is checked the same way, whatever its language
- `.gitattributes` states which non-text files are admitted, so a binary passes only when declared

the hook checks and never edits, so the gate stays apart from formatting.

## install

add the hook to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/D7x7z49/lint-editor
    rev: v0.1.0
    hooks:
      - id: lint-editor
```

then run `pre-commit install`.

the hook needs the `git` command, which pre-commit already needs.
its only python dependency is the [editorconfig](https://pypi.org/project/editorconfig) core library.

## how it works

pre-commit passes the staged paths to the hook. for each path:

- a text file is checked against its `.editorconfig` properties
- a non-text file passes only when `.gitattributes` declares it non-text

a non-text file without a declaration fails, so the allowlist stays explicit.
a text file with no matching `.editorconfig` rule fails, so the repository must configure one.

### text or non-text

a file counts as non-text when its first 8000 bytes contain a NUL byte.
this is the rule git uses, so the hook and git agree.

### the allowlist is `.gitattributes`

there is no separate allowlist file. declare a non-text file in `.gitattributes`:

```gitattributes
assets/logo.png binary
docs/report.pdf -text
```

nested `.gitattributes` files and git precedence apply as usual, because the hook resolves attributes with `git check-attr`.

## checks

the hook verifies these `.editorconfig` properties:

- `charset`
- `end_of_line`
- `insert_final_newline`
- `trim_trailing_whitespace`
- `indent_style`
- `max_line_length`

`indent_size` and `tab_width` are not checked, because file content cannot verify them without false positives.

## usage

run the tool directly on paths:

```bash
lint-editor src/app.py README.md
```

exit codes:

- `0` every input passes
- `1` one or more findings
- `2` the tool itself failed, such as a broken `.editorconfig`

## development

run `make help` for all targets.

```bash
make install     # sync dependencies
make all         # lint, typecheck, and test
make self-test   # run this hook on the repository
```

## license

MIT license, see `LICENSE`.
