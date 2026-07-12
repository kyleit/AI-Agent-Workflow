# Brainstorming: FEAT Manual Test Execution

## Context & Rationale
Automatic running of tests after every implementation cycle or file modification degrades performance, consumes extensive CPU/RAM resources, and causes test execution overhead in environments that don't need it. 

To address this, we introduce an **Explicit / On-Demand Test Execution Policy**. Tests are decoupled from implicit execution hooks and are only invoked when explicitly requested by a user, Verify workflow, or Release workflow.

## Execution Policies
We define four configuration options under `test_execution.execution_policy` in `runtime-policy.json`:
1. `manual` (default): No automatic tests. Runs only when explicitly requested.
2. `verify_only`: Tests run only during verification/final gates.
3. `release_only`: Tests run only when executing a release.
4. `always`: Legacy behavior (always run tests).

## Support Subcommands
We expand the `/test` commands with specific target selectors:
- `/test unit` -> pytest `skills/*/tests/unit/`
- `/test integration` -> pytest `skills/*/tests/integration/`
- `/test browser` -> pytest `skills/*/tests/browser/`
- `/test e2e` -> pytest `skills/*/tests/e2e/`
- `/test changed` -> pytest for changed test files
- `/test affected` -> test impact analysis resolved tests
- `/test all` -> runs full pytest suite

## Caching Outcomes
To further save resources, if the test coordinator determines that the target test scope and git revision have not changed since the last successful execution, it will reuse the cached `test_outcome_<dedup_key>.json` on disk, bypassing new pytest subprocess invocation unless overridden by `--force`.
