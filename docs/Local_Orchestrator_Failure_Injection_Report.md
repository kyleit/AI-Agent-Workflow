# Local Orchestrator Failure Injection Report
| Drill ID | Failure Scenario | Target Node | Recovery Handler | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Kill subagent | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 2 | Corrupt backup checkpoint | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 3 | Lock lease timeout | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 4 | Fail and repair test | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 5 | Simulate provider timeout | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 6 | Token limit compression | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 7 | Orchestrator restart | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 8 | Supervisor restart | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 9 | Interrupt test runner | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 10 | Revision conflict rollback | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 11 | Queue state recovery | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 12 | Reassign stale agent | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 13 | Retry budget exhaustion | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 14 | Blocked dependencies checks | FEAT-201/205/207 | Automated Recovery / Retry | PASS |
| 15 | Invalid evidence validation | FEAT-201/205/207 | Automated Recovery / Retry | PASS |