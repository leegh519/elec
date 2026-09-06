#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps


PROJECT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT.parent / "공무원 기출" / "전자공학개론"
DATA_DIR = PROJECT / "data"
ASSET_DIR = PROJECT / "assets" / "questions"
REVIEW_DIR = PROJECT / "review"
WORK_DIR = PROJECT / "_build"
VISION_BIN = PROJECT / "tools" / "vision_ocr"
RUNTIME = Path("/Users/gh/.cache/codex-runtimes/codex-primary-runtime/dependencies")
PDFTOPPM = RUNTIME / "bin" / "override" / "pdftoppm"
SWIFTC = shutil.which("swiftc") or "/usr/bin/swiftc"
RENDER_DPI = 240

AGENCY_SLUG = {"국가직": "national", "지방직": "local", "군무원": "military"}
QUESTION_RE = re.compile(r"^\s*(?:(?:문\s*[.ㆍ·:]?|#)\s*)?(\d{1,2})\s*[.)．]\s*")
EXTRA_QUESTION_RE = re.compile(r"^\s*(?:(?:문\s*[.ㆍ·:]?|#)\s*)?(2[1-5])\s*[.)．]\s+")
INLINE_QUESTION_RE = re.compile(r"(?<!\d)(\d{1,2})\s*[.)．]\s+")


@dataclass
class Anchor:
    number: int
    page: int
    column: int
    x: float
    y: float
    width: float
    height: float
    confidence: float
    text: str


def run(command: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=True, text=True, **kwargs)


def ensure_vision_binary() -> None:
    source = PROJECT / "tools" / "vision_ocr.swift"
    if VISION_BIN.exists() and VISION_BIN.stat().st_mtime >= source.stat().st_mtime:
        return
    env = dict(**__import__("os").environ)
    env["CLANG_MODULE_CACHE_PATH"] = "/private/tmp/codex-clang-cache"
    env["SWIFT_MODULECACHE_PATH"] = "/private/tmp/codex-swift-cache"
    run([SWIFTC, str(source), "-o", str(VISION_BIN)], env=env)


def exam_from_path(path: Path) -> dict:
    match = re.fullmatch(r"(\d{4})-(국가직|지방직|군무원)\.pdf", path.name)
    if not match:
        raise ValueError(f"unexpected PDF filename: {path.name}")
    year = int(match.group(1))
    agency = match.group(2)
    slug = AGENCY_SLUG[agency]
    return {
        "id": f"{slug}-{year}",
        "year": year,
        "agency": agency,
        "slug": slug,
        "title": f"{year}년 {agency} 전자공학개론",
        "sourcePdf": f"../공무원 기출/전자공학개론/{path.name}",
        "sourcePath": path,
        "expectedQuestions": 20,
    }


