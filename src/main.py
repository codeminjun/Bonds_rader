import sys
import os
from datetime import datetime, timezone, timedelta

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.collectors.sofr import collect_sofr
from src.collectors.move import collect_move
from src.collectors.cot import collect_cot
from src.storage.json_store import (
    get_weekly_rates, get_weekly_moves, get_latest_cot,
    get_latest_rate, get_latest_move,
)
from src.alerts.thresholds import (
    check_sofr_spread, check_move, check_move_intraday,
    check_cot_change, check_composite,
)
from src.alerts.state import is_alert_active, activate_alert, resolve_alert, get_alert_info
from src.discord.webhook import send_discord_message
from src.discord.embeds import (
    build_daily_briefing, build_weekly_report, build_move_update,
    build_sofr_alert, build_move_alert, build_composite_alert,
    build_cot_alert, build_recovery_alert,
)


def _process_alerts(rate_data: dict | None, move_data: dict | None, dry_run: bool = False) -> None:
    """임계값 체크 → 경고/복귀 알림 발송."""
    date = (rate_data or move_data or {}).get("date", "N/A")

    # SOFR 스프레드 체크
    if rate_data:
        sofr_alert = check_sofr_spread(rate_data["spread_bp"])
        if sofr_alert:
            if activate_alert("sofr_spread", f"스프레드 {rate_data['spread_bp']:+.0f}bp"):
                payload = build_sofr_alert(
                    rate_data["spread_bp"], rate_data["sofr"], rate_data["iorb"],
                    rate_data.get("prev_spread_bp"), date,
                )
                send_discord_message(payload, dry_run=dry_run)
        else:
            if resolve_alert("sofr_spread"):
                info = get_alert_info("sofr_spread")
                payload = build_recovery_alert(
                    "sofr_spread", rate_data["spread_bp"],
                    info["triggered_at"] if info else "", date,
                )
                send_discord_message(payload, dry_run=dry_run)

    # MOVE 체크
    if move_data:
        move_alert = check_move(move_data["move_index"])
        if move_alert:
            alert_type = move_alert["alert_type"]
            if activate_alert(alert_type, f"MOVE {move_data['move_index']:.1f}"):
                payload = build_move_alert(
                    move_data["move_index"], move_data.get("change_pct"),
                    date, move_alert["level"],
                )
                send_discord_message(payload, dry_run=dry_run)
        else:
            # MOVE가 정상 범위로 복귀했는지 체크
            for at in ["move_danger", "move_warning"]:
                if resolve_alert(at):
                    info = get_alert_info(at)
                    payload = build_recovery_alert(
                        at, move_data["move_index"],
                        info["triggered_at"] if info else "", date,
                    )
                    send_discord_message(payload, dry_run=dry_run)

    # 복합 경고 체크
    if rate_data and move_data:
        comp = check_composite(rate_data["spread_bp"], move_data["move_index"])
        if comp:
            if activate_alert("composite", "복합 경고"):
                payload = build_composite_alert(rate_data["spread_bp"], move_data["move_index"], date)
                send_discord_message(payload, dry_run=dry_run)
        else:
            if resolve_alert("composite"):
                info = get_alert_info("composite")
                payload = build_recovery_alert(
                    "composite", move_data["move_index"],
                    info["triggered_at"] if info else "", date,
                )
                send_discord_message(payload, dry_run=dry_run)


def run_daily_briefing(dry_run: bool = False) -> None:
    """일간 브리핑: SOFR + MOVE 수집 → 저장 → 임계값 체크 → Embed 발송."""
    print("[일간 브리핑] 데이터 수집 시작...")

    rate_data = None
    move_data = None
    has_new_data = False

    try:
        rate_data = collect_sofr()
        if rate_data:
            has_new_data = True
            print(f"  SOFR: {rate_data['sofr']:.2f}%, IORB: {rate_data['iorb']:.2f}%, 스프레드: {rate_data['spread_bp']:+.0f}bp")
        else:
            # 새 데이터 없으면 저장소에서 최신 데이터로 브리핑 구성
            rate_data = get_latest_rate()
            if rate_data:
                print(f"  SOFR: 저장된 데이터 사용 ({rate_data['date']})")
    except Exception as e:
        print(f"  [ERROR] SOFR 수집 실패: {e}")

    try:
        move_data = collect_move()
        if move_data:
            has_new_data = True
            print(f"  MOVE: {move_data['move_index']:.1f} ({move_data.get('change_pct', 'N/A')}%)")
        else:
            # 새 데이터 없으면 저장소에서 최신 데이터로 브리핑 구성
            move_data = get_latest_move()
            if move_data:
                print(f"  MOVE: 저장된 데이터 사용 ({move_data['date']})")
    except Exception as e:
        print(f"  [ERROR] MOVE 수집 실패: {e}")

    if not has_new_data:
        print("[일간 브리핑] 새 데이터 없음 — 브리핑 미발송")
        return

    # 일간 브리핑 발송 — 새 데이터 + 저장소 fallback 포함
    payload = build_daily_briefing(rate_data, move_data)
    send_discord_message(payload, dry_run=dry_run)

    # 임계값 경고 체크
    _process_alerts(rate_data, move_data, dry_run=dry_run)

    print("[일간 브리핑] 완료")


