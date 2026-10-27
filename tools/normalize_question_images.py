#!/usr/bin/env python3
"""검수된 원 번호를 PNG에서 지우고 실제 순백 바깥 여백만 정리한다."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image
from clean_page_artifacts import clean_image
from trim_image_margins import find_trim_rectangle, trim_preserving_content, sync_browser_questions

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'data/normalized_question_images.json'
    questions = json.loads((ROOT / 'data/questions.json').read_text())
    masks = json.loads((ROOT / 'data/print_number_masks.json').read_text())
    previous = json.loads(path.read_text()) if path.exists() else None
    if previous:
        for row in previous['images']:
            actual = hashlib.sha256((ROOT / row['src']).read_bytes()).hexdigest()
            if actual != row['afterSha256']:
                raise ValueError(f"정리 이후 변경된 이미지: {row['id']}")
        print('already normalized=1100')
        return
    printed = json.loads((ROOT / 'print/electronics_1100_print.render.json').read_text())['questions']
    byid = {r['id']: r for r in printed}
    pending = []
    for q in questions:
        source = ROOT / q['image']['src']
        with Image.open(source) as image:
            if list(image.size) != [q['image']['width'], q['image']['height']]:
                raise ValueError(f"이미지 크기 불일치: {q['id']}")
            mask = masks[q['id']]
            cleaned = clean_image(image, [mask] if mask else [])
            crop = find_trim_rectangle(cleaned, padding=8, min_margin=1)
            result = trim_preserving_content(cleaned, crop)
            # All retained content equals the previously printed image with its reviewed number mask.
            assert result.tobytes() == cleaned.crop(crop).tobytes()
            number_changed = image.tobytes() != cleaned.tobytes()
            pending.append((q, {'id': q['id'], 'sequence': byid[q['id']]['sequence'],
                'source': byid[q['id']]['source'], 'src': q['image']['src'],
                'beforeSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'originalSize': list(image.size), 'size': list(result.size),
                'numberMaskBefore': mask, 'numberPixelsChanged': number_changed,
                'cropPixels': crop, 'rightMarginRemoved': image.width - crop[2],
                'marginChanged': crop != [0, 0, image.width, image.height]}))
    print('scanned=', len(pending), 'numbers removed=', sum(r['numberPixelsChanged'] for _, r in pending),
          'trimmed=', sum(r['marginChanged'] for _, r in pending))
    if not args.apply:
        return
    rows = []
    for q, row in pending:
        source = ROOT / q['image']['src']
        if hashlib.sha256(source.read_bytes()).hexdigest() != row['beforeSha256']:
            raise ValueError(f"검사 이후 이미지 변경: {q['id']}")
        with Image.open(source) as original:
            cleaned = clean_image(original, [row['numberMaskBefore']] if row['numberMaskBefore'] else [])
            image = trim_preserving_content(cleaned, row['cropPixels'])
        if row['numberPixelsChanged'] or row['marginChanged']:
            image.save(source, format='PNG')
        row['afterSha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        q['image']['width'], q['image']['height'] = image.size
        masks[q['id']] = None
        rows.append(row)
    rows.sort(key=lambda r: r['sequence'])
    report = {'scannedImages': len(rows), 'numbersRemovedInPng': True, 'paddingPixels': 8,
              'onlyReviewedNumberPixelsAndPureWhiteMarginsChanged': True,
              'resampled': False, 'images': rows}
    for target, value in [(path, report), (ROOT / 'data/questions.json', questions),
                          (ROOT / 'data/print_number_masks.json', masks),
                          (ROOT / 'data/print_image_crops.json', {})]:
        target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    sync_browser_questions(questions)


if __name__ == '__main__':
    main()
