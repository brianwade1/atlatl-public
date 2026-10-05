# Daily regression and readiness

Run from the repository root:

```text
uv run python -B -m tests.support.regression core --coverage
uv run python -B -m tests.support.regression full --coverage
uv run python -B -m tests.support.regression core --repeat --coverage
uv run python -B -m tests.support.regression full --repeat --coverage
```

Repeat runs normal collection twice, then reverse collection once. Fresh fixtures
use distinct disposable workspaces, coverage data, reports and JUnit results.
Existing fixed child hash/RNG seeds remain in effect. Errors stop the runner and
preserve pytest's nonzero status. Empty selections, missing prerequisites,
unexpected failures and strict XPASS fail; no retries are enabled.

Artifacts live under `tests/.artifacts/core-1` or `full-1`, with `-2` and `-3`
for repetitions. `python.json` contains statement/branch data; `html/index.html`
is navigable. `javascript/summary.json` reports observed/executed V8 function
ranges per original browser script; per-case JSON retains node IDs and counts.
`playwright/` retains failure traces/screenshots independently for each pass.
CDP source hashes distinguish inline blocks with overlapping offsets and merge
identical sources across pages. Loaded inline HTML scripts are included. Module top-level ranges count as
functions. Unloaded scripts are absent: counts are not a whole-source percentage.
`browser/replay.js` is replay input data and is excluded: workflow tests route
generated fixture data at that URL, rather than loading original source code.
CDP collection precedes page/context closure, including multiple contexts and
navigations. JavaScript branch/statement coverage and non-Chromium coverage are
not claimed. No instrumented production copy is used.

Coverage 7.16.1 / pytest-cov 7.1.0 use `patch = subprocess`. The runner sets
absolute source/config/data paths before pytest starts; changed child working
directories retain them. The S17 child probe verifies measured body lines in
`Status.dscoreKill`, which its parent never imports. No numerical threshold is
imposed yet. Namespace directories remain in the denominator even when core
does not import their source. Interface stubs and demos remain in the denominator; no exclusions
inflate totals. For manual coverage commands, set `ATLATL_COVERAGE_ROOT` and
`COVERAGE_FILE` to absolute repository/test-local paths before starting pytest.

Start each session by reading the plan, progress and known issues, then inspect
Git status. Select node IDs/paths, run focused checks, then affected regression
suites. Record counts, durations, skips/XFAIL, defects and protection reports.
The default core includes AI/import probes; S17 measured roughly 125–137 seconds
with coverage after removing redundant import cleanup lookups. This exceeds the
original roughly one-minute budget; use targeted paths during iteration. Full
CPU/Chromium passes took approximately 13.6 minutes on this host. Timings diagnose slow
cases rather than test algorithmic correctness. Transport/browser/CPU ML checks
retain bounded deadlines and finite inputs; no training batch is a daily gate.

Readiness requires chosen P0/P1 cases to execute, individually documented
defects/skips, real parity/generated-replay integration, browser error checks,
owned-process teardown and unchanged protected content. Proposed engine targets
remain 90% statements and 85% branches for map/unit/status/game. Coverage does
not approve characterized defects. Linux/macOS, alternate browser engines and
GPU remain unverified. Mutation diagnostics are optional and were not performed.

PROGRESS.md's source-to-test manifest uses stable pytest node IDs as case IDs:
`tests/<suite>/<file>.py::test_<condition>[parameter]`. File-prefix rows own all
cases in that file; AI_MATRIX.md and S16_MATRIX.md refine alias/helper scope.
Renaming cases requires updating ownership. Saved models/scenarios/sample data
remain read-only inputs without blanket runtime assertions.
