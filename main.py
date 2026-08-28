"""주식 일일 시황 카카오톡 자동 발송 - 매일 09:00 KST 실행 진입점."""
import argparse
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

import calendar_events
import earnings
import formatter
import indicators
import kakao
import news
import summarize
import webpage

KST = ZoneInfo("Asia/Seoul")


def collect_indicators(fred_key: str) -> dict:
    crypto = indicators.get_crypto_prices()
    return {
        "kospi": indicators.get_yf_quote("^KS11"),
        "kosdaq": indicators.get_yf_quote("^KQ11"),
        "sp500": indicators.get_yf_quote("^GSPC"),
        "nasdaq": indicators.get_yf_quote("^IXIC"),
        "gold": indicators.get_yf_quote("GC=F"),
        "usdkrw": indicators.get_yf_quote("KRW=X"),
        "fed_rate": indicators.fed_funds_rate(fred_key),
        "us10y": indicators.us10y_yield(fred_key),
        "cpi": indicators.cpi_yoy(fred_key),
        "ppi": indicators.ppi_yoy(fred_key),
        "unemployment": indicators.unemployment_rate(fred_key),
        "btc": crypto.get("bitcoin"),
        "eth": crypto.get("ethereum"),
        "sol": crypto.get("solana"),
        "fomc_next": calendar_events.next_fomc_meeting(date.today()),
    }


def collect_news_summaries(start_utc, end_utc, gemini_key: str) -> dict:
    summaries = {}
    for category in ("macro", "us_market", "bitcoin", "tesla"):
        items = news.fetch_category_items(category, start_utc, end_utc)
        summaries[category] = summarize.summarize_category(category, items, gemini_key)
    return summaries


def collect_earnings(start_utc, end_utc, gemini_key: str) -> list:
    """윈도우 내에 실적을 발표한 관심 기업들의 재무 수치 + 컨퍼런스콜 요약을 수집."""
    result = []
    for ticker in earnings.find_recent_earnings(start_utc, end_utc):
        name = earnings.TRACKED[ticker]
        financials = earnings.get_financials(ticker)
        call_items = earnings.fetch_call_coverage(name, ticker, start_utc, end_utc)
        call_summary = summarize.summarize_earnings_call(name, call_items, gemini_key)
        revenue_verdict = summarize.extract_revenue_verdict(name, call_items, gemini_key)
        result.append(
            {
                "name": name,
                "financials": financials,
                "call_summary": call_summary,
                "revenue_verdict": revenue_verdict,
            }
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="발송 없이 콘솔에만 출력")
    args = parser.parse_args()

    load_dotenv()
    fred_key = os.environ.get("FRED_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    start_utc, end_utc = news.get_window_utc()
    ind = collect_indicators(fred_key)
    news_summaries = collect_news_summaries(start_utc, end_utc, gemini_key)
    earnings_reports = collect_earnings(start_utc, end_utc, gemini_key)
    messages = formatter.build_messages(today_str, ind, news_summaries, earnings_reports)

    html_content = webpage.render_html(today_str, ind, news_summaries, earnings_reports)
    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    if args.dry_run:
        for i, m in enumerate(messages, 1):
            print(f"--- 메시지 {i} ({len(m)}자) ---")
            print(m)
            print()
        return

    rest_api_key = os.environ["KAKAO_REST_API_KEY"]
    refresh_token = os.environ["KAKAO_REFRESH_TOKEN"]
    client_secret = os.environ.get("KAKAO_CLIENT_SECRET")

    token_data = kakao.refresh_access_token(rest_api_key, refresh_token, client_secret)
    access_token = token_data["access_token"]

    for m in messages:
        kakao.send_text_message(access_token, m)

    new_refresh_token = token_data.get("refresh_token")
    if new_refresh_token:
        gh_pat = os.environ.get("GH_PAT")
        gh_repo = os.environ.get("GH_REPO")
        if gh_pat and gh_repo:
            kakao.update_github_secret(gh_repo, "KAKAO_REFRESH_TOKEN", new_refresh_token, gh_pat)


if __name__ == "__main__":
    main()
