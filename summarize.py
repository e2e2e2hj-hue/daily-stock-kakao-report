"""Gemini 무료 티어로 카테고리별 뉴스를 한국어로 요약. 무료 티어는 가끔 일시적으로
과부하(503) 상태가 되므로 재시도로 대부분 흡수하고, 그래도 실패하면 영문 헤드라인
나열로 폴백한다. 반환값에는 주제 헤더를 포함하지 않는다(헤더는 formatter.py가 붙인다).
"""
import time

import requests

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-lite-latest:generateContent"
)

CATEGORY_LABELS = {
    "macro": "거시경제",
    "us_market": "미국 증시",
    "bitcoin": "비트코인",
    "tesla": "테슬라",
}


def summarize_category(category: str, items: list, api_key: str) -> str:
    label = CATEGORY_LABELS.get(category, category)
    if not items:
        return "최근 24시간 내 주요 뉴스가 확인되지 않았습니다."
    if api_key:
        prompt = (
            f"다음은 최근 24시간 동안의 '{label}' 관련 뉴스 헤드라인들이다(영문 원문 포함 가능).\n"
            f"{_headlines_block(items)}\n\n"
            f"반드시 한국어로만, 장기투자자 관점에서 중요한 내용을 3~5개 항목으로 정리해줘. "
            f"정보를 생략하지 말되, 각 항목은 완전한 문장이 아니라 '사업 영역 확대', "
            f"'금리 동결 시사'처럼 핵심만 압축한 명사형 구절로 짧게 써줘. "
            f"각 항목 앞에 '- '를 붙이고, 불필요한 수식어나 인사말은 넣지 마."
        )
        result = _call_gemini(prompt, api_key)
        if result:
            return result
    return _fallback_headlines(items)


def summarize_earnings_call(company_name: str, items: list, api_key: str) -> str:
    """실적 발표 컨퍼런스콜(설명회) 보도를 A4 반페이지 수준으로 압축 요약."""
    if not items:
        return "관련 컨퍼런스콜 보도가 확인되지 않았습니다."
    if api_key:
        prompt = (
            f"다음은 '{company_name}'의 최근 분기 실적 발표 및 컨퍼런스콜(실적 설명회) 관련 "
            f"뉴스 보도들이다(영문 원문 포함 가능).\n{_headlines_block(items)}\n\n"
            f"반드시 한국어로만, 장기투자자 관점에서 중요한 내용을 A4 반페이지 분량 수준으로 "
            f"압축 정리해줘(대략 10~15개 항목). 실적 하이라이트, 향후 가이던스, 경영진 코멘트, "
            f"주요 리스크·이슈, 애널리스트 질의응답에서 나온 핵심 내용을 최대한 담아줘. "
            f"정보를 생략하지 말되, 각 항목은 완전한 문장이 아니라 명사형 구절로 압축해서 짧게 써줘. "
            f"각 항목 앞에 '- '를 붙이고, 불필요한 수식어나 인사말은 넣지 마."
        )
        result = _call_gemini(prompt, api_key)
        if result:
            return result
    return _fallback_headlines(items)


def extract_revenue_verdict(company_name: str, items: list, api_key: str) -> str:
    """뉴스 보도에서 매출이 시장 예상치(컨센서스)를 상회/하회했는지 판단.
    정확한 예상 수치는 매칭이 어려워 '상회'/'하회'/'정보없음'으로만 반환한다."""
    if not items or not api_key:
        return "정보없음"
    prompt = (
        f"다음은 '{company_name}'의 최근 분기 실적 발표 관련 뉴스 보도다.\n{_headlines_block(items)}\n\n"
        f"이 보도들에서 매출(revenue)이 시장 예상치(컨센서스)를 상회했는지 하회했는지 "
        f"명시적으로 언급되어 있으면 '상회' 또는 '하회' 한 단어로만 답해줘. "
        f"명확히 언급되어 있지 않으면 '정보없음' 한 단어로만 답해줘. 다른 설명은 절대 붙이지 마."
    )
    result = _call_gemini(prompt, api_key, attempts=2)
    if result:
        if "상회" in result:
            return "상회"
        if "하회" in result:
            return "하회"
    return "정보없음"


def _headlines_block(items: list) -> str:
    return "\n".join(f"- {i['title']}: {i['summary']}" for i in items)


def _call_gemini(prompt: str, api_key: str, attempts: int = 3):
    for attempt in range(attempts):
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            if attempt < attempts - 1:
                time.sleep(4)
    return None


def _fallback_headlines(items: list) -> str:
    lines = []
    for i in items[:2]:
        title = i["title"]
        if len(title) > 70:
            title = title[:67] + "..."
        lines.append(f"- {title}")
    return "\n".join(lines)
