# 제본 PDF

[전체 1,100문제 PDF](electronics_1100_print.pdf)는 A4 **297쪽**입니다. 영역별 표지 3쪽과 문제 294쪽으로 구성하며, **모든 문제 페이지에 2~4문항**을 배치합니다. 한 문제만 한 페이지에 넣는 배치는 사용하지 않습니다. 기본 2×2 배치에서 세로로 긴 문제는 한 열의 세로 두 칸을 사용하고, 나머지 칸에는 다른 문제를 배치합니다.

문제 위에는 새 일련번호만 표시합니다. 작은 출처는 오른쪽 위, 해당 페이지 정답들은 오른쪽 아래에 모읍니다. 명조체를 사용하며 중·소분류명은 문제 위에 인쇄하지 않습니다. 소분류별 순서와 문제 번호 1~1100은 유지합니다. 원본 PNG에 있던 시험 문항번호는 검수된 좌표로 직접 지워 **PNG 자체를 번호 없는 이미지로 교체**했습니다.

- [원 번호 삭제·여백 정리 목록](../review/numberless-margin-report.md): 전체 1,100문항과 우측 큰 여백 추가 정리 47문항, 최신 PDF 페이지.
- [엑셀용 전체 변경 목록](../review/numberless-margin-report.csv)
- [현재 PDF 문항 순서](electronics_1100_print.csv)
- [소분류 순서 계획](study_order_subtopics.csv), [태그별 순서 계획](study_order_tags.csv)
- [전체 분류표](../review/study-classification.md), [문항별 분류 검토표](../review/full-bank-classification.csv)

정렬은 대분류 → 대표 중분류 → 대표 소분류 → 연도 → 시험구분 → 원 문항번호입니다. 한 문항이 여러 분류에 속해도 ID당 한 번만 수록합니다. 현재 영역은 회로이론 301문제, 전자회로 532문제, 디지털회로 267문제이며 표지는 1·81·224쪽입니다. 문항 수와 분류 순서는 기존과 같습니다.

## 생성

계획만 생성하려면 Python 표준 라이브러리가 필요합니다. PDF 생성에는 `pip install pymupdf fonttools pillow`와 Noto Serif CJK 글꼴이 필요합니다. 글꼴은 사용하는 문자만 포함합니다. 다른 환경에서는 `--font /path/to/KoreanSerif.otf`를 지정할 수 있습니다.

```bash
# 전체 PDF: 한 문제만 배치되는 페이지 금지, 분류명 숨김, 영역 표지
python3 tools/build_print_pdf.py --avoid-single-question-pages --adaptive-sizing --section-covers --hide-classification --remove-original-numbers --output print/electronics_1100_print.pdf

# 계획만 생성
python3 tools/build_print_pdf.py --plan-only --output /tmp/all-subtopics.pdf

# 같은 중분류 안에서 대표 태그별 정렬
python3 tools/build_print_pdf.py --plan-only --group-by tag --tag-priority power --output /tmp/all-tags.pdf

# 특정 대분류 / 소분류 선택
python3 tools/build_print_pdf.py --category circuit-theory --output /tmp/circuit-theory.pdf
python3 tools/build_print_pdf.py --subtopic bridge-transform/bridge --subtopic network-theorems/norton --output /tmp/sample.pdf
```

`--category`, `--topic`, `--subtopic`, `--tag`를 여러 번 지정하면 같은 조건은 OR, 다른 조건은 AND로 적용합니다. 같은 문제는 ID당 한 번만 수록합니다. `--avoid-single-question-pages`는 영역별 문항 순서를 유지하며 매 페이지 2~4문항을 배치하고, 조건상 불가능하면 오류로 중단합니다. `--adaptive-sizing`은 세로로 긴 문항과 `data/print_layout_overrides.json`의 최소 배치 크기를 반영합니다. 현재 전체 PDF에는 가로 두 칸을 모두 독점하는 문항이 없습니다.

생성 후 PDF를 다시 열어 쪽수·문항 수·이미지 수·출처·정답을 대조해 `.render.json`에 남깁니다. `.json`·`.csv`에는 실제 페이지와 칸을 포함한 문항 순서가 저장됩니다.

## 번호 없는 PNG와 여백

`tools/normalize_question_images.py`는 검수된 기존 번호 좌표만 흰색 처리한 뒤, 모든 내용 픽셀을 포함하는 바깥 영역에서 8픽셀 여유를 남겨 순백 여백만 제거합니다. 보존 영역은 이전 PDF에서 보이던 내용과 픽셀 단위로 동일하고, 다시 그리거나 재표본화하지 않습니다. 오른쪽 여백도 내용의 오른쪽 끝을 기준으로 정리합니다. 본문·회로·그래프·표 안의 공간은 내용 배치를 유지하기 위해 그대로 둡니다.

```bash
# 검수된 원 번호 삭제 + 바깥 여백 정리, PNG·메타데이터 반영
python3 tools/normalize_question_images.py --apply
```

`data/normalized_question_images.json`은 전체 1,100문항의 이전 번호 좌표·자른 영역·전후 크기·전후 해시를 기록합니다. `data/questions.json`과 브라우저용 `data/data.js`의 크기도 함께 갱신합니다. 원 번호를 PNG에서 이미 지웠으므로 `data/print_number_masks.json`의 값은 전부 `null`이며, PDF가 같은 좌표로 본문을 다시 가리지 않습니다. `--remove-original-numbers`는 호환을 위해 유지하지만 현재 PNG에서는 추가로 지울 부분이 없습니다. 이미 정리된 파일은 해시를 검증한 뒤 다시 수정하지 않습니다.

165·223·626·759번의 한 페이지 한 문항 배치는 해제했습니다. 다른 문제와 같은 페이지에 배치하고 새 PNG를 사용합니다. 페이지당 4문항이 236쪽, 3문항이 40쪽, 2문항이 18쪽입니다.

## 이전 정리 이력

- `data/page_artifact_masks.json`, `review/page-artifact-cleanup.json`: 페이지 테두리·쪽번호 조각 제거 이력. 회로·그래프·표·보기 테두리는 유지했습니다.
- `data/image_margin_trims.json`: 최초 649문항 순백 여백 정리와 후속 3문항 잡선 제거 후 여백 정리 이력.
- `review/numberless-images-audit.json`: 전체 PNG가 이전에 검수한 번호 영역 및 순백 바깥 여백을 제외하고 동일한지 대조한 최신 검증 결과.

이전 좌표·해시는 당시 원본 기준으로 유지합니다. 현재 파일 검증에는 이후 여백 변환과 `normalized_question_images.json`을 함께 적용합니다. 번호 좌표는 이 파일에 보관되어 있어 기존 검수 내역을 잃지 않습니다.

`circuit_theory_299_print.pdf`, `circuit_theory_301_print.pdf`, `subtopic_sample.pdf`는 과거 생성물이며 현재 전체 제본으로 대체되지 않습니다.
