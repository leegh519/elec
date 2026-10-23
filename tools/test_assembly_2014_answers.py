"""사용자 지정 2014 국회직 정답과 재생성 경로를 검증한다."""
import json
import unittest
from unittest.mock import patch

import merge_staging_bank
from update_official_answers import ANSWERS, PROJECT, source_for


class Assembly2014AnswersTest(unittest.TestCase):
    def test_data_copies_use_requested_answers(self):
        expected = list(map(int, "51332214513412443535"))
        self.assertEqual(ANSWERS["assembly-2014"], expected)
        questions = json.loads((PROJECT / "data/questions.json").read_text())
        browser = json.loads((PROJECT / "data/data.js").read_text().strip()
                             .removeprefix("window.QUESTION_BANK = ")[:-1])
        self.assertEqual(browser["questions"], questions)
        keys = json.loads((PROJECT / "data/answer_keys.json").read_text())["assembly-2014"]
        selected = sorted((q for q in questions if q["examId"] == "assembly-2014"),
                          key=lambda q: q["number"])
        self.assertEqual(len(selected), 20)
        for question, choice in zip(selected, expected):
            self.assertEqual(question["answer"], keys[str(question["number"])])
            self.assertEqual(question["answer"], {
                "choice": choice, "status": "cross-checked",
                "sources": [source_for("assembly-2014")],
            })

    def test_merge_preserves_correction_without_reading_wrong_pdf(self):
        def extract(year, path):
            self.assertNotEqual(year, 2014)
            return [1] * 20, "가"

        with patch.object(merge_staging_bank, "assembly_answers", side_effect=extract), \
                patch.object(merge_staging_bank, "seoul_answers", return_value=([1] * 20, "A")):
            entries = merge_staging_bank.answer_map()
        for number, choice in enumerate(ANSWERS["assembly-2014"], 1):
            self.assertEqual(entries[f"assembly-2014-{number:02d}"]["choice"], choice)


if __name__ == "__main__":
    unittest.main()