def run_move_update(dry_run: bool = False) -> None:
    """장마감 업데이트: MOVE 수집 → 변동 클 때만 발송."""
    print("[장마감 업데이트] MOVE 수집 시작...")

    move_data = collect_move()

    if move_data is None:
        print("[장마감 업데이트] 새 데이터 없음 — 업데이트 미발송")
        return

    print(f"  MOVE: {move_data['move_index']:.1f} ({move_data.get('change_pct', 'N/A')}%)")

    # 변동률 기준 충족 시에만 업데이트 발송
    if check_move_intraday(move_data.get("change_pct")):
        payload = build_move_update(move_data)
        send_discord_message(payload, dry_run=dry_run)
        print("  → 변동률 기준 충족, 업데이트 발송")
    else:
        print("  → 변동률 기준 미달, 업데이트 미발송")

    # 임계값 경고 체크 (MOVE만)
    _process_alerts(None, move_data, dry_run=dry_run)

    print("[장마감 업데이트] 완료")


def run_weekly_report(dry_run: bool = False) -> None:
    """주간 리포트: COT 수집 → 주간 데이터 조회 → Embed 발송."""
    print("[주간 리포트] 데이터 수집 시작...")

    cot_data = collect_cot()

    if cot_data is None:
        print("[주간 리포트] 새 COT 데이터 없음 — 리포트 미발송")
        return

    print(f"  COT Net: {cot_data['leveraged_net_position']:,} ({cot_data.get('net_change_pct', 'N/A')}%)")

    weekly_rates = get_weekly_rates(5)
    weekly_moves = get_weekly_moves(5)

    # 주간 리포트 발송
    payload = build_weekly_report(weekly_rates, weekly_moves, cot_data)
    send_discord_message(payload, dry_run=dry_run)

    # COT 임계값 체크
    cot_alert = check_cot_change(cot_data.get("net_change_pct"))
    if cot_alert:
        if activate_alert("cot_change", f"COT 변동 {cot_data['net_change_pct']:+.1f}%"):
            payload = build_cot_alert(cot_data)
            send_discord_message(payload, dry_run=dry_run)
    else:
        if resolve_alert("cot_change"):
            info = get_alert_info("cot_change")
            payload = build_recovery_alert(
                "cot_change", abs(cot_data.get("net_change_pct", 0)),
                info["triggered_at"] if info else "", cot_data["report_date"],
            )
            send_discord_message(payload, dry_run=dry_run)

    print("[주간 리포트] 완료")


def determine_mode() -> str:
    """현재 UTC 시간 기반으로 실행 모드 결정."""
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()  # 0=월 ~ 6=일

    # 토요일 UTC 01:00 → 주간 리포트
    if weekday == 5 and hour <= 2:
        return "weekly"
    # 평일 UTC 22:00 (KST 07:00) → 장마감 업데이트
    if weekday < 5 and 21 <= hour <= 23:
        return "update"
    # 평일 UTC 13:00 (KST 22:00) → 일간 브리핑
    if weekday < 5 and 12 <= hour <= 14:
        return "daily"

    return "daily"  # 기본값


def main(mode: str | None = None, dry_run: bool = False) -> None:
    if mode is None:
        mode = determine_mode()

    print(f"=== 실행 모드: {mode} (dry_run={dry_run}) ===")

    if mode == "daily":
        run_daily_briefing(dry_run=dry_run)
    elif mode == "update":
        run_move_update(dry_run=dry_run)
    elif mode == "weekly":
        run_weekly_report(dry_run=dry_run)
    else:
        print(f"알 수 없는 모드: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
