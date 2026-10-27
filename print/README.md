# 제본 PDF

`tools/build_print_pdf.py`는 같은 소분류 또는 풀이 태그끼리 묶어 A4 2×2 PDF와 문항목록(JSON/CSV)을 만듭니다. 중복 분류된 문제도 문항 ID당 한 번만 수록합니다. 기본 순서는 대분류 → 대표 중분류 → 대표 소분류 → 연도 → 시험구분 → 원 문항번호입니다. 각 문제에 새 일련번호, 중·소분류, 오른쪽 위 작은 출처를 표시하고 정답 4개는 페이지 오른쪽 아래에 모읍니다. 명조체 글꼴을 사용하며 문제 내용은 유지하고 큰 순백 여백만 정리합니다.

- [전체 1,100문제 제본 PDF](electronics_1100_print.pdf): A4 289쪽(문제 286쪽 + 영역 표지 3쪽), 새 번호만 표시, 원 번호 제거, 출처·정답 오른쪽 정렬. 세로/가로 비율과 최소 배치 보정에 따라 긴 27문항은 세로 두 칸을 사용해 확대합니다. 소분류별 순서는 유지하며 분류명은 문제 위에 인쇄하지 않습니다.
- [회로이론 301문제 최신 제본 PDF](circuit_theory_301_print.pdf): 소분류순, A4 76쪽, 원 번호 제거.
- [소분류 정렬 2쪽 샘플](subtopic_sample.pdf): 브리지 5문제와 노턴 3문제. 원 번호 제거 적용.
- [전체 소분류별 문항 순서](study_order_subtopics.csv): 1,100문제, 275쪽.
- [전체 태그별 문항 순서](study_order_tags.csv): 같은 중분류 내에서 대표 태그별 묶음.
- [전체 분류표](../review/study-classification.md), [문항별 분류 검토표](../review/full-bank-classification.csv).

계획 JSON/CSV에는 대표 분류와 관련 분류의 중복이 제거된 최종 순서·페이지·배치칸·출처·정답이 저장됩니다. 실제 출력할 때도 동일한 정렬 함수를 사용합니다. 소분류가 한 페이지를 다 채우지 않아도 다음 소분류를 이어 배치하므로, 전체 계획은 1,100 ÷ 4 = 275쪽입니다.

## 실행

계획만 생성할 때는 Python 표준 라이브러리만 필요합니다. PDF를 만들 때는 `pip install pymupdf fonttools pillow`가 필요하고, 기본 글꼴은 Linux의 Noto Serif CJK입니다. 다른 환경에서는 `--font /path/to/KoreanSerif.otf`를 지정하세요. 글꼴은 사용하는 문자만 포함해 PDF 용량을 줄입니다.

```bash
# 전체 제본: 영역별 표지, 분류명 숨김, 원 번호 제거
python3 tools/build_print_pdf.py --adaptive-sizing --section-covers --hide-classification --remove-original-numbers --output print/electronics_1100_print.pdf

# 소분류별 전체 문항 순서·페이지 계획만 생성
python3 tools/build_print_pdf.py --plan-only --output /tmp/all-subtopics.pdf

# 대표 태그별 계획. power 태그가 있으면 원래 대표 태그보다 우선 선택
python3 tools/build_print_pdf.py --plan-only --group-by tag --tag-priority power --output /tmp/all-tags.pdf

# 회로이론만 PDF 생성
python3 tools/build_print_pdf.py --category circuit-theory --output /tmp/circuit-theory.pdf

# 특정 소분류 2개를 합쳐 PDF 생성. 같은 문항이 둘에 속해도 1회만 수록
python3 tools/build_print_pdf.py --subtopic bridge-transform/bridge --subtopic network-theorems/norton --remove-original-numbers --output /tmp/sample.pdf

# 전압이득 태그 문제 중 BJT/FET 증폭기를 모아 소분류순으로 생성
python3 tools/build_print_pdf.py --topic bjt-amplifier --topic fet-amplifier --tag voltage-gain --output /tmp/gain.pdf
```

`--category`, `--topic`, `--subtopic`, `--tag`는 각각 여러 번 지정할 수 있습니다. 같은 조건은 OR, 다른 조건은 AND입니다. 관련 소분류로 검색해도 PDF에는 대표 소분류 위치에 한 번만 배치합니다. 잘못된 분류 ID·0문항·내용이 서로 다른 중복 ID는 오류로 중단합니다.

## 원 문항번호 제거

