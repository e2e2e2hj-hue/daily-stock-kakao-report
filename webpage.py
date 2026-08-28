"""매일 수집한 지표/뉴스/실적 데이터를 GitHub Pages용 HTML 한 페이지로 렌더링."""
import html

import formatter

NEWS_LABELS = {
    "us_market": "미국증시",
    "bitcoin": "비트코인",
    "tesla": "테슬라",
    "macro": "거시경제",
}


def _esc(text: str) -> str:
    return html.escape(str(text))


def _news_html(body: str) -> str:
    lines = [l for l in body.split("\n") if l.strip()]
    if not lines:
        return "<p>관련 뉴스 없음</p>"
    items = "".join(f"<li>{_esc(l.lstrip('- ').strip())}</li>" for l in lines)
    return f"<ul>{items}</ul>"


def render_html(today_str: str, ind: dict, news: dict, earnings: list = None) -> str:
    indicator_rows = "".join(
        f"<tr><th>{label}</th><td>{value}</td></tr>"
        for label, value in [
            ("코스피", formatter.fmt_price(ind.get("kospi"))),
            ("코스닥", formatter.fmt_price(ind.get("kosdaq"))),
            ("S&P500", formatter.fmt_price(ind.get("sp500"))),
            ("나스닥", formatter.fmt_price(ind.get("nasdaq"))),
            ("연준 기준금리", formatter.fmt_rate(ind.get("fed_rate"))),
            ("美 10년물", formatter.fmt_rate(ind.get("us10y"))),
            ("원/달러", formatter.fmt_price(ind.get("usdkrw"))),
            ("금", formatter.fmt_price(ind.get("gold"))),
            ("비트코인", formatter.fmt_price(ind.get("btc"))),
            ("이더리움", formatter.fmt_price(ind.get("eth"))),
            ("솔라나", formatter.fmt_price(ind.get("sol"))),
            ("다음 FOMC", ind.get("fomc_next", "정보없음")),
            ("CPI(YoY)", formatter.fmt_num(ind.get("cpi"), "%")),
            ("PPI(YoY)", formatter.fmt_num(ind.get("ppi"), "%")),
            ("실업률", formatter.fmt_num(ind.get("unemployment"), "%")),
        ]
    )

    news_sections = "".join(
        f"<section><h2>{label}</h2>{_news_html(news.get(key, ''))}</section>"
        for key, label in NEWS_LABELS.items()
    )

    earnings_sections = ""
    for e in earnings or []:
        name = _esc(e["name"])
        fin = e.get("financials") or {}
        verdict = e.get("revenue_verdict", "정보없음")
        revenue = formatter.fmt_usd_billions(fin.get("revenue"))
        if verdict in ("상회", "하회"):
            revenue += f" (예상치 {verdict})"
        earnings_sections += f"""
        <section class="earnings">
          <h2>{name} 실적발표</h2>
          <table>
            <tr><th>매출</th><td>{revenue}</td></tr>
            <tr><th>영업이익</th><td>{formatter.fmt_usd_billions(fin.get('op_income'))}</td></tr>
            <tr><th>순이익</th><td>{formatter.fmt_usd_billions(fin.get('net_income'))}</td></tr>
            <tr><th>EPS 실제/예상</th><td>{formatter.fmt_usd(fin.get('eps_actual'))} / {formatter.fmt_usd(fin.get('eps_estimate'))}</td></tr>
            <tr><th>총부채</th><td>{formatter.fmt_usd_billions(fin.get('debt'))}</td></tr>
          </table>
          <h3>컨퍼런스콜 요약</h3>
          {_news_html(e.get('call_summary', ''))}
        </section>
        """

    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>주식 일일 시황</title>
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#1a1a2e">
<link rel="apple-touch-icon" href="icon.png">
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 640px; margin: 0 auto;
         padding: 16px; background: #0f0f1a; color: #eee; }}
  h1 {{ font-size: 1.3em; }}
  h2 {{ font-size: 1.05em; border-bottom: 1px solid #333; padding-bottom: 4px; margin-top: 28px; }}
  h3 {{ font-size: 0.95em; color: #aaa; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 6px 4px; border-bottom: 1px solid #222; font-size: 0.92em; }}
  th {{ color: #999; font-weight: normal; width: 40%; }}
  ul {{ padding-left: 18px; }}
  li {{ margin-bottom: 6px; font-size: 0.92em; line-height: 1.4; }}
  .updated {{ color: #777; font-size: 0.8em; margin-top: 32px; }}
  .earnings {{ background: #1a1a2e; border-radius: 8px; padding: 8px 12px; }}
</style>
</head>
<body>
  <h1>주식 일일 시황 · {_esc(today_str)}</h1>
  <section>
    <h2>지수·금리·원자재·암호화폐·물가</h2>
    <table>{indicator_rows}</table>
  </section>
  {news_sections}
  {earnings_sections}
  <p class="updated">최종 갱신: {_esc(today_str)} (KST)</p>
</body>
</html>
"""
