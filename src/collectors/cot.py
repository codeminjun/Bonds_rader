import requests

from src.storage.json_store import save_weekly_cot, get_latest_cot


CFTC_API_URL = "https://publicreporting.cftc.gov/resource/gpe5-46if.json"


def collect_cot() -> dict:
    """CFTC Socrata API에서 10-Year Treasury COT 데이터를 수집하고 저장."""
    params = {
        "contract_market_name": "UST 10Y NOTE",
        "$order": "report_date_as_yyyy_mm_dd DESC",
        "$limit": 2,  # 최신 2건 (현재 + 전주)
    }
    resp = requests.get(CFTC_API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        raise ValueError("CFTC COT 데이터를 가져올 수 없습니다.")

    latest = data[0]
    report_date = latest["report_date_as_yyyy_mm_dd"][:10]  # "2026-02-10T00:00:00.000" → "2026-02-10"

    lev_long = int(latest.get("lev_money_positions_long", 0))
    lev_short = int(latest.get("lev_money_positions_short", 0))
    lev_net = lev_long - lev_short
    oi = int(latest.get("open_interest_all", 0))

    # 전주 데이터
    prev_net = None
    net_change_pct = None
    if len(data) >= 2:
        prev = data[1]
        prev_long = int(prev.get("lev_money_positions_long", 0))
        prev_short = int(prev.get("lev_money_positions_short", 0))
        prev_net = prev_long - prev_short
        if prev_net != 0:
            net_change_pct = round((lev_net - prev_net) / abs(prev_net) * 100, 2)

    save_weekly_cot(
        report_date=report_date,
        leveraged_net=lev_net,
        leveraged_long=lev_long,
        leveraged_short=lev_short,
        open_interest=oi,
        prev_net=prev_net,
        net_change_pct=net_change_pct,
    )

    return {
        "report_date": report_date,
        "leveraged_net_position": lev_net,
        "leveraged_long": lev_long,
        "leveraged_short": lev_short,
        "open_interest": oi,
        "prev_net_position": prev_net,
        "net_change_pct": net_change_pct,
    }
