"""소분류 의미, 전 문항 커버리지, 제본 중복·정렬·필터를 검증한다."""
import copy
import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path

from study_taxonomy import build_print_plan, indexes, validate_classification

ROOT = Path(__file__).resolve().parents[1]


class StudyTaxonomyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questions = json.loads((ROOT / 'data/questions.json').read_text())
        cls.taxonomy = json.loads((ROOT / 'data/taxonomy.json').read_text())
        cls.audit = json.loads((ROOT / 'review/full-bank-classification-audit.json').read_text())

    def test_every_question_has_valid_nonempty_details(self):
        _, topics, leaves = indexes(self.taxonomy)
        counts = Counter()
        for q in self.questions:
            validate_classification(q['classification'], self.taxonomy)
            counts.update(q['classification']['subtopics'])
        self.assertEqual(len(self.questions), 1100)
        self.assertEqual(len({q['id'] for q in self.questions}), 1100)
        self.assertEqual(len(topics), 58)
        self.assertEqual(set(counts), set(leaves))

    def test_review_coverage_and_protected_content(self):
        rows = {r['id']: r for r in self.audit['questions']}
        trims_path = ROOT / 'data/image_margin_trims.json'
        trims = {r['id']: r for r in json.loads(trims_path.read_text())['images']} if trims_path.exists() else {}
        normalized_path = ROOT / 'data/normalized_question_images.json'
        normalized = {r['id']: r for r in json.loads(normalized_path.read_text())['images']} if normalized_path.exists() else {}
        self.assertEqual(set(rows), {q['id'] for q in self.questions})
        for q in self.questions:
            protected = {k: v for k, v in q.items() if k != 'classification'}
            if q['id'] in normalized:
                width, height = normalized[q['id']]['originalSize']
                protected['image'] = {**protected['image'], 'width': width, 'height': height}
            # The classification audit predates the authorized blank-margin trim.
            # Restore only the recorded pre-trim dimensions when checking that audit;
            # test_image_margins verifies current dimensions, hashes and coordinates.
            if q['id'] in trims:
                width, height = trims[q['id']]['originalSize']
                protected['image'] = {**protected['image'], 'width': width, 'height': height}
            digest = hashlib.sha256(json.dumps(protected, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            self.assertEqual(digest, rows[q['id']]['protectedContentSha256'], q['id'])
            self.assertEqual(q['classification']['primarySubtopic'], rows[q['id']]['after']['primarySubtopic'])
            self.assertEqual(q['classification']['tags'], rows[q['id']]['after']['tags'])

    def test_semantic_regressions(self):
        actual = {q['id']: q['classification']['primarySubtopic'] for q in self.questions}
        expected = {'national-2020-08': 'arithmetic-circuits/compare',
                    'national-2023-12': 'digital-communication/pcm',
                    'assembly-2021-07': 'adc-dac/weighted',
                    'national-2022-07': 'differential-mirror/pair',
                    'assembly-2024-03': 'rectifier-smoothing/bridge',
                    'national-2023-15': 'differentiator-integrator/differentiator',
                    'seoul-2018-13': 'bridge-transform/bridge',
                    'military-2026-06': 'resonance/series',
                    'assembly-2023-03': 'error-correction/channel',
                    'military-2022-03': 'elements-basics/battery'}
        for key, value in expected.items():
            self.assertEqual(actual[key], value, key)

    def test_print_order_is_unique_deterministic_and_contiguous(self):
        plan = build_print_plan(self.questions, self.taxonomy)
        reverse = build_print_plan(list(reversed(self.questions)), self.taxonomy)
        duplicates = build_print_plan(self.questions + self.questions[:20], self.taxonomy)
        self.assertEqual(plan, reverse)
        self.assertEqual(plan, duplicates)
        self.assertEqual(len(plan), 1100)
        self.assertEqual(plan[-1]['page'], 275)
        groups = [(r['category'], r['topic'], r['group']) for r in plan]
        closed = set()
        previous = None
        for g in groups:
            if g != previous:
                self.assertNotIn(g, closed)
                closed.add(g)
                previous = g

    def test_tag_grouping_is_contiguous_and_priority_applies(self):
        plan = build_print_plan(self.questions, self.taxonomy, group_by='tag', tag_priority=['power'])
        previous = None
        closed = set()
        byid = {q['id']: q for q in self.questions}
        for r in plan:
            if 'power' in byid[r['id']]['classification']['tags']:
                self.assertEqual(r['group'], 'power')
            key = (r['category'], r['topic'], r['group'])
            if key != previous:
                self.assertNotIn(key, closed)
                closed.add(key)
                previous = key

    def test_related_filters_never_duplicate_a_question(self):
        selected = build_print_plan(self.questions, self.taxonomy,
                                    subtopics=['bridge-transform/bridge', 'bridge-transform/wye-delta'])
        ids = [r['id'] for r in selected]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('seoul-2021-11', ids)
        tag_plan = build_print_plan(self.questions, self.taxonomy, categories=['digital-engineering'], tags=['timing'])
        self.assertTrue(tag_plan)
        for r in tag_plan:
            self.assertEqual(r['category'], 'digital-engineering')
            self.assertIn('timing', r['tags'])

    def test_bad_filters_and_conflicting_duplicates_fail(self):
        with self.assertRaisesRegex(ValueError, '존재하지 않는 소분류'):
            build_print_plan(self.questions, self.taxonomy, subtopics=['bad'])
        altered = copy.deepcopy(self.questions[0])
        altered['number'] += 1
        with self.assertRaisesRegex(ValueError, '내용이 다른 중복'):
            build_print_plan(self.questions + [altered], self.taxonomy)


if __name__ == '__main__':
    unittest.main()
