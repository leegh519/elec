# 전체 학습 분류표

1,100문항 · 58개 중분류 · 238개 소분류. 원본 이미지 대조 214문항, 대표 중분류 이동 121문항.

질문 OCR·기존 분류를 전 문항 대조하고, 회로·그래프 식별이 필요한 문항은 원본까지 확인했습니다. 정답을 다시 푸는 검수와는 별개입니다. 문항별 결과는 [검토표](full-bank-classification.csv), 이전/이후 분류와 원본 식별 정보는 [감사 기록](full-bank-classification-audit.json)에 있습니다.

대표 소분류는 PDF의 수록 위치를 결정합니다. 관련 소분류로도 문제를 찾을 수 있으나 PDF에서 같은 문제를 반복하지 않습니다. 표의 관련 포함 개수는 대표를 포함한 검색 결과 수로, 합산하면 중복될 수 있습니다.

## 회로이론 — 301문항

### 기본소자 — 대표 30문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 저항·비저항 | `elements-basics/resistance` | 4 | 4 |
| 커패시터·정전용량 | `elements-basics/capacitance` | 3 | 3 |
| 인덕터·전압전류 관계 | `elements-basics/inductance` | 1 | 1 |
| 전하·에너지 보존 | `elements-basics/energy` | 2 | 2 |
| 배터리 용량·특성 | `elements-basics/battery` | 3 | 3 |
| 직류 정상상태 | `elements-basics/dc-steady` | 4 | 4 |
| 전류·전력·정격 | `elements-basics/power` | 5 | 5 |
| R·L·C 기본특성 | `elements-basics/rlc` | 8 | 8 |

### 회로해석 — 대표 42문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 직병렬·합성저항 | `circuit-analysis/equivalent` | 6 | 6 |
| 커패시터·인덕터 합성 | `circuit-analysis/capacitor-network` | 3 | 3 |
| 전압·전류분배 | `circuit-analysis/divider` | 9 | 9 |
| 종속전원 회로해석 | `circuit-analysis/dependent` | 4 | 4 |
| KCL·노드해석 | `circuit-analysis/node` | 15 | 15 |
| KVL·루프해석 | `circuit-analysis/loop` | 3 | 3 |
| 부하선·비선형 소자 해석 | `circuit-analysis/nonlinear` | 1 | 1 |
| 직류회로 전압·전류·전력 | `circuit-analysis/dc-network` | 1 | 1 |

### 브리지·Y–Δ 변환 — 대표 5문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 브리지 평형·해석 | `bridge-transform/bridge` | 5 | 5 |
| Y–Δ 변환 | `bridge-transform/wye-delta` | 0 | 1 |

### 회로망 정리 — 대표 47문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 최대전력전달·공액정합 | `network-theorems/maximum-ac` | 8 | 8 |
| 최대전력전달·저항정합 | `network-theorems/maximum-dc` | 16 | 18 |
| 노턴 등가회로 | `network-theorems/norton` | 3 | 3 |
| 테브난 등가회로 | `network-theorems/thevenin` | 15 | 15 |
| 중첩정리 | `network-theorems/superposition` | 1 | 1 |
| 전원변환 | `network-theorems/source` | 3 | 3 |
| 밀러·밀만·상반정리 | `network-theorems/miller` | 1 | 1 |

### 정현파·페이저 — 대표 22문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 정현파·주파수·실효값 | `sinusoidal-phasor/wave` | 4 | 4 |
| 페이저·위상·합성 | `sinusoidal-phasor/phasor` | 2 | 2 |
| 임피던스·어드미턴스 | `sinusoidal-phasor/impedance` | 6 | 6 |
| 교류회로 전압·전류 | `sinusoidal-phasor/ac-analysis` | 10 | 10 |

### 교류전력·역률 — 대표 14문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 역률·역률개선 | `ac-power/factor` | 4 | 4 |
| 복소전력·전력삼각형 | `ac-power/triangle` | 3 | 3 |
| 유효전력·평균전력 | `ac-power/average` | 7 | 7 |

### 필터 — 대표 35문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 능동필터·전달함수 | `filter/active` | 16 | 16 |
| 대역통과·대역저지 | `filter/band` | 4 | 4 |
| 수동 고역통과필터 | `filter/highpass` | 4 | 4 |
| 수동 저역통과필터 | `filter/lowpass` | 4 | 4 |
| 필터 전달함수·주파수응답 | `filter/response` | 5 | 5 |
| 필터 판별·차단주파수 | `filter/cutoff` | 2 | 2 |

