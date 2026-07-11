# AIWF OS v1.0.0 Rollback Guide

## 1. Git Rollback
- Revert commit phát hành và khôi phục về trạng thái baseline cũ:
  `git stash pop` hoặc `git reset --hard HEAD~1`

## 2. DB Reversion
- Khôi phục file backup `.agents/runtime/journal.db.bak` về `.agents/runtime/journal.db`.
