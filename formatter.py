"""수집된 지표/뉴스 요약을 카카오 텍스트 메시지(각 200자 이하) 5통으로 조립."""


def _price(quote):
    if quote is None:
        return "조회실패"
    val, pct = quote
    sign = "+" if pct >= 0 else ""
    return f"{val:,} ({sign}{pct}%)"


def _num(val, unit=""):
    if val is None:
        return "조회실패"
    return f"{val}{unit}"


def build_messages(today_str: str, ind: dict, news: dict) -> list:
    msg1 = (
        f"[주식 일일 시황 {today_str}]\n"
        f"■ 지수\n"
        f"코스피 {_price(ind.get('kospi'))}\n"
        f"코스닥 {_price(ind.get('kosdaq'))}\n"
        f"S&P500 {_price(ind.get('sp500'))}\n"
        f"나스닥 {_price(ind.get('nasdaq'))}\n"
        f"■ 금리·환율\n"
        f"연준금리 {_num(ind.get('fed_rate'), '%')}\n"
        f"美10년물 {_num(ind.get('us10y'), '%')}\n"
        f"원/달러 {_price(ind.get('usdkrw'))}"
    )

    msg2 = (
        f"[원자재·암호화폐 {today_str}]\n"
        f"금 {_price(ind.get('gold'))}\n"
        f"비트코인 {_price(ind.get('btc'))}\n"
        f"이더리움 {_price(ind.get('eth'))}\n"
        f"솔라나 {_price(ind.get('sol'))}\n"
        f"다음 FOMC: {ind.get('fomc_next', '정보없음')}"
    )

    msg3 = (
        f"[물가·고용 {today_str}]\n"
        f"CPI(YoY) {_num(ind.get('cpi'), '%')}\n"
        f"PPI(YoY) {_num(ind.get('ppi'), '%')}\n"
        f"실업률 {_num(ind.get('unemployment'), '%')}"
    )

    msg4 = news.get("us_market", "")
    msg5 = news.get("bitcoin", "")
    msg6 = news.get("tesla", "")
    msg7 = news.get("macro", "")

    return [msg1, msg2, msg3, msg4, msg5, msg6, msg7]