### 공진 — 대표 17문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| Q·선택도·대역폭 | `resonance/quality` | 6 | 6 |
| 병렬공진 | `resonance/parallel` | 4 | 4 |
| 직렬공진 | `resonance/series` | 3 | 3 |
| 공진조건·주파수 | `resonance/basics` | 4 | 4 |

### 과도현상 — 대표 18문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 초기값·최종값 | `transient/initial-final` | 3 | 3 |
| RLC 과도응답·감쇠 | `transient/rlc` | 3 | 3 |
| RL 과도응답·시정수 | `transient/rl` | 4 | 4 |
| RC 과도응답·시정수 | `transient/rc` | 8 | 8 |

### 변압기·상호유도 — 대표 9문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 상호인덕턴스·결합계수 | `coupled-transformer/coupling` | 1 | 1 |
| 임피던스 변환·정합 | `coupled-transformer/matching` | 5 | 5 |
| 변압기 권선비·전압·전류 | `coupled-transformer/ratio` | 3 | 3 |

### 4단자망 — 대표 6문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| ABCD·전송파라미터 | `two-port/abcd` | 2 | 2 |
| Y 파라미터 | `two-port/y` | 2 | 2 |
| Z 파라미터 | `two-port/z` | 2 | 2 |

### 라플라스변환 — 대표 7문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 역라플라스·수렴영역 | `laplace/inverse` | 2 | 2 |
| s영역 회로해석 | `laplace/circuit` | 2 | 2 |
| 라플라스 변환·시간이동 | `laplace/forward` | 3 | 3 |

### 선형시불변시스템 — 대표 14문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| LTI·임펄스응답·컨벌루션 | `signals-systems/convolution` | 5 | 5 |
| 표본화·에일리어싱 | `signals-systems/sampling` | 2 | 2 |
| 전력스펙트럼·잡음 | `signals-systems/spectrum` | 4 | 4 |
| 보드선도·극점·영점 | `signals-systems/bode` | 1 | 1 |
| 전달함수·주파수응답 | `signals-systems/transfer` | 2 | 2 |

### 블록선도·제어시스템 — 대표 4문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 안정도·특성방정식 | `control-systems/stability` | 1 | 1 |
| 블록선도·신호흐름선도 | `control-systems/block` | 2 | 2 |
| 제어계 응답 | `control-systems/response` | 1 | 1 |

### 3상회로 — 대표 1문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 평형 3상·Y·Δ 결선 | `three-phase/balanced` | 1 | 1 |

### 비정현파·푸리에급수 — 대표 10문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 푸리에 변환·성질 | `non-sinusoidal-fourier/transform` | 3 | 3 |
| 푸리에급수·고조파 | `non-sinusoidal-fourier/series` | 1 | 1 |
| 고조파 평균전력 | `non-sinusoidal-fourier/harmonic-power` | 1 | 1 |
| 비정현파 평균값·실효값 | `non-sinusoidal-fourier/rms` | 5 | 5 |

### 전계·자계·전자유도 — 대표 20문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 유전체·정전용량 | `electromagnetic-basics/capacitance` | 5 | 5 |
| 쿨롱 법칙·전하 간 힘 | `electromagnetic-basics/coulomb` | 1 | 1 |
| 전계·전위 | `electromagnetic-basics/field` | 2 | 2 |
| 전류밀도·미분형 옴의 법칙 | `electromagnetic-basics/ohm` | 2 | 2 |
| 전자유도·유도기전력 | `electromagnetic-basics/induction` | 1 | 1 |
| 도선·자극 사이 힘 | `electromagnetic-basics/force` | 5 | 5 |
| 자계·자속·자기회로 | `electromagnetic-basics/magnetic` | 4 | 4 |


## 전자회로 — 532문항

### 반도체 기초 — 대표 23문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 에너지대·페르미준위 | `semiconductor-basics/energy` | 4 | 5 |
| 이동도·확산·드리프트 | `semiconductor-basics/transport` | 2 | 2 |
| 광전·열전효과 | `semiconductor-basics/photo-thermal` | 2 | 2 |
| 온도·진성캐리어 | `semiconductor-basics/temperature` | 1 | 1 |
| 진성·불순물 반도체·도핑 | `semiconductor-basics/doping` | 14 | 14 |

