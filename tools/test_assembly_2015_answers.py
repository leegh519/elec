"""2015 국회직 공식 정답·추출·브라우저 데이터 회귀 검증."""
import json
import unittest

from merge_staging_bank import PROJECT, answer_source, assembly_answers
from update_official_answers import ANSWERS, source_for


class Assembly2015AnswersTest(unittest.TestCase):
    def test_official_pdf_matches_verified_answers(self):
        choices, booktype = assembly_answers(2015, answer_source("국회직", 2015))
        self.assertEqual(booktype, "가")
        self.assertEqual(choices, ANSWERS["assembly-2015"])
        self.assertEqual(choices[11], 2)

    def test_wrong_subject_count_is_rejected(self):
        from unittest.mock import patch
        wrong_table = "\n".join(f"문 {n} " + " ".join(["1"] * 17) for n in range(1, 21))
        with patch("merge_staging_bank.pdf_text", return_value=wrong_table):
            with self.assertRaisesRegex(ValueError, "과목 수 불일치"):
                assembly_answers(2015, PROJECT / "wrong.pdf")

    def test_all_data_copies_match(self):
        questions = json.loads((PROJECT / "data/questions.json").read_text())
        raw = (PROJECT / "data/data.js").read_text().strip()
        browser = json.loads(raw.removeprefix("window.QUESTION_BANK = ")[:-1])
        self.assertEqual(browser["questions"], questions)
        keys = json.loads((PROJECT / "data/answer_keys.json").read_text())["assembly-2015"]
        selected = [q for q in questions if q["examId"] == "assembly-2015"]
        self.assertEqual(len(selected), 20)
        for question in selected:
            entry = keys[str(question["number"])]
            self.assertEqual(question["answer"], entry)
            self.assertEqual(entry["choice"], ANSWERS["assembly-2015"][question["number"] - 1])
            self.assertEqual(entry["sources"], [source_for("assembly-2015")])


if __name__ == "__main__":
    unittest.main()
