#!/usr/bin/env python3
"""순백 여백만 제거하고 PNG 크기·번호 가림 좌표를 함께 갱신한다."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
PADDING = 12
MIN_MARGIN = 36


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_trim_rectangle(image, padding=PADDING, min_margin=MIN_MARGIN):
    # A single non-white pixel, including faint antialiasing, counts as content.
    box = ImageChops.invert(image.convert('L')).getbbox()
    if box is None:
        raise ValueError('빈 이미지입니다')
    width, height = image.size
    left, top, right, bottom = box
    left, top = max(0, left - padding), max(0, top - padding)
    right, bottom = min(width, right + padding), min(height, bottom + padding)
    return [left if left >= min_margin else 0,
            top if top >= min_margin else 0,
            right if width - right >= min_margin else width,
            bottom if height - bottom >= min_margin else height]


def trim_preserving_content(image, rectangle):
    left, top, right, bottom = rectangle
    if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
        raise ValueError(f'여백 정리 좌표 오류: {rectangle}')
    outside = image.convert('L')
    outside.paste(255, (left, top, right, bottom))
    if outside.getextrema() != (255, 255):
        raise ValueError('제외 영역에 내용이 있습니다')
    return image.crop(rectangle)


def translate_mask(mask, rectangle):
    if mask is None:
        return None
    left, top, right, bottom = rectangle
    a, b, c, d = mask
    a, b, c, d = max(a, left), max(b, top), min(c, right), min(d, bottom)
    if a >= c or b >= d:
        return None
    return [a - left, b - top, c - left, d - top]


def sync_browser_questions(questions):
    path = ROOT / 'data/data.js'
    if path.exists():
        payload = json.loads(path.read_text().strip().removeprefix('window.QUESTION_BANK = ')[:-1])
        payload['questions'] = questions
        path.write_text('window.QUESTION_BANK = ' + json.dumps(payload, ensure_ascii=False) + ';\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='원본 PNG·메타데이터·번호 좌표에 반영')
    args = parser.parse_args()
    questions_path = ROOT / 'data/questions.json'
    masks_path = ROOT / 'data/print_number_masks.json'
    report_path = ROOT / 'data/image_margin_trims.json'
    crops_path = ROOT / 'data/print_image_crops.json'
    questions = json.loads(questions_path.read_text())
    masks = json.loads(masks_path.read_text())
    crops = json.loads(crops_path.read_text()) if crops_path.exists() else {}
    old_report = json.loads(report_path.read_text()) if report_path.exists() else {'images': []}
    previous = {r['id']: r for r in old_report['images']}
    printed = json.loads((ROOT / 'print/electronics_1100_print.render.json').read_text())['questions']
    byid = {r['id']: r for r in printed}
    pending = []
    # Validate the complete batch before changing any file.
    for question in questions:
        source = ROOT / question['image']['src']
        with Image.open(source) as image:
            if image.size != (question['image']['width'], question['image']['height']):
                raise ValueError(f"크기 메타데이터 불일치: {question['id']}")
            rectangle = find_trim_rectangle(image)
            if rectangle == [0, 0, image.width, image.height]:
                continue
            if question['id'] in previous:
                raise ValueError(f"이미 정리한 이미지의 재검수 필요: {question['id']}")
            trimmed = trim_preserving_content(image, rectangle)
            if question['id'] in crops and sha256(source) != crops[question['id']]['imageSha256']:
                raise ValueError(f"PDF 여백 검수 이후 원본 변경: {question['id']}")
            pending.append((question, rectangle, image.size, trimmed.size, sha256(source)))
    print(f"{'update' if args.apply else 'would update'}={len(pending)} scanned={len(questions)}")
    if not args.apply:
        return
    if not pending:
        sync_browser_questions(questions)
        return
    rows = old_report['images']
    for question, rectangle, before_size, after_size, before_sha in pending:
        qid = question['id']
        source = ROOT / question['image']['src']
        old_mask = masks[qid]
        with Image.open(source) as image:
            trimmed = trim_preserving_content(image, rectangle)
            trimmed.save(source, format='PNG')
        masks[qid] = translate_mask(old_mask, rectangle)
        question['image']['width'], question['image']['height'] = after_size
        # The source PNG now has its own crop. Do not apply an old PDF-only crop twice.
        crops.pop(qid, None)
        rows.append({'id': qid, 'sequence': byid[qid]['sequence'], 'source': byid[qid]['source'],
                     'src': question['image']['src'], 'originalSize': list(before_size),
                     'cropPixels': rectangle, 'size': list(after_size),
                     'beforeSha256': before_sha, 'afterSha256': sha256(source),
                     'originalNumberMaskPixels': old_mask, 'numberMaskPixels': masks[qid]})
    rows.sort(key=lambda r: r['sequence'])
    report = {'scannedImages': len(questions), 'trimmedImages': len(rows),
              'paddingPixels': PADDING, 'minimumRemovedMarginPixels': MIN_MARGIN,
              'excludedPixels': '255 (pure white) only', 'resampled': False, 'images': rows}
    for path, value in [(questions_path, questions), (masks_path, masks),
                        (report_path, report), (crops_path, crops)]:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    sync_browser_questions(questions)


if __name__ == '__main__':
    main()
