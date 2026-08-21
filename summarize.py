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
        result = _summarize_with_gemini(label, items, api_key)
        if result:
            return result
    return _fallback_headlines(items)


def _summarize_with_gemini(label: str, items: list, api_key: str, attempts: int = 3):
    headlines = "\n".join(f"- {i['title']}: {i['summary']}" for i in items)
    prompt = (
        f"다음은 최근 24시간 동안의 '{label}' 관련 뉴스 헤드라인들이다(영문 원문 포함 가능).\n{headlines}\n\n"
        f"반드시 한국어로만, 장기투자자 관점에서 중요한 내용을 3~5개 항목으로 정리해줘. "
        f"정보를 생략하지 말되, 각 항목은 완전한 문장이 아니라 '사업 영역 확대', "
        f"'금리 동결 시사'처럼 핵심만 압축한 명사형 구절로 짧게 써줘. "
        f"각 항목 앞에 '- '를 붙이고, 불필요한 수식어나 인사말은 넣지 마."
    )
    for attempt in range(attempts):
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20,
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