### 다이오드 — 대표 26문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 다이오드 ON/OFF·회로해석 | `diode-basics/circuit` | 7 | 7 |
| 다이오드 온도특성 | `diode-basics/temperature` | 2 | 2 |
| 다이오드 I–V·항복특성 | `diode-basics/iv` | 1 | 2 |
| PN접합·공핍층·바이어스 | `diode-basics/junction` | 16 | 18 |

### 특수 반도체소자 — 대표 17문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| LED·광소자 | `special-devices/led` | 5 | 7 |
| SCR·사이리스터·TRIAC | `special-devices/thyristor` | 2 | 2 |
| 버랙터·가변용량 다이오드 | `special-devices/varactor` | 3 | 3 |
| 터널·쇼트키 다이오드 | `special-devices/tunnel` | 1 | 1 |
| 특수소자 종류·특성 비교 | `special-devices/comparison` | 6 | 6 |

### 정류·평활회로 — 대표 32문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 첨두값 검출기 | `rectifier-smoothing/peak` | 2 | 2 |
| 정밀정류기 | `rectifier-smoothing/precision` | 6 | 6 |
| 평활·리플·맥동률 | `rectifier-smoothing/smoothing` | 8 | 8 |
| 브리지 전파정류 | `rectifier-smoothing/bridge` | 6 | 6 |
| 중간탭 전파정류 | `rectifier-smoothing/center` | 3 | 3 |
| 반파정류 | `rectifier-smoothing/half` | 4 | 4 |
| 전파정류 | `rectifier-smoothing/full` | 2 | 2 |
| 정류 파형·평균값·실효값 | `rectifier-smoothing/rectification` | 1 | 1 |

### 리미터·클램퍼 — 대표 31문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 제너 리미터 | `limiter-clamper/zener` | 7 | 7 |
| 클램퍼·직류레벨 이동 | `limiter-clamper/clamp` | 4 | 4 |
| 바이어스·양방향 리미터 | `limiter-clamper/biased` | 15 | 15 |
| 리미터 전달특성·출력파형 | `limiter-clamper/clip` | 5 | 5 |

### 정전압회로 — 대표 25문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 직류전원 구성·변동률 | `voltage-regulator/supply` | 3 | 3 |
| 스위칭 조정기·DC–DC | `voltage-regulator/switching` | 2 | 2 |
| 직렬·병렬 선형조정기 | `voltage-regulator/linear` | 7 | 7 |
| 제너 정전압·허용부하 | `voltage-regulator/zener` | 13 | 13 |

### BJT 기초·바이어스 — 대표 64문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| BJT·FET 특성 비교 | `bjt-device/comparison` | 6 | 8 |
| BJT 스위칭·포화 | `bjt-device/switch` | 4 | 4 |
| α·β·전류 관계 | `bjt-device/current` | 6 | 6 |
| BJT 구조·동작영역·얼리효과 | `bjt-device/operation` | 10 | 12 |
| 바이어스 안정화·부하선 | `bjt-device/stability` | 2 | 2 |
| 전압분배 바이어스 | `bjt-device/divider` | 3 | 3 |
| BJT 직류 바이어스 계산 | `bjt-device/bias` | 33 | 33 |

### BJT 증폭기 — 대표 39문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| CC·이미터 팔로워 | `bjt-amplifier/cc` | 8 | 8 |
| CB·공통베이스 | `bjt-amplifier/cb` | 2 | 2 |
| CE·CB·CC 특성 비교 | `bjt-amplifier/comparison` | 5 | 5 |
| 소신호 등가회로·임피던스 | `bjt-amplifier/model` | 7 | 7 |
| 이미터 저항·바이패스 | `bjt-amplifier/bypass` | 7 | 7 |
| CE·공통이미터 이득·위상 | `bjt-amplifier/ce` | 10 | 10 |

### FET 기초·바이어스 — 대표 36문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| MOS 커패시터·축적·공핍·반전 | `fet-device/mos-cap` | 3 | 3 |
| FET 전달컨덕턴스 | `fet-device/gm` | 3 | 3 |
| JFET·핀치오프 | `fet-device/jfet` | 5 | 5 |
| 문턱전압·몸체효과 | `fet-device/threshold` | 3 | 3 |
| MOSFET 전류·치수·바이어스 | `fet-device/current` | 6 | 6 |
| MOSFET 구조·동작영역 | `fet-device/operation` | 16 | 24 |

