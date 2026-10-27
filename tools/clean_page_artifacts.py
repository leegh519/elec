#!/usr/bin/env python3
"""검수된 페이지 테두리·쪽번호 영역만 흰색 처리한다. 캔버스·다른 픽셀은 유지."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_image(image, rectangles):
    result = image.copy()
    for left, top, right, bottom in rectangles:
        if not (0 <= left < right <= image.width and 0 <= top < bottom <= image.height):
            raise ValueError(f'범위를 벗어난 정리 좌표: {[left, top, right, bottom]}')
        result.paste(255 if image.mode == 'L' else (255, 255, 255), (left, top, right, bottom))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='검수된 원본 PNG 경로에 반영')
    args = parser.parse_args()
    path = ROOT / 'data/page_artifact_masks.json'
    manifest = json.loads(path.read_text())
    trims_path = ROOT / 'data/image_margin_trims.json'
    trims = {r['id']: r for r in json.loads(trims_path.read_text())['images']} if trims_path.exists() else {}
    normalized_path = ROOT / 'data/normalized_question_images.json'
    normalized = {r['id']: r for r in json.loads(normalized_path.read_text())['images']} if normalized_path.exists() else {}
    changed = 0
    for row in manifest['images']:
        source = ROOT / row['src']
        current = sha256(source)
        trim = trims.get(row['id'], {})
        final_trim = trim.get('followup', trim)
        if current == row.get('afterSha256'):
            continue
        if current != row['beforeSha256'] and current == normalized.get(row['id'], {}).get('afterSha256'):
            continue
        if current != row['beforeSha256'] and current == final_trim.get('afterSha256'):
            continue
        if current != row['beforeSha256']:
            raise ValueError(f"검수 이후 이미지가 변경되었습니다: {row['id']}")
        with Image.open(source) as original:
            if list(original.size) != row['size'] or original.mode not in ('L', 'RGB'):
                raise ValueError(f"예상하지 못한 크기·색상 모드: {row['id']}")
            cleaned = clean_image(original, row['rectangles'])
            if args.apply:
                cleaned.save(source, format='PNG')
                row['afterSha256'] = sha256(source)
        changed += 1
    if args.apply:
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(f"{'updated' if args.apply else 'would update'}={changed} reviewed={len(manifest['images'])}")


if __name__ == '__main__':
    main()
