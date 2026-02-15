import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Data directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# FRED series IDs
SOFR_SERIES_ID = "SOFR"
IORB_SERIES_ID = "IORB"

# SOFR 스프레드 임계값 (bp)
SOFR_SPREAD_WARNING = 5

# MOVE 지수 임계값
MOVE_WARNING = 120
MOVE_DANGER = 140
MOVE_WATCH = 100  # 관망 구간 시작

# MOVE 장마감 업데이트 발송 조건 (전일 대비 변동률 %)
MOVE_INTRADAY_THRESHOLD = 3.0

# COT 변동 임계값 (%)
COT_NET_CHANGE_WARNING = 10

# 위험도 색상 (Discord Embed)
COLOR_SAFE = 3066993       # 🟢 초록
COLOR_WATCH = 16776960     # 🟡 노랑
COLOR_WARNING = 16744192   # 🟠 주황
COLOR_DANGER = 15158332    # 🔴 빨강
