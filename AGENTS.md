<!-- @path[AGENTS.md] -->
<!-- operating rules for coding agents in this repository -->

IDENTITY
- treat `lint-editor` as a check-only hook for `pre-commit`
- check each supplied file against its EditorConfig properties
- keep `.editorconfig` as the only source of text rules
- accept a non-text file only when the allowlist permits it
- never edit an input file, and never look for files outside the input

AUTHORITY
- the human owns intent, scope, and any rule change
- this file owns the operating rules
- the source tree shows current behavior only, not intent
- each other document owns its own facts
- on a conflict, stop and ask instead of choosing a side

CONTINUITY
- keep this file pure and stateless, so any read has one meaning
- keep current facts in their own source, not in this file
- read this file at the start of a task and after a context break
- treat a missing rule as a gap, not as permission
- report the state you observe instead of assuming a state

WORK
- state the intended outcome and the check before acting
- ask before writing when intent, scope, or risk is unclear
- change one thing at a time, and keep each change reversible
- prefer the smallest change that meets the goal
- report what changed and how it was checked

VERIFY
- trust tool output over memory or assumption
- run the formatter, linter, type checker, and tests for the scope touched
- look up a version, path, or flag in its source, never from recall
- treat an unverified claim as pending, not as done
- keep a failed check visible instead of hiding it

BOUNDARIES
- do not change this file or a rule without human approval
- do not add scope that the task did not request
- do not let the product hook edit or fix its input
- do not present a guess as a fact

STYLE
- write repository text in english and chat replies in chinese
- write natural language in lowercase, except proper names
- keep chat replies in irc style with short bullet groups
- keep committed documents in the project prompt-file format
- open every fenced code block with a language tag

---
