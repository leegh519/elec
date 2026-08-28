#!/usr/bin/env python3
"""Fetch provisional national-exam answer keys from the public CBTBank pages."""
from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT / "data" / "answer_keys.json"
BASE = "https://cbtbank.kr/exam/"
EXAMS = {
    "national-2007": "cp20070414", "national-2008": "cp20080412",
    "national-2009": "cp20090411", "national-2010": "cp20100410",
    "national-2011": "cp20110409", "national-2012": "cp20120407",
    "national-2013": "cp20130727", "national-2014": "cp20140419",
    "national-2015": "cp20150418", "national-2016": "cp20160409",
    "national-2017": "cp20170408", "national-2018": "cp20180407",
    "national-2019": "cp20190406", "national-2020": "cp20200711",
    "national-2021": "cp20210417", "national-2022": "cp20220402",
    "national-2023": "cp20230408", "national-2024": "cp20240323",
    "national-2025": "cp20250405",
}
ANSWER_RE = re.compile(
    r'question-num="(\d+)".*?<ol class="circlednumbers" correct="([1-4])">',
    re.S,
)


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 question-bank-builder/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def main() -> int:
    existing = json.loads(OUTPUT.read_text(encoding="utf-8")) if OUTPUT.exists() else {}
    for index, (exam_id, code) in enumerate(EXAMS.items(), start=1):
        url = BASE + code
        html = fetch(url)
        answers = {int(number): int(choice) for number, choice in ANSWER_RE.findall(html)}
        if set(answers) != set(range(1, 21)):
            raise RuntimeError(f"{exam_id}: expected 20 answers, got {sorted(answers)}")
        existing[exam_id] = {
            str(number): {
                "choice": answers[number],
                "status": "unverified",
                "sources": [{"type": "secondary", "label": "CBT문제은행", "url": url}],
            }
            for number in range(1, 21)
        }
        print(f"[{index}/{len(EXAMS)}] {exam_id}: 20 provisional answers")
        time.sleep(0.15)
    OUTPUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
