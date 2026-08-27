"""수집된 지표/뉴스/실적 요약을 카카오 텍스트 메시지(각 200자 이하)로 조립.
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


def _usd_billions(val):
    if val is None:
        return "조회실패"
    sign = "-" if val < 0 else ""
    return f"{sign}${abs(val) / 1e9:.1f}B"


def _usd(val):
    if val is None:
        return "조회실패"
    return f"${val:.2f}"


def pack_lines(header: str, lines: list) -> list:
    """header + lines를 MAX_LEN 이하 메시지 여러 개로 나눈다. 넘치면 헤더를 반복해
    다음 메시지로 이어 보낸다(한 줄 자체가 헤더와 합쳐도 넘치는 극단적인 경우는 예외).
    나중에 붙는 '(N/M)' 접미사 자리를 남겨두기 위해 여유분을 두고 나눈다."""
    budget = MAX_LEN - 10
    chunks = [[header]]
    for line in lines:
        if not line:
            continue
        current = chunks[-1]
        if len("\n".join(current + [line])) > budget and len(current) > 1:
            chunks.append([header])
            current = chunks[-1]
        current.append(line)

    total = len(chunks)
    result = []
    for idx, chunk in enumerate(chunks):
        head = chunk[0] if total == 1 else f"{chunk[0]} ({idx + 1}/{total})"
        result.append("\n".join([head] + chunk[1:]))
    return result


def build_messages(today_str: str, ind: dict, news: dict, earnings: list = None) -> list:
    messages = []

    messages += pack_lines(
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

    messages += pack_lines(
        "■원자재·암호화폐",
        [
            f"금 {_price(ind.get('gold'))}",
            f"비트코인 {_price(ind.get('btc'))}",
            f"이더리움 {_price(ind.get('eth'))}",
            f"솔라나 {_price(ind.get('sol'))}",
            f"다음 FOMC: {ind.get('fomc_next', '정보없음')}",
        ],
    )

    messages += pack_lines(
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
        messages += pack_lines(header, lines)

    for e in earnings or []:
        name = e["name"]
        fin = e.get("financials") or {}
        verdict = e.get("revenue_verdict", "정보없음")
        revenue_line = f"매출 {_usd_billions(fin.get('revenue'))}"
        if verdict in ("상회", "하회"):
            revenue_line += f" (예상치 {verdict})"
        messages += pack_lines(
            f"■{name} 실적발표",
            [
                revenue_line,
                f"영업이익 {_usd_billions(fin.get('op_income'))}",
                f"순이익 {_usd_billions(fin.get('net_income'))}",
                f"EPS 실제 {_usd(fin.get('eps_actual'))} / 예상 {_usd(fin.get('eps_estimate'))}",
                f"총부채 {_usd_billions(fin.get('debt'))}",
            ],
        )
        call_summary = e.get("call_summary", "")
        call_lines = call_summary.split("\n") if call_summary else ["컨퍼런스콜 관련 보도 없음"]
        messages += pack_lines(f"■{name} 컨퍼런스콜 요약", call_lines)

    return messages
