# 제본 PDF

`tools/build_print_pdf.py`는 같은 소분류 또는 풀이 태그끼리 묶어 A4 2×2 PDF와 문항목록(JSON/CSV)을 만듭니다. 중복 분류된 문제도 문항 ID당 한 번만 수록합니다. 기본 순서는 대분류 → 대표 중분류 → 대표 소분류 → 연도 → 시험구분 → 원 문항번호입니다. 각 문제에 새 일련번호, 중·소분류, 오른쪽 위 작은 출처를 표시하고 정답 4개는 페이지 오른쪽 아래에 모읍니다. 명조체 글꼴을 사용하며 이미지를 자르거나 재압축하지 않습니다.

- [전체 1,100문제 제본 PDF](electronics_1100_print.pdf): A4 291쪽(문제 288쪽 + 영역 표지 3쪽), 새 번호만 표시, 원 번호 제거, 출처·정답 오른쪽 정렬. 세로/가로 비율이 1.6을 넘는 긴 27문항은 세로 두 칸을 사용해 확대합니다. 소분류별 순서는 유지하며 분류명은 문제 위에 인쇄하지 않습니다.
- [회로이론 301문제 최신 제본 PDF](circuit_theory_301_print.pdf): 소분류순, A4 76쪽, 원 번호 제거.
- [소분류 정렬 2쪽 샘플](subtopic_sample.pdf): 브리지 5문제와 노턴 3문제. 원 번호 제거 적용.
- [전체 소분류별 문항 순서](study_order_subtopics.csv): 1,100문제, 275쪽.
- [전체 태그별 문항 순서](study_order_tags.csv): 같은 중분류 내에서 대표 태그별 묶음.
- [전체 분류표](../review/study-classification.md), [문항별 분류 검토표](../review/full-bank-classification.csv).

계획 JSON/CSV에는 대표 분류와 관련 분류의 중복이 제거된 최종 순서·페이지·배치칸·출처·정답이 저장됩니다. 실제 출력할 때도 동일한 정렬 함수를 사용합니다. 소분류가 한 페이지를 다 채우지 않아도 다음 소분류를 이어 배치하므로, 전체 계획은 1,100 ÷ 4 = 275쪽입니다.

## 실행

계획만 생성할 때는 Python 표준 라이브러리만 필요합니다. PDF를 만들 때는 `pip install pymupdf fonttools`가 필요하고, 기본 글꼴은 Linux의 Noto Serif CJK입니다. 다른 환경에서는 `--font /path/to/KoreanSerif.otf`를 지정하세요. 글꼴은 사용하는 문자만 포함해 PDF 용량을 줄입니다.

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

전체 제본은 회로이론 301문제(79쪽), 전자회로 532문제(139쪽), 디지털회로 267문제(70쪽)이며 표지 위치는 1·81·221쪽입니다. 영역마다 새 페이지에서 시작하므로 표지 없는 전체 계획 275쪽과는 쪽수가 다릅니다.
