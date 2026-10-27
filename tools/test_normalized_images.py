"""원 번호가 PNG에 직접 반영되고 여백·메타데이터가 일치하는지 검증."""
import hashlib
import json
import unittest
from pathlib import Path
from PIL import Image
from trim_image_margins import find_trim_rectangle

ROOT = Path(__file__).resolve().parents[1]


class NormalizedImagesTest(unittest.TestCase):
    def test_all_assets_are_numberless_and_tightly_bounded(self):
        report = json.loads((ROOT / 'data/normalized_question_images.json').read_text())
        questions = {q['id']: q for q in json.loads((ROOT / 'data/questions.json').read_text())}
        masks = json.loads((ROOT / 'data/print_number_masks.json').read_text())
        self.assertEqual(len(report['images']), 1100)
        self.assertEqual({r['id'] for r in report['images']}, set(questions))
        self.assertTrue(all(value is None for value in masks.values()))
        for row in report['images']:
            source = ROOT / row['src']
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), row['afterSha256'], row['id'])
            with Image.open(source) as image:
                self.assertEqual(list(image.size), row['size'], row['id'])
                self.assertEqual(image.size, (questions[row['id']]['image']['width'], questions[row['id']]['image']['height']))
                self.assertEqual(find_trim_rectangle(image, padding=8, min_margin=1), [0, 0, image.width, image.height], row['id'])


if __name__ == '__main__':
    unittest.main()
