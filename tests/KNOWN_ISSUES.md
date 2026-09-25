# Confirmed issues

No production defects have been runtime-confirmed by S01. The K01–K18 entries in
`../test_plan.md` remain an investigation queue, not expected failures.

When a later step reproduces an issue, record its stable ID, minimal pytest node
ID and command, expected result, exact observed result/exception, affected suites,
and whether it is a required contract or characterization. Use individual strict
xfails with `raises=KnownDefect` from `tests.support.isolation`. Raise that exception
only after matching the documented wrong signature. Unexpected failures must
propagate, and an unexpected pass must fail. Do not patch production code.

Environment note: this Windows sandbox denied pytest's restricted temporary
directories and Playwright subprocess named pipes. Running the same suite with
approved execution outside the sandbox passed. This is not a production defect
or a reason to skip the browser test. Browser installation is a separate explicit
setup step; missing plugins/binaries fail instead of producing skipped successes.
