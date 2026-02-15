from datetime import datetime

from src.alerts.thresholds import determine_risk_color
from config import COLOR_WARNING, COLOR_DANGER, COLOR_SAFE


def _weekday_kr(date_str: str) -> str:
    """날짜 문자열 → 한글 요일."""
    days = ["월", "화", "수", "목", "금", "토", "일"]
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return days[dt.weekday()]


def _format_change(current: float, prev: float | None, unit: str = "") -> str:
    """전일 대비 변동 포맷."""
    if prev is None:
        return ""
    diff = current - prev
    arrow = "▲" if diff > 0 else "▼" if diff < 0 else "―"
    return f"(전일 {prev:+.0f}{unit} {arrow})" if unit == "bp" else f"(전일 대비 {diff:+.1f}% {arrow})"


def build_daily_briefing(rate_data: dict | None, move_data: dict | None) -> dict:
    """일간 브리핑 Embed 생성. 일부 데이터 누락 시에도 동작."""
    date = (rate_data or move_data or {}).get("date", "N/A")
    spread_bp = rate_data.get("spread_bp") if rate_data else None
    move_index = move_data.get("move_index") if move_data else None
    color = determine_risk_color(spread_bp, move_index)

    fields = []

    if rate_data:
        spread_value = f"{rate_data['spread_bp']:+.0f}bp"
        if rate_data.get("prev_spread_bp") is not None:
            prev_bp = rate_data["prev_spread_bp"]
            diff = rate_data["spread_bp"] - prev_bp
            arrow = "▲" if diff > 0 else "▼" if diff < 0 else "―"
            spread_value += f" (전일 {prev_bp:+.0f}bp {arrow})"
        fields.append({"name": "SOFR", "value": f"{rate_data['sofr']:.2f}%", "inline": True})
        fields.append({"name": "IORB", "value": f"{rate_data['iorb']:.2f}%", "inline": True})
        fields.append({"name": "스프레드", "value": spread_value, "inline": True})
    else:
        fields.append({"name": "SOFR/IORB", "value": "수집 실패", "inline": True})

    if move_data:
        move_value = f"{move_data['move_index']:.1f}"
        if move_data.get("change_pct") is not None:
            pct = move_data["change_pct"]
            arrow = "▲" if pct > 0 else "▼" if pct < 0 else "―"
            move_value += f" (전일 대비 {pct:+.1f}% {arrow})"
        fields.append({"name": "MOVE", "value": move_value, "inline": False})
    else:
        fields.append({"name": "MOVE", "value": "수집 실패", "inline": False})

    return {
        "embeds": [{
            "title": f"📊 일간 브리핑 | {date.replace('-', '.')} ({_weekday_kr(date) if date != 'N/A' else '?'})",
            "color": color,
            "fields": fields,
            "footer": {"text": f"데이터 기준: {date} 종가"},
        }]
    }


def build_weekly_report(
    weekly_rates: list[dict],
    weekly_moves: list[dict],
    cot_data: dict | None,
) -> dict:
    """주간 리포트 Embed 생성."""
    # 날짜 범위
    if weekly_rates:
        start = weekly_rates[0]["date"].replace("-", ".")
        end = weekly_rates[-1]["date"].replace("-", ".")
    elif weekly_moves:
        start = weekly_moves[0]["date"].replace("-", ".")
        end = weekly_moves[-1]["date"].replace("-", ".")
    else:
        start = end = "N/A"

    # 최신 값으로 색상 결정
    latest_spread = weekly_rates[-1]["spread_bp"] if weekly_rates else None
    latest_move = weekly_moves[-1]["move_index"] if weekly_moves else None
    color = determine_risk_color(latest_spread, latest_move)

    fields = []

    # SOFR 스프레드 추이
    if weekly_rates:
        spreads = " / ".join(
            f"{_weekday_kr(r['date'])} {r['spread_bp']:+.0f}"
            for r in weekly_rates
        )
        fields.append({"name": "SOFR 스프레드 (bp)", "value": spreads, "inline": False})

    # MOVE 추이
    if weekly_moves:
        moves_str = " / ".join(
            f"{_weekday_kr(r['date'])} {r['move_index']:.0f}"
            for r in weekly_moves
        )
        if len(weekly_moves) >= 2:
            first = weekly_moves[0]["move_index"]
            last = weekly_moves[-1]["move_index"]
            if first != 0:
                week_pct = (last - first) / first * 100
                moves_str += f" (주간 {week_pct:+.1f}%)"
        fields.append({"name": "MOVE 지수", "value": moves_str, "inline": False})

    # COT 데이터
    if cot_data:
        net = cot_data["leveraged_net_position"]
        oi = cot_data["open_interest"]
        cot_value = f"Net Short: {net:,}"
        if cot_data.get("prev_net_position") is not None:
            prev_net = cot_data["prev_net_position"]
            pct = cot_data.get("net_change_pct", 0)
            cot_value += f" (전주 {prev_net:,}, {pct:+.1f}%)"
        cot_value += f"\n미결제약정: {oi:,}"
        if cot_data.get("prev_net_position") is not None:
            # 미결제약정 전주 비교는 별도 저장 필요 → 현재는 생략
            pass
        fields.append({"name": "COT 10Y Treasury (Leveraged Funds)", "value": cot_value, "inline": False})

    footer_text = f"{start} ~ {end}"
    if cot_data:
        footer_text += f" | COT: {cot_data['report_date']} 기준"

    return {
        "embeds": [{
            "title": f"📋 주간 리포트 | {start} ~ {end.split('.')[-1] if '.' in end else end}",
            "color": color,
            "fields": fields,
            "footer": {"text": footer_text},
        }]
    }


