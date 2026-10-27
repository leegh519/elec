#!/usr/bin/env python3
"""제본용 A4 2×2 PDF/문항계획 생성. 대표 소분류 또는 태그로 묶고 문항 ID 중복을 제외한다."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from itertools import groupby
from pathlib import Path

from study_taxonomy import build_print_plan, indexes

ROOT = Path(__file__).resolve().parents[1]


def load_image_crops():
    path = ROOT / 'data/print_image_crops.json'
    return json.loads(path.read_text()) if path.exists() else {}


def crop_print_image(image_path, crop):
    """검수된 순백 여백만 제외한다. 글자·도형 픽셀이 있으면 출력 중단."""
    from io import BytesIO
    from PIL import Image
    if hashlib.sha256(image_path.read_bytes()).hexdigest() != crop['imageSha256']:
        raise ValueError(f'출력 여백 검수 이후 이미지 변경: {image_path}')
    with Image.open(image_path) as original:
        left, top, right, bottom = crop['rect']
        if not (0 <= left < right <= original.width and 0 <= top < bottom <= original.height):
            raise ValueError(f'출력 여백 좌표 오류: {image_path}')
        outside = original.convert('L')
        outside.paste(255, (left, top, right, bottom))
        if outside.getextrema() != (255, 255):
            raise ValueError(f'출력에서 제외할 영역에 내용이 있습니다: {image_path}')
        buffer = BytesIO()
        original.crop((left, top, right, bottom)).save(buffer, format='PNG')
        return buffer.getvalue()


def paginate_print_plan(plan, section_covers=False):
    """영역 표지 뒤에는 항상 새 문제 페이지를 시작하고 실제 PDF 쪽수를 기록한다."""
    layout = []
    sections = [list(rows) for _, rows in groupby(plan, key=lambda r: r['category'])] if section_covers else [plan]
    for rows in sections:
        if section_covers:
            layout.append({'kind': 'cover', 'category': rows[0]['category'], 'questionCount': len(rows), 'questions': []})
        occupied = set()
        group = []
        def flush():
            if group:
                layout.append({'kind': 'questions', 'category': group[0]['category'], 'questions': list(group)})
                group.clear()
                occupied.clear()
        for item in rows:
            span = item.get('rowSpan', 1)
            candidates = [slot for slot in range(1, 5) if slot not in occupied and
                          (span == 1 or (slot <= 2 and slot + 2 not in occupied))]
            if not candidates:
                flush()
                candidates = [1]
            slot = candidates[0]
            item['page'] = len(layout) + 1
            item['slot'] = slot
            occupied.add(slot)
            if span == 2:
                occupied.add(slot + 2)
            group.append(item)
        flush()
    return layout


def save_plan(path, plan, taxonomy, group_by, layout=None):
    metadata = {'taxonomyVersion': taxonomy['version'], 'groupBy': group_by,
                'questionCount': len(plan), 'uniqueQuestionCount': len({q['id'] for q in plan}),
                'pages': len(layout) if layout is not None else math.ceil(len(plan) / 4),
                'covers': [{'page': i + 1, 'category': p['category']} for i, p in enumerate(layout or []) if p['kind'] == 'cover'],
                'questions': plan}
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with path.with_suffix('.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(['새번호', '페이지', '칸', '문항ID', '대분류', '중분류', '소분류', '정렬묶음', '출처', '정답'])
        for row in plan:
            writer.writerow([row[k] for k in ['sequence', 'page', 'slot', 'id', 'categoryLabel', 'topicLabel',
                                              'subtopicLabel', 'groupLabel', 'source', 'answer']])


def subset_font(path, text):
    # Embedded Korean serif subset avoids embedding the full ~25 MB font in every PDF.
    from fontTools import subset
    from fontTools.ttLib import TTFont
    font = TTFont(str(path), fontNumber=1 if path.suffix.lower() == '.ttc' else -1)
    options = subset.Options()
    options.layout_features = ['*']
    sub = subset.Subsetter(options=options)
    sub.populate(text=text)
    sub.subset(font)
    from io import BytesIO
    buffer = BytesIO()
    if 'CFF ' in font:
        # CID-keyed CFF subsets can extract as text yet render blank in PDF readers.
        # Convert the small subset to ordinary TrueType outlines before embedding.
        from fontTools.fontBuilder import FontBuilder
        from fontTools.pens.ttGlyphPen import TTGlyphPen
        from fontTools.pens.cu2quPen import Cu2QuPen
        glyph_set = font.getGlyphSet()
        glyphs = {}
        for name in font.getGlyphOrder():
            pen = TTGlyphPen(glyph_set)
            glyph_set[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
            glyphs[name] = pen.glyph()
        builder = FontBuilder(font['head'].unitsPerEm, isTTF=True)
        builder.setupGlyphOrder(font.getGlyphOrder())
        builder.setupCharacterMap(font.getBestCmap())
        builder.setupGlyf(glyphs)
        builder.setupHorizontalMetrics(font['hmtx'].metrics)
        builder.setupHorizontalHeader(ascent=font['hhea'].ascent, descent=font['hhea'].descent)
        builder.setupOS2(sTypoAscender=font['OS/2'].sTypoAscender,
                         sTypoDescender=font['OS/2'].sTypoDescender,
                         usWinAscent=font['OS/2'].usWinAscent,
                         usWinDescent=font['OS/2'].usWinDescent)
        builder.setupNameTable({'familyName': 'Study Serif Subset', 'styleName': 'Regular',
                                'uniqueFontIdentifier': 'StudySerifSubset',
                                'fullName': 'Study Serif Subset', 'psName': 'StudySerifSubset'})
        builder.setupPost()
        builder.setupMaxp()
        builder.save(buffer)
    else:
        font.save(buffer)
    font.close()
    return buffer.getvalue()


def render_pdf(path, plan, questions, taxonomy, font_path, masks=None, *, show_classification=True, section_covers=False):
    import fitz
    cats, topics, _ = indexes(taxonomy)
    byid = {q['id']: q for q in questions}
    image_crops = load_image_crops()
    if masks is not None:
        missing = [p['id'] for p in plan if p['id'] not in masks]
        if missing:
            raise ValueError(f"번호 제거 영역 검수가 필요한 문항 {len(missing)}개: {', '.join(missing[:12])}. "
                             '검수된 --number-masks를 제공하거나 번호 제거 옵션 없이 생성하세요.')
    labels = '전자공학개론 기출문제 회로이론 문제 전자회로 문제 디지털회로 문제 정답 / · › 번 0123456789①②③④⑤'
    labels += ''.join(r['source'] + r['subtopicLabel'] + r['groupLabel'] + topics[r['topic']][2]['label']
                      + cats[r['category']][1]['label'] for r in plan)
    font_bytes = subset_font(font_path, labels)
    font = fitz.Font(fontbuffer=font_bytes)
    doc = fitz.open()
    width, height, margin, gap = 595.276, 841.89, 36, 24
    cell_width = (width - 2 * margin - gap) / 2
    cell_height = 350
    layout = paginate_print_plan(plan, section_covers)
    pages = len(layout)
    toc, seen = [], set()
    images = {}
    manifest = []
    for page_index, page_layout in enumerate(layout):
        page = doc.new_page(width=width, height=height)
        page.insert_font(fontname='kr', fontbuffer=font_bytes)

        def text(x, y, value, size=8, right=False, limit=None):
            if limit:
                while size > 4 and font.text_length(value, fontsize=size) > limit:
                    size -= .25
            if right:
                x -= font.text_length(value, fontsize=size)
            if x < margin - 1:
                raise ValueError(f'문구가 페이지 밖으로 나갑니다: {value}')
            page.insert_text((x, y), value, fontname='kr', fontsize=size, color=(.12, .12, .12))

        if page_layout['kind'] == 'cover':
            title = cats[page_layout['category']][1]['label'] + ' 문제'
            for y, value, size in [(320, '전자공학개론 기출문제', 12), (390, title, 32),
                                   (440, f"{page_layout['questionCount']}문제", 12)]:
                text((width - font.text_length(value, fontsize=size)) / 2, y, value, size)
            page.draw_line((width / 2 - 95, 410), (width / 2 + 95, 410), color=(.2, .2, .2), width=.6)
            text(width - margin, height - 25, f'{page_index + 1} / {pages}', 8, True)
            toc.append([1, title, page_index + 1])
            seen.add(page_layout['category'])
            continue

        text(margin, 35, '전자공학개론 기출문제', 10)
        text(width - margin, 35, f'{len(plan)}문제', 9, True)
        page.draw_line((margin, 46), (width - margin, 46), color=(.2, .2, .2), width=.6)
        group = page_layout["questions"]
        for item in group:
            slot = item['slot'] - 1
            q = byid[item['id']]
            x = margin + slot % 2 * (cell_width + gap)
            y = 72 + slot // 2 * cell_height
            label = topics[item['topic']][2]['label'] + ' › ' + item['subtopicLabel']
            text(x, y + 10, f"{item['sequence']:03d}", 8)
            if show_classification:
                text(x + 23, y + 10, label, 6.5, limit=cell_width - 23)
            text(x + cell_width, y + 21, item['source'], 6, True)
            iw, ih = q['image']['width'], q['image']['height']
            crop = image_crops.get(q['id'])
            crop_left, crop_top = 0, 0
            if crop:
                crop_left, crop_top, crop_right, crop_bottom = crop['rect']
                iw, ih = crop_right - crop_left, crop_bottom - crop_top
            available_height = cell_height * item.get('rowSpan', 1) - 70
            scale = min(cell_width / iw, available_height / ih)
            rect = fitz.Rect(x, y + 32, x + iw * scale, y + 32 + ih * scale)
            if rect.y1 >= height - 65:
                raise ValueError(f"이미지 범위 초과: {q['id']}")
            image_path = ROOT / q['image']['src']
            image_xref = images.get(q['id'])
            cropped_bytes = crop_print_image(image_path, crop) if crop and not image_xref else None
            images[q['id']] = page.insert_image(rect, xref=image_xref or 0,
                                                filename=None if image_xref or crop else str(image_path),
                                                stream=cropped_bytes)
            mask = masks.get(q['id']) if masks is not None else None
            if mask:
                a, b, c, d = mask
                if not (crop_left <= a <= c <= crop_left + iw and crop_top <= b <= d <= crop_top + ih):
                    raise ValueError(f"번호 가림 범위 오류: {q['id']}")
                a, b, c, d = a - crop_left, b - crop_top, c - crop_left, d - crop_top
                page.draw_rect(fitz.Rect(x + a * scale, y + 32 + b * scale,
                                         x + c * scale, y + 32 + d * scale),
                               color=None, fill=(1, 1, 1), overlay=True)
            manifest.append({**item, 'pdfRect': list(rect), 'numberMaskPixels': mask,
                             **({'sourceCropPixels': crop['rect']} if crop else {}),
                             'imageSha256': hashlib.sha256(image_path.read_bytes()).hexdigest()})
            key = (item['category'], item['topic'], item['group'])
            if key not in seen:
                if item['category'] not in seen:
                    toc.append([1, cats[item['category']][1]['label'], page_index + 1])
                    seen.add(item['category'])
                if (item['category'], item['topic']) not in seen:
                    toc.append([2, topics[item['topic']][2]['label'], page_index + 1])
                    seen.add((item['category'], item['topic']))
                toc.append([3, item['groupLabel'], page_index + 1])
                seen.add(key)
        answers = '정답   ' + '   ·   '.join(f"{r['sequence']:03d}번 {['', '①', '②', '③', '④', '⑤'][r['answer']]}" for r in group)
        text(width - margin, height - 47, answers, 6, True)
        text(width - margin, height - 25, f'{page_index + 1} / {pages}', 8, True)
    doc.set_toc(toc)
    doc.set_metadata({'title': f'전자공학개론 기출 {len(plan)}문제',
                      'subject': 'A4 2×2 · 대표 소분류/태그별 · 문항 ID 중복 제외'})
    doc.save(path, garbage=4, deflate=True, use_objstms=1, compression_effort=100)
    doc.close()
    check = fitz.open(path)
    assert len(check) == pages
    assert sum(len(p.get_image_info()) for p in check) == len(plan)
    for i, page in enumerate(check):
        text_content = page.get_text().translate(str.maketrans('➀➁➂➃➄', '①②③④⑤'))
        rows = layout[i]['questions']
        if layout[i]['kind'] == 'cover':
            assert len(page.get_image_info()) == 0
            assert cats[layout[i]['category']][1]['label'] + ' 문제' in text_content
            continue
        if not show_classification:
            assert all(topics[r['topic']][2]['label'] not in text_content for r in rows)
        assert len(page.get_image_info()) == len(rows)
        assert text_content.count('정답') == 1
        for row in rows:
            assert row['source'] in text_content
            assert f"{row['sequence']:03d}번 {['', '①', '②', '③', '④', '⑤'][row['answer']]}" in text_content
    check.close()
    path.with_suffix('.render.json').write_text(json.dumps({'verified': True, 'pages': pages,
                    'numberRemoval': masks is not None, 'classificationShown': show_classification,
                    'covers': [{'page': i + 1, 'category': p['category']} for i, p in enumerate(layout) if p['kind'] == 'cover'],
                    'questions': manifest}, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['category', 'topic', 'subtopic', 'tag']:
        parser.add_argument('--' + name, action='append', help='ID 지정. 여러 번 사용하면 해당 조건 안에서 OR')
    parser.add_argument('--group-by', choices=['subtopic', 'tag'], default='subtopic')
    parser.add_argument('--tag-priority', action='append', help='태그 정렬시 대표 태그보다 우선할 태그. 지정 순서 적용')
    parser.add_argument('--output', type=Path, required=True, help='PDF 경로. 계획 JSON/CSV도 같은 이름으로 생성')
    parser.add_argument('--hide-classification', action='store_true', help='문제 위에 새 번호만 표시하고 중·소분류명을 숨김')
    parser.add_argument('--section-covers', action='store_true', help='각 대분류 앞에 영역 표지를 추가하고 새 페이지에서 시작')
    parser.add_argument('--adaptive-sizing', action='store_true', help='세로로 긴 문제는 세로 두 칸 사용')
    parser.add_argument('--plan-only', action='store_true', help='PDF 없이 전체 문항 순서·쪽 배치만 생성')
    parser.add_argument('--remove-original-numbers', action='store_true', help='검수된 좌표로 원 번호만 가림. 미검수 문항은 오류로 중단')
    parser.add_argument('--number-masks', type=Path, default=ROOT / 'data/print_number_masks.json')
    parser.add_argument('--font', type=Path, default=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'))
    args = parser.parse_args()
    taxonomy = json.loads((ROOT / 'data/taxonomy.json').read_text())
    questions = json.loads((ROOT / 'data/questions.json').read_text())
    try:
        plan = build_print_plan(questions, taxonomy, categories=args.category, topics=args.topic,
                               subtopics=args.subtopic, tags=args.tag, group_by=args.group_by,
                               tag_priority=args.tag_priority)
        if args.adaptive_sizing:
            byid = {q['id']: q for q in questions}
            image_crops = load_image_crops()
            overrides_path = ROOT / 'data/print_layout_overrides.json'
            overrides = json.loads(overrides_path.read_text()) if overrides_path.exists() else {}
            for item in plan:
                image = byid[item['id']]['image']
                crop = image_crops.get(item['id'])
                iw, ih = image['width'], image['height']
                if crop:
                    left, top, right, bottom = crop['rect']
                    iw, ih = right - left, bottom - top
                minimum_span = overrides.get(item['id'], {}).get('minimumRowSpan', 1)
                if minimum_span not in (1, 2):
                    raise ValueError(f"잘못된 최소 배치 크기: {item['id']}")
                item['rowSpan'] = max(minimum_span, 2 if ih / iw > 1.6 else 1)
        if not plan:
            raise ValueError('조건에 맞는 문항이 없습니다')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if not args.plan_only:
            masks = json.loads(args.number_masks.read_text()) if args.remove_original_numbers else None
            render_pdf(args.output, plan, questions, taxonomy, args.font, masks,
                       show_classification=not args.hide_classification, section_covers=args.section_covers)
        layout = paginate_print_plan(plan, args.section_covers)
        save_plan(args.output.with_suffix('.json'), plan, taxonomy, args.group_by, layout)
    except (ValueError, FileNotFoundError) as error:
        parser.error(str(error))
    print(f"questions={len(plan)} unique={len({q['id'] for q in plan})} pages={len(layout)} group={args.group_by}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
