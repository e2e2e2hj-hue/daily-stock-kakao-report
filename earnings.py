"""관심 기업의 분기 실적 발표를 24시간 윈도우 내에서 감지하고, 재무 수치와
컨퍼런스콜(실적 설명회) 관련 보도를 수집한다. SpaceX는 비상장이라 대상에서 제외.
"""
import calendar
from datetime import datetime, timezone
from urllib.parse import quote

import feedparser
import yfinance as yf

TRACKED = {
    "TSLA": "테슬라",
    "MSTR": "스트래티지",
    "GOOGL": "구글",
    "MSFT": "마이크로소프트",
    "NVDA": "엔비디아",
    "AAPL": "애플",
    "META": "메타",
    "AMZN": "아마존",
}

_REVENUE_KEYS = ["Total Revenue", "TotalRevenue"]
_OP_INCOME_KEYS = ["Operating Income", "OperatingIncome"]
_NET_INCOME_KEYS = ["Net Income", "NetIncome", "Net Income Common Stockholders"]
_DEBT_KEYS = ["Total Debt", "TotalDebt", "Total Liabilities Net Minority Interest"]


def find_recent_earnings(start_utc: datetime, end_utc: datetime) -> list:
    """윈도우(start_utc~end_utc) 내에 실적을 발표한 티커 목록을 반환."""
    reported = []
    for ticker in TRACKED:
        try:
            dates = yf.Ticker(ticker).get_earnings_dates(limit=4)
            if dates is None or dates.empty:
                continue
            for idx in dates.index:
                ts_utc = idx.to_pydatetime().astimezone(timezone.utc)
                if start_utc <= ts_utc <= end_utc:
                    reported.append(ticker)
                    break
        except Exception:
            continue
    return reported


def _first_present(row_source, keys, col):
    for key in keys:
        if key in row_source.index:
            return row_source.loc[key, col]
    return None


def get_financials(ticker: str):
    """분기 실적 딕셔너리(매출/영업이익/순이익/EPS실제/EPS예상/총부채). 실패 시 None."""
    try:
        t = yf.Ticker(ticker)
        income = t.quarterly_income_stmt
        balance = t.quarterly_balance_sheet

        revenue = op_income = net_income = None
        if income is not None and not income.empty:
            col = income.columns[0]
            revenue = _first_present(income, _REVENUE_KEYS, col)
            op_income = _first_present(income, _OP_INCOME_KEYS, col)
            net_income = _first_present(income, _NET_INCOME_KEYS, col)

        debt = None
        if balance is not None and not balance.empty:
            debt = _first_present(balance, _DEBT_KEYS, balance.columns[0])

        eps_actual = eps_estimate = None
        dates = t.get_earnings_dates(limit=8)
        if dates is not None and not dates.empty:
            reported = dates[dates["Reported EPS"].notna()]
            if not reported.empty:
                row = reported.iloc[0]
                eps_actual = row.get("Reported EPS")
                eps_estimate = row.get("EPS Estimate")

        return {
            "revenue": revenue,
            "op_income": op_income,
            "net_income": net_income,
            "eps_actual": eps_actual,
            "eps_estimate": eps_estimate,
            "debt": debt,
        }
    except Exception:
        return None


def fetch_call_coverage(company_name: str, ticker: str, start_utc: datetime, end_utc: datetime, limit: int = 8):
    """실적 발표/컨퍼런스콜 관련 보도를 구글 뉴스 검색 RSS로 수집."""
    query = f'"{ticker}" earnings call OR "{company_name}" conference call transcript'
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-US&gl=US&ceid=US:en"
    items = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = entry.get("published_parsed")
            if not published:
                continue
            pub_dt = datetime.fromtimestamp(calendar.timegm(published), tz=timezone.utc)
            if start_utc <= pub_dt <= end_utc:
                items.append({"title": entry.get("title", ""), "summary": entry.get("summary", "")})
    except Exception:
        pass
    return items[:limit]