def build_move_update(move_data: dict) -> dict:
    """장마감 MOVE 업데이트 Embed."""
    color = determine_risk_color(None, move_data["move_index"])
    pct = move_data.get("change_pct", 0)
    arrow = "▲" if pct > 0 else "▼"

    return {
        "embeds": [{
            "title": "🔄 MOVE 장마감 업데이트",
            "color": color,
            "description": f"현재 {move_data['move_index']:.1f} (전일 대비 {pct:+.1f}% {arrow})",
            "footer": {"text": f"{move_data['date']} 종가 기준"},
        }]
    }


# --- 임계값 경고 Embeds ---

def build_sofr_alert(spread_bp: float, sofr: float, iorb: float, prev_spread: float | None, date: str) -> dict:
    """SOFR 스프레드 경고 Embed."""
    desc = f"현재 {spread_bp:+.0f}bp (SOFR {sofr:.2f}% / IORB {iorb:.2f}%)"
    if prev_spread is not None:
        desc += f"\n전일 {prev_spread:+.0f}bp"
    return {
        "embeds": [{
            "title": "⚠️ SOFR 스프레드 +5bp 초과",
            "color": COLOR_WARNING,
            "description": desc,
            "footer": {"text": f"{date} 기준"},
        }]
    }


def build_move_alert(move_index: float, change_pct: float | None, date: str, level: str) -> dict:
    """MOVE 지수 경고 Embed."""
    threshold = 140 if level == "danger" else 120
    icon = "🔴" if level == "danger" else "⚠️"
    color = COLOR_DANGER if level == "danger" else COLOR_WARNING

    desc = f"현재 {move_index:.1f}"
    if change_pct is not None:
        desc += f" (전일 대비 {change_pct:+.1f}%)"

    return {
        "embeds": [{
            "title": f"{icon} MOVE {threshold} 돌파",
            "color": color,
            "description": desc,
            "footer": {"text": f"{date} 종가 기준"},
        }]
    }


def build_composite_alert(spread_bp: float, move_index: float, date: str) -> dict:
    """복합 경고 Embed."""
    return {
        "embeds": [{
            "title": "🔴 복합 경고 발생",
            "color": COLOR_DANGER,
            "fields": [
                {
                    "name": "SOFR 스프레드",
                    "value": f"{spread_bp:+.0f}bp ⚠️ (임계값 +5bp 초과)",
                    "inline": False,
                },
                {
                    "name": "MOVE 지수",
                    "value": f"{move_index:.1f} 🔴",
                    "inline": False,
                },
            ],
            "footer": {"text": f"{date} 종가 기준"},
        }]
    }


def build_cot_alert(cot_data: dict) -> dict:
    """COT 급변 경고 Embed."""
    net = cot_data["leveraged_net_position"]
    prev = cot_data.get("prev_net_position")
    pct = cot_data.get("net_change_pct", 0)

    desc = f"Leveraged Funds Net Short\n{net:,}"
    if prev is not None:
        desc += f" (전주 {prev:,})"
    desc += f"\n변동률: {pct:+.1f}%"

    return {
        "embeds": [{
            "title": "⚠️ COT 포지션 급변 (10Y Treasury)",
            "color": COLOR_WARNING,
            "description": desc,
            "footer": {"text": f"COT 데이터: {cot_data['report_date']} 기준"},
        }]
    }


def build_recovery_alert(alert_type: str, current_value: float, triggered_at: str, date: str) -> dict:
    """정상 복귀 Embed."""
    labels = {
        "sofr_spread": ("SOFR 스프레드", "5bp 이하로 복귀"),
        "move_warning": ("MOVE", "120 이하로 복귀"),
        "move_danger": ("MOVE", "140 이하로 복귀"),
        "cot_change": ("COT 변동", "정상 범위 복귀"),
        "composite": ("복합 경고", "해제"),
    }
    label, desc_suffix = labels.get(alert_type, (alert_type, "정상 복귀"))

    triggered_date = triggered_at[:10] if triggered_at else "N/A"

    return {
        "embeds": [{
            "title": f"✅ {label} 정상 복귀",
            "color": COLOR_SAFE,
            "description": f"현재 {current_value:.1f} ({desc_suffix})\n경고 발생: {triggered_date}",
            "footer": {"text": f"{date} 기준"},
        }]
    }
