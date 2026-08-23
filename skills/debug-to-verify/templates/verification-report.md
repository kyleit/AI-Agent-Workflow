# Verification Session Report: {{TITLE}}

- **Verification ID**: `{{VERIFICATION_ID}}`
- **Execution ID**: `{{EXECUTION_ID}}`
- **Debug Session ID**: `{{DEBUG_SESSION_ID}}`
- **Blueprint ID**: `{{BLUEPRINT_ID}}`
- **Version**: `{{VERSION}}`
- **Verification Outcome**: `{{VERIFICATION_OUTCOME}}`

---

## 1. Verification Activity Summary
- **Static Verification**: `PASS` (Schema, contract, route & hash checks)
- **Build Verification**: `NOT_RUN` / `PASS` (Static build check)
- **Test Execution**: `NOT_RUN` (No TEST_EXECUTION_APPROVAL)
- **Test Execution Owner**: `TESTER` Agent

## 2. Acceptance Criteria Mapping
| Criteria ID | Verification Method | Status | Limitations |
|---|---|---|---|
| `AC-01` | `STATIC_CHECK` | `SATISFIED` | Static analysis complete |
| `AC-02` | `UNIT_TEST` | `NOT_VERIFIED` | Test execution unauthorized (`NOT_RUN`) |

## 3. Architecture Conformance & Next Steps
- **Final Architecture Conformance**: `AWAITING_CONFORMANCE` (`review_type: FINAL_CONFORMANCE`)
- **Unverified Items**: `{{UNVERIFIED_ITEMS}}`
