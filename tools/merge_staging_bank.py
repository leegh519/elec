#!/usr/bin/env python3
"""문제은행선작업의 국회직·서울시 420문제를 본 문제은행에 병합한다."""
from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

import pdfplumber


PROJECT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT.parent
STAGING = WORKSPACE / "문제은행선작업"
SOURCE_ROOT = WORKSPACE / "공무원 기출" / "전자공학개론"

# pdfplumber가 추출한 국회직 정답표 행에서 전자공학개론 열의 0 기반 위치.
ASSEMBLY_SUBJECT_INDEX = {
    2014: 15, 2015: 16, 2016: 13, 2017: 13, 2018: 12,
    2019: 15, 2020: 13, 2021: 13, 2022: 12, 2023: 13,
    2024: 10, 2025: 13,
}
SEOUL_BOOKTYPE = {
    2014: "A", 2015: "A", 2016: "A", 2017: "A", 2018: "A",
    2019: "A", 2020: "B", 2021: "A",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def number_rows(text: str) -> list[list[int]]:
    rows = []
    for line in text.splitlines():
        match = re.match(r"문\s*(\d+)\s+(.+)$", line.strip())
        if not match:
            continue
        values = [int(value) for value in re.findall(r"(?<!\d)[1-5](?!\d)", match.group(2))]
        rows.append([int(match.group(1)), *values])
    return rows


def assembly_answers(year: int, path: Path) -> tuple[list[int], str]:
    text = pdf_text(path)
    if year == 2009:
        section = text.split("정답표(전자공학개론)", 1)[1].split("정답표(통신이론)", 1)[0]
        answers = []
        rows = []
        for line in section.splitlines():
            match = re.fullmatch(r"\s*(\d{1,2})\s+([1-5])\s+([1-5])\s*", line)
            if match:
                rows.append([int(value) for value in match.groups()])
        for number, *values in rows[:20]:
            if number != len(answers) + 1 or len(values) < 2:
                raise ValueError(f"{path.name}: 2009 가형 정답 행 오류")
            answers.append(values[0])
        booktype = "가"
    else:
        index = ASSEMBLY_SUBJECT_INDEX[year]
        rows = number_rows(text)[:20]
        answers = []
        for number, *values in rows:
            if number != len(answers) + 1 or len(values) <= index:
                raise ValueError(f"{path.name}: {number}번 전자공학개론 열 추출 실패")
            answers.append(values[index])
        booktype = "가" if year <= 2021 else "단일"
    if len(answers) != 20:
        raise ValueError(f"{path.name}: 정답 {len(answers)}개")
    return answers, booktype


def seoul_answers(year: int, path: Path) -> tuple[list[int], str]:
    booktype = SEOUL_BOOKTYPE[year]
    pattern = re.compile(
        rf"^전자공학개론[^\n]*?\s{booktype}(?:형)?\s+((?:[1-5]\s+){{19}}[1-5])\s*$",
        re.MULTILINE,
    )
    match = pattern.search(pdf_text(path))
    if not match:
        raise ValueError(f"{path.name}: 전자공학개론 {booktype}형 정답행을 찾지 못함")
    answers = [int(value) for value in match.group(1).split()]
    if len(answers) != 20:
        raise ValueError(f"{path.name}: 정답 {len(answers)}개")
    return answers, booktype


def answer_map() -> dict[str, dict]:
    result = {}
    for agency, slug, years in (
        ("국회직", "assembly", [2009, *range(2014, 2026)]),
        ("서울시", "seoul", range(2014, 2022)),
    ):
        for year in years:
            source = SOURCE_ROOT / agency / f"{year}-{agency}-정답.pdf"
            answers, booktype = (
                assembly_answers(year, source) if agency == "국회직"
                else seoul_answers(year, source)
            )
            for number, choice in enumerate(answers, start=1):
                result[f"{slug}-{year}-{number:02d}"] = {
                    "choice": choice,
                    "status": "official",
                    "sources": [{
                        "type": "official",
                        "label": f"{year}년 {agency} 전자공학개론 공식 정답표 ({booktype}형)",
                        "path": f"official-answers/{year}-{agency}-정답.pdf",
                        "booktype": booktype,
                    }],
                }
    return result


def main() -> int:
    staged_exams = load_json(STAGING / "data" / "exams.json")
    staged_questions = load_json(STAGING / "data" / "questions.json")
    answers = answer_map()
    if len(staged_exams) != 21 or len(staged_questions) != 420 or len(answers) != 420:
        raise ValueError("선작업 또는 정답 건수가 예상값(21개 시험·420문제)과 다릅니다.")

    for question in staged_questions:
        question["answer"] = answers[question["id"]]
        question["choiceCount"] = 5 if question["agency"] == "국회직" or question["examId"] == "seoul-2014" else 4
        question.setdefault("review", {})["answer"] = "approved"

    exams_path = PROJECT / "data" / "exams.json"
    questions_path = PROJECT / "data" / "questions.json"
    exams = load_json(exams_path)
    questions = load_json(questions_path)
    staged_exam_ids = {exam["id"] for exam in staged_exams}
    staged_question_ids = {question["id"] for question in staged_questions}
    exams = [exam for exam in exams if exam["id"] not in staged_exam_ids] + staged_exams
    questions = [question for question in questions if question["id"] not in staged_question_ids] + staged_questions
    exams.sort(key=lambda item: (item["year"], item["agency"]))
    questions.sort(key=lambda item: (item["year"], item["agency"], item["number"]))

    exams_path.write_text(json.dumps(exams, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    questions_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for agency in ("assembly", "seoul"):
        shutil.copytree(
            STAGING / "assets" / "questions" / agency,
            PROJECT / "assets" / "questions" / agency,
            dirs_exist_ok=True,
        )
    for sheet in (STAGING / "review" / "contact-sheets").glob("*.jpg"):
        shutil.copy2(sheet, PROJECT / "review" / "contact-sheets" / sheet.name)
    for agency, years in (("국회직", [2009, *range(2014, 2026)]), ("서울시", range(2014, 2022))):
        for year in years:
            source = SOURCE_ROOT / agency / f"{year}-{agency}-정답.pdf"
            shutil.copy2(source, PROJECT / "official-answers" / source.name)

    report = {
        "mergedAt": date.today().isoformat(),
        "addedExamCount": len(staged_exams),
        "addedQuestionCount": len(staged_questions),
        "totalExamCount": len(exams),
        "totalQuestionCount": len(questions),
        "officialAnswerCount": sum(q.get("answer", {}).get("status") == "official" for q in questions),
        "agencies": {
            agency: {
                "examCount": sum(exam["agency"] == agency for exam in exams),
                "questionCount": sum(question["agency"] == agency for question in questions),
            }
            for agency in sorted({exam["agency"] for exam in exams})
        },
    }
    (PROJECT / "review" / "staging-merge-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
