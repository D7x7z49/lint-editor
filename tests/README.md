<!-- @path[tests/README.md] -->
<!-- test philosophy for lint-editor -->

PURPOSE
- verify necessary conditions only
- no suite covers infinite input space
- focus on high-importance inputs
- consolidate the logic you trust
- rely on monitoring and fast rollback for untested areas

SCOPES
- mirror the `src` package tree under `tests/<package>/`
- name each file after the module and the scope, as `*.unit.test.py`
- keep `data/` on the same package and subject path
- keep `e2e/` as a separate tree for test modules
- keep e2e cases under `tests/data/e2e/<package>/<case>/project/`
- keep e2e test modules under `tests/e2e/<package>/`

DATA
- pair input and expected output in one case directory
- use `stdin.txt` for a single input file
- use `project/` for an e2e input tree
- keep e2e input trees under `tests/data/e2e/`
- store `stdout.txt` and `stderr.txt` only when the case checks them
- keep exit codes in the test code
- keep data paths in `conftest.py`, not in test modules
- let fixtures return a `Path` to the prepared input

CONFTEST
- keep shared fixtures in `tests/conftest.py`
- keep package data fixtures in `tests/<package>/conftest.py`
- keep e2e case preparation in `tests/e2e/conftest.py`
- let tests request named fixtures instead of composing data paths

UNIT TESTS
- file pattern: `*.unit.test.py`
- one test per cyclomatic complexity branch
- no external calls, use in-memory fakes

COMPONENT TESTS
- file pattern: `*.component.test.py`
- cover the main scenarios of a public interface
- cover critical exceptions too

INTEGRATION TESTS
- file pattern: `*.integration.test.py`
- test only the component combinations actually used
- mock only at component boundaries

END-TO-END TESTS
- file pattern: `*.e2e.test.py`
- keep the count between five and fifteen
- include only workflows with direct business impact

EXTERNAL DEPENDENCIES
- unit tests: no external calls
- component tests: stub all external dependencies
- integration tests: mock at boundaries, test real interactions once safe
- e2e tests: use real dependencies in a controlled environment

COVERAGE
- do not treat coverage as a goal
- use coverage only to find uncovered high-importance inputs

REVIEW
- ask these five questions before committing a test
- without this test, does confidence in key logic drop
- on failure, must the fix be immediate or can it wait
- in three months, will the reason for this test be clear
- where would the system break if this test is deleted
- does the test cover logic or implementation details

COMMENTS
- add unix-style comments only for non-obvious assertions or data setup
- keep comments short
- use prepositions instead of colons or dashes
- for example, write `# check for empty list`, not `# verify empty list returns zero: edge case`

LIMITS
- this approach is not suitable for safety-critical or life-critical systems
- rely on monitoring and fast rollback for untested areas

---
