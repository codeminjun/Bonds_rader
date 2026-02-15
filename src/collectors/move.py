import yfinance as yf

from src.storage.json_store import save_daily_move, get_prev_move


def collect_move() -> dict:
    """yfinance로 MOVE 지수 최신 데이터를 수집하고 저장. 결과 dict 반환."""
    ticker = yf.Ticker("^MOVE")
    hist = ticker.history(period="5d")

    if hist.empty:
        raise ValueError("MOVE 지수 데이터를 가져올 수 없습니다.")

    latest_date = hist.index[-1].strftime("%Y-%m-%d")
    latest_close = round(float(hist["Close"].iloc[-1]), 2)

    # 전일 종가
    prev_close = None
    change_pct = None
    if len(hist) >= 2:
        prev_close = round(float(hist["Close"].iloc[-2]), 2)
        if prev_close != 0:
            change_pct = round((latest_close - prev_close) / prev_close * 100, 2)

    save_daily_move(latest_date, latest_close, prev_close, change_pct)

    return {
        "date": latest_date,
        "move_index": latest_close,
        "prev_close": prev_close,
        "change_pct": change_pct,
    }
