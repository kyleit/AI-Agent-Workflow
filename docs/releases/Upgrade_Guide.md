# AIWF OS v1.0.0 Upgrade Guide

## 1. Prerequisites
- Đảm bảo Python 3.10+ đã được cài đặt và môi trường virtualenv sạch.

## 2. Upgrade Instructions
- Tải gói phân phối AIWF OS mới nhất.
- Chạy lệnh migration tự động:
  `python skills/workflow-runtime/scripts/workflow_runtime.py db-migrate`
