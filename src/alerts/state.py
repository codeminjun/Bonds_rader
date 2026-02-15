from datetime import datetime

from src.storage.json_store import load_alert_state, save_alert_state


def is_alert_active(alert_type: str) -> bool:
    """해당 alert_type이 현재 활성(미해제) 상태인지 확인."""
    state = load_alert_state()
    return alert_type in state and state[alert_type].get("resolved_at") is None


def activate_alert(alert_type: str, message: str) -> bool:
    """알림 활성화. 이미 활성 상태면 False 반환 (중복 방지)."""
    if is_alert_active(alert_type):
        return False  # 이미 활성 → 발송 안 함

    state = load_alert_state()
    state[alert_type] = {
        "triggered_at": datetime.utcnow().isoformat(),
        "resolved_at": None,
        "message": message,
    }
    save_alert_state(state)
    return True  # 신규 활성 → 발송 필요


def resolve_alert(alert_type: str) -> bool:
    """알림 해제. 활성 상태였으면 True 반환 (복귀 메시지 발송 필요)."""
    state = load_alert_state()
    if alert_type not in state:
        return False
    if state[alert_type].get("resolved_at") is not None:
        return False  # 이미 해제됨

    state[alert_type]["resolved_at"] = datetime.utcnow().isoformat()
    save_alert_state(state)
    return True  # 해제됨 → 복귀 메시지 발송


def get_alert_info(alert_type: str) -> dict | None:
    """활성 알림 정보 조회."""
    state = load_alert_state()
    return state.get(alert_type)
