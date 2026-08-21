"""수집된 지표/뉴스 요약을 카카오 텍스트 메시지(각 200자 이하)로 조립.
메시지마다 맨 위에 '■주제' 헤더를 붙이고, 내용이 200자를 넘으면 잘라내는 대신
같은 주제의 메시지를 여러 통(2/2, 3/3 ...)으로 이어서 보낸다.
"""

MAX_LEN = 200


def _price(quote):
    if quote is None:
        return "조회실패"
    val, pct = quote
    sign = "+" if pct >= 0 else ""
    return f"{val:,} ({sign}{pct}%)"


def _rate(pair, unit="%"):
    if pair is None:
        return "조회실패"
    val, pct = pair
    sign = "+" if pct >= 0 else ""
    return f"{val}{unit} ({sign}{pct}%)"


def _num(val, unit=""):
    if val is None:
        return "조회실패"
    return f"{val}{unit}"


def _pack_lines(header: str, lines: list) -> list:
    """header + lines를 MAX_LEN 이하 메시지 여러 개로 나눈다. 넘치면 헤더를 반복해
    다음 메시지로 이어 보낸다(한 줄 자체가 헤더와 합쳐도 넘치는 극단적인 경우는 예외)."""
    chunks = [[header]]
    for line in lines:
        if not line:
            continue
        current = chunks[-1]
        if len("\n".join(current + [line])) > MAX_LEN and len(current) > 1:
            chunks.append([header])
            current = chunks[-1]
        current.append(line)

    total = len(chunks)
    result = []
    for idx, chunk in enumerate(chunks):
        head = chunk[0] if total == 1 else f"{chunk[0]} ({idx + 1}/{total})"
        result.append("\n".join([head] + chunk[1:]))
    return result


def build_messages(today_str: str, ind: dict, news: dict) -> list:
    messages = []

    messages += _pack_lines(
        f"■일일시황 {today_str}",
        [
            f"코스피 {_price(ind.get('kospi'))}",
            f"코스닥 {_price(ind.get('kosdaq'))}",
            f"S&P500 {_price(ind.get('sp500'))}",
            f"나스닥 {_price(ind.get('nasdaq'))}",
            f"연준금리 {_rate(ind.get('fed_rate'))}",
            f"美10년물 {_rate(ind.get('us10y'))}",
            f"원/달러 {_price(ind.get('usdkrw'))}",
        ],
    )

    messages += _pack_lines(
        "■원자재·암호화폐",
        [
            f"금 {_price(ind.get('gold'))}",
            f"비트코인 {_price(ind.get('btc'))}",
            f"이더리움 {_price(ind.get('eth'))}",
            f"솔라나 {_price(ind.get('sol'))}",
            f"다음 FOMC: {ind.get('fomc_next', '정보없음')}",
        ],
    )

    messages += _pack_lines(
        "■물가·고용",
        [
            f"CPI(YoY) {_num(ind.get('cpi'), '%')}",
            f"PPI(YoY) {_num(ind.get('ppi'), '%')}",
            f"실업률 {_num(ind.get('unemployment'), '%')}",
        ],
    )

    news_sections = [
        ("us_market", "■미국증시"),
        ("bitcoin", "■비트코인"),
        ("tesla", "■테슬라"),
        ("macro", "■거시경제"),
    ]
    for key, header in news_sections:
        body = news.get(key, "")
        lines = body.split("\n") if body else ["관련 뉴스 없음"]
        messages += _pack_lines(header, lines)

    return messages
