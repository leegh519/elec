#!/usr/bin/env python3
"""공식 사이버국가고시센터 정답을 문제은행 형식으로 반영한다."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode


PROJECT = Path(__file__).resolve().parents[1]
KEY_FILE = PROJECT / "data" / "answer_keys.json"
QUESTIONS_FILE = PROJECT / "data" / "questions.json"
DATA_JS_FILE = PROJECT / "data" / "data.js"
MISMATCH_FILE = PROJECT / "review" / "answer-source-mismatches.json"
BASE = "https://gongmuwon.gosi.kr"


ANSWERS = {
    "national-2007": [2, 4, 4, 2, 1, 3, 4, 3, 1, 4, 1, 3, 3, 3, 4, 2, 2, 1, 1, 3],
    "national-2008": [1, 3, 1, 3, 1, 2, 4, 4, 4, 4, 2, 3, 1, 2, 4, 3, 1, 2, 3, 3],
    "national-2009": [4, 1, 4, 3, 3, 2, 1, 1, 2, 4, 3, 2, 3, 2, 3, 4, 1, 2, 4, 3],
    "national-2010": [1, 3, 2, 2, 1, 4, 4, 2, 1, 3, 2, 3, 1, 4, 3, 4, 1, 3, 4, 2],
    "national-2011": [3, 2, 3, 4, 2, 4, 2, 4, 1, 4, 4, 2, 3, 2, 3, 2, 1, 4, 3, 1],
    "national-2012": [3, 1, 3, 3, 3, 1, 4, 4, 2, 1, 2, 2, 1, 2, 4, 2, 3, 3, 1, 1],
    "national-2013": [3, 2, 3, 1, 1, 4, 2, 4, 3, 4, 3, 3, 1, 3, 1, 1, 4, 1, 2, 2],
    "national-2014": [4, 3, 1, 3, 4, 2, 4, 1, 1, 2, 1, 2, 3, 4, 1, 2, 4, 2, 3, 4],
    "national-2015": [2, 4, 1, 3, 1, 4, 4, 1, 1, 3, 3, 3, 4, 2, 2, 4, 3, 2, 1, 2],
    "national-2016": [1, 2, 2, 4, 1, 3, 4, 1, 1, 4, 1, 2, 2, 3, 2, 3, 4, 3, 1, 4],
    "national-2017": [4, 2, 1, 4, 3, 3, 2, 4, 2, 3, 1, 1, 4, 1, 2, 1, 1, 3, 3, 4],
    "national-2018": [1, 4, 4, 2, 1, 4, 2, 3, 3, 3, 2, 3, 4, 2, 2, 3, 3, 2, 2, 1],
    "national-2019": [3, 3, 1, 2, 4, 3, 3, 2, 2, 3, 4, 1, 4, 2, 2, 1, 1, 1, 3, 4],
    "national-2020": [4, 1, 1, 4, 3, 1, 4, 3, 2, 3, 1, 2, 1, 3, 2, 4, 3, 3, 2, 3],
    "national-2021": [2, 1, 1, 2, 2, 4, 3, 2, 3, 4, 3, 3, 3, 1, 4, 1, 2, 4, 4, 2],
    "national-2022": [4, 3, 2, 4, 3, 2, 2, 3, 3, 4, 1, 2, 3, 4, 1, 4, 1, 3, 4, 1],
    "national-2023": [2, 2, 1, 3, 2, 3, 2, 2, 1, 1, 4, 3, 1, 4, 4, 3, 3, 4, 1, 1],
    "national-2024": [3, 4, 3, 2, 4, 4, 1, 2, 2, 1, 1, 3, 3, 3, 2, 2, 4, 2, 1, 1],
    "national-2025": [1, 4, 4, 2, 4, 2, 1, 3, 1, 1, 3, 2, 2, 2, 4, 3, 2, 3, 4, 2],
    "national-2026": [2, 2, 2, 1, 4, 1, 1, 4, 2, 2, 4, 3, 1, 1, 3, 3, 3, 3, 2, 3],
    "local-2009": [2, 1, 3, 4, 2, 4, 1, 3, 4, 1, 4, 2, 1, 3, 1, 2, 4, 3, 2, 3],
    "local-2010": [4, 2, 4, 1, 1, 1, 4, 3, 2, 4, 2, 3, 2, 4, 2, 1, 4, 3, 2, 3],
    "local-2011": [4, 4, 2, 4, 1, 3, 2, 3, 3, 1, 1, 3, 4, 2, 4, 2, 2, 3, 1, 1],
    "local-2012": [3, 4, 4, 1, 3, 2, 4, 4, 4, 2, 2, 1, 2, 1, 1, 3, 1, 3, 4, 1],
    "local-2022": [1, 1, 4, 4, 4, 3, 2, 3, 2, 2, 1, 4, 1, 3, 3, 2, 3, 1, 3, 4],
    "local-2023": [1, 3, 2, 1, 4, 1, 2, 3, 1, 2, 4, 2, 3, 1, 1, 3, 2, 2, 1, 4],
    "local-2024": [2, 4, 2, 2, 4, 2, 2, 3, 1, 3, 3, 2, 1, 2, 1, 4, 1, 4, 3, 4],
    "local-2025": [4, 4, 3, 2, 1, 4, 2, 2, 2, 4, 3, 1, 1, 3, 2, 1, 4, 3, 3, 2],
    "local-2026": [4, 2, 2, 1, 1, 4, 3, 1, 4, 4, 3, 4, 3, 2, 3, 4, 3, 1, 4, 1],
    "military-2022": [4, 3, 4, 1, 2, 3, 4, 3, 2, 1, 3, 1, 3, 2, 2, 4, 2, 1, 1, 3],
    "military-2023": [4, 2, 1, 4, 4, 3, 1, 4, 1, 3, 2, 2, 3, 2, 1, 1, 4, 4, 2, 1],
    "military-2024": [2, 4, 2, 1, 4, 2, 1, 3, 2, 3, 2, 2, 3, 3, 3, 1, 4, 1, 3, 4],
    "military-2025": [4, 3, 4, 1, 2, 4, 1, 3, 2, 3, 1, 3, 2, 2, 4, 3, 2, 3, 4, 1],
    "military-2026": [2, 2, 2, 2, 4, 1, 3, 2, 1, 4, 4, 4, 3, 3, 1, 1, 1, 4, 1, 3],
}


LEGACY = {
    "national-2007": ("08049", "08", "937", "국"),
    "national-2008": ("08050", "08", "937", "안"),
    "national-2009": ("08051", "08", "937", "녹"),
    "national-2010": ("08052", "08", "937", "고"),
    "national-2011": ("08053", "08", "937", "인"),
    "national-2012": ("08054", "08", "937", "인"),
    "local-2009": ("33004", "33", "764", "A"),
    "local-2010": ("33005", "33", "764", "A"),
    "local-2011": ("33006", "33", "764", "A"),
    "local-2012": ("33007", "33", "764", "A"),
}

POSTS = {
    **{f"national-{year}": post for year, post in {
        2013: 2412, 2014: 2566, 2015: 2765, 2016: 2968, 2017: 3177,
        2018: 3376, 2019: 3535, 2020: 3782, 2021: 3934, 2022: 4112,
        2023: 4285, 2024: 4464, 2025: 4704, 2026: 5993,
    }.items()},
    **{f"local-{year}": post for year, post in {
        2022: 4145, 2023: 4322, 2024: 4531, 2025: 4742, 2026: 6011,
    }.items()},
}

BOOKTYPES = {
    "national-2013": "인", "national-2014": "S", "national-2015": "사",
    "national-2016": "2", "national-2017": "나", "national-2018": "가",
    "national-2019": "나", "national-2020": "가", "national-2021": "나",
    "national-2022": "가", "national-2023": "나", "national-2024": "가",
    "national-2025": "나", "national-2026": "가", "local-2022": "A",
    "local-2023": "B", "local-2024": "C", "local-2025": "B", "local-2026": "D",
}


def source_for(exam_id: str) -> dict:
    agency, raw_year = exam_id.split("-")
    year = int(raw_year)
    if agency == "military":
        booktype = None
        encoded_path = "%EA%B3%B5%EB%AC%B4%EC%9B%90/%EA%B5%B0%EB%AC%B4%EC%9B%90/9%EA%B8%89"
        encoded_subject = "%EC%A0%84%EC%9E%90%EA%B3%B5%ED%95%99"
        encoded_answer = f"{year}_%EC%A0%95%EB%8B%B5.pdf"
        url = f"https://d2u7om5rih5x7z.cloudfront.net/exam-archive/{encoded_path}/{year}/{encoded_subject}/answer/{encoded_answer}"
        label = f"국방부 {year}년도 일반군무원 채용 필기시험 정답표 (전자공학 9급)"
        return {"type": "official", "label": label, "url": url, "booktype": booktype}
    if exam_id in LEGACY:
        plan, test, subject, booktype = LEGACY[exam_id]
        query = urlencode({
            "enfcYr": year, "planCd": plan, "cransSeCd": 2,
            "bktpNm": booktype, "testCd": test, "sbjctCd": subject,
        })
        url = f"{BASE}/oprut/GosiJungdap.do?{query}"
    else:
        booktype = BOOKTYPES[exam_id]
        post_id = POSTS[exam_id]
        url = f"{BASE}/oprut/EvmArPrblmCransGdDtl.do?pstId={post_id}&bbsId=BBSMSTR_000000000138"
    label = f"사이버국가고시센터 {year}년 {'국가직' if agency == 'national' else '지방직'} 최종정답 ({booktype}책형)"
    return {"type": "official", "label": label, "url": url, "booktype": booktype}


def sync_question_data(answer_keys: dict) -> int:
    """정답 원본을 문제 JSON과 브라우저용 데이터에도 함께 반영한다."""
    if not QUESTIONS_FILE.exists():
        return 0
    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))
    changed = 0
    for question in questions:
        entry = answer_keys.get(question["examId"], {}).get(str(question["number"]))
        if entry is None or question.get("answer") == entry:
            continue
        question["answer"] = entry
        question.setdefault("review", {})["answer"] = "approved"
        changed += 1
    QUESTIONS_FILE.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if DATA_JS_FILE.exists():
        prefix = "window.QUESTION_BANK = "
        raw = DATA_JS_FILE.read_text(encoding="utf-8").strip()
        if not raw.startswith(prefix) or not raw.endswith(";"):
            raise ValueError("data.js 형식이 올바르지 않습니다")
        payload = json.loads(raw[len(prefix):-1])
        payload["questions"] = questions
        DATA_JS_FILE.write_text(prefix + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")
    return changed


def main() -> None:
    old = json.loads(KEY_FILE.read_text(encoding="utf-8")) if KEY_FILE.exists() else {}
    mismatches = []
    result = {}
    for exam_id, choices in ANSWERS.items():
        if len(choices) != 20 or any(choice not in {1, 2, 3, 4} for choice in choices):
            raise ValueError(f"invalid answer row: {exam_id}")
        source = source_for(exam_id)
        result[exam_id] = {}
        for number, choice in enumerate(choices, start=1):
            previous = old.get(exam_id, {}).get(str(number))
            previous_choice = previous.get("choice") if isinstance(previous, dict) else previous
            if previous_choice is not None and previous_choice != choice:
                mismatches.append({
                    "examId": exam_id, "number": number,
                    "previousChoice": previous_choice, "officialChoice": choice,
                    "previousSources": previous.get("sources", []) if isinstance(previous, dict) else [],
                })
            result[exam_id][str(number)] = {
                "choice": choice, "status": "official", "sources": [source],
            }

    KEY_FILE.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    synced = sync_question_data(result)
    MISMATCH_FILE.parent.mkdir(parents=True, exist_ok=True)
    MISMATCH_FILE.write_text(json.dumps(mismatches, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"official exams={len(result)} answers={sum(map(len, result.values()))} "
        f"mismatches={len(mismatches)} synced={synced}"
    )


if __name__ == "__main__":
    main()
