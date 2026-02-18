import json

from config import DISCORD_WEBHOOK_URL
from src.http_client import request_with_retry


def send_discord_message(payload: dict, dry_run: bool = False) -> bool:
    """Discord 웹훅으로 메시지 발송. dry_run=True면 출력만."""
    if dry_run:
        print("[DRY RUN] Discord payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return True

    if not DISCORD_WEBHOOK_URL:
        print("[ERROR] DISCORD_WEBHOOK_URL이 설정되지 않았습니다.")
        return False

    resp = request_with_retry("POST", DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    if resp.status_code == 204:
        print("[OK] Discord 메시지 발송 성공")
        return True
    else:
        print(f"[ERROR] Discord 발송 실패: {resp.status_code} {resp.text}")
        return False
