# Confirmed issues

No production defects have been runtime-confirmed by S01 or S02. The K01–K18 entries in
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

S02 harness issue (resolved): pytest-playwright's session-scoped synchronous
driver retained a running event loop after browser cases, causing the subsequent
pytest-asyncio cases to fail with `Runner.run() cannot be called from a running
event loop`. The test-local conftest now reuses the plugin's driver/browser
fixture bodies with function scope, so teardown stops the driver before the next
test. This is a harness lifecycle issue, not a production defect or an xfail.
