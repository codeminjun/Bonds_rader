import json
import os
from datetime import datetime, timedelta

from config import DATA_DIR


def _file_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)


def _load(filename: str) -> list | dict:
    path = _file_path(filename)
    if not os.path.exists(path):
        return [] if filename != "alert_state.json" else {}
    with open(path, "r") as f:
        return json.load(f)


def _save(filename: str, data: list | dict) -> None:
    path = _file_path(filename)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# --- daily_rates.json ---

def save_daily_rate(date: str, sofr: float, iorb: float, spread_bp: float) -> None:
    records = _load("daily_rates.json")
    # 같은 날짜 데이터가 있으면 업데이트
    for r in records:
        if r["date"] == date:
            r["sofr"] = sofr
            r["iorb"] = iorb
            r["spread_bp"] = spread_bp
            _save("daily_rates.json", records)
            return
    records.append({
        "date": date,
        "sofr": sofr,
        "iorb": iorb,
        "spread_bp": spread_bp,
    })
    records.sort(key=lambda x: x["date"])
    _save("daily_rates.json", records)


def get_latest_rate() -> dict | None:
    records = _load("daily_rates.json")
    return records[-1] if records else None


def get_prev_rate() -> dict | None:
    records = _load("daily_rates.json")
    return records[-2] if len(records) >= 2 else None


def get_weekly_rates(n: int = 5) -> list[dict]:
    records = _load("daily_rates.json")
    return records[-n:]


# --- daily_move.json ---

def save_daily_move(date: str, move_index: float, prev_close: float | None, change_pct: float | None) -> None:
    records = _load("daily_move.json")
    for r in records:
        if r["date"] == date:
            r["move_index"] = move_index
            r["prev_close"] = prev_close
            r["change_pct"] = change_pct
            _save("daily_move.json", records)
            return
    records.append({
        "date": date,
        "move_index": move_index,
        "prev_close": prev_close,
        "change_pct": change_pct,
    })
    records.sort(key=lambda x: x["date"])
    _save("daily_move.json", records)


def get_latest_move() -> dict | None:
    records = _load("daily_move.json")
    return records[-1] if records else None


def get_prev_move() -> dict | None:
    records = _load("daily_move.json")
    return records[-2] if len(records) >= 2 else None


def get_weekly_moves(n: int = 5) -> list[dict]:
    records = _load("daily_move.json")
    return records[-n:]


# --- weekly_cot.json ---

def save_weekly_cot(
    report_date: str,
    leveraged_net: int,
    leveraged_long: int,
    leveraged_short: int,
    open_interest: int,
    prev_net: int | None,
    net_change_pct: float | None,
) -> None:
    records = _load("weekly_cot.json")
    for r in records:
        if r["report_date"] == report_date:
            r.update({
                "leveraged_net_position": leveraged_net,
                "leveraged_long": leveraged_long,
                "leveraged_short": leveraged_short,
                "open_interest": open_interest,
                "prev_net_position": prev_net,
                "net_change_pct": net_change_pct,
            })
            _save("weekly_cot.json", records)
            return
    records.append({
        "report_date": report_date,
        "leveraged_net_position": leveraged_net,
        "leveraged_long": leveraged_long,
        "leveraged_short": leveraged_short,
        "open_interest": open_interest,
        "prev_net_position": prev_net,
        "net_change_pct": net_change_pct,
    })
    records.sort(key=lambda x: x["report_date"])
    _save("weekly_cot.json", records)


def get_latest_cot() -> dict | None:
    records = _load("weekly_cot.json")
    return records[-1] if records else None


def get_prev_cot() -> dict | None:
    records = _load("weekly_cot.json")
    return records[-2] if len(records) >= 2 else None


# --- alert_state.json ---

def load_alert_state() -> dict:
    return _load("alert_state.json")


def save_alert_state(state: dict) -> None:
    _save("alert_state.json", state)