### FET 증폭기 — 대표 16문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| CD·소스 팔로워 | `fet-amplifier/cd` | 2 | 2 |
| CS·CG·CD 특성 비교 | `fet-amplifier/comparison` | 2 | 2 |
| CS·공통소스 이득·임피던스 | `fet-amplifier/cs` | 12 | 12 |

### 증폭기 일반특성 — 대표 8문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 입출력 임피던스·버퍼 | `amplifier-basics/impedance` | 2 | 2 |
| 전압·전력이득·dB·dBm | `amplifier-basics/db` | 6 | 7 |

### 주파수응답·다단증폭기 — 대표 19문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 잡음지수·다단 잡음 | `amplifier-response/noise` | 1 | 1 |
| 달링턴 증폭기 | `amplifier-response/darlington` | 3 | 3 |
| 캐스코드 증폭기 | `amplifier-response/cascode` | 2 | 2 |
| 다단증폭기·종합이득·대역폭 | `amplifier-response/cascade` | 5 | 5 |
| 연산증폭기 GBW·대역폭 | `amplifier-response/gbw` | 4 | 4 |
| 증폭기 주파수응답·차단주파수 | `amplifier-response/frequency` | 4 | 4 |

### 전력증폭기 — 대표 6문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| B·AB급 푸시풀·교차왜곡 | `power-amplifier/pushpull` | 1 | 1 |
| 전력증폭기 효율·최대출력 | `power-amplifier/efficiency` | 2 | 2 |
| A·B·AB·C급 동작특성 | `power-amplifier/classes` | 3 | 3 |

### 부궤환증폭기 — 대표 8문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 귀환형식·입출력 임피던스 | `feedback-amplifier/topology` | 1 | 1 |
| 폐루프 이득·귀환율·대역폭 | `feedback-amplifier/gain` | 2 | 2 |
| 부궤환 효과·안정도·왜곡 | `feedback-amplifier/effects` | 5 | 5 |

### 차동증폭기·전류미러 — 대표 11문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 전류미러 | `differential-mirror/mirror` | 1 | 1 |
| 차동·동상이득·CMRR | `differential-mirror/cmrr` | 6 | 6 |
| 차동쌍 회로·이득·입출력 위상 | `differential-mirror/pair` | 4 | 4 |

### 연산증폭기 — 대표 70문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 이상적 OP AMP·가상단락 | `opamp/ideal` | 7 | 7 |
| 슬루율·비이상 특성 | `opamp/slew` | 1 | 1 |
| 반전증폭기 | `opamp/inverting` | 5 | 5 |
| 비반전증폭기 | `opamp/noninverting` | 8 | 8 |
| 가산기·가중합 | `opamp/summer` | 7 | 7 |
| 감산기·차동연산 | `opamp/difference` | 19 | 19 |
| 전압 팔로워·버퍼 | `opamp/follower` | 3 | 3 |
| 전류·전압 변환·전류증폭 | `opamp/current` | 6 | 6 |
| 복합 연산·다단 OP AMP | `opamp/compound` | 14 | 14 |

### 미분기·적분기 — 대표 11문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 적분기·출력파형 | `differentiator-integrator/integrator` | 7 | 8 |
| 미분기·주파수특성 | `differentiator-integrator/differentiator` | 3 | 4 |
| 미분기·적분기 비교 | `differentiator-integrator/comparison` | 1 | 1 |

### 비교기·슈미트 트리거 — 대표 17문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 슈미트 트리거·히스테리시스 | `comparator-schmitt/schmitt` | 9 | 9 |
| 슈미트 문턱전압·전달특성 | `comparator-schmitt/threshold` | 4 | 4 |
| 전압 비교기·포화출력 | `comparator-schmitt/comparator` | 4 | 4 |

### 발진기 — 대표 37문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| PLL·VCO·주파수합성 | `oscillator/pll` | 3 | 3 |
| 수정발진기 | `oscillator/crystal` | 1 | 1 |
| 빈 브리지 발진기 | `oscillator/wien` | 6 | 6 |
| RC 위상천이 발진기 | `oscillator/phase` | 3 | 3 |
| LC·하틀리·콜피츠·클랩 | `oscillator/lc` | 13 | 13 |
| 발진조건·발진기 비교 | `oscillator/condition` | 11 | 11 |

