"""텍스트 추출 성공만으로 놓칠 수 있는 PDF 명조체 렌더링 누락을 검증."""
import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from build_print_pdf import subset_font, paginate_print_plan, crop_print_image, load_image_crops, ROOT


class PrintCropTest(unittest.TestCase):
    def test_crop_preserves_content_pixels_and_rejects_nonwhite_exclusions(self):
        from io import BytesIO
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'question.png'
            image = Image.new('L', (100, 200), 255)
            image.paste(0, (10, 10, 90, 70))
            image.save(path)
            crop = {'rect': [0, 0, 100, 80], 'imageSha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            result = Image.open(BytesIO(crop_print_image(path, crop)))
            self.assertEqual(result.size, (100, 80))
            self.assertEqual(result.tobytes(), image.crop(crop['rect']).tobytes())
            with self.assertRaises(ValueError):
                crop_print_image(path, {**crop, 'rect': [0, 0, 100, 60]})
            image.putpixel((0, 190), 254)
            image.save(path)
            with self.assertRaises(ValueError):
                crop_print_image(path, crop)
            crop['imageSha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(ValueError):
                crop_print_image(path, crop)

    def test_reviewed_print_crops_are_blank_outside(self):
        questions = {q['id']: q for q in json.loads((ROOT / 'data/questions.json').read_text())}
        for qid, crop in load_image_crops().items():
            self.assertTrue(crop_print_image(ROOT / questions[qid]['image']['src'], crop))


class PrintPaginationTest(unittest.TestCase):
    def test_covers_keep_sections_on_separate_pages_and_numbering_continuous(self):
        plan = [{'id': str(i), 'category': category, 'sequence': i}
                for i, category in enumerate(['circuit'] * 5 + ['electronic'] * 4 + ['digital'] * 3, 1)]
        layout = paginate_print_plan(plan, section_covers=True)
        self.assertEqual([i + 1 for i, p in enumerate(layout) if p['kind'] == 'cover'], [1, 4, 6])
        self.assertEqual(len(layout), 7)
        self.assertEqual([r['page'] for r in plan], [2, 2, 2, 2, 3, 5, 5, 5, 5, 7, 7, 7])
        self.assertEqual([r['sequence'] for r in plan], list(range(1, 13)))
        self.assertEqual([r['slot'] for r in plan], [1, 2, 3, 4, 1, 1, 2, 3, 4, 1, 2, 3])

    def test_tall_question_occupies_both_rows_without_overlap(self):
        plan = [{'category': 'circuit', 'sequence': i, 'rowSpan': span}
                for i, span in enumerate([1, 2, 1, 2, 2], 1)]
        layout = paginate_print_plan(plan)
        self.assertEqual([len(p['questions']) for p in layout], [3, 2])
        self.assertEqual([(r['page'], r['slot']) for r in plan],
                         [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)])
        for page in layout:
            used = []
            for row in page['questions']:
                used.append(row['slot'])
                if row['rowSpan'] == 2:
                    used.append(row['slot'] + 2)
            self.assertEqual(len(used), len(set(used)))

    def test_default_layout_keeps_four_questions_per_page(self):
        plan = [{'category': str(i), 'sequence': i} for i in range(5)]
        layout = paginate_print_plan(plan)
        self.assertEqual([len(p['questions']) for p in layout], [4, 1])
        self.assertEqual([r['page'] for r in plan], [1, 1, 1, 1, 2])


@unittest.skipUnless(importlib.util.find_spec('fitz') and importlib.util.find_spec('fontTools'),
                     'PDF 검증에는 pymupdf/fonttools 필요')
class PrintFontTest(unittest.TestCase):
    def test_subset_font_renders_korean_not_only_extractable_text(self):
        import fitz
        font_path = Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc')
        if not font_path.exists():
            self.skipTest('Noto Serif CJK가 설치되지 않은 환경')
        value = '회로이론 정답 ①②③④'
        font_bytes = subset_font(font_path, value)
        self.assertLess(len(font_bytes), 500_000)
        doc = fitz.open()
        page = doc.new_page(width=300, height=100)
        page.insert_font(fontname='kr', fontbuffer=font_bytes)
        page.insert_text((20, 45), value, fontsize=16, fontname='kr')
        for char in '회로이론정답':
            glyph_page = doc.new_page(width=80, height=80)
            glyph_page.insert_font(fontname='kr', fontbuffer=font_bytes)
            glyph_page.insert_text((10, 45), char, fontsize=32, fontname='kr')
            rendered = glyph_page.get_pixmap(colorspace=fitz.csGRAY)
            self.assertGreater(sum(v < 160 for v in rendered.samples), 30,
                               f'한글 {char} 글자가 실제로 렌더링되어야 합니다')
        page = doc[0]
        extracted = page.get_text().translate(str.maketrans('➀➁➂➃➄', '①②③④⑤'))
        self.assertIn(value, extracted)
        doc.close()


if __name__ == '__main__':
    unittest.main()
