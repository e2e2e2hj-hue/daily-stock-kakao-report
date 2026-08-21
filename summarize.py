"""Gemini 무료 티어로 카테고리별 뉴스 3~4줄 요약. 실패 시 헤드라인 나열로 폴백."""
import requests

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-flash-latest:generateContent"
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
        return f"[{label}] 최근 24시간 내 주요 뉴스가 확인되지 않았습니다."
    if api_key:
        result = _summarize_with_gemini(label, items, api_key)
        if result:
            return result
    return _fallback_headlines(label, items)


def _summarize_with_gemini(label: str, items: list, api_key: str):
    headlines = "\n".join(f"- {i['title']}: {i['summary']}" for i in items)
    prompt = (
        f"다음은 최근 24시간 동안의 '{label}' 관련 뉴스 헤드라인들이다.\n{headlines}\n\n"
        f"장기투자자 관점에서 중요한 내용 위주로 한국어 3~4줄로 간결하게 요약해줘. "
        f"각 줄은 핵심 사실 위주로, 불필요한 수식어 없이 작성해줘."
    )
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
        return None


def _fallback_headlines(label: str, items: list) -> str:
    lines = [f"[{label}]"] + [f"- {i['title']}" for i in items[:3]]
    return "\n".join(lines)