### 펄스회로·555 타이머 — 대표 5문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 555 비안정·듀티비·시정수 | `pulse-555/555` | 3 | 3 |
| 멀티바이브레이터·안정상태 | `pulse-555/multi` | 2 | 2 |

### 반도체 제조공정 — 대표 1문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 포토리소그래피·포토레지스트 | `fabrication/photo` | 1 | 1 |

### 아날로그 통신 — 대표 15문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| FM 프리엠퍼시스·디엠퍼시스 | `analog-communication/fm-emphasis` | 3 | 3 |
| FM·PM 편이·대역폭 | `analog-communication/fm` | 2 | 2 |
| AM·DSB·SSB·변조도 | `analog-communication/am` | 8 | 8 |
| 변조 목적·통신방식 | `analog-communication/principle` | 2 | 2 |

### 전자기파·안테나·고주파회로 — 대표 8문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 맥스웰 방정식·변위전류 | `rf-electromagnetic/maxwell` | 3 | 3 |
| 전송선로·특성임피던스 | `rf-electromagnetic/line` | 2 | 2 |
| 안테나 길이·전파 | `rf-electromagnetic/antenna` | 1 | 1 |
| 전자기파·파장·전파속도 | `rf-electromagnetic/wave` | 2 | 2 |

### 계측·센서 — 대표 7문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 전압계·전류계·측정오차 | `measurement-sensors/meter` | 5 | 5 |
| 오실로스코프·리사쥬 | `measurement-sensors/scope` | 2 | 2 |


## 디지털회로 — 267문항

### 진법변환·보수연산 — 대표 21문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 보수·부호표현·이진연산 | `number-systems/complement` | 8 | 8 |
| 정수·소수 진법변환 | `number-systems/radix` | 13 | 13 |

### 코드변환 — 대표 12문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| Gray 코드 변환 | `codes-arithmetic/gray` | 6 | 6 |
| Excess-3 코드 | `codes-arithmetic/excess` | 1 | 1 |
| BCD·7세그먼트 | `codes-arithmetic/bcd` | 1 | 1 |
| 코드 종류·특성 비교 | `codes-arithmetic/types` | 4 | 7 |

### 불대수·논리게이트 — 대표 53문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 불대수 법칙·드모르간 | `boolean-gates/algebra` | 9 | 9 |
| NAND·NOR 범용게이트 | `boolean-gates/universal` | 4 | 4 |
| 진리표·타이밍·출력값 | `boolean-gates/truth` | 13 | 13 |
| XOR·XNOR·등가논리 | `boolean-gates/xor` | 6 | 6 |
| 논리회로↔논리식 | `boolean-gates/expression` | 21 | 21 |

### 카르노맵·논리식 간소화 — 대표 43문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 무관항·Don’t care | `minimization-kmap/dontcare` | 6 | 7 |
| 최소항·최대항·정규형 | `minimization-kmap/minterm` | 3 | 3 |
| 카르노맵 간소화 | `minimization-kmap/kmap` | 17 | 17 |
| 불대수식 간소화 | `minimization-kmap/algebra` | 17 | 17 |

### 전자소자 게이트 — 대표 26문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 다이오드 논리·DTL | `logic-families/diode` | 2 | 2 |
| TR 논리·TTL | `logic-families/ttl` | 3 | 3 |
| 팬아웃·잡음여유·소비전력 | `logic-families/fanout` | 3 | 3 |
| CMOS·NMOS 논리회로 | `logic-families/cmos` | 18 | 18 |

### 가산기·감산기·비교기 — 대표 13문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 반가산기 | `arithmetic-circuits/half` | 4 | 4 |
| 전가산기·병렬가산기 | `arithmetic-circuits/full` | 3 | 3 |
| 가감산기·보수연산 회로 | `arithmetic-circuits/addsub` | 2 | 2 |
| 디지털 크기·등가비교기 | `arithmetic-circuits/compare` | 3 | 3 |
| 조합논리회로 기능 비교 | `arithmetic-circuits/overview` | 1 | 2 |

### 인코더·디코더·MUX·DEMUX — 대표 7문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| MUX·논리함수 구현 | `encoder-mux/mux` | 6 | 6 |
| 디코더·출력해석 | `encoder-mux/decoder` | 1 | 3 |
| 인코더·디코더·MUX·DEMUX 비교 | `encoder-mux/selection` | 0 | 1 |

