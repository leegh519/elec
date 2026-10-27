"""중분류 교정 후 선택 가능한 문제와 재생성 결과의 무결성 검증."""
import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import reclassify_questions as classifier

PROJECT = Path(__file__).resolve().parents[1]


class ClassificationIntegrityTest(unittest.TestCase):
    def setUp(self):
        self.questions = json.loads((PROJECT / 'data/questions.json').read_text())
        self.taxonomy = json.loads((PROJECT / 'data/taxonomy.json').read_text())

    def test_every_selectable_topic_has_valid_questions(self):
        _, topics = classifier.taxonomy_indexes(self.taxonomy)
        counts = Counter()
        for question in self.questions:
            classification = question['classification']
            self.assertTrue(classification['topics'], question['id'])
            self.assertEqual(len(classification['topics']), len(set(classification['topics'])))
            for topic in classification['topics']:
                self.assertIn((classification['category'], topic), topics, question['id'])
                counts[topic] += 1
        for _, topic in topics:
            self.assertGreater(counts[topic], 0, topic)
        report = json.loads((PROJECT / 'review/classification-report.json').read_text())
        self.assertEqual(dict(counts), report['topicCounts'])
        self.assertEqual(len(self.questions), report['questionCount'])

    def test_browser_and_regeneration_data_match(self):
        browser = json.loads((PROJECT / 'data/data.js').read_text().strip()
                             .removeprefix('window.QUESTION_BANK = ')[:-1])
        self.assertEqual(browser['questions'], self.questions)
        self.assertEqual(browser['taxonomy'], self.taxonomy)
        overrides = json.loads((PROJECT / 'data/classification_overrides.json').read_text())
        for question in self.questions:
            self.assertEqual(question['classification'], overrides[question['id']])

    def test_reviewed_circuit_classifications_survive_regeneration(self):
        audit = json.loads((PROJECT / 'review/empty-topic-audit.json').read_text())
        _, topics = classifier.taxonomy_indexes(self.taxonomy)
        questions = {q['id']: q for q in self.questions}
        for entry in audit['questionChanges']:
            question = questions[entry['id']]
            self.assertEqual(classifier.classify(question, topics), question['classification'])
            self.assertEqual(question['classification'], classifier.CURRICULUM_CLASSIFICATIONS[entry['id']])

    def test_scoped_regeneration_preserves_unselected_question(self):
        selected = next(q for q in self.questions if q['id'] == 'seoul-2021-11')
        untouched = self.questions[0]
        untouched['review']['classification'] = 'pending-local-review'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data = root / 'data'
            data.mkdir()
            (root / 'review').mkdir()
            for name, value in [('questions', [untouched, selected]),
                                ('taxonomy', self.taxonomy), ('exams', [])]:
                (data / f'{name}.json').write_text(json.dumps(value))
            with patch.object(classifier, 'PROJECT', root), \
                    patch.object(classifier, 'DATA', data), \
                    patch.object(sys, 'argv', ['reclassify', '--only', selected['id']]):
                self.assertEqual(classifier.main(), 0)
                first = (data / 'questions.json').read_bytes()
                self.assertEqual(json.loads(first)[0], untouched)
                self.assertEqual(classifier.main(), 0)
                self.assertEqual((data / 'questions.json').read_bytes(), first)

    def test_organization_corrections_survive_regeneration(self):
        _, topics = classifier.taxonomy_indexes(self.taxonomy)
        questions = {q['id']: q for q in self.questions}
        for key, correction in classifier.ORGANIZATION_CORRECTIONS.items():
            q = questions[key]
            self.assertEqual(q['classification'], classifier.CURRICULUM_CLASSIFICATIONS[key], key)
            self.assertEqual(classifier.classify(q, topics), q['classification'], key)

    def test_curriculum_covers_electronic_and_digital_topics(self):
        for category in self.taxonomy['categories']:
            if category['id'] in {'electronic-circuits', 'digital-engineering'}:
                self.assertTrue(all(topic.get('concepts') for topic in category['topics']))
        questions = {q['id']: q for q in self.questions}
        # 키워드 OCR 오염으로 대분류까지 잘못 들어갔던 실제 사례.
        self.assertEqual(questions['national-2013-12']['classification']['category'], 'electronic-circuits')
        self.assertEqual(questions['military-2022-03']['classification']['category'], 'circuit-theory')
        self.assertIn('memory', questions['national-2021-04']['classification']['topics'])
        self.assertNotIn('minimization-kmap', questions['national-2023-12']['classification']['topics'])

    def test_curriculum_merge_and_content_preservation(self):
        audit = json.loads((PROJECT / 'review/curriculum-migration.json').read_text())
        questions = {q['id']: q for q in self.questions}
        self.assertEqual([len(c['topics']) for c in self.taxonomy['categories']], [17, 24, 17])
        for entry in audit['changes']:
            self.assertEqual(questions[entry['id']]['classification'], classifier.CURRICULUM_CLASSIFICATIONS[entry['id']])
        _, topics = classifier.taxonomy_indexes(self.taxonomy)
        for question in self.questions:
            self.assertEqual(classifier.classify(question, topics), question['classification'])
        for topic in ['series-parallel', 'kcl-kvl', 'node-analysis', 'loop-analysis']:
            self.assertEqual(audit['mapping'][topic]['topic'], 'circuit-analysis')


if __name__ == '__main__':
    unittest.main()
