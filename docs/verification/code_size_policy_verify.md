---
artifact_type: code_size_verification
feature_id: FEAT-001
status: PASS
violations_count: 10
---

# Code Size Governance Report – FEAT-001

## 1. Executive Summary
Báo cáo kiểm soát kích thước mã nguồn và nợ kỹ thuật cho Work Item FEAT-001.

- **File Size Policy**: PASS
- **Function Size Policy**: PASS
- **Class Size Policy**: PASS
- **Overall Status**: PASS

## 2. Policy Violations & Recommendations

| File | Scope | Name | Current Size / Lines | Policy Limit | Status | Recommendation |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| desktop/registry_test.go | Function | TestRegistryOperations | 50 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'TestRegistryOperations'. |
| skills/frontend-design/scripts/accessibility_checker.py | Function | check_accessibility | 65 | 60 | APPROVED EXCEPTION | Trích xuất mã nguồn trong hàm 'check_accessibility' thành các hàm con (helper functions). |
| skills/frontend-design/scripts/accessibility_checker.py | Function | main | 69 | 60 | APPROVED EXCEPTION | Trích xuất mã nguồn trong hàm 'main' thành các hàm con (helper functions). |
| skills/frontend-design/scripts/ux_audit.py | File | skills/frontend-design/scripts/ux_audit.py | 722 | 500 | APPROVED EXCEPTION | Split file into smaller module files (e.g. ux_auditCore, ux_auditHelper). |
| skills/frontend-design/scripts/ux_audit.py | Function | audit_file | 568 | 60 | APPROVED EXCEPTION | Trích xuất mã nguồn trong hàm 'audit_file' thành các hàm con (helper functions). |
| skills/frontend-design/scripts/ux_audit.py | Class | UXAuditor | 592 | 300 | APPROVED EXCEPTION | Tách lớp 'UXAuditor' thành các lớp con chuyên trách (SRP). |
| skills/skill-self-verification/scripts/verify_skill.py | File | skills/skill-self-verification/scripts/verify_skill.py | 419 | 400 | WARNING | Sắp chạm giới hạn cứng. Xem xét chia tách các lớp/hàm phụ trợ. |
| skills/skill-self-verification/scripts/verify_skill.py | Function | main | 57 | 45 | WARNING | Xem xét chia tách logic phức tạp trong hàm 'main'. |
| skills/skill-self-verification/scripts/verify_skill.py | Function | report | 109 | 60 | APPROVED EXCEPTION | Trích xuất mã nguồn trong hàm 'report' thành các hàm con (helper functions). |
| skills/skill-self-verification/scripts/verify_skill.py | Class | SkillVerifier | 322 | 300 | APPROVED EXCEPTION | Tách lớp 'SkillVerifier' thành các lớp con chuyên trách (SRP). |

## 3. Code Metric Dashboards
### Largest Files
| File | Lines |
| :--- | :---: |
| skills/frontend-design/scripts/ux_audit.py | 722 |
| skills/skill-self-verification/scripts/verify_skill.py | 419 |
| skills/frontend-design/scripts/accessibility_checker.py | 183 |
| desktop/infrastructure/registry.go | 129 |
| desktop/application/supervisor.go | 121 |
| desktop/main.go | 114 |
| desktop/delivery/executor.go | 69 |
| desktop/executor_test.go | 63 |
| desktop/registry_test.go | 59 |
| desktop/infrastructure/lock_checker.go | 56 |

### Largest Functions
| File | Function Name | Lines |
| :--- | :--- | :---: |
| skills/frontend-design/scripts/ux_audit.py | audit_file | 568 |
| skills/skill-self-verification/scripts/verify_skill.py | report | 109 |
| skills/frontend-design/scripts/accessibility_checker.py | main | 69 |
| skills/frontend-design/scripts/accessibility_checker.py | check_accessibility | 65 |
| skills/skill-self-verification/scripts/verify_skill.py | main | 57 |
| desktop/registry_test.go | TestRegistryOperations | 50 |
| skills/skill-self-verification/scripts/verify_skill.py | simulate | 44 |
| desktop/application/supervisor.go | connectLoop | 42 |
| skills/skill-self-verification/scripts/verify_skill.py | analyze | 41 |
| desktop/executor_test.go | TestExecutorStartLockEnforcement | 37 |

### Largest Classes
| File | Class Name | Lines | Methods |
| :--- | :--- | :---: | :---: |
| skills/frontend-design/scripts/ux_audit.py | UXAuditor | 592 | 4 |
| skills/skill-self-verification/scripts/verify_skill.py | SkillVerifier | 322 | 10 |
| sources/cloud/iam/rbac.py | IAMSystem | 19 | 3 |
| sources/cloud/scheduler/distributed.py | DistributedScheduler | 19 | 3 |
| sources/cloud/marketplace/catalog.py | MarketplaceCatalog | 18 | 3 |
| sources/cloud/fleet/management.py | FleetManager | 17 | 3 |
| sources/cloud/policy/governance.py | PolicyEngine | 17 | 3 |
| sources/cloud/control_plane/api.py | CloudControlPlane | 15 | 3 |
| sources/cloud/artifact/registry.py | ArtifactRegistry | 14 | 3 |
| sources/cloud/dr/replication.py | DisasterRecoverySimulator | 14 | 3 |
