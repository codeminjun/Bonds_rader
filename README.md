# Bonds Radar

미국 채권 시장의 레버리지 청산(Deleveraging) 리스크를 모니터링하는 디스코드 봇.

3가지 핵심 지표를 수집하여 디스코드 웹훅으로 정기 리포트 및 임계값 경고를 발송한다.

## 모니터링 지표

| 지표 | 의미 | 소스 | 주기 |
|------|------|------|------|
| **SOFR 스프레드** | 국채 담보 자금 조달 비용. 확대 시 자금 경색 신호 | FRED API (SOFR - IORB) | 평일 1일 1회 |
| **MOVE 지수** | 채권 옵션 변동성. 급등 시 리스크 패리티 펀드 매도 촉발 | Yahoo Finance (yfinance) | 평일 1일 1회 |
| **CFTC COT** | 헤지펀드(Leveraged Funds) 10Y 국채 순매도 포지션 | CFTC Socrata API | 주 1회 |

## 알림 스케줄

| 알림 | 시간 (KST) | 조건 |
|------|------------|------|
| 일간 브리핑 | 평일 09:00 | 무조건 발송 |
| 장마감 업데이트 | 평일 23:00 | MOVE 전일 대비 3% 이상 변동 시 |
| 주간 리포트 | 토요일 10:00 | 무조건 발송 |
| 임계값 경고 | 수집 시점 | 조건 충족 시 즉시 (중복 방지) |

## 임계값

| 조건 | 등급 |
|------|------|
| SOFR 스프레드 > +5bp | 경고 |
| MOVE > 120 | 경고 |
| MOVE > 140 | 위험 |
| SOFR > +5bp AND MOVE > 120 | 복합 위험 |
| COT Net Short 전주 대비 ±10% | 경고 |

## 아키텍처

```
GitHub Actions (cron)
  ├─ FRED API → SOFR, IORB
  ├─ yfinance → MOVE 지수
  ├─ CFTC API → COT 데이터
  ├─ JSON 파일 저장 (data/)
  ├─ 임계값 체크
  └─ Discord Webhook 발송
```

## 로컬 실행

```bash
# 환경 설정
cp .env.example .env
# .env 파일에 FRED_API_KEY, DISCORD_WEBHOOK_URL 입력

# 의존성 설치
pip install -r requirements.txt

# 실행
python run_local.py daily --dry-run    # 일간 브리핑 (발송 없이 확인)
python run_local.py daily              # 일간 브리핑 (실제 발송)
python run_local.py update             # 장마감 MOVE 업데이트
python run_local.py weekly             # 주간 리포트
```

## GitHub Actions 설정

Repository Settings > Secrets and variables > Actions에 등록:

| Secret | 내용 |
|--------|------|
| `FRED_API_KEY` | [FRED API 키](https://fredaccount.stlouisfed.org/apikeys) |
| `DISCORD_WEBHOOK_URL` | 디스코드 웹훅 URL |
