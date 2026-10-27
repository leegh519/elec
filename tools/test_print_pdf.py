"""텍스트 추출 성공만으로 놓칠 수 있는 PDF 명조체 렌더링 누락을 검증."""
import importlib.util
import unittest
from pathlib import Path

from build_print_pdf import subset_font


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
