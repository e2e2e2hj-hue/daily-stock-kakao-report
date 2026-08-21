"""11개 수치형 지표 수집. 각 함수는 실패 시 None을 반환하고, 호출부(main.py)에서
None이면 '데이터 조회 실패'로 표시해 나머지 지표 처리에는 영향을 주지 않는다.
"""
import requests
import yfinance as yf

FRED_URL = "https://api.stlouisfed.org/fred/series/observations"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def get_yf_quote(symbol: str):
    """(최신 종가, 전일 대비 등락률%) 반환. 실패 시 None."""
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        closes = hist["Close"].dropna()
        if len(closes) < 2:
            return None
        last, prev = closes.iloc[-1], closes.iloc[-2]
        pct = (last - prev) / prev * 100
        return round(float(last), 2), round(float(pct), 2)
    except Exception:
        return None


def _fred_latest(series_id: str, api_key: str, units: str = None):
    try:
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 1,
        }
        if units:
            params["units"] = units
        resp = requests.get(FRED_URL, params=params, timeout=10)
        resp.raise_for_status()
        obs = resp.json()["observations"][0]
        return round(float(obs["value"]), 2)
    except Exception:
        return None


def _fred_change(series_id: str, api_key: str):
    """(최신값, 직전 관측치 대비 변화율%) 반환. 실패 시 None."""
    try:
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "sort_order": "desc",
            "limit": 2,
        }
        resp = requests.get(FRED_URL, params=params, timeout=10)
        resp.raise_for_status()
        obs = resp.json()["observations"]
        latest = float(obs[0]["value"])
        prev = float(obs[1]["value"])
        pct = (latest - prev) / prev * 100 if prev else 0.0
        return round(latest, 2), round(pct, 2)
    except Exception:
        return None


def fed_funds_rate(api_key: str):
    """(연준 기준금리 목표범위 문자열 '3.5~3.75', 상단 기준 전일 대비 변화율%). 실패 시 None."""
    lower = _fred_latest("DFEDTARL", api_key)
    upper_change = _fred_change("DFEDTARU", api_key)
    if lower is None or upper_change is None:
        return None
    upper, pct = upper_change
    return f"{lower}~{upper}", pct


def us10y_yield(api_key: str):
    """(미10년물 금리%, 전일 대비 변화율%). 실패 시 None."""
    return _fred_change("DGS10", api_key)


def unemployment_rate(api_key: str):
    return _fred_latest("UNRATE", api_key)


def cpi_yoy(api_key: str):
    return _fred_latest("CPIAUCSL", api_key, units="pc1")


def ppi_yoy(api_key: str):
    return _fred_latest("PPIACO", api_key, units="pc1")


def get_crypto_prices(ids=("bitcoin", "ethereum", "solana")):
    """{id: (usd가격, 24h 등락률%)} 반환. 실패 시 빈 dict."""
    try:
        resp = requests.get(
            COINGECKO_URL,
            params={
                "ids": ",".join(ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for coin_id in ids:
            if coin_id in data:
                result[coin_id] = (
                    round(data[coin_id]["usd"], 2),
                    round(data[coin_id].get("usd_24h_change", 0), 2),
                )
        return result
    except Exception:
        return {}
