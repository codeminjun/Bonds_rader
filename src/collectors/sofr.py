from config import FRED_API_KEY, SOFR_SERIES_ID, IORB_SERIES_ID
from src.http_client import request_with_retry
from src.storage.json_store import save_daily_rate, get_latest_rate, get_prev_rate


def _fetch_fred_latest(series_id: str) -> tuple[str, float]:
    """FRED API에서 최신 데이터 1건 조회. (날짜, 값) 반환."""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1,
    }
    resp = request_with_retry("GET", url, params=params)
    resp.raise_for_status()
    obs = resp.json()["observations"][0]
    return obs["date"], float(obs["value"])


def collect_sofr() -> dict | None:
    """SOFR, IORB 최신 데이터를 수집하고 저장. 새 데이터가 없으면 None 반환."""
    sofr_date, sofr_value = _fetch_fred_latest(SOFR_SERIES_ID)
    iorb_date, iorb_value = _fetch_fred_latest(IORB_SERIES_ID)

    # 두 시리즈의 날짜가 다를 수 있음 (공휴일 등) → SOFR 날짜 기준
    date = sofr_date
    spread_bp = round((sofr_value - iorb_value) * 100, 2)

    # 이미 저장된 최신 데이터와 날짜가 같으면 새 데이터 없음
    stored = get_latest_rate()
    if stored and stored["date"] == date:
        print(f"  [SKIP] SOFR: 새 데이터 없음 (최신 저장 날짜: {date})")
        return None

    save_daily_rate(date, sofr_value, iorb_value, spread_bp)
    prev = get_prev_rate()

    return {
        "date": date,
        "sofr": sofr_value,
        "iorb": iorb_value,
        "spread_bp": spread_bp,
        "prev_spread_bp": prev["spread_bp"] if prev else None,
    }
