"""연준(FOMC) 정례회의 일정. 연준이 매년 발표하는 공식 일정을 기준으로 하며,
다음 해 일정이 나오면 이 리스트를 수동으로 갱신해야 한다.
출처: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
"""
from datetime import date

FOMC_MEETINGS_2026 = [
    (date(2026, 1, 27), date(2026, 1, 28)),
    (date(2026, 3, 17), date(2026, 3, 18)),
    (date(2026, 4, 28), date(2026, 4, 29)),
    (date(2026, 6, 16), date(2026, 6, 17)),
    (date(2026, 7, 28), date(2026, 7, 29)),
    (date(2026, 9, 15), date(2026, 9, 16)),
    (date(2026, 10, 27), date(2026, 10, 28)),
    (date(2026, 12, 8), date(2026, 12, 9)),
]


def next_fomc_meeting(today: date) -> str:
    """오늘 이후 가장 가까운 FOMC 회의를 'MM/DD~MM/DD (D-n)' 형식으로 반환."""
    for start, end in FOMC_MEETINGS_2026:
        if end >= today:
            d_day = (start - today).days
            d_label = f"D-{d_day}" if d_day > 0 else "D-DAY"
            return f"{start.strftime('%m/%d')}~{end.strftime('%m/%d')} ({d_label})"
    return "일정 미등록 (연준 공식 발표 확인 필요)"
