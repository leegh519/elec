"""페이지 잡선 정리가 검수 영역 밖의 픽셀과 캔버스를 보존하는지 검증."""
import hashlib
import json
import unittest
from pathlib import Path

from PIL import Image
from clean_page_artifacts import clean_image

ROOT = Path(__file__).resolve().parents[1]


class PageArtifactTest(unittest.TestCase):
    def test_only_approved_rectangle_is_whitened(self):
        image = Image.new('L', (100, 80), 0)
        cleaned = clean_image(image, [[90, 0, 100, 80], [0, 70, 100, 80]])
        self.assertEqual(cleaned.size, image.size)
        self.assertEqual(cleaned.crop((0, 0, 90, 70)).tobytes(), image.crop((0, 0, 90, 70)).tobytes())
        self.assertEqual(cleaned.getpixel((99, 20)), 255)
        self.assertEqual(cleaned.getpixel((20, 79)), 255)
        self.assertEqual(image.getpixel((99, 20)), 0)
        with self.assertRaises(ValueError):
            clean_image(image, [[0, 0, 101, 80]])

    def test_reviewed_assets_match_manifest_and_remain_clean(self):
        manifest = json.loads((ROOT / 'data/page_artifact_masks.json').read_text())
        self.assertEqual(len({r['id'] for r in manifest['images']}), len(manifest['images']))
        for row in manifest['images']:
            path = ROOT / row['src']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), row['afterSha256'], row['id'])
            with Image.open(path) as image:
                self.assertEqual(list(image.size), row['size'], row['id'])
                for rect in row['rectangles']:
                    self.assertEqual(image.crop(rect).getextrema(), (255, 255), row['id'])
                self.assertEqual(clean_image(image, row['rectangles']).tobytes(), image.tobytes())


if __name__ == '__main__':
    unittest.main()
