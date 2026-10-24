<!-- @path[README.md] -->
# lint-editor

[![ci](https://github.com/D7x7z49/lint-editor/actions/workflows/ci.yml/badge.svg)](https://github.com/D7x7z49/lint-editor/actions/workflows/ci.yml)

pre-commit hooks that enforce EditorConfig text rules, explicit non-text declarations, and conventional commit messages.

## why

language formatters cover their own language. the rest of the repository has no shared rule, so three kinds of noise slip through:

- a non-text file arrives unannounced, and it may carry a secret
- a text file drifts from the conventions, and its diff stops being readable
- a commit type is a claim, and nothing checks it against the change

two hooks close the gap with contracts already in the repository:

- `lint-editor` reads `.editorconfig` for text rules and `.gitattributes` for non-text admission
- `lint-commit` reads `lint-commit.toml` for path rules and checks the message against them

both hooks check and never edit, so the gate stays apart from formatting.

## install

add the hooks to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/D7x7z49/lint-editor
    rev: v0.2.0

    hooks:
      - id: lint-editor
      - id: lint-commit
```

then install both stages:

```bash
pre-commit install --hook-type pre-commit --hook-type commit-msg
```

the hooks need the `git` command, which pre-commit already needs.
the only python dependencies are [editorconfig](https://pypi.org/project/editorconfig) and [pathspec](https://pypi.org/project/pathspec).

## lint-editor

### how it works

pre-commit passes the staged paths to the hook. for each path:

- an ignored path is skipped
- a text file is checked against its `.editorconfig` properties
- a non-text file passes only when `.gitattributes` declares it non-text

a non-text file without a declaration fails, so the allowlist stays explicit.
a text file with no matching `.editorconfig` rule fails, so the repository must configure one.

#### text or non-text

a file counts as non-text when its first 8000 bytes contain a NUL byte.
this is the rule git uses, so the hook and git agree.

#### the allowlist is `.gitattributes`

there is no separate allowlist file. declare a non-text file in `.gitattributes`:

```gitattributes
assets/logo.png binary
docs/report.pdf -text
```

nested `.gitattributes` files and git precedence apply as usual, because the hook resolves attributes with `git check-attr`.

#### the ignore list is `lint-editor.ignore`

some files hold intentionally malformed input, such as test data.
list them in `lint-editor.ignore`, either at the repository root or in `config/`:

```gitignore
# test data holds intentionally malformed inputs
tests/data/
```

- one gitignore style pattern per line
- `#` starts a comment, blank lines are ignored
- a match skips the file before any check
- both locations are read when present, and every pattern is relative to the repository root
- a missing file excludes nothing
- `--ignore-file PATH` replaces the auto discovery and may be repeated

### checks

the hook verifies these `.editorconfig` properties:

- `charset`
- `end_of_line`
- `insert_final_newline`
- `trim_trailing_whitespace`
- `indent_style`
- `max_line_length`

`indent_size` and `tab_width` are not checked, because file content cannot verify them without false positives.

### usage

run the tool directly on paths:

```bash
lint-editor src/app.py README.md
```

exit codes:

- `0` every input passes
- `1` one or more findings
- `2` the tool itself failed, such as a broken `.editorconfig`

## lint-commit

### how it works

pre-commit passes the commit message file to the hook at the `commit-msg` stage.
the hook reads the staged paths from the git index, then:

- every staged path resolves to the last `[rules]` entry that matches it
- all resolved type sets are intersected
- an empty intersection means the changes span incompatible rules, so the commit should be split
- the message type must lie in the intersection
- the message scope must equal the deepest shared directory name, or be empty at the repository root

a path with no matching rule fails, so every area must be declared.

### configuration

place `lint-commit.toml` at the repository root or under `config/`:

```toml
[types]
feat = "new feature"
fix = "bug fix"
docs = "documentation only"
chore = "maintenance work"

[rules]
"**" = ["chore"]
"src/**" = ["feat", "fix", "refactor", "perf"]
"docs/**" = ["docs"]
```

- `[types]` lists the accepted types and a short description.
- `[rules]` maps a gitignore style pattern to the types that path may use.
- rules are read in file order, and the last match wins.
- a nested path is covered by the rule that matches it last, so put a catch-all first.

### message shape

```text
type(scope)!: description

- body entry
- body entry
- body entry
- body entry
- body entry

BREAKING-CHANGE: breaking detail
REFERENCE-LINK: https://example.com/spec
```

- the description must be 32 to 72 characters, counted after the colon and space.
- the body is optional. when present it must be a list of 5 to 9 single line entries.
- `BREAKING-CHANGE` may appear once and must be 32 to 128 characters.
- only `!` or `BREAKING-CHANGE` may declare a breaking change, and both must agree.

### reference footers

reference marks start with `REFERENCE-`, and the value is checked with a regular expression.
five marks are built in:

- `REFERENCE-LINK` an absolute URL
- `REFERENCE-GITHUB` `#123` or `owner/repo#123`
- `REFERENCE-GITLAB` `#123` or `group/project#123`
- `REFERENCE-COMMIT` a short or full commit hash
- `REFERENCE-FILE` a repository path

add or override a mark in the config:

```toml
[reference]
"TICKET" = '^TICKET-[0-9]+$'
```

a config entry with the same name as a built in mark replaces it.

### usage

run the tool on a message file:

```bash
lint-commit .git/COMMIT_EDITMSG
```

without a message file it reads `.git/COMMIT_EDITMSG`.
without `--config` the hook looks for `lint-commit.toml` at the root or under `config/`.
`--config PATH` replaces the auto discovery.

exit codes:

- `0` the message passes
- `1` the message is rejected, with one reason
- `2` the tool or the config failed

merge commits and `fixup!` or `squash!` commits are skipped.

## development

run `make help` for all targets.

```bash
make install     # sync dependencies
make all         # lint, typecheck, and test
make self-test   # run the editor hook on the repository
```

## license

MIT license, see `LICENSE`.
