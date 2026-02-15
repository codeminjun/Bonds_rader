from config import (
    SOFR_SPREAD_WARNING,
    MOVE_WARNING,
    MOVE_DANGER,
    MOVE_WATCH,
    MOVE_INTRADAY_THRESHOLD,
    COT_NET_CHANGE_WARNING,
    COLOR_SAFE,
    COLOR_WATCH,
    COLOR_WARNING,
    COLOR_DANGER,
)


def check_sofr_spread(spread_bp: float) -> dict | None:
    """SOFR 스프레드 임계값 체크. 초과 시 경고 dict 반환."""
    if spread_bp > SOFR_SPREAD_WARNING:
        return {
            "alert_type": "sofr_spread",
            "level": "warning",
            "value": spread_bp,
            "threshold": SOFR_SPREAD_WARNING,
        }
    return None


def check_move(move_index: float) -> dict | None:
    """MOVE 지수 임계값 체크. 초과 시 경고 dict 반환."""
    if move_index > MOVE_DANGER:
        return {
            "alert_type": "move_danger",
            "level": "danger",
            "value": move_index,
            "threshold": MOVE_DANGER,
        }
    if move_index > MOVE_WARNING:
        return {
            "alert_type": "move_warning",
            "level": "warning",
            "value": move_index,
            "threshold": MOVE_WARNING,
        }
    return None


def check_move_intraday(change_pct: float | None) -> bool:
    """장마감 업데이트 시 발송 여부 판단."""
    if change_pct is None:
        return False
    return abs(change_pct) >= MOVE_INTRADAY_THRESHOLD


def check_cot_change(net_change_pct: float | None) -> dict | None:
    """COT 포지션 변동 임계값 체크."""
    if net_change_pct is None:
        return None
    if abs(net_change_pct) >= COT_NET_CHANGE_WARNING:
        return {
            "alert_type": "cot_change",
            "level": "warning",
            "value": net_change_pct,
            "threshold": COT_NET_CHANGE_WARNING,
        }
    return None


def check_composite(spread_bp: float | None, move_index: float | None) -> dict | None:
    """복합 경고 체크: SOFR 스프레드 > 5bp AND MOVE > 120."""
    if spread_bp is None or move_index is None:
        return None
    if spread_bp > SOFR_SPREAD_WARNING and move_index > MOVE_WARNING:
        return {
            "alert_type": "composite",
            "level": "danger",
            "spread_bp": spread_bp,
            "move_index": move_index,
        }
    return None


def determine_risk_color(spread_bp: float | None, move_index: float | None) -> int:
    """현재 위험도에 따른 Discord Embed 색상 반환."""
    s = spread_bp or 0
    m = move_index or 0

    # 🔴 위험: (SOFR > 5bp AND MOVE > 120) OR MOVE > 140
    if (s > SOFR_SPREAD_WARNING and m > MOVE_WARNING) or m > MOVE_DANGER:
        return COLOR_DANGER
    # 🟠 경고: SOFR > 5bp OR MOVE > 120
    if s > SOFR_SPREAD_WARNING or m > MOVE_WARNING:
        return COLOR_WARNING
    # 🟡 관망: MOVE 100~120
    if m >= MOVE_WATCH:
        return COLOR_WATCH
    # 🟢 안정
    return COLOR_SAFE