### 플립플롭·래치 — 대표 28문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 셋업·홀드·트리거 | `latch-flipflop/timing` | 2 | 2 |
| 마스터–슬레이브·레이스 | `latch-flipflop/master` | 2 | 2 |
| SR 래치·SR FF | `latch-flipflop/sr` | 4 | 4 |
| JK 플립플롭·타이밍 | `latch-flipflop/jk` | 6 | 7 |
| D 플립플롭·래치 | `latch-flipflop/d` | 6 | 8 |
| T 플립플롭·타이밍 | `latch-flipflop/t` | 1 | 2 |
| 순차회로 상태표·설계 | `latch-flipflop/state` | 7 | 7 |

### 카운터·분주회로 — 대표 12문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 계수범위·필요 FF 수 | `counter/bits` | 3 | 3 |
| 분주·출력주파수 | `counter/divide` | 3 | 3 |
| 카운트 순서·상태표·설계 | `counter/sequence` | 3 | 3 |
| 동기·비동기 카운터 특성 | `counter/types` | 3 | 3 |

### 레지스터·시프트레지스터 — 대표 4문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 순환 시프트 | `register/circular` | 1 | 1 |
| 시프트레지스터·데이터 이동 | `register/shift` | 3 | 3 |

### 메모리 — 대표 2문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| ROM·디코더 | `memory/rom` | 1 | 1 |
| RAM·DRAM·HBM | `memory/ram` | 1 | 1 |

### ADC·DAC — 대표 4문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| R–2R DAC | `adc-dac/r2r` | 1 | 1 |
| 가중저항 DAC·출력전압 | `adc-dac/weighted` | 3 | 3 |

### 오류검출·정정 — 대표 3문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 패리티 검사 | `error-correction/parity` | 1 | 2 |
| 채널부호화·오류정정 | `error-correction/channel` | 1 | 1 |
| 패리티·CRC·FEC·ARQ 비교 | `error-correction/overview` | 1 | 5 |

### 디지털 통신 — 대표 22문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| PCM·표본화·양자화·비트율 | `digital-communication/pcm` | 8 | 8 |
| 라인코드·NRZ·RZ·맨체스터 | `digital-communication/linecode` | 2 | 2 |
| 심벌률·비트율·QAM 계산 | `digital-communication/rate` | 4 | 4 |
| ASK·FSK·PSK·QAM 방식 | `digital-communication/qam` | 7 | 7 |
| 디지털 방송·전송방식 | `digital-communication/broadcast` | 1 | 1 |

### 정보이론·데이터전송 — 대표 7문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| 샤논 채널용량·SNR | `information-data/capacity` | 2 | 2 |
| 영상 데이터량·전송률 | `information-data/image` | 3 | 3 |
| 음성 데이터량·압축·저장 | `information-data/audio` | 2 | 2 |

### 컴퓨터 인터페이스·통신규격 — 대표 1문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| RS-232·직렬통신·처리율 | `mcu-interface/serial` | 1 | 1 |

### 네트워크·프로토콜 — 대표 9문항

| 소분류 | ID | 대표 문항 | 관련 포함 |
|---|---|---:|---:|
| OSI 7계층·기능 | `network-protocol/osi` | 3 | 3 |
| TCP/IP·TCP·UDP | `network-protocol/tcpip` | 3 | 3 |
| 이더넷·LAN 프레임 | `network-protocol/ethernet` | 1 | 1 |
| 교환방식·토폴로지 | `network-protocol/switching` | 2 | 2 |

## 풀이 태그

태그는 소자의 종류와 별개로 무엇을 계산·판별하는지 나타냅니다. 대표 태그는 하나이고 관련 태그는 복수일 수 있습니다.

| 태그 | ID | 관련 문항 |
|---|---|---:|
| 개념·특성 판별 | `concept` | 326 |
| 전압이득 | `voltage-gain` | 56 |
| 전류이득 | `current-gain` | 22 |
| 임피던스·등가저항 | `impedance` | 61 |
| 전력·효율 | `power` | 91 |
| 바이어스·동작점 | `bias` | 69 |
| 온도영향 | `temperature` | 12 |
| 주파수·대역폭 | `frequency` | 122 |
| 출력파형 | `waveform` | 68 |
| 전달함수·응답 | `transfer` | 30 |
| 논리식·진리표 | `logic` | 78 |
| 타이밍·상태변화 | `timing` | 19 |
| 진법·코드변환 | `code` | 33 |
| 전압·전류 계산 | `voltage-current` | 303 |
