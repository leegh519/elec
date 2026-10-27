"""여백 제거가 내용과 번호 가림 좌표를 보존하는지 검증."""
import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image
from trim_image_margins import find_trim_rectangle, trim_preserving_content, translate_mask

ROOT = Path(__file__).resolve().parents[1]


class ImageMarginTest(unittest.TestCase):
    def test_asymmetric_margins_preserve_faint_content_and_padding(self):
        image = Image.new('L', (400, 500), 255)
        image.paste(0, (100, 90, 260, 200))
        image.putpixel((300, 350), 254)
        rectangle = find_trim_rectangle(image)
        self.assertEqual(rectangle, [88, 78, 313, 363])
        cropped = trim_preserving_content(image, rectangle)
        self.assertEqual(cropped.tobytes(), image.crop(rectangle).tobytes())
        self.assertEqual(cropped.getpixel((212, 272)), 254)
        with self.assertRaises(ValueError):
            trim_preserving_content(image, [88, 78, 300, 351])

    def test_small_margins_are_unchanged_and_masks_clip_and_translate(self):
        image = Image.new('L', (100, 100), 255)
        image.paste(0, (20, 20, 80, 80))
        self.assertEqual(find_trim_rectangle(image), [0, 0, 100, 100])
        self.assertEqual(translate_mask([0, 10, 130, 60], [88, 5, 300, 200]), [0, 5, 42, 55])
        self.assertIsNone(translate_mask([0, 10, 20, 60], [88, 5, 300, 200]))
        self.assertIsNone(translate_mask(None, [88, 5, 300, 200]))

    def test_trimmed_assets_sizes_hashes_and_masks_match_metadata(self):
        path = ROOT / 'data/image_margin_trims.json'
        if not path.exists():
            self.skipTest('아직 여백 정리 전')
        report = json.loads(path.read_text())
        questions = {q['id']: q for q in json.loads((ROOT / 'data/questions.json').read_text())}
        masks = json.loads((ROOT / 'data/print_number_masks.json').read_text())
        self.assertEqual(report['trimmedImages'], len(report['images']))
        self.assertEqual(len({r['id'] for r in report['images']}), len(report['images']))
        for row in report['images']:
            source = ROOT / row['src']
            final = row.get('followup', row)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), final['afterSha256'], row['id'])
            expected_mask = translate_mask(row['originalNumberMaskPixels'], row['cropPixels'])
            if 'followup' in row:
                self.assertEqual(final['beforeSha256'], row['afterSha256'], row['id'])
                expected_mask = translate_mask(expected_mask, final['cropPixels'])
            self.assertEqual(masks[row['id']], expected_mask, row['id'])
            with Image.open(source) as image:
                self.assertEqual(list(image.size), final['size'], row['id'])
                self.assertEqual(image.size, (questions[row['id']]['image']['width'], questions[row['id']]['image']['height']))
                self.assertEqual(find_trim_rectangle(image), [0, 0, image.width, image.height], row['id'])


if __name__ == '__main__':
    unittest.main()
