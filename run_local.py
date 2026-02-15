#!/usr/bin/env python3
"""로컬 테스트 실행 스크립트.

사용법:
    python run_local.py daily              # 일간 브리핑 (실제 Discord 발송)
    python run_local.py daily --dry-run    # 일간 브리핑 (발송 없이 출력만)
    python run_local.py update             # 장마감 MOVE 업데이트
    python run_local.py update --dry-run
    python run_local.py weekly             # 주간 리포트
    python run_local.py weekly --dry-run
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import main


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    dry_run = "--dry-run" in sys.argv

    if mode not in ("daily", "update", "weekly"):
        print("사용법: python run_local.py [daily|update|weekly] [--dry-run]")
        sys.exit(1)

    main(mode=mode, dry_run=dry_run)
