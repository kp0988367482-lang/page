#!/usr/bin/env bash
# 全站一致性稽核與自我修復。
#   bash check.sh          只檢查
#   bash check.sh --fix    先自動修好能修的，再檢查剩下的
exec python3 "$(dirname "$0")/sitecheck.py" "$@"