기본 생성은 원본 번호를 유지합니다. 이전 제본처럼 제거하려면 `--remove-original-numbers`를 사용합니다. 원본 이미지를 자르지 않고 검수된 번호 좌표만 흰색으로 가립니다. `data/print_number_masks.json`에는 전체 1,100문항의 좌표가 있습니다. 미검수 문항이 포함되면 본문 손실을 막기 위해 오류로 중단하며 자동으로 추정해 가리지 않습니다. 추가 좌표를 검수한 뒤 이 파일을 보완하거나 `--number-masks`로 별도 JSON을 지정할 수 있습니다. 번호가 원본에 이미 없는 경우는 JSON 값 `null`을 사용합니다.

실제 생성 후 PDF를 다시 열어 쪽수·문제 이미지 수·출처·정답을 대조하고 `.render.json`에 결과를 남깁니다. `.json`과 `.csv`는 제본 순서표입니다.

기존 `circuit_theory_299_print.pdf`는 이전 분류의 산출물입니다. 현재 회로이론은 301문항이며, 기존 PDF와 문항목록을 자동으로 덮어쓰지 않습니다.

전체 제본은 회로이론 301문제(78쪽), 전자회로 532문제(138쪽), 디지털회로 267문제(70쪽)이며 표지 위치는 1·80·219쪽입니다. 영역마다 새 페이지에서 시작하므로 표지 없는 전체 계획 275쪽과는 쪽수가 다릅니다.

## 페이지 테두리 잡선 정리

전체 1,100개 PNG에서 긴 수평·수직선을 검사하고 176개 후보 이미지와 추가 지적된 6문항을 직접 확인했습니다. 78문항의 92개 검수 영역에서 페이지 테두리·쪽번호·페이지 연결부 조각을 제거했습니다. 회로·그래프·표·보기의 테두리는 유지했습니다. 기존 `assets/questions/` PNG 경로에 반영했으며 이미지 크기, 문제 위치와 검수 영역 밖의 픽셀은 바꾸지 않았습니다. 전체 제본 PDF도 정리된 PNG로 다시 생성했습니다. 당시 정리에서는 문항 순서와 캔버스를 유지했습니다. 이후 아래 여백 정리로 전체 제본은 289쪽입니다.

검수 좌표와 전후 파일 해시는 `data/page_artifact_masks.json`, 검사 결과는 `review/page-artifact-cleanup.json`에 있습니다. `python3 tools/clean_page_artifacts.py`는 변경 예정 목록을 확인하고 `--apply`를 붙이면 반영합니다. 이미 정리된 파일은 건너뛰며 검수 이후 수정된 파일은 오류로 중단합니다. 처리에는 Pillow가 필요합니다.

추가 검수에서 218·469·617·665·842·857번의 짧은 쪽번호·과목명 조각과 가로선을 제거했습니다. 872번은 처음에는 PDF에서만 여백을 제외했으나, 아래 작업에서 PNG에도 반영했습니다.

## PNG의 큰 빈 여백 정리

전체 1,100문항 중 649문항(872번 포함)의 상하좌우 순백 여백을 정리해 기존 PNG를 교체했습니다. 모든 글자·그림·희미한 픽셀까지 포함하는 내용 범위에서 최소 12픽셀 여유를 두고, 36픽셀 이상인 큰 여백만 제거합니다. 제외한 76,566,865픽셀은 전부 순백(255)이며 남긴 내용은 확대·재표본화 없이 원본 픽셀 그대로입니다. 답·출처·분류는 유지합니다.

`data/image_margin_trims.json`에 원래 크기·잘라낸 영역·새 크기·전후 해시·새 번호 가림 좌표를 기록했습니다. `data/questions.json`과 브라우저용 `data/data.js`의 이미지 크기, `data/print_number_masks.json`의 좌표도 함께 갱신했습니다. 이전 잡선 정리 좌표는 당시 원본 기준 이력으로 남기며, 정리 도구·검증에서는 이후 여백 변환을 함께 적용합니다. 기존 PDF 전용 872번 보정(`data/print_image_crops.json`)은 PNG에 반영되어 해제했습니다. 623번은 `data/print_layout_overrides.json`으로 기존 확대 배치를 유지해 글자 크기가 줄지 않게 했습니다.

- [수정 649문항 목록·새 PDF 페이지](../review/image-margin-trim-report.md)
- [엑셀용 수정 목록](../review/image-margin-trim-report.csv)
- [내용 픽셀 보존 검증](../review/image-margin-trim-audit.json)

```bash
# 현재 PNG의 큰 순백 여백 검사 / PNG·크기·번호 좌표 반영
python3 tools/trim_image_margins.py
python3 tools/trim_image_margins.py --apply
```

같은 파일을 다시 실행하면 추가 변경은 없습니다. PDF는 문항 번호·순서를 유지해 289쪽으로 다시 만들었으며, 모든 문항의 실제 글자 배율이 이전 PDF보다 작아지지 않는지 대조했습니다.
