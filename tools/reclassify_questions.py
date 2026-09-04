#!/usr/bin/env python3
"""전자공학개론 680문항을 세분화된 복수 중분류 체계로 재분류한다."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
DATA = PROJECT / "data"


def rule(category: str, topic: str, concept: str, *patterns: str) -> tuple:
    return category, topic, concept, tuple(patterns)


RULES = [
    # 회로이론: 포괄 묶음 대신 실제 풀이 단위로 구분한다.
    rule("circuit-theory", "thevenin", "테브난 등가회로", r"테브[난닌넌]", r"thevenin"),
    rule("circuit-theory", "norton", "노턴 등가회로", r"노[턴튼]", r"norton"),
    rule("circuit-theory", "maximum-power", "최대전력", r"최대\s*전력", r"전력\s*전달\s*효율", r"공액\s*정합", r"부하.*정합"),
    rule("circuit-theory", "superposition", "중첩 원리", r"중첩\s*(정리|원리)"),
    rule("circuit-theory", "other-theorems", "밀러·밀만·상반정리", r"밀러\s*(등가|정리)", r"miller\s*(equivalent|theorem)", r"밀만", r"상반\s*정리"),
    rule("circuit-theory", "source-transform", "전원변환", r"전원\s*변환", r"전압원.*전류원", r"전류원.*전압원"),
    rule("circuit-theory", "node-analysis", "노드전압", r"노드\s*(전압|해석)", r"절점\s*(전압|방정식)", r"node\s*voltage", r"슈퍼노드"),
    rule("circuit-theory", "loop-analysis", "루프전류", r"루프\s*(전류|해석)", r"망로\s*전류", r"mesh\s*current", r"슈퍼메시"),
    rule("circuit-theory", "bridge", "브리지 평형", r"휘트스톤", r"브리지\s*(회로|평형)"),
    rule("circuit-theory", "wye-delta", "Y－Δ 변환", r"y\s*[-－]?\s*[△δΔ]", r"[△δΔ]\s*[-－]?\s*y", r"스타.*델타", r"델타.*스타"),
    rule("circuit-theory", "kcl-kvl", "KCL·KVL", r"kcl", r"kvl", r"키르히호프", r"전류\s*법칙", r"전압\s*법칙"),
    rule("circuit-theory", "series-parallel", "직·병렬 등가", r"직렬.*병렬", r"병렬.*직렬", r"등가\s*(저항|커패시턴스|인덕턴스)", r"합성\s*(저항|용량)"),
    rule("circuit-theory", "elements-basics", "R·L·C", r"커패시터와 인덕터", r"정전용량", r"인덕턴스", r"전하량", r"저항률", r"배터리\s*용량"),
    rule("circuit-theory", "transient", "스위칭 과도응답", r"과도\s*(현상|상태)", r"시[정상]\s*수", r"time\s*constant", r"t\s*[=<]\s*0.*스위치", r"스위치.*정상상태", r"충전.*msec", r"방전.*시간"),
    rule("circuit-theory", "sinusoidal-phasor", "정현파·페이저", r"페이저", r"정현파", r"sin\s*\(?\s*\d", r"cos\s*\(?\s*\d", r"각주파수", r"주파수.*주기"),
    rule("circuit-theory", "ac-power", "교류전력·역률", r"역률", r"유효\s*전력", r"무효\s*전력", r"피상\s*전력", r"복소\s*전력", r"v.?rms.*a.?rms"),
    rule("circuit-theory", "resonance", "공진회로", r"공진", r"선택도", r"quality\s*factor", r"q\s*[값계수]", r"대역폭.*공진"),
    rule("circuit-theory", "coupled-transformer", "유도결합·변압기", r"상호\s*인덕턴스", r"결합\s*계수", r"변압기", r"권선수비", r"권선비"),
    rule("circuit-theory", "two-port", "4단자망", r"4\s*단자", r"2\s*단자쌍", r"abcd\s*파라미터", r"전송\s*파라미터", r"[zyh]\s*파라미터"),
    rule("circuit-theory", "distributed-parameter", "특성임피던스", r"분포\s*정수", r"전송\s*선로", r"특성\s*임피던스", r"전파\s*정수", r"무왜형", r"반사\s*계수", r"정재파"),
    rule("circuit-theory", "non-sinusoidal-fourier", "비정현파·푸리에", r"푸리에", r"고조파", r"비정현파", r"파고율", r"파형률", r"실효값.*평균값", r"평균값.*실효값"),
    rule("circuit-theory", "laplace", "라플라스 변환", r"라플라스", r"laplace", r"역변환"),
    rule("circuit-theory", "transfer-response", "전달함수·주파수응답", r"전달\s*함수", r"극점", r"영점", r"보드\s*선도", r"bode", r"주파수\s*응답"),
    rule("circuit-theory", "passive-filter", "수동필터", r"수동\s*필터", r"rc\s*(저역|고역|low|high)", r"직렬\s*rc\s*회로", r"저대역\s*통과.*r.*c"),
    rule("circuit-theory", "three-phase", "3상회로", r"3\s*상", r"삼상", r"평형\s*3", r"선간\s*전압", r"상전압.*선전압"),
    rule("circuit-theory", "electrostatics-field", "전계·전위", r"전계\s*(강도)?", r"전기\s*퍼텐셜", r"전위.*자유공간", r"점\s*전하", r"점\s*전기량", r"쿨롱", r"유전율", r"평행판.*커패시터"),
    rule("circuit-theory", "magnetic-circuit", "자기회로·전자기력", r"자속\s*밀도", r"자기장\s*세기", r"자기\s*저항", r"자속선", r"도선.*자기력", r"두\s*도선.*힘", r"코어.*자속"),
    rule("circuit-theory", "electromagnetic-induction", "전자유도", r"유도\s*기전력", r"패러데이", r"렌츠", r"자속.*변화", r"와전류"),

    # 반도체 소자이론.
    rule("semiconductor", "bands", "에너지대", r"에너지\s*(대|밴드)", r"페르미", r"가전자대", r"전도대", r"밴드갭", r"도체.*절연체.*반도체"),
    rule("semiconductor", "carriers", "캐리어·반도체 물성", r"진성\s*반도체", r"불순물\s*반도체", r"n\s*형", r"p\s*형", r"다수\s*캐리어", r"소수\s*캐리어", r"이동도", r"전도도", r"정공"),
    rule("semiconductor", "phenomena", "반도체 현상", r"드리프트", r"확산\s*전류", r"생성.*재결합", r"재결합", r"홀\s*효과", r"hall\s*effect", r"광전\s*효과", r"열전\s*효과"),
    rule("semiconductor", "pn-junction", "PN 접합", r"pn\s*접합", r"공핍층", r"확산\s*전위", r"built.?in", r"순방향\s*바이어스", r"역방향\s*바이어스", r"접합\s*커패시턴스"),
    rule("semiconductor", "diode-model", "다이오드 특성·모델", r"다이오드.*전류.?전압", r"다이오드.*등가", r"다이오드.*특성", r"순방향\s*전압\s*강하", r"이상적.*다이오드"),
    rule("semiconductor", "special-diodes", "특수 다이오드", r"제너\s*다이오드", r"zener", r"쇼트키", r"터널\s*다이오드", r"버랙터", r"가변\s*용량\s*다이오드"),
    rule("semiconductor", "opto-devices", "광반도체 소자", r"포토\s*다이오드", r"태양\s*전지", r"발광\s*다이오드", r"\bled\b", r"광결합", r"포토\s*트랜지스터"),
    rule("semiconductor", "bjt-device", "BJT 소자이론", r"bjt", r"바이폴라", r"베이스\s*전류", r"컬렉터\s*전류", r"이미터\s*전류", r"활성\s*영역", r"포화\s*영역", r"차단\s*영역", r"전류\s*이득\s*[βb]"),
    rule("semiconductor", "jfet-device", "JFET 소자이론", r"jfet", r"mesfet", r"핀치\s*오프", r"pinch.?off", r"쇼클리\s*방정식"),
    rule("semiconductor", "mosfet-device", "MOSFET 소자이론", r"mosfet", r"문턱\s*전압", r"threshold", r"증가형", r"공핍형", r"채널\s*길이\s*변조"),
    rule("semiconductor", "power-devices", "전력반도체", r"\bscr\b", r"triac", r"diac", r"thyristor", r"사이리스터", r"\bujt\b", r"\bigbt\b"),
    rule("semiconductor", "fabrication", "반도체 공정", r"웨이퍼", r"이온\s*주입", r"산화막", r"반도체\s*공정", r"집적도", r"패키징", r"확산\s*공정", r"포토리소"),

    # 전자회로.
    rule("electronic-circuits", "rectifier-smoothing", "정류·평활", r"반파\s*정류", r"전파\s*정류", r"브리지\s*정류", r"정류\s*회로", r"정류기", r"리플", r"평활"),
    rule("electronic-circuits", "limiter-clipper", "리미터·클리퍼", r"리미터", r"limiter", r"클리퍼", r"clipper", r"제한\s*전압"),
    rule("electronic-circuits", "clamper-multiplier", "클램퍼·배전압", r"클램퍼", r"clamper", r"클램프\s*회로", r"배전압", r"첨두값\s*검출", r"피크\s*검출"),
    rule("electronic-circuits", "zener-regulator", "제너 정전압", r"제너.*정전압", r"제너.*전압\s*조정", r"제너.*부하", r"제너.*레귤"),
    rule("electronic-circuits", "bjt-bias", "BJT 바이어스", r"바이어스\s*회로", r"직류\s*부하선", r"동작점", r"고정\s*바이어스", r"전압\s*분배\s*바이어스", r"vce.*ic", r"컬렉터.*dc\s*전류"),
    rule("electronic-circuits", "bjt-amplifier", "BJT 증폭기", r"공통\s*(이미터|에미터|베이스|컬렉터)", r"이미터\s*(공통|폴로워)", r"emitter\s*follower", r"common.?emitter", r"트랜지스터.*증폭", r"h[ifro]e", r"소신호.*bjt"),
    rule("electronic-circuits", "fet-amplifier", "FET 증폭기", r"공통\s*소스", r"공통\s*드레인", r"공통\s*게이트", r"소스\s*팔로", r"fet.*증폭", r"mosfet.*증폭"),
    rule("electronic-circuits", "amplifier-frequency", "증폭기 주파수특성", r"증폭기.*차단\s*주파수", r"저주파.*고주파", r"밀러\s*효과", r"바이패스\s*커패시터", r"결합\s*커패시터", r"잡음\s*지수", r"왜곡률|왜율"),
    rule("electronic-circuits", "multistage-special", "다단·특수증폭기", r"다단\s*증폭", r"달링턴", r"캐스코드", r"부트스트랩", r"동조\s*증폭"),
    rule("electronic-circuits", "power-amplifier", "전력증폭기", r"전력\s*증폭", r"푸시\s*풀", r"push.?pull", r"[ab c]{1,2}\s*급\s*증폭", r"컬렉터\s*효율"),
    rule("electronic-circuits", "differential-mirror", "차동증폭기·전류미러", r"차동\s*증폭", r"차동\s*이득", r"cmrr", r"동상\s*제거", r"전류\s*미러"),
    rule("electronic-circuits", "feedback-amplifier", "부귀환증폭기", r"부귀환", r"음귀환", r"feedback", r"귀환\s*증폭", r"폐루프\s*이득"),
    rule("electronic-circuits", "opamp-basics", "연산증폭기 기초", r"이상적.*op.?amp", r"이상적.*연산증폭기", r"가상\s*(단락|접지)", r"슬루율", r"slew\s*rate", r"op.?amp.*입력\s*저항"),
    rule("electronic-circuits", "opamp-operations", "연산증폭기 연산회로", r"반전\s*증폭", r"비반전\s*증폭", r"가산\s*회로", r"감산\s*회로", r"적분기", r"미분기", r"전압\s*추종", r"연산\s*회로", r"op.?amp.*출력"),
    rule("electronic-circuits", "comparator-schmitt", "비교기·슈미트 트리거", r"비교기", r"comparator", r"슈미트", r"schmitt", r"히스테리시스", r"트리거\s*기준\s*전압", r"영교차"),
    rule("electronic-circuits", "active-filter", "능동필터", r"능동\s*필터", r"op.?amp.*(저역|고역|대역)", r"저대역\s*통과\s*필터", r"고대역\s*통과\s*필터"),
    rule("electronic-circuits", "oscillator", "발진회로", r"발진기", r"발진\s*회로", r"발진\s*조건", r"콜피츠", r"하틀리", r"wien", r"수정\s*발진", r"위상\s*(천이|편이).*발진"),
    rule("electronic-circuits", "pulse-555", "펄스회로·555", r"555", r"멀티\s*바이브레이터", r"단안정", r"비안정", r"구형파\s*발생", r"펄스\s*발생"),
    rule("electronic-circuits", "power-supply-regulator", "전원·전압조정", r"전압\s*조정기", r"전압\s*레귤", r"선형\s*전압", r"스위칭\s*전원", r"dc.?dc", r"벅\s*컨버터", r"부스트\s*컨버터", r"정전압\s*출력"),
    rule("electronic-circuits", "amplifier-basics", "증폭기 기초특성", r"전압\s*증폭도", r"전압\s*이득\s*\[?db", r"입력\s*(저항|임피던스).*출력\s*(저항|임피던스)", r"증폭기.*임피던스\s*정합", r"감쇄기"),
    rule("electronic-circuits", "signals-systems", "신호·시스템", r"선형\s*시불변", r"lti", r"임펄스\s*응답", r"컨볼루션|convolution", r"이산\s*시스템", r"표본화.*에일리어싱", r"aliasing"),
    rule("electronic-circuits", "control-systems", "제어공학", r"신호\s*흐름도", r"메이슨", r"폐루프\s*제어", r"특성\s*방정식.*안정", r"루스", r"routh", r"제어\s*(계통|시스템)"),
    rule("electronic-circuits", "analog-communication", "아날로그 변복조", r"진폭\s*변조", r"주파수\s*변조", r"위상\s*변조", r"\bam\b", r"\bfm\b", r"dsb", r"ssb", r"변조\s*지수", r"변조도", r"프리\s*엠퍼시스", r"디엠퍼시스", r"반송파"),
    rule("electronic-circuits", "rf-antenna", "안테나·전파", r"안테나", r"무선\s*전파", r"광섬유", r"동축\s*케이블"),
    rule("electronic-circuits", "electromagnetic-waves", "전자기파·전파전파", r"전자기파", r"맥스웰", r"굴절률.*전파", r"전파\s*속도", r"편파"),
    rule("electronic-circuits", "measurement-sensors", "계측·센서", r"전압계", r"전류계", r"멀티미터", r"오실로스코프", r"계측", r"센서", r"서미스터", r"스트레인\s*게이지"),

    # 디지털공학.
    rule("digital-engineering", "number-systems", "수 체계·진법변환", r"진수", r"진법", r"십진수.*이진수", r"이진수.*십진수", r"2\s*진", r"8\s*진", r"16\s*진"),
    rule("digital-engineering", "codes-arithmetic", "코드·2진연산", r"보수", r"gray|그레이", r"\bbcd\b", r"ascii", r"해밍\s*코드", r"2진\s*연산"),
    rule("digital-engineering", "minimization-kmap", "논리식 최소화·카르노맵", r"카르노", r"karnaugh", r"최소항", r"최대항", r"don.?t\s*care", r"간략화|최소화"),
    rule("digital-engineering", "logic-families", "논리군·전기적 특성", r"\bttl\b", r"cmos.*(논리|인버터)", r"팬\s*(인|아웃)", r"fan.?out", r"잡음\s*여유", r"전달\s*지연", r"논리\s*군"),
    rule("digital-engineering", "arithmetic-circuits", "산술회로", r"전가산기", r"반가산기", r"가산기", r"감산기", r"\balu\b"),
    rule("digital-engineering", "encoder-decoder", "인코더·디코더", r"인코더", r"encoder", r"디코더", r"decoder"),
    rule("digital-engineering", "mux-demux", "멀티플렉서·디멀티플렉서", r"멀티플렉서", r"multiplexer", r"\bmux\b", r"디멀티플렉서", r"demultiplexer"),
    rule("digital-engineering", "other-combinational", "기타 조합논리", r"패리티", r"디지털\s*비교기", r"코드\s*변환기"),
    rule("digital-engineering", "latch-flipflop", "래치·플립플롭", r"플립\s*-?\s*플롭", r"flip.?flop", r"\b[rsjkdt]-?ff\b", r"d\s*래치", r"래치", r"여기표", r"레이스\s*현상"),
    rule("digital-engineering", "counter", "카운터", r"카운터", r"counter", r"계수기", r"분주", r"존슨\s*카운터", r"링\s*카운터"),
    rule("digital-engineering", "register", "레지스터", r"시프트\s*레지스터", r"shift\s*register", r"레지스터", r"직렬.*병렬\s*변환"),
    rule("digital-engineering", "memory", "메모리", r"메모리", r"memory", r"\brom\b", r"\bram\b", r"sram", r"dram", r"hbm", r"플래시"),
    rule("digital-engineering", "pld-fpga", "PLD·FPGA", r"\bpld\b", r"\bpla\b", r"\bpal\b", r"cpld", r"fpga"),
    rule("digital-engineering", "adc-dac", "ADC·DAC", r"\badc\b", r"\bdac\b", r"a/d", r"d/a", r"양자화", r"분해능", r"r\s*-?\s*2r", r"아날로그.*디지털.*변환"),
    rule("digital-engineering", "microprocessor", "마이크로프로세서", r"마이크로\s*프로세서", r"microprocessor", r"\bcpu\b", r"주소\s*버스", r"명령\s*처리"),
    rule("digital-engineering", "mcu-interface", "MCU·인터페이스", r"마이크로\s*컨트롤러", r"아두이노|arduino", r"rs\s*-?\s*232", r"uart", r"\bspi\b", r"i2c", r"직렬\s*통신", r"병렬\s*전송"),
    rule("digital-engineering", "digital-communication", "디지털 변복조·PCM", r"\bask\b", r"\bfsk\b", r"\bpsk\b", r"qpsk", r"bpsk", r"qam", r"펄스\s*코드\s*변조", r"\bpcm\b", r"심볼\s*(속도|전송률)", r"비트\s*오류", r"ber"),
    rule("digital-engineering", "information-data", "정보이론·데이터통신", r"채널\s*용량", r"샤논|shannon", r"나이퀴스트", r"신호대\s*잡음", r"snr", r"최소\s*비트율", r"데이터\s*(속도|전송률|전송속도)", r"화소.*전송"),
    rule("digital-engineering", "network-protocol", "네트워크 프로토콜", r"osi\s*7", r"데이터\s*링크\s*계층", r"네트워크\s*계층", r"전송\s*계층", r"\btcp\b", r"\budp\b", r"\bftp\b", r"인터넷\s*프로토콜", r"라우팅"),
    rule("digital-engineering", "boolean-gates", "불대수·논리게이트", r"부울|불대수|boolean", r"드모르간", r"논리\s*함수", r"논리식", r"nand|nor|xor|xnor", r"논리\s*게이트", r"출력\s*[fy].*입력\s*[ab]"),
]


OLD_TOPIC_FALLBACK = {
    "basic-laws": ("circuit-theory", "elements-basics"), "coupled": ("circuit-theory", "coupled-transformer"),
    "laplace": ("circuit-theory", "laplace"), "network-theorems": ("circuit-theory", "thevenin"),
    "non-sinusoidal": ("circuit-theory", "non-sinusoidal-fourier"), "resonance": ("circuit-theory", "resonance"),
    "sinusoidal": ("circuit-theory", "sinusoidal-phasor"), "transfer-function": ("circuit-theory", "transfer-response"),
    "transient": ("circuit-theory", "transient"), "two-port": ("circuit-theory", "two-port"),
    "bands": ("semiconductor", "bands"), "materials": ("semiconductor", "carriers"),
    "phenomena": ("semiconductor", "phenomena"), "pn-junction": ("semiconductor", "pn-junction"),
    "diode-devices": ("semiconductor", "special-diodes"), "bjt-device": ("semiconductor", "bjt-device"),
    "fet-device": ("semiconductor", "mosfet-device"), "power-devices": ("semiconductor", "power-devices"),
    "fabrication": ("semiconductor", "fabrication"), "diode-applications": ("electronic-circuits", "rectifier-smoothing"),
    "bjt-bias": ("electronic-circuits", "bjt-bias"), "bjt-amplifiers": ("electronic-circuits", "bjt-amplifier"),
    "fet-amplifiers": ("electronic-circuits", "fet-amplifier"), "frequency-response": ("electronic-circuits", "amplifier-frequency"),
    "power-amplifiers": ("electronic-circuits", "power-amplifier"), "feedback": ("electronic-circuits", "feedback-amplifier"),
    "op-amp": ("electronic-circuits", "opamp-operations"), "oscillators": ("electronic-circuits", "oscillator"),
    "pulse-circuits": ("electronic-circuits", "pulse-555"), "number-systems": ("digital-engineering", "number-systems"),
    "boolean": ("digital-engineering", "boolean-gates"), "logic-families": ("digital-engineering", "logic-families"),
    "combinational": ("digital-engineering", "other-combinational"), "converters": ("digital-engineering", "adc-dac"),
    "sequential": ("digital-engineering", "latch-flipflop"), "registers-counters": ("digital-engineering", "register"),
    "memory-pld": ("digital-engineering", "memory"), "processor": ("digital-engineering", "microprocessor"),
    "mcu-interface": ("digital-engineering", "mcu-interface"),
}


ID_OVERRIDES = {
    # OCR만으로 회로 형태를 판별하기 어려운 문항은 문제 이미지를 대조해 지정한다.
    "national-2007-08": ("circuit-theory", ["node-analysis"]),
    "national-2007-12": ("electronic-circuits", ["opamp-operations"]),
    "national-2007-18": ("circuit-theory", ["transient"]),
    "national-2007-04": ("digital-engineering", ["boolean-gates"]),
    "national-2007-09": ("electronic-circuits", ["power-supply-regulator"]),
    "national-2007-11": ("circuit-theory", ["kcl-kvl"]),
    "national-2008-12": ("digital-engineering", ["boolean-gates"]),
    "national-2008-18": ("electronic-circuits", ["clamper-multiplier"]),
    "national-2008-19": ("circuit-theory", ["transient"]),
    "national-2008-11": ("circuit-theory", ["dc-steady-state"]),
    "national-2009-16": ("circuit-theory", ["transient"]),
    "national-2009-18": ("circuit-theory", ["transient"]),
    "national-2009-09": ("digital-engineering", ["mux-demux"]),
    "local-2009-02": ("electronic-circuits", ["bjt-amplifier"]),
    "local-2009-12": ("circuit-theory", ["dc-steady-state"]),
    "local-2009-20": ("circuit-theory", ["series-parallel"]),
    "military-2022-07": ("circuit-theory", ["transient"]),
    "national-2026-07": ("circuit-theory", ["transient"]),
    "military-2026-09": ("circuit-theory", ["transient"]),
    "national-2012-07": ("digital-engineering", ["latch-flipflop", "register"]),
    # 선지의 '변압기'가 아니라 선형·스위칭 조정기의 특성 비교가 핵심이다.
    "national-2011-05": ("electronic-circuits", ["power-supply-regulator"]),
    "national-2011-10": ("electronic-circuits", ["clamper-multiplier"]),
    "national-2011-11": ("digital-engineering", ["information-data"]),
    "national-2010-02": ("electronic-circuits", ["bjt-bias"]),
    "national-2010-01": ("electronic-circuits", ["opamp-operations"]),
    "national-2010-03": ("electronic-circuits", ["bjt-bias"]),
    "local-2010-19": ("circuit-theory", ["sinusoidal-phasor", "series-parallel"]),
    "local-2010-06": ("circuit-theory", ["sinusoidal-phasor"]),
    "national-2011-03": ("circuit-theory", ["ac-power"]),
    "national-2011-07": ("electronic-circuits", ["opamp-operations", "limiter-clipper"]),
    "national-2011-09": ("semiconductor", ["bjt-device"]),
    "local-2012-16": ("electronic-circuits", ["limiter-clipper"]),
    "national-2012-08": ("circuit-theory", ["node-analysis"]),
    "national-2013-08": ("electronic-circuits", ["clamper-multiplier"]),
    "national-2013-18": ("electronic-circuits", ["rectifier-smoothing"]),
    "national-2014-12": ("digital-engineering", ["boolean-gates"]),
    "national-2014-10": ("electronic-circuits", ["opamp-operations"]),
    "national-2015-14": ("digital-engineering", ["information-data"]),
    "national-2017-01": ("digital-engineering", ["boolean-gates"]),
    "national-2017-08": ("circuit-theory", ["passive-filter"]),
    "national-2017-10": ("circuit-theory", ["elements-basics"]),
    "national-2017-20": ("circuit-theory", ["transfer-response", "passive-filter"]),
    "national-2018-08": ("electronic-circuits", ["amplifier-frequency"]),
    "national-2018-13": ("electronic-circuits", ["oscillator"]),
    "national-2018-10": ("electronic-circuits", ["power-supply-regulator"]),
    "national-2024-08": ("electronic-circuits", ["power-supply-regulator"]),
    "national-2020-02": ("circuit-theory", ["source-transform"]),
    "national-2016-07": ("circuit-theory", ["sinusoidal-phasor"]),
    "national-2016-17": ("electronic-circuits", ["fet-amplifier"]),
    "national-2019-04": ("electronic-circuits", ["bjt-bias"]),
    "national-2019-14": ("circuit-theory", ["series-parallel"]),
    "national-2016-09": ("electronic-circuits", ["zener-regulator"]),
    "national-2016-10": ("circuit-theory", ["superposition"]),
    "national-2017-03": ("electronic-circuits", ["opamp-operations"]),
    "national-2017-04": ("electronic-circuits", ["amplifier-frequency"]),
    "national-2021-13": ("digital-engineering", ["network-protocol"]),
    "military-2022-01": ("circuit-theory", ["magnetic-circuit"]),
    "military-2022-05": ("circuit-theory", ["transfer-response"]),
    "military-2022-15": ("circuit-theory", ["elements-basics"]),
    "military-2022-17": ("circuit-theory", ["elements-basics"]),
    "military-2022-18": ("circuit-theory", ["elements-basics"]),
    "military-2022-10": ("electronic-circuits", ["amplifier-frequency"]),
    "military-2022-06": ("semiconductor", ["opto-devices"]),
    "military-2022-08": ("electronic-circuits", ["opamp-operations"]),
    "military-2023-12": ("circuit-theory", ["elements-basics"]),
    "military-2023-13": ("electronic-circuits", ["bjt-bias"]),
    "military-2023-15": ("electronic-circuits", ["power-amplifier"]),
    "military-2023-17": ("circuit-theory", ["maximum-power"]),
    "military-2023-20": ("circuit-theory", ["series-parallel"]),
    "military-2023-05": ("circuit-theory", ["passive-filter"]),
    "local-2023-01": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "local-2023-12": ("electronic-circuits", ["fet-amplifier"]),
    "local-2023-15": ("electronic-circuits", ["amplifier-frequency"]),
    "national-2023-18": ("electronic-circuits", ["opamp-operations"]),
    "local-2022-18": ("electronic-circuits", ["active-filter"]),
    "national-2024-14": ("electronic-circuits", ["amplifier-frequency"]),
    "national-2024-03": ("electronic-circuits", ["power-supply-regulator"]),
    "national-2024-16": ("circuit-theory", ["transient"]),
    "military-2024-08": ("circuit-theory", ["series-parallel"]),
    "military-2024-09": ("circuit-theory", ["ac-power"]),
    "local-2024-19": ("digital-engineering", ["logic-families"]),
    "national-2025-04": ("circuit-theory", ["passive-filter"]),
    "national-2025-09": ("electronic-circuits", ["active-filter"]),
    "national-2025-17": ("digital-engineering", ["network-protocol"]),
    "military-2025-03": ("circuit-theory", ["magnetic-circuit"]),
    "military-2025-16": ("circuit-theory", ["elements-basics"]),
    "military-2025-18": ("electronic-circuits", ["bjt-bias"]),
    "local-2025-19": ("circuit-theory", ["maximum-power"]),
    "national-2026-03": ("digital-engineering", ["network-protocol"]),
    "national-2026-15": ("electronic-circuits", ["amplifier-frequency"]),
    "military-2026-16": ("circuit-theory", ["magnetic-circuit"]),
    "military-2026-11": ("circuit-theory", ["elements-basics"]),
    "military-2026-13": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "local-2026-09": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "local-2026-17": ("digital-engineering", ["boolean-gates"]),
    "local-2026-11": ("circuit-theory", ["source-transform"]),
    "military-2026-10": ("circuit-theory", ["series-parallel", "elements-basics"]),
    "military-2026-12": ("circuit-theory", ["thevenin"]),

    # 국회직·서울시 선작업 420문제 중 OCR만으로 구분되지 않은 문항.
    "assembly-2009-06": ("circuit-theory", ["elements-basics"]),
    "assembly-2009-08": ("circuit-theory", ["magnetic-circuit"]),
    "assembly-2009-16": ("circuit-theory", ["node-analysis"]),
    "assembly-2014-10": ("electronic-circuits", ["clamper-multiplier"]),
    "seoul-2014-06": ("digital-engineering", ["information-data"]),
    "seoul-2014-08": ("circuit-theory", ["node-analysis"]),
    "seoul-2014-09": ("circuit-theory", ["sinusoidal-phasor"]),
    "seoul-2014-16": ("circuit-theory", ["electrostatics-field"]),
    "seoul-2015-08": ("electronic-circuits", ["control-systems"]),
    "seoul-2016-13": ("electronic-circuits", ["opamp-operations"]),
    "seoul-2016-16": ("circuit-theory", ["electrostatics-field"]),
    "seoul-2016-19": ("circuit-theory", ["bridge"]),
    "assembly-2017-17": ("digital-engineering", ["logic-families"]),
    "seoul-2017-03": ("circuit-theory", ["maximum-power"]),
    "seoul-2017-04": ("circuit-theory", ["series-parallel"]),
    "seoul-2017-05": ("digital-engineering", ["number-systems"]),
    "seoul-2017-13": ("circuit-theory", ["transient"]),
    "seoul-2017-17": ("circuit-theory", ["electromagnetic-induction"]),
    "seoul-2017-20": ("electronic-circuits", ["differential-mirror"]),
    "assembly-2018-17": ("circuit-theory", ["sinusoidal-phasor"]),
    "seoul-2018-14": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "assembly-2019-05": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "assembly-2019-08": ("semiconductor", ["carriers"]),
    "assembly-2019-09": ("semiconductor", ["fabrication"]),
    "assembly-2019-15": ("circuit-theory", ["node-analysis"]),
    "assembly-2019-18": ("circuit-theory", ["maximum-power"]),
    "seoul-2019-04": ("circuit-theory", ["magnetic-circuit"]),
    "seoul-2019-06": ("circuit-theory", ["node-analysis"]),
    "seoul-2019-11": ("circuit-theory", ["passive-filter"]),
    "seoul-2019-13": ("circuit-theory", ["resonance"]),
    "assembly-2020-02": ("digital-engineering", ["counter"]),
    "assembly-2020-05": ("circuit-theory", ["series-parallel", "elements-basics"]),
    "assembly-2020-06": ("electronic-circuits", ["electromagnetic-waves"]),
    "assembly-2020-12": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2020-17": ("digital-engineering", ["boolean-gates"]),
    "seoul-2020-01": ("circuit-theory", ["elements-basics"]),
    "seoul-2020-05": ("circuit-theory", ["magnetic-circuit"]),
    "seoul-2020-13": ("digital-engineering", ["latch-flipflop"]),
    "seoul-2020-19": ("electronic-circuits", ["oscillator", "opamp-operations"]),
    "assembly-2021-10": ("electronic-circuits", ["bjt-bias"]),
    "seoul-2021-03": ("circuit-theory", ["node-analysis"]),
    "seoul-2021-10": ("electronic-circuits", ["control-systems"]),
    "seoul-2021-11": ("circuit-theory", ["series-parallel"]),
    "seoul-2021-13": ("circuit-theory", ["magnetic-circuit"]),
    "seoul-2021-14": ("circuit-theory", ["passive-filter"]),
    "assembly-2022-06": ("circuit-theory", ["two-port"]),
    "assembly-2022-07": ("electronic-circuits", ["active-filter"]),
    "assembly-2022-15": ("digital-engineering", ["boolean-gates"]),
    "assembly-2022-19": ("electronic-circuits", ["feedback-amplifier"]),
    "assembly-2022-20": ("electronic-circuits", ["electromagnetic-waves"]),
    "assembly-2023-04": ("digital-engineering", ["digital-communication"]),
    "assembly-2023-14": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2024-12": ("electronic-circuits", ["signals-systems"]),
    "assembly-2025-09": ("digital-engineering", ["minimization-kmap"]),
    "assembly-2025-10": ("digital-engineering", ["number-systems"]),
    "assembly-2025-12": ("semiconductor", ["carriers"]),
    "assembly-2025-14": ("electronic-circuits", ["bjt-amplifier"]),
    "assembly-2025-18": ("electronic-circuits", ["zener-regulator"]),

    # 국회직·서울시 자동분류 교차검토 보정.
    "assembly-2009-02": ("circuit-theory", ["other-theorems"]),
    "assembly-2009-05": ("electronic-circuits", ["opamp-operations"]),
    "assembly-2009-10": ("circuit-theory", ["non-sinusoidal-fourier", "ac-power"]),
    "assembly-2009-12": ("electronic-circuits", ["rectifier-smoothing"]),
    "assembly-2009-18": ("electronic-circuits", ["limiter-clipper"]),
    "assembly-2014-03": ("circuit-theory", ["node-analysis"]),
    "assembly-2014-06": ("digital-engineering", ["encoder-decoder"]),
    "assembly-2014-07": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2014-08": ("electronic-circuits", ["power-supply-regulator"]),
    "assembly-2014-11": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2014-12": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2014-14": ("circuit-theory", ["series-parallel"]),
    "assembly-2014-19": ("electronic-circuits", ["oscillator"]),
    "assembly-2015-03": ("semiconductor", ["mosfet-device"]),
    "assembly-2015-04": ("circuit-theory", ["node-analysis"]),
    "assembly-2015-09": ("electronic-circuits", ["fet-amplifier"]),
    "assembly-2015-15": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2015-18": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2016-01": ("semiconductor", ["special-diodes"]),
    "assembly-2016-03": ("electronic-circuits", ["fet-amplifier"]),
    "assembly-2016-07": ("circuit-theory", ["electrostatics-field"]),
    "assembly-2016-17": ("electronic-circuits", ["amplifier-frequency"]),
    "assembly-2016-20": ("electronic-circuits", ["limiter-clipper"]),
    "assembly-2017-01": ("electronic-circuits", ["rectifier-smoothing"]),
    "assembly-2017-16": ("electronic-circuits", ["feedback-amplifier"]),
    "assembly-2017-15": ("circuit-theory", ["node-analysis"]),
    "assembly-2017-20": ("semiconductor", ["mosfet-device"]),
    "assembly-2018-04": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2018-05": ("electronic-circuits", ["clamper-multiplier"]),
    "assembly-2018-09": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "assembly-2018-13": ("electronic-circuits", ["limiter-clipper"]),
    "assembly-2018-15": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2018-20": ("digital-engineering", ["codes-arithmetic", "number-systems"]),
    "assembly-2019-03": ("digital-engineering", ["counter", "latch-flipflop"]),
    "assembly-2019-06": ("circuit-theory", ["electrostatics-field"]),
    "assembly-2019-07": ("circuit-theory", ["electrostatics-field"]),
    "assembly-2019-12": ("circuit-theory", ["bridge"]),
    "assembly-2019-13": ("circuit-theory", ["coupled-transformer", "maximum-power"]),
    "assembly-2020-09": ("digital-engineering", ["counter"]),
    "assembly-2020-10": ("circuit-theory", ["transient"]),
    "assembly-2020-11": ("circuit-theory", ["maximum-power"]),
    "assembly-2020-13": ("circuit-theory", ["node-analysis"]),
    "assembly-2020-14": ("electronic-circuits", ["limiter-clipper"]),
    "assembly-2020-15": ("semiconductor", ["pn-junction", "diode-model"]),
    "assembly-2020-16": ("electronic-circuits", ["rectifier-smoothing", "power-supply-regulator"]),
    "assembly-2021-01": ("circuit-theory", ["node-analysis"]),
    "assembly-2021-04": ("electronic-circuits", ["bjt-amplifier"]),
    "assembly-2021-08": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2021-14": ("electronic-circuits", ["fet-amplifier"]),
    "assembly-2021-15": ("circuit-theory", ["source-transform"]),
    "assembly-2021-16": ("electronic-circuits", ["fet-amplifier"]),
    "assembly-2022-02": ("circuit-theory", ["coupled-transformer", "maximum-power"]),
    "assembly-2022-03": ("circuit-theory", ["transfer-response", "passive-filter"]),
    "assembly-2022-08": ("electronic-circuits", ["limiter-clipper", "zener-regulator"]),
    "assembly-2022-10": ("electronic-circuits", ["clamper-multiplier", "opamp-operations"]),
    "assembly-2022-12": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2022-16": ("electronic-circuits", ["opamp-basics"]),
    "assembly-2022-18": ("electronic-circuits", ["electromagnetic-waves"]),
    "assembly-2023-02": ("digital-engineering", ["counter", "latch-flipflop"]),
    "assembly-2023-03": ("digital-engineering", ["digital-communication"]),
    "assembly-2023-12": ("semiconductor", ["bjt-device"]),
    "assembly-2023-15": ("circuit-theory", ["electrostatics-field"]),
    "assembly-2023-17": ("semiconductor", ["phenomena"]),
    "assembly-2023-19": ("circuit-theory", ["sinusoidal-phasor"]),
    "assembly-2024-01": ("circuit-theory", ["maximum-power"]),
    "assembly-2024-02": ("electronic-circuits", ["active-filter", "opamp-operations"]),
    "assembly-2024-05": ("circuit-theory", ["source-transform"]),
    "assembly-2024-06": ("electronic-circuits", ["limiter-clipper"]),
    "assembly-2024-07": ("electronic-circuits", ["opamp-operations"]),
    "assembly-2024-08": ("electronic-circuits", ["rectifier-smoothing"]),
    "assembly-2024-11": ("electronic-circuits", ["signals-systems"]),
    "assembly-2024-16": ("circuit-theory", ["node-analysis"]),
    "assembly-2024-20": ("circuit-theory", ["passive-filter", "sinusoidal-phasor"]),
    "assembly-2025-01": ("electronic-circuits", ["opamp-basics"]),
    "assembly-2025-02": ("electronic-circuits", ["opamp-operations", "multistage-special"]),
    "assembly-2025-06": ("circuit-theory", ["norton"]),
    "assembly-2025-07": ("circuit-theory", ["transient"]),
    "assembly-2025-11": ("digital-engineering", ["boolean-gates"]),
    "assembly-2025-13": ("electronic-circuits", ["opamp-operations"]),
    "assembly-2025-16": ("circuit-theory", ["two-port"]),
    "assembly-2025-17": ("electronic-circuits", ["bjt-bias"]),
    "assembly-2025-19": ("electronic-circuits", ["electromagnetic-waves"]),

    "seoul-2014-03": ("digital-engineering", ["mux-demux"]),
    "seoul-2014-07": ("semiconductor", ["mosfet-device"]),
    "seoul-2014-11": ("digital-engineering", ["boolean-gates"]),
    "seoul-2015-02": ("circuit-theory", ["sinusoidal-phasor"]),
    "seoul-2015-03": ("electronic-circuits", ["zener-regulator"]),
    "seoul-2015-06": ("electronic-circuits", ["power-amplifier"]),
    "seoul-2015-07": ("digital-engineering", ["codes-arithmetic", "number-systems"]),
    "seoul-2015-10": ("electronic-circuits", ["opamp-basics"]),
    "seoul-2015-11": ("circuit-theory", ["magnetic-circuit"]),
    "seoul-2015-12": ("electronic-circuits", ["bjt-amplifier"]),
    "seoul-2015-13": ("circuit-theory", ["node-analysis"]),
    "seoul-2016-02": ("circuit-theory", ["maximum-power"]),
    "seoul-2016-03": ("circuit-theory", ["node-analysis"]),
    "seoul-2016-06": ("electronic-circuits", ["bjt-amplifier", "bjt-bias"]),
    "seoul-2016-08": ("electronic-circuits", ["bjt-bias"]),
    "seoul-2016-10": ("semiconductor", ["bjt-device"]),
    "seoul-2016-11": ("semiconductor", ["pn-junction"]),
    "seoul-2016-12": ("electronic-circuits", ["opamp-operations"]),
    "seoul-2017-01": ("electronic-circuits", ["bjt-amplifier", "multistage-special"]),
    "seoul-2017-02": ("electronic-circuits", ["active-filter", "opamp-operations"]),
    "seoul-2017-07": ("circuit-theory", ["series-parallel"]),
    "seoul-2017-08": ("circuit-theory", ["series-parallel"]),
    "seoul-2017-10": ("semiconductor", ["mosfet-device"]),
    "seoul-2017-11": ("electronic-circuits", ["bjt-amplifier"]),
    "seoul-2017-16": ("circuit-theory", ["dc-steady-state"]),
    "seoul-2014-14": ("circuit-theory", ["distributed-parameter"]),
    "seoul-2018-03": ("electronic-circuits", ["control-systems"]),
    "seoul-2018-06": ("electronic-circuits", ["active-filter", "opamp-operations"]),
    "seoul-2018-07": ("electronic-circuits", ["rectifier-smoothing"]),
    "seoul-2018-11": ("circuit-theory", ["electromagnetic-induction"]),
    "seoul-2018-13": ("circuit-theory", ["node-analysis"]),
    "seoul-2018-16": ("circuit-theory", ["transient"]),
    "seoul-2018-17": ("electronic-circuits", ["signals-systems"]),
    "seoul-2018-18": ("electronic-circuits", ["signals-systems"]),
    "seoul-2019-05": ("semiconductor", ["phenomena"]),
    "seoul-2019-08": ("semiconductor", ["pn-junction"]),
    "seoul-2019-09": ("digital-engineering", ["arithmetic-circuits"]),
    "seoul-2019-14": ("circuit-theory", ["transient"]),
    "seoul-2019-16": ("electronic-circuits", ["bjt-amplifier"]),
    "seoul-2019-17": ("semiconductor", ["bjt-device"]),
    "seoul-2020-08": ("electronic-circuits", ["opamp-operations"]),
    "seoul-2020-09": ("circuit-theory", ["transfer-response", "passive-filter"]),
    "seoul-2020-10": ("electronic-circuits", ["opamp-operations"]),
    "seoul-2020-11": ("semiconductor", ["special-diodes"]),
    "seoul-2020-12": ("circuit-theory", ["series-parallel"]),
    "seoul-2020-15": ("electronic-circuits", ["opamp-operations"]),
    "seoul-2020-17": ("electronic-circuits", ["oscillator"]),
    "seoul-2021-01": ("circuit-theory", ["coupled-transformer"]),
    "seoul-2021-05": ("electronic-circuits", ["bjt-amplifier"]),
    "seoul-2021-09": ("electronic-circuits", ["differential-mirror"]),
    "seoul-2021-15": ("digital-engineering", ["other-combinational", "boolean-gates"]),
    "seoul-2021-16": ("electronic-circuits", ["comparator-schmitt", "opamp-operations"]),
    "seoul-2021-20": ("electronic-circuits", ["comparator-schmitt", "limiter-clipper"]),
}

# 1,100문항 전수 교차검토(문제 이미지·OCR·기존 분류) 결과.
# 자동 규칙이 회로의 주변 소자나 선지 문구를 핵심 개념으로 오인한 문항을
# 실제 풀이에 필요한 중분류 기준으로 고정한다.
ID_OVERRIDES.update({
    # 회로이론 및 회로 응용.
    "national-2008-03": ("circuit-theory", ["sinusoidal-phasor", "ac-power"]),
    "national-2008-17": ("circuit-theory", ["passive-filter"]),
    "local-2011-06": ("electronic-circuits", ["oscillator"]),
    "national-2013-09": ("circuit-theory", ["transfer-response"]),
    "national-2014-19": ("circuit-theory", ["non-sinusoidal-fourier"]),
    "national-2016-14": ("circuit-theory", ["resonance"]),
    "national-2016-16": ("electronic-circuits", ["oscillator"]),
    "national-2019-13": ("electronic-circuits", ["rectifier-smoothing"]),
    "national-2023-13": ("electronic-circuits", ["oscillator"]),
    "assembly-2024-05": ("circuit-theory", ["thevenin"]),
    "military-2024-11": ("circuit-theory", ["coupled-transformer", "ac-power"]),
    "military-2024-15": ("electronic-circuits", ["rectifier-smoothing"]),
    "military-2024-20": ("circuit-theory", ["laplace"]),
    "local-2024-07": ("electronic-circuits", ["oscillator"]),
    "military-2025-02": ("circuit-theory", ["passive-filter"]),
    "military-2025-16": ("circuit-theory", ["electrostatics-field"]),
    "local-2025-05": ("circuit-theory", ["resonance"]),
    "local-2025-09": ("electronic-circuits", ["rectifier-smoothing"]),
    "local-2026-07": ("circuit-theory", ["series-parallel", "elements-basics"]),
    "military-2026-19": ("circuit-theory", ["series-parallel"]),
    "national-2026-20": ("electronic-circuits", ["active-filter"]),

    # 다이오드 응용 및 연산증폭기.
    "national-2008-02": ("electronic-circuits", ["zener-regulator"]),
    "national-2008-08": ("electronic-circuits", ["opamp-operations"]),
    "national-2008-16": ("electronic-circuits", ["active-filter", "opamp-operations"]),
    "national-2009-10": ("electronic-circuits", ["limiter-clipper"]),
    "national-2009-12": ("electronic-circuits", ["active-filter", "opamp-operations"]),
    "local-2009-15": ("electronic-circuits", ["rectifier-smoothing"]),
    "local-2010-05": ("electronic-circuits", ["opamp-operations"]),
    "national-2011-06": ("electronic-circuits", ["opamp-operations"]),
    "national-2011-13": ("electronic-circuits", ["limiter-clipper", "opamp-operations"]),
    "local-2012-08": ("electronic-circuits", ["limiter-clipper"]),
    "local-2012-14": ("electronic-circuits", ["opamp-operations"]),
    "national-2013-16": ("electronic-circuits", ["opamp-operations"]),
    "national-2014-02": ("semiconductor", ["diode-model"]),
    "assembly-2014-15": ("electronic-circuits", ["amplifier-frequency", "active-filter"]),
    "assembly-2015-16": ("electronic-circuits", ["opamp-operations"]),
    "national-2020-14": ("electronic-circuits", ["limiter-clipper", "opamp-operations"]),
    "military-2023-19": ("electronic-circuits", ["rectifier-smoothing"]),
    "military-2024-13": ("electronic-circuits", ["opamp-operations"]),
    "military-2025-17": ("electronic-circuits", ["limiter-clipper"]),
    "local-2025-10": ("electronic-circuits", ["limiter-clipper"]),

    # BJT·FET 소자와 증폭회로의 경계 보정.
    "local-2009-01": ("digital-engineering", ["logic-families"]),
    "national-2009-06": ("semiconductor", ["carriers", "bjt-device", "mosfet-device"]),
    "national-2012-12": ("semiconductor", ["mosfet-device"]),
    "national-2013-10": ("electronic-circuits", ["bjt-amplifier", "multistage-special"]),
    "national-2013-11": ("semiconductor", ["bjt-device", "mosfet-device"]),
    "national-2016-19": ("electronic-circuits", ["bjt-amplifier"]),
    "national-2018-07": ("electronic-circuits", ["differential-mirror"]),
    "national-2018-12": ("electronic-circuits", ["bjt-amplifier"]),
    "national-2018-19": ("electronic-circuits", ["fet-amplifier"]),
    "national-2020-17": ("electronic-circuits", ["oscillator"]),
    "national-2021-14": ("semiconductor", ["bjt-device", "mosfet-device"]),
    "national-2022-08": ("electronic-circuits", ["bjt-bias"]),
    "military-2023-10": ("electronic-circuits", ["fet-amplifier"]),
    "military-2024-10": ("electronic-circuits", ["bjt-bias"]),
    "local-2024-11": ("electronic-circuits", ["bjt-bias"]),
    "national-2025-01": ("electronic-circuits", ["bjt-bias"]),
    "national-2025-06": ("electronic-circuits", ["bjt-bias"]),
    "national-2026-09": ("electronic-circuits", ["bjt-amplifier"]),
    "national-2026-17": ("electronic-circuits", ["fet-amplifier"]),
    "local-2026-18": ("electronic-circuits", ["bjt-bias"]),
    "military-2026-07": ("semiconductor", ["bjt-device"]),

    # CMOS 논리회로와 조합·순차회로.
    "national-2009-14": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "national-2012-17": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "assembly-2014-06": ("digital-engineering", ["codes-arithmetic", "arithmetic-circuits", "encoder-decoder"]),
    "assembly-2016-19": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "assembly-2019-04": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "national-2022-16": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "national-2023-07": ("semiconductor", ["mosfet-device"]),
    "military-2023-14": ("digital-engineering", ["logic-families", "boolean-gates"]),
    "local-2024-02": ("digital-engineering", ["counter", "latch-flipflop"]),
    "national-2024-19": ("digital-engineering", ["arithmetic-circuits", "encoder-decoder", "other-combinational"]),
})

CONCEPT_OVERRIDES = {
    "national-2011-05": ["선형·직렬·병렬 조정기", "스위칭 전원"],
    "national-2008-11": ["정상상태 등가회로"],
    "local-2009-12": ["정상상태 등가회로"],
    "seoul-2017-16": ["커패시터 개방"],
    "seoul-2014-14": ["특성임피던스"],
    "assembly-2023-14": ["정현파", "주파수·주기", "페이저"],
}

QUESTION_TYPE_OVERRIDES = {
    "national-2011-05": ["개념형"],
}

MAX_POWER_IDS = {
    "national-2008-05", "national-2009-11", "national-2014-05", "national-2015-06",
    "national-2018-09", "national-2021-05", "national-2021-06", "national-2022-17",
    "national-2022-20", "national-2024-10", "local-2024-16",
}


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def taxonomy_indexes(taxonomy: dict) -> tuple[dict, dict]:
    topics = {}
    categories = {}
    for category in taxonomy["categories"]:
        categories[category["id"]] = category
        for topic in category["topics"]:
            topics[(category["id"], topic["id"])] = topic
    return categories, topics


def generic_fallback(text: str) -> tuple[str, list[str]] | None:
    """고유명사가 OCR에서 빠진 문항을 문장 구조로 보수적으로 분류한다."""
    if re.search(r"연산\s*증폭|op.?amp|가산\s*회로|레벨\s*시프터", text):
        return "electronic-circuits", ["opamp-operations"]
    if re.search(r"트랜지스터|콜렉터|컬렉터|이미터|에미터", text):
        if re.search(r"dc|바이어스|vce|vbe|동작점|직류", text):
            return "electronic-circuits", ["bjt-bias"]
        return "electronic-circuits", ["bjt-amplifier"]
    if re.search(r"mos\s*커패시터|mos\s*구조", text):
        return "semiconductor", ["mosfet-device"]
    if re.search(r"다이오드", text):
        if re.search(r"파형|전달\s*특성|출력\s*전압", text):
            return "electronic-circuits", ["limiter-clipper"]
        return "semiconductor", ["diode-model"]
    if re.search(r"플립|래치|상태표|현재상태|다음상태", text):
        return "digital-engineering", ["latch-flipflop"]
    if re.search(r"논리|로직|출력\s*[fyz].*입력|함수\s*[fyz]", text):
        return "digital-engineering", ["boolean-gates"]
    if re.search(r"증폭기|증폭회로|전압\s*이득|전류\s*이득", text):
        return "electronic-circuits", ["amplifier-basics"]
    if re.search(r"회로", text) and re.search(r"저항|전류|전압", text):
        return "circuit-theory", ["kcl-kvl"]
    if re.search(r"저항", text) and re.search(r"길이|단면|재질|비저항", text):
        return "circuit-theory", ["elements-basics"]
    return None


def classify(question: dict, topic_index: dict) -> dict:
    text = normalized(question.get("ocrText", ""))
    old = question.get("classification", {})
    scored: dict[tuple[str, str], dict] = defaultdict(lambda: {"score": 0, "concepts": []})
    for category, topic, concept, patterns in RULES:
        hits = sum(1 for pattern in patterns if re.search(pattern, text, re.I))
        if hits:
            scored[(category, topic)]["score"] += hits * 2
            scored[(category, topic)]["concepts"].append(concept)

    if question["id"] in ID_OVERRIDES:
        category, topics = ID_OVERRIDES[question["id"]]
        confidence = "curated"
    else:
        category_scores: Counter = Counter()
        for (cat, _topic), payload in scored.items():
            category_scores[cat] += payload["score"]
        if old.get("topic") != "mixed-signal" and old.get("category"):
            category_scores[old["category"]] += 1
        if category_scores:
            category = category_scores.most_common(1)[0][0]
            candidates = [(topic, payload["score"]) for (cat, topic), payload in scored.items() if cat == category]
            candidates.sort(key=lambda item: item[1], reverse=True)
            if candidates:
                best = candidates[0][1]
                topics = [topic for topic, score in candidates if score >= max(2, best * 0.6)][:3]
                confidence = "rule-reviewed" if best >= 4 else "rule-candidate"
            else:
                topics = []
                confidence = "fallback"
        else:
            category, topics, confidence = None, [], "fallback"

        if not topics:
            existing_topics = [topic for topic in old.get("topics", []) if (old.get("category"), topic) in topic_index]
            fallback = OLD_TOPIC_FALLBACK.get(old.get("topic"))
            generic = generic_fallback(text)
            if generic:
                category, topics = generic
                confidence = "generic-reviewed"
            elif existing_topics:
                category, topics = old["category"], existing_topics
            elif fallback:
                category, topic = fallback
                topics = [topic]
            elif old.get("category") == "digital-engineering":
                category, topics = "digital-engineering", ["boolean-gates"]
            elif old.get("category") == "semiconductor":
                category, topics = "semiconductor", ["carriers"]
            elif old.get("category") == "circuit-theory":
                category, topics = "circuit-theory", ["elements-basics"]
            else:
                category, topics = "electronic-circuits", ["opamp-operations"]

    if question["id"] in MAX_POWER_IDS:
        category = "circuit-theory"
        topics = [topic for topic in topics if topic in {"thevenin", "norton", "maximum-power", "coupled-transformer"}]
        if "maximum-power" not in topics:
            topics.append("maximum-power")
        confidence = "curated"

    topics = list(dict.fromkeys(topics))
    concepts = []
    for topic in topics:
        allowed = topic_index[(category, topic)]["concepts"]
        payload = scored.get((category, topic), {})
        matched = [concept for concept in payload.get("concepts", []) if concept in allowed]
        concepts.extend(matched or allowed[:1])
    concepts = list(dict.fromkeys(concepts))
    if question["id"] in CONCEPT_OVERRIDES:
        concepts = CONCEPT_OVERRIDES[question["id"]]
    if len(topics) > 1:
        question_types = list(dict.fromkeys([*(old.get("questionTypes") or []), "복수개념"]))
    else:
        question_types = old.get("questionTypes") or ["개념형"]
    if question["id"] in QUESTION_TYPE_OVERRIDES:
        question_types = QUESTION_TYPE_OVERRIDES[question["id"]]
    return {
        "category": category,
        "topics": topics,
        "concepts": concepts,
        "auxiliaryTags": old.get("auxiliaryTags") or [],
        "questionTypes": question_types,
        "status": "approved" if confidence in {"curated", "rule-reviewed", "rule-candidate", "generic-reviewed"} else "needs-review",
        "method": f"curriculum-v2:{confidence}",
    }


def main() -> int:
    taxonomy = json.loads((DATA / "taxonomy.json").read_text(encoding="utf-8"))
    questions_path = DATA / "questions.json"
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    _categories, topic_index = taxonomy_indexes(taxonomy)
    overrides = {}
    for question in questions:
        classification = classify(question, topic_index)
        question["classification"] = classification
        question.setdefault("review", {})["classification"] = classification["status"]
        overrides[question["id"]] = classification

    questions_path.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (DATA / "classification_overrides.json").write_text(json.dumps(overrides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    exams = json.loads((DATA / "exams.json").read_text(encoding="utf-8"))
    payload = {
        "schemaVersion": 2,
        "taxonomyVersion": taxonomy["version"],
        "generatedAt": __import__("datetime").date.today().isoformat(),
        "taxonomy": taxonomy,
        "exams": exams,
        "questions": questions,
    }
    (DATA / "data.js").write_text("window.QUESTION_BANK = " + json.dumps(payload, ensure_ascii=False) + ";\n", encoding="utf-8")

    topic_counts = Counter(topic for q in questions for topic in q["classification"]["topics"])
    uncertain = [q for q in questions if q["classification"]["status"] != "approved"]
    report = {
        "taxonomyVersion": taxonomy["version"],
        "questionCount": len(questions),
        "multiTopicQuestionCount": sum(len(q["classification"]["topics"]) > 1 for q in questions),
        "needsReviewCount": len(uncertain),
        "topicCounts": dict(sorted(topic_counts.items())),
        "needsReview": [{"id": q["id"], "ocrText": q.get("ocrText", ""), "classification": q["classification"]} for q in uncertain],
    }
    (PROJECT / "review" / "classification-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"reclassified={len(questions)} multi={report['multiTopicQuestionCount']} needs-review={len(uncertain)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
