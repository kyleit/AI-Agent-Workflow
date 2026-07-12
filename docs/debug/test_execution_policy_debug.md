# Debug: Test Execution Policy Debugging

## Verification of Policies
We verify the correct behavior of the four execution policies:

| Policy | Phase | Tests Executed | Expected Log |
| :--- | :--- | :--- | :--- |
| `manual` | debug | No | `[INFO] Skipping pytest execution (policy: manual, phase: debug)` |
| `manual` | verify | Yes | Pytest runs |
| `verify_only` | debug | No | `[INFO] Skipping pytest execution (policy: verify_only, phase: debug)` |
| `verify_only` | verify | Yes | Pytest runs |
| `release_only` | debug | No | `[INFO] Skipping pytest execution (policy: release_only, phase: debug)` |
| `release_only` | verify | No | `[INFO] Skipping pytest execution (policy: release_only, phase: verify)` |
| `release_only` | release | Yes | Pytest runs |
| `always` | debug | Yes | Pytest runs |
| `always` | verify | Yes | Pytest runs |

## Caching Check
When running multiple tests without code modifications, we observe the following logs demonstrating cache hits:
`[INFO] Reusing cached successful test result for dedup_key <hash>.`
This confirms that the cached `test_outcome_<dedup_key>.json` is resolved successfully.