def render_exam(exam: dict, force: bool = False) -> list[Path]:
    page_dir = WORK_DIR / "pages" / exam["id"]
    page_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted(page_dir.glob("page-*.png"))
    if pages and not force:
        return pages
    for old in pages:
        old.unlink()
    prefix = page_dir / "page"
    run(
        [str(PDFTOPPM), "-png", "-r", str(RENDER_DPI), str(exam["sourcePath"]), str(prefix)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rendered = sorted(page_dir.glob("page-*.png"))
    if not rendered:
        raise RuntimeError(f"no pages rendered for {exam['id']}")
    return rendered


def ocr_page(page_path: Path, exam_id: str, page_number: int, force: bool = False) -> dict:
    ocr_dir = WORK_DIR / "ocr" / exam_id
    ocr_dir.mkdir(parents=True, exist_ok=True)
    output = ocr_dir / f"page-{page_number:02d}.json"
    if output.exists() and not force:
        return json.loads(output.read_text(encoding="utf-8"))
    completed = run([str(VISION_BIN), str(page_path)], capture_output=True)
    data = json.loads(completed.stdout)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def find_anchors(ocr_pages: list[dict], exam_id: str) -> tuple[dict[int, Anchor], list[dict]]:
    candidates: dict[int, list[Anchor]] = {number: [] for number in range(1, 21)}
    for page_index, data in enumerate(ocr_pages, start=1):
        for line in data["lines"]:
            match = QUESTION_RE.match(line["text"])
            matches: list[tuple[re.Match, float]] = []
            if match:
                matches.append((match, line["x"]))

            # Vision sometimes joins the left and right question headers into one
            # wide OCR observation. Recover the right-hand number by estimating
            # its horizontal position from the character offset.
            if line["width"] > 0.72:
                text_length = max(1, len(line["text"]))
                for inline_match in INLINE_QUESTION_RE.finditer(line["text"]):
                    projected_x = line["x"] + line["width"] * (inline_match.start() / text_length)
                    if projected_x >= 0.40 and inline_match.start() > 0 and not any(existing.group(1) == inline_match.group(1) for existing, _ in matches):
                        matches.append((inline_match, max(0.50, projected_x)))

            for number_match, detected_x in matches:
                number = int(number_match.group(1))
                if not 1 <= number <= 20:
                    continue
                # Printed headers close to the gutter can start just left of 0.5.
                column = 0 if detected_x < 0.47 else 1
                relative_x = detected_x - (0.5 * column)
                if relative_x > 0.10:
                    continue
                candidates[number].append(Anchor(
                    number=number,
                    page=page_index,
                    column=column,
                    x=detected_x,
                    y=line["y"],
                    width=line["width"],
                    height=line["height"],
                    confidence=line["confidence"],
                    text=line["text"],
                ))

    override_file = DATA_DIR / "anchor_overrides.json"
    overrides = json.loads(override_file.read_text(encoding="utf-8")) if override_file.exists() else {}
    applied_overrides: set[int] = set()
    for raw_number, override in overrides.get(exam_id, {}).items():
        number = int(raw_number)
        candidates[number] = [Anchor(
            number=number,
            page=int(override["page"]),
            column=int(override["column"]),
            x=0.02 if int(override["column"]) == 0 else 0.50,
            y=float(override["y"]),
            width=0.46,
            height=0.02,
            confidence=1.0,
            text=f"manual override: {override.get('reason', '')}",
        )]
        applied_overrides.add(number)

    selected: dict[int, Anchor] = {}
    issues: list[dict] = []
    previous_position = (-1, -1, -1.0)
    for number in range(1, 21):
        options = sorted(
            candidates[number],
            key=lambda a: (a.page, a.column, a.y, -a.confidence),
        )
        valid = [a for a in options if (a.page, a.column, a.y) > previous_position]
        chosen = valid[0] if valid else (options[0] if options else None)
        if chosen is None:
            issues.append({"question": number, "type": "anchor-missing", "detail": "문제번호를 찾지 못함"})
            continue
        selected[number] = chosen
        previous_position = (chosen.page, chosen.column, chosen.y)
        if number in applied_overrides:
            issues.append({
                "question": number,
                "type": "anchor-manual-override",
                "detail": chosen.text,
            })
        elif len(options) > 1:
            issues.append({
                "question": number,
                "type": "anchor-duplicate",
                "detail": f"후보 {len(options)}개 중 첫 순차 후보 선택",
            })
    return selected, issues


def trim_bottom(image: Image.Image, max_bottom: int | None = None) -> Image.Image:
    gray = np.asarray(image.convert("L"))
    if max_bottom is not None:
        gray = gray[:max_bottom, :]
    ink = gray < 244
    row_counts = ink.sum(axis=1)
    meaningful = np.flatnonzero(row_counts > max(3, image.width // 500))
    if meaningful.size == 0:
        return image
    last = int(meaningful[-1])
    # A separated footer/page label should not determine the crop bottom.
    gaps = np.diff(meaningful)
    large_gap_indexes = np.flatnonzero(gaps > max(80, image.height // 15))
    for gap_index in reversed(large_gap_indexes.tolist()):
        before = int(meaningful[gap_index])
        after = int(meaningful[gap_index + 1])
        if after > image.height * 0.82 and before > image.height * 0.25:
            last = before
            break
    bottom = min(image.height, last + max(42, image.height // 55))
    return image.crop((0, 0, image.width, bottom))


def crop_questions(exam: dict, pages: list[Path], ocr_pages: list[dict], anchors: dict[int, Anchor]) -> tuple[list[dict], list[dict]]:
    output_dir = ASSET_DIR / exam["slug"] / str(exam["year"])
    output_dir.mkdir(parents=True, exist_ok=True)
    questions: list[dict] = []
    issues: list[dict] = []
    page_images: dict[int, Image.Image] = {}
    crop_override_file = DATA_DIR / "crop_overrides.json"
    crop_overrides = json.loads(crop_override_file.read_text(encoding="utf-8")) if crop_override_file.exists() else {}
    classification_override_file = DATA_DIR / "classification_overrides.json"
    classification_overrides = json.loads(classification_override_file.read_text(encoding="utf-8")) if classification_override_file.exists() else {}

    for number in range(1, 21):
        anchor = anchors.get(number)
        if anchor is None:
            continue
        page_image = page_images.setdefault(anchor.page, Image.open(pages[anchor.page - 1]).convert("RGB"))
        width, height = page_image.size
        gutter = width // 2
        x0 = 16 if anchor.column == 0 else gutter + 16
        x1 = gutter - 16 if anchor.column == 0 else width - 16
        top = max(0, int(anchor.y * height) - max(12, height // 250))

        following = [
            other for other in anchors.values()
            if other.page == anchor.page and other.column == anchor.column and other.y > anchor.y + 0.01
        ]
        # Some military PDFs contain 25 questions while this bank intentionally
        # imports 1–20. Treat a detected Q21+ header as the bottom boundary of Q20.
        for line in ocr_pages[anchor.page - 1]["lines"]:
            extra_match = EXTRA_QUESTION_RE.match(line["text"])
            detected_column = 0 if line["x"] < 0.47 else 1
            relative_x = line["x"] - (0.5 * detected_column)
            if (not extra_match or relative_x > 0.10 or detected_column != anchor.column
                    or line["y"] <= anchor.y + 0.01):
                continue
            following.append(Anchor(
                number=int(extra_match.group(1)), page=anchor.page, column=detected_column,
                x=line["x"], y=line["y"], width=line["width"], height=line["height"],
                confidence=line["confidence"], text=line["text"],
            ))
        if following:
            next_anchor = min(following, key=lambda item: item.y)
            bottom = max(top + 120, int(next_anchor.y * height) - max(10, height // 280))
        else:
            # Keep the full page here. trim_bottom() removes a separated footer,
            # while the generous limit protects answer choices near the page edge.
            bottom = height - max(12, height // 220)

        override = crop_overrides.get(exam["id"], {}).get(str(number), {})
        if override:
            print(f"  crop override Q{number}: {override.get('reason', 'manual crop adjustment')}", flush=True)
        if "bottom" in override:
            bottom = int(float(override["bottom"]) * height)
        preliminary = page_image.crop((x0, top, x1, bottom))
        cropped = preliminary if override.get("disableTrim") else trim_bottom(preliminary)
        primary_crop_height = cropped.height
        continuation_crops = []
        continuation_texts = []
        for continuation in override.get("continuations", []):
            continuation_page = int(continuation["page"])
            continuation_column = int(continuation["column"])
            continuation_image = page_images.setdefault(
                continuation_page,
                Image.open(pages[continuation_page - 1]).convert("RGB"),
            )
            continuation_width, continuation_height = continuation_image.size
            continuation_gutter = continuation_width // 2
            continuation_x0 = 16 if continuation_column == 0 else continuation_gutter + 16
            continuation_x1 = continuation_gutter - 16 if continuation_column == 0 else continuation_width - 16
            continuation_top = int(float(continuation["top"]) * continuation_height)
            continuation_bottom = int(float(continuation["bottom"]) * continuation_height)
            region = continuation_image.crop((
                continuation_x0, continuation_top, continuation_x1, continuation_bottom,
            ))
            continuation_crops.append({
                "image": region,
                "source": [continuation_x0, continuation_top, continuation_x1, continuation_bottom],
                "page": continuation_page,
                "column": "left" if continuation_column == 0 else "right",
            })
            for line in ocr_pages[continuation_page - 1]["lines"]:
                line_column = 0 if line["x"] < 0.5 else 1
                line_top = int(line["y"] * continuation_height)
                if line_column == continuation_column and continuation_top <= line_top < continuation_bottom:
                    continuation_texts.append(line["text"])

        if continuation_crops:
            separator = 24
            combined_width = max([cropped.width] + [item["image"].width for item in continuation_crops])
            combined_height = cropped.height + sum(item["image"].height + separator for item in continuation_crops)
            combined = Image.new("RGB", (combined_width, combined_height), "white")
            combined.paste(cropped, (0, 0))
            paste_y = cropped.height + separator
            for item in continuation_crops:
                combined.paste(item["image"], (0, paste_y))
                paste_y += item["image"].height + separator
            cropped = combined
        target = output_dir / f"q{number:02d}.png"
        cropped = ImageOps.grayscale(cropped)
        cropped.save(target, format="PNG", optimize=True, compress_level=9)

        crop_height = cropped.height
        review_state = "approved"
        if not override.get("reviewApproved") and (crop_height < height * 0.08 or crop_height > height * 0.75):
            review_state = "needs-review"
            issues.append({
                "question": number,
                "type": "crop-size-suspicious",
                "detail": f"crop={cropped.width}x{cropped.height}, page={width}x{height}",
            })

        line_texts = []
        for line in ocr_pages[anchor.page - 1]["lines"]:
            line_column = 0 if line["x"] < 0.5 else 1
            line_top = int(line["y"] * height)
            if line_column == anchor.column and top - 8 <= line_top < bottom:
                line_texts.append(line["text"])
        ocr_text = " ".join(line_texts + continuation_texts)
        question_id = f"{exam['id']}-{number:02d}"
        classification = classification_overrides.get(question_id, classify_question(ocr_text))
        relative_path = target.relative_to(PROJECT).as_posix()
        questions.append({
            "id": question_id,
            "examId": exam["id"],
            "year": exam["year"],
            "agency": exam["agency"],
            "number": number,
            "image": {
                "src": relative_path,
                "mimeType": "image/png",
                "width": cropped.width,
                "height": cropped.height,
            },
            "classification": classification,
            "answer": {"choice": None, "status": "unresolved", "sources": []},
            "source": {
                "pdf": exam["sourcePdf"],
                "page": anchor.page,
                "column": "left" if anchor.column == 0 else "right",
                "crop": [x0, top, x1, top + primary_crop_height],
                "continuations": [
                    {key: value for key, value in item.items() if key != "image"}
                    for item in continuation_crops
                ],
            },
            "ocrText": ocr_text,
            "review": {
                "crop": review_state,
                "classification": classification["status"],
                "answer": "needs-review",
            },
        })
    return questions, issues


def contains_any(text: str, words: list[str]) -> bool:
    return any(word.lower() in text for word in words)


def classify_question(raw_text: str) -> dict:
    text = re.sub(r"\s+", " ", raw_text).lower()
    rules = [
        ("circuit-theory", "network-theorems", "테브난 정리", ["테브난", "thevenin"]),
        ("circuit-theory", "network-theorems", "노턴 정리", ["노턴", "노튼", "norton"]),
        ("circuit-theory", "network-theorems", "중첩 정리", ["중첩 정리", "중첩의 정리"]),
        ("circuit-theory", "network-theorems", "최대전력 전달", ["최대전력", "최대 전력 전달"]),
        ("circuit-theory", "network-theorems", "밀만·상반 정리", ["밀만", "상반 정리"]),
        ("digital-engineering", "number-systems", "수 체계·코드", ["진법", "2진", "8진", "16진", "보수", "gray", "그레이", "ascii", "코드"]),
        ("digital-engineering", "boolean", "불대수·최소화", ["부울", "boolean", "논리식", "카르노", "demorgan", "드모르간"]),
        ("digital-engineering", "combinational", "조합논리회로", ["멀티플렉서", "multiplexer", "디멀티플렉서", "인코더", "decoder", "디코더", "가산기", "감산기"]),
        ("digital-engineering", "sequential", "순서논리회로", ["플립플롭", "flip-flop", "래치", "latch", "여기표", "상태표", "racing"]),
        ("digital-engineering", "registers-counters", "레지스터·카운터", ["레지스터", "register", "카운터", "counter", "분주"]),
        ("digital-engineering", "memory-pld", "메모리·PLD", ["memory", "메모리", "rom", "ram", "sram", "dram", "hbm", "pld", "fpga"]),
        ("digital-engineering", "processor", "마이크로프로세서", ["마이크로프로세서", "microprocessor", "cpu", "주소버스", "데이터버스"]),
        ("digital-engineering", "mcu-interface", "마이크로컨트롤러·인터페이스", ["마이크로컨트롤러", "arduino", "아두이노", "rs-232", "uart", "spi", "i2c", "직렬", "병렬 전송"]),
        ("digital-engineering", "converters", "ADC·DAC", ["a/d", "d/a", "adc", "dac", "양자화", "분해능"]),
        ("digital-engineering", "logic-families", "논리게이트·논리군", ["논리게이트", "논리 회로", "ttl", "cmos", "fan-out", "팬아웃", "nand", "nor", "게이트"]),
        ("electronic-circuits", "op-amp", "차동·연산증폭기", ["연산증폭기", "op amp", "op-amp", "차동증폭", "cmrr", "전류미러", "반전증폭", "비반전", "적분기", "미분기"]),
        ("electronic-circuits", "oscillators", "발진회로", ["발진기", "발진 회로", "발진조건", "콜피츠", "하틀리", "wien", "수정발진"]),
        ("electronic-circuits", "pulse-circuits", "펄스·파형회로", ["555", "멀티바이브레이터", "슈미트", "구형파 발생", "펄스 발생"]),
        ("electronic-circuits", "feedback", "부귀환 증폭기", ["부귀환", "음귀환", "feedback", "궤환 증폭"]),
        ("electronic-circuits", "power-amplifiers", "전력증폭기", ["전력증폭", "a급", "b급", "ab급", "c급", "푸시풀", "push-pull"]),
        ("electronic-circuits", "diode-applications", "다이오드 응용", ["정류회로", "정류 회로", "클리퍼", "클램퍼", "평활회로", "배전압", "리플률", "전압변동률"]),
        ("electronic-circuits", "fet-amplifiers", "FET 증폭기", ["fet 증폭", "mosfet 증폭", "공통 소스", "common source", "소스 팔로어"]),
        ("electronic-circuits", "bjt-bias", "BJT 바이어스", ["바이어스 회로", "동작점", "직류부하선", "고정 바이어스", "전압분배 바이어스"]),
        ("electronic-circuits", "bjt-amplifiers", "BJT 증폭기", ["트랜지스터 증폭", "소신호 증폭", "공통 이미터", "common-emitter", "h파라미터", "h 파라미터"]),
        ("electronic-circuits", "frequency-response", "주파수 특성", ["차단주파수", "주파수 특성", "밀러", "잡음지수", "왜율", "왜곡률"]),
        ("electronic-circuits", "semiconductor-basics", "원자·에너지대", ["에너지대", "에너지 밴드", "energy band", "페르미", "가전자대", "전도대", "밴드갭"]),
        ("electronic-circuits", "materials", "반도체 물성", ["진성반도체", "불순물 반도체", "n형", "p형", "캐리어", "정공", "이동도", "전도도"]),
        ("electronic-circuits", "semiconductor-basics", "반도체 현상", ["광전효과", "열전효과", "홀효과", "hall effect", "재결합"]),
        ("electronic-circuits", "diode-basics", "PN 접합", ["pn 접합", "공핍층", "확산전위", "순방향 바이어스", "역방향 바이어스"]),
        ("electronic-circuits", "special-devices", "특수·전력반도체", ["scr", "triac", "diac", "igbt", "thyristor", "사이리스터", "ujt"]),
        ("electronic-circuits", "fet-device", "FET·MOSFET 소자이론", ["mosfet", "jfet", "전계효과", "문턱전압", "pinch-off", "핀치오프", "공핍형", "증가형"]),
        ("electronic-circuits", "bjt-device", "BJT 소자이론", ["bjt", "베이스 전류", "컬렉터 전류", "이미터 전류", "활성영역", "포화영역", "차단영역"]),
        ("electronic-circuits", "diode-devices", "다이오드 소자", ["제너 다이오드", "터널 다이오드", "버랙터", "쇼트키", "led", "포토다이오드", "다이오드의 특성"]),
        ("electronic-circuits", "semiconductor-basics", "집적회로·공정", ["웨이퍼", "도핑", "이온주입", "산화막", "반도체 공정", "집적도", "패키징"]),
        ("circuit-theory", "network-theorems", "회로망 정리", ["테브난", "thevenin", "노턴", "norton", "중첩 정리", "최대전력", "밀만"]),
        ("circuit-theory", "two-port", "4단자망", ["4단자", "2단자쌍", "abcd", "전송 파라미터", "z파라미터", "y파라미터"]),
        ("circuit-theory", "transient", "과도현상", ["과도현상", "시정수", "초기값", "최종값", "스위치를 닫", "스위치를 열"]),
        ("circuit-theory", "resonance", "공진회로", ["공진주파수", "직렬 공진", "병렬 공진", "선택도", "q값", "대역폭"]),
        ("circuit-theory", "sinusoidal", "정현파·페이저", ["정현파", "페이저", "역률", "유효전력", "무효전력", "복소전력"]),
        ("circuit-theory", "non-sinusoidal", "비정현파", ["실효값", "평균값", "푸리에", "고조파", "비정현파"]),
        ("circuit-theory", "laplace", "라플라스 변환", ["라플라스", "laplace"]),
        ("circuit-theory", "transfer-function", "전달함수·주파수응답", ["전달함수", "극점", "영점", "보드선도", "bode"]),
        ("circuit-theory", "three-phase", "3상회로", ["3상", "삼상", "y결선", "델타결선"]),
        ("circuit-theory", "coupled", "유도결합회로", ["상호인덕턴스", "결합계수", "이상변압기", "변압기"]),
        ("circuit-theory", "network-analysis", "회로망 해석", ["마디전압", "망로전류", "전원변환", "브리지 회로", "kcl", "kvl"]),
        ("circuit-theory", "basic-laws", "회로의 기초 법칙", ["옴의 법칙", "키르히호프", "전압과 전류", "소비전력", "평균전력"]),
    ]

    matches: list[tuple[int, tuple]] = []
    for rule in rules:
        hits = sum(1 for keyword in rule[3] if keyword in text)
        if hits:
            matches.append((hits, rule))
    matches.sort(key=lambda item: item[0], reverse=True)
    if matches:
        hits, best = matches[0]
        status = "approved" if hits >= 2 else "needs-review"
        category, topic, concept = best[:3]
    else:
        category, topic, concept = "electronic-circuits", "mixed-signal", "분류 검토 필요"
        status = "needs-review"

    applications = []
    app_rules = {
        "통신": ["통신", "변조", "복조", "rs-232", "전송", "bps"],
        "제어": ["제어", "제어계", "블록선도", "안정도"],
        "계측": ["계측", "측정", "오실로스코프", "멀티미터"],
        "센서": ["센서", "검출기", "thermistor", "서미스터"],
        "임베디드": ["arduino", "아두이노", "마이크로컨트롤러", "mcu"],
        "컴퓨터·메모리": ["메모리", "memory", "cpu", "hbm", "프로세서"],
        "신호처리": ["신호", "푸리에", "샘플링", "필터"],
        "전력전자": ["전력", "정류", "인버터", "컨버터", "scr", "igbt"],
        "광전자": ["led", "포토", "광전", "레이저"],
        "RF·전파": ["안테나", "rf", "고주파", "전파"],
    }
    for label, keywords in app_rules.items():
        if contains_any(text, keywords):
            applications.append(label)

    question_types = ["개념형"] if contains_any(text, ["설명으로", "옳은 것은", "옳지 않은", "특성으로"]) else ["계산형"]
    if contains_any(text, ["회로에서", "회로의", "회로가"]):
        question_types.append("회로도 포함")
    if contains_any(text, ["파형", "그래프", "타이밍"]):
        question_types.append("파형해석")
    if contains_any(text, ["특성곡선", "동작영역", "소자 특성"]):
        question_types.append("소자특성")
    if contains_any(text, ["논리식", "카르노", "진리표"]):
        question_types.append("논리식·카르노맵")

    topic_migrations = {
        "basic-laws": "elements-basics", "elements": "elements-basics", "sinusoidal": "sinusoidal-phasor",
        "coupled": "coupled-transformer", "network-analysis": "kcl-kvl", "network-theorems": "thevenin",
        "non-sinusoidal": "non-sinusoidal-fourier", "transfer-function": "transfer-response",
        "diode-devices": "special-devices", "materials": "semiconductor-basics", "fet-device": "fet-device",
        "diode-applications": "rectifier-smoothing", "bjt-amplifiers": "bjt-amplifier",
        "fet-amplifiers": "fet-amplifier", "frequency-response": "amplifier-frequency",
        "power-amplifiers": "power-amplifier", "feedback": "feedback-amplifier", "op-amp": "opamp-operations",
        "oscillators": "oscillator", "pulse-circuits": "pulse-555", "mixed-signal": "signals-systems",
        "number-systems": "number-systems", "boolean": "boolean-gates", "combinational": "other-combinational",
        "converters": "adc-dac", "sequential": "latch-flipflop", "registers-counters": "register",
        "memory-pld": "memory", "processor": "microprocessor",
    }
    topic = topic_migrations.get(topic, topic)
    return {
        "category": category,
        "topics": [topic],
        "concepts": [concept],
        "auxiliaryTags": applications,
        "questionTypes": list(dict.fromkeys(question_types)),
        "status": status,
        "method": "ocr-keyword-v1",
    }


def apply_answer_keys(questions: list[dict]) -> None:
    key_file = DATA_DIR / "answer_keys.json"
    if not key_file.exists():
        return
    answer_keys = json.loads(key_file.read_text(encoding="utf-8"))
    for question in questions:
        exam_answers = answer_keys.get(question["examId"], {})
        entry = exam_answers.get(str(question["number"]))
        if entry is None:
            continue
        if isinstance(entry, int):
            entry = {"choice": entry, "status": "unverified", "sources": []}
        question["answer"] = {
            "choice": entry.get("choice"),
            "status": entry.get("status", "unverified"),
            "sources": entry.get("sources", []),
        }
        question["review"]["answer"] = "approved" if entry.get("status") in {"official", "cross-checked"} else "needs-review"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_contact_sheet(exam: dict, questions: list[dict]) -> str:
    sheet_dir = REVIEW_DIR / "contact-sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    columns = 4
    cell_w, cell_h = 620, 500
    header_h = 90
    rows = 5
    sheet = Image.new("RGB", (columns * cell_w, header_h + rows * cell_h), "#edf1f5")
    draw = ImageDraw.Draw(sheet)
    draw.text((28, 22), f"{exam['title']} - 문제 이미지 검수표", fill="#111827", font=font(34))
    for index, question in enumerate(sorted(questions, key=lambda q: q["number"])):
        row, col = divmod(index, columns)
        left, top = col * cell_w, header_h + row * cell_h
        draw.rounded_rectangle((left + 10, top + 10, left + cell_w - 10, top + cell_h - 10), 16, fill="white", outline="#cbd5e1", width=2)
        label = f"Q{question['number']:02d} · {question['classification']['concepts'][0]} · crop:{question['review']['crop']}"
        draw.text((left + 26, top + 22), label, fill="#0f172a", font=font(20))
        image = Image.open(PROJECT / question["image"]["src"]).convert("RGB")
        thumb = ImageOps.contain(image, (cell_w - 52, cell_h - 78), Image.Resampling.LANCZOS)
        x = left + (cell_w - thumb.width) // 2
        y = top + 58 + (cell_h - 72 - thumb.height) // 2
        sheet.paste(thumb, (x, y))
    target = sheet_dir / f"{exam['id']}.jpg"
    sheet.save(target, format="JPEG", quality=88, optimize=True)
    return target.relative_to(PROJECT).as_posix()


def write_outputs(exams: list[dict], questions: list[dict], build_issues: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    public_exams = [{key: value for key, value in exam.items() if key not in {"sourcePath", "slug"}} for exam in exams]
    taxonomy = json.loads((DATA_DIR / "taxonomy.json").read_text(encoding="utf-8"))
    payload = {
        "schemaVersion": 2,
        "taxonomyVersion": taxonomy.get("version", 2),
        "generatedAt": date.today().isoformat(),
        "taxonomy": taxonomy,
        "exams": public_exams,
        "questions": questions,
    }
    (DATA_DIR / "exams.json").write_text(json.dumps(public_exams, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "questions.json").write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA_DIR / "data.js").write_text("window.QUESTION_BANK = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    unresolved = [
        {
            "id": q["id"], "year": q["year"], "agency": q["agency"], "number": q["number"],
            "image": q["image"]["src"], "choice": q["answer"]["choice"], "status": q["answer"]["status"],
            "reason": "정답 번호 없음" if q["answer"]["choice"] is None else "잠정 정답—공식 정답표 교차검증 필요",
            "sources": q["answer"]["sources"], "ocrText": q["ocrText"],
        }
        for q in questions if q["answer"]["choice"] is None or q["answer"]["status"] not in {"official", "cross-checked"}
    ]
    (REVIEW_DIR / "unresolved-answers.json").write_text(json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8")
    with (REVIEW_DIR / "unresolved-answers.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "year", "agency", "number", "choice", "status", "reason", "image", "sources", "ocrText"])
        writer.writeheader()
        writer.writerows([{**row, "sources": json.dumps(row["sources"], ensure_ascii=False)} for row in unresolved])

    with (REVIEW_DIR / "crop-review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["examId", "question", "type", "detail"])
        writer.writeheader()
        writer.writerows(build_issues)

    category_counts = Counter(q["classification"]["category"] for q in questions)
    report = {
        "examCount": len(exams),
        "questionCount": len(questions),
        "expectedQuestionCount": sum(exam["expectedQuestions"] for exam in exams),
        "unresolvedAnswerCount": len(unresolved),
        "provisionalAnswerCount": sum(q["answer"]["choice"] is not None and q["answer"]["status"] not in {"official", "cross-checked"} for q in questions),
        "missingAnswerCount": sum(q["answer"]["choice"] is None for q in questions),
        "buildIssueCount": len(build_issues),
        "cropIssueCount": sum(issue["type"] == "crop-size-suspicious" for issue in build_issues),
        "anchorReviewCount": sum(issue["type"].startswith("anchor-") for issue in build_issues),
        "classificationNeedsReviewCount": sum(q["review"]["classification"] != "approved" for q in questions),
        "categoryCounts": category_counts,
        "issues": build_issues,
    }
    (REVIEW_DIR / "build-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="전자공학개론 문제 이미지·데이터셋 생성")
    parser.add_argument("--force-render", action="store_true")
    parser.add_argument("--force-ocr", action="store_true")
    parser.add_argument("--exam", help="예: national-2024")
    args = parser.parse_args()

    ensure_vision_binary()
    pdfs = sorted(SOURCE_DIR.glob("*.pdf"))
    exams = [exam_from_path(path) for path in pdfs]
    if args.exam:
        exams = [exam for exam in exams if exam["id"] == args.exam]
    if not exams:
        raise SystemExit("대상 시험이 없습니다")

    all_questions: list[dict] = []
    all_issues: list[dict] = []
    for index, exam in enumerate(exams, start=1):
        print(f"[{index}/{len(exams)}] {exam['id']} render", flush=True)
        pages = render_exam(exam, force=args.force_render)
        ocr_pages = []
        for page_number, page_path in enumerate(pages, start=1):
            print(f"  OCR page {page_number}/{len(pages)}", flush=True)
            ocr_pages.append(ocr_page(page_path, exam["id"], page_number, force=args.force_ocr))
        anchors, issues = find_anchors(ocr_pages, exam["id"])
        questions, crop_issues = crop_questions(exam, pages, ocr_pages, anchors)
        exam_issues = [{"examId": exam["id"], **issue} for issue in issues + crop_issues]
        all_issues.extend(exam_issues)
        all_questions.extend(questions)
        if len(questions) != exam["expectedQuestions"]:
            all_issues.append({
                "examId": exam["id"], "question": "", "type": "question-count-mismatch",
                "detail": f"expected={exam['expectedQuestions']} actual={len(questions)}",
            })
        make_contact_sheet(exam, questions)
        print(f"  extracted {len(questions)} questions, issues {len(exam_issues)}", flush=True)

    all_questions.sort(key=lambda q: (q["year"], q["agency"], q["number"]))
    apply_answer_keys(all_questions)
    write_outputs(exams, all_questions, all_issues)
    print(f"DONE exams={len(exams)} questions={len(all_questions)} issues={len(all_issues)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
