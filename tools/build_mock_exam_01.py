#!/usr/bin/env python3
"""창작 전자공학개론 25문항: 벡터 회로도, 2단 문제지, 별도 정답·해설."""
import json
import math
import re
from collections import Counter
from pathlib import Path
import fitz
from build_print_pdf import subset_font

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'print/mock_exam_01'
Q = []

def add(level, topic, stem, choices, answer, explanation, diagram=None):
    Q.append(dict(number=len(Q)+1, difficulty=level, topic=topic, stem=stem,
                  choices=choices, answer=answer, explanation=explanation, diagram=diagram))

add(1,'기본소자','정전용량이 각각 3 μF, 6 μF인 이상적인 커패시터를 병렬로 연결하였다. 합성 정전용량[μF]은?',
    ['2','3','6','9'],4,'병렬 커패시터의 정전용량은 더한다. C = 3 + 6 = 9 μF.')
add(2,'공진','직렬 RLC 회로에서 R = 10 Ω, L = 20 mH, C = 2 μF이다. 공진 각주파수[rad/s]는?',
    ['2,500','5,000','10,000','20,000'],2,'ω₀ = 1/√(LC) = 1/√(0.02 × 0.000002) = 5,000 rad/s.')
add(1,'BJT 기초','활성영역에서 동작하는 BJT의 공통 베이스(CB) 전류이득 α에 대한 설명으로 옳은 것은?',
    ['α는 일반적으로 1보다 크다.','α는 컬렉터전류를 베이스전류로 나눈 값이다.','α는 1에 가깝지만 1보다 작다.','α는 부하저항에만 비례한다.'],3,
    'α = I꜀/Iₑ = β/(β + 1)이므로 1에 가깝지만 1보다 작다.')
add(2,'카르노맵','3변수 논리함수 F(A, B, C) = Σm(1, 3, 4, 5, 7)을 간략화한 식은? (단, 최소항 번호는 ABC를 이진수로 해석하며 A가 최상위 비트이다. ¬는 NOT을 뜻한다.)',
    ['C + A¬B','B + A¬C','¬C + AB','A + ¬BC'],1,
    '1·3·5·7을 묶으면 C, 4·5를 묶으면 A¬B이다. 따라서 F = C + A¬B.')
add(1,'TCP/IP','TCP/IP에서 IP의 주된 역할로 옳은 것은?',
    ['수신 확인과 재전송을 통한 신뢰성 보장','논리 주소를 이용한 패킷 전달','응용 프로세스의 포트 번호 할당','데이터의 암호화와 복호화'],2,
    'IP는 인터넷 계층에서 IP 주소를 이용해 패킷을 전달한다. UDP와는 별개의 프로토콜이다.')
add(3,'테브난·최대전력','그림에서 부하 RＬ에 최대 전력이 전달되도록 할 때 RＬ[Ω]과 최대 전력 PＬ[W]의 조합은? (단, 전원과 저항은 이상적이다.)',
    ['RＬ = 2, PＬ = 4.5','RＬ = 2, PＬ = 9','RＬ = 3, PＬ = 4.5','RＬ = 3, PＬ = 9'],1,
    '부하를 떼면 Vth = 18 × 3/(6 + 3) = 6 V. 전원을 단락하면 Rth = 6∥3 = 2 Ω. RＬ = 2 Ω, Pmax = 6²/(4 × 2) = 4.5 W.','thevenin')
add(2,'다이오드','9.4 V 직류전원에 2 kΩ 저항과 실리콘 다이오드 2개를 직렬로 연결하였다. 두 다이오드 모두 순방향으로 도통하며 각각의 전압강하는 0.7 V로 일정하다. 전류[mA]는?',
    ['2','3','4','4.7'],3,'저항 양단 전압은 9.4 − 0.7 − 0.7 = 8 V. I = 8/2,000 = 4 mA.')
add(1,'부궤환','안정하게 동작하는 전압 증폭기에 부궤환을 적용했을 때의 일반적인 효과로 옳지 않은 것은?',
    ['이득의 소자 변화에 대한 민감도가 줄어든다.','비선형 왜곡이 감소한다.','폐루프 이득이 개루프 이득보다 커진다.','이득과 대역폭의 교환 관계가 나타난다.'],3,
    '부궤환 폐루프 이득은 A/(1 + Aβ)이다. 일반적인 중역에서 이득은 줄어들고 안정성·선형성이 개선된다.')
add(2,'연산증폭기','그림의 전압이득 Vout/Vin은? (단, 연산증폭기는 이상적이고 선형영역에서 동작한다.)',
    ['−6','−5','5','6'],4,'비반전 증폭기이므로 Av = 1 + Rf/Rg = 1 + 10/2 = 6.','noninv')
add(3,'미분기','그림 (가)의 입력을 그림 (나)에 인가하였다. 2 < t < 4 [s]에서 출력전압[V]은? (단, 연산증폭기는 이상적이며 선형영역에서 동작한다. 꼭짓점에서의 순간 동작은 제외한다.)',
    ['−4','−2','2','4'],3,'2~4 s의 입력 기울기는 (0 − 8)/(4 − 2) = −4 V/s. RC = 25 kΩ × 20 μF = 0.5 s. Vout = −RC·dVin/dt = +2 V.','diff')
add(1,'논리 게이트','2입력 XOR 게이트의 출력이 1이 되는 입력 (A, B)를 모두 고른 것은?',
    ['(0, 0), (1, 1)','(0, 1), (1, 0)','(0, 0), (0, 1)','(1, 0), (1, 1)'],2,
    'XOR는 두 입력이 서로 다를 때 1이다.')
add(2,'BJT 바이어스','그림에서 컬렉터–이미터 전압 VＣＥ[V]는? (단, β = 100, VＢＥ = 0.7 V이며 얼리 효과는 무시한다.)',
    ['5','6','7','8'],3,'IＢ = (12 − 0.7)/226 kΩ = 50 μA. IＣ = 5 mA. VＣＥ = 12 − 5 mA × 1 kΩ = 7 V로 활성영역 가정도 성립한다.','bjt')
add(4,'슈미트 트리거','그림의 비반전 슈미트 트리거에서 입력전압의 하강 문턱 VＴＬ과 상승 문턱 VＴＨ[V]는? (단, 연산증폭기는 이상적이며 출력 포화전압은 +8 V, −8 V이다.)',
    ['VＴＬ = −3, VＴＨ = 5','VＴＬ = −1, VＴＨ = 7','VＴＬ = 1, VＴＨ = 5','VＴＬ = 1, VＴＨ = 7'],2,
    '전환 직전 V＋ = V− = 2 V. (Vin − 2)/20 kΩ + (Vout − 2)/40 kΩ = 0이므로 Vin = 3 − Vout/2. 출력이 +8 V일 때 하강 문턱 −1 V, −8 V일 때 상승 문턱 7 V이다.','schmitt')
add(1,'발진기','하틀리(Hartley) 발진기의 주파수 선택용 LC 탱크회로를 구성하는 기본 소자 조합은? (단, 바이어스 및 결합용 소자는 제외한다.)',
    ['인덕터 1개와 커패시터 2개','인덕터 2개와 커패시터 1개','저항 2개와 커패시터 2개','저항 3개와 커패시터 3개'],2,
    '하틀리는 인덕터 2개(또는 탭 인덕터)와 커패시터 1개를 사용한다. 커패시터 2개와 인덕터 1개인 것은 콜피츠이다.')
add(3,'FET 증폭기','그림의 JFET 증폭기에서 중역 전압이득 Vout/Vin은? (단, IＤＳＳ = 8 mA, VＰ = −4 V, 직류 VＧＳ = −2 V이다. 게이트 전류와 출력 컨덕턴스는 무시하고 쇼클리 식을 적용한다. 결합 커패시터는 교류에서 단락이다.)',
    ['−12','−6','−3','6'],2,
    'gm₀ = 2IＤＳＳ/|VＰ| = 4 mS. gm = gm₀(1 − VＧＳ/VＰ) = 2 mS. 소스가 교류 접지이므로 Av = −gmRＤ = −0.002 × 3,000 = −6. IＤ = 2 mA, VＤＳ = 6 V로 포화영역 조건도 만족한다.','fet')
add(2,'평균값·실효값','주기적인 전류가 한 주기의 1/4 동안 일정한 양의 값 Iｍ이고, 나머지 3/4 동안 0이다. 평균전류가 3 A일 때 실효전류[A]는?',
    ['3','3√2','6','12'],3,'Iavg = Iｍ/4 = 3이므로 Iｍ = 12 A. Irms = Iｍ√(1/4) = 6 A.')
add(1,'플립플롭','양의 에지에서 동작하는 JK 플립플롭에서 J = K = 1이 유지된다. 유효 클록 에지가 들어올 때의 동작은?',
    ['항상 0으로 리셋된다.','항상 1로 세트된다.','현재 출력을 유지한다.','현재 출력의 반대 값으로 바뀐다.'],4,
    'JK 플립플롭은 J = K = 1일 때 토글한다.')
add(2,'AM 측파대','반송파 주파수 800 kHz, 단일 정현파 정보신호 주파수 4 kHz인 AM 신호의 하측파대와 상측파대 주파수[kHz]는?',
    ['792, 808','796, 804','798, 802','800, 804'],2,
    '측파대는 fc ± fm이므로 796 kHz와 804 kHz이다.')
add(3,'순서논리','그림의 회로에서 Q의 초기값은 0이다. 연속된 네 번의 상승 클록 에지 직전에 입력 x가 차례로 1, 0, 1, 1로 안정되어 있다. 각 상승 에지 직후의 Q를 순서대로 쓴 것은? (단, 전파지연은 무시한다.)',
    ['1 → 0 → 1 → 1','1 → 1 → 0 → 1','0 → 1 → 1 → 0','1 → 0 → 0 → 1'],2,
    'D = x XOR Q이므로 x = 1이면 토글, x = 0이면 유지한다. Q: 0 → 1 → 1 → 0 → 1.','dff')
add(1,'CMOS','이상적인 CMOS 인버터의 입력이 0 V 또는 전원전압으로 안정되어 있을 때 정적 소비전력이 거의 0인 주된 이유는? (단, 누설전류는 무시한다.)',
    ['두 MOSFET이 모두 항상 켜져 있기 때문이다.','출력 부하의 저항이 항상 0이기 때문이다.','전원과 접지 사이의 직류 도통 경로가 차단되기 때문이다.','출력전압이 항상 0 V이기 때문이다.'],3,
    '정상적인 논리 상태에서는 PMOS와 NMOS 중 하나가 꺼져 전원–접지 직류 경로를 차단한다.')
add(2,'교류전력','R = 6 Ω, 유도성 리액턴스 XＬ = 8 Ω인 직렬 회로에 실효값 100 V의 정현파 전압을 인가하였다. 회로의 유효전력[W]은?',
    ['360','600','800','1,000'],2,
    '|Z| = √(6² + 8²) = 10 Ω, Irms = 10 A. P = I²R = 100 × 6 = 600 W.')
add(2,'정류·평활','50 Hz 전원을 사용하는 전파정류 평활회로에서 부하전류는 약 20 mA로 일정하고 평활 커패시터는 1,000 μF이다. ΔVpp ≈ IＬ/(frC)로 근사할 때 출력 리플의 첨두간 전압[V]은? (단, fr는 리플 주파수이다.)',
    ['0.1','0.2','0.4','2'],2,
    '전파정류의 리플 주파수 fr = 2 × 50 = 100 Hz. ΔVpp = 0.020/(100 × 0.001) = 0.2 V.')
add(1,'정전압회로','제너 다이오드를 이용한 일반적인 병렬 정전압회로에서 제너 다이오드가 전압을 안정시키는 동작영역은?',
    ['순방향 차단영역','역방향 항복영역','역방향 항복 전의 차단영역','항상 순방향 도통영역'],2,
    '제너 다이오드의 역방향 항복영역에서 전류가 변해도 전압이 비교적 일정한 특성을 이용한다.')
add(2,'다단 증폭기','그림의 다단 연산증폭기 회로에서 전체 전압이득 Vout/Vin은? (단, 두 연산증폭기는 이상적이며 선형영역에서 동작한다.)',
    ['−20','−15','15','20'],2,
    '1단 비반전 이득은 1 + 12/3 = 5, 2단 반전 이득은 −18/6 = −3. 전체 이득은 −15.','cascade')
add(3,'커패시터 전하 재분배','그림에서 C₁ = 2 μF는 9 V, C₂ = 4 μF는 3 V로 충전되어 있다. 두 커패시터는 전원에서 분리되어 있으며 아래쪽 단자는 공통이다. 스위치 S를 닫아 충분히 지난 후 공통전압 Vｆ[V]와 결합 전후 커패시터에 저장된 총 에너지의 감소량 ΔE[μJ]는? (단, 스위치·배선의 미소 저항으로 과도전류가 감쇠하며 누설은 없다.)',
    ['Vｆ = 5, ΔE = 0','Vｆ = 5, ΔE = 24','Vｆ = 6, ΔE = 24','Vｆ = 6, ΔE = 48'],2,
    '전하 보존: Vｆ = (2 × 9 + 4 × 3)/(2 + 4) = 5 V. 초기 에너지 = (2 × 9² + 4 × 3²)/2 = 99 μJ. 최종 = (2 + 4) × 5²/2 = 75 μJ. 감소량은 24 μJ로 배선 등의 저항에서 소모된다.','charge')

# 정답 위치를 7·6·6·6개로 분산한다. 문항·보기는 이 스크립트에서 처음 작성했다.
TARGETS = [3,1,4,2,3,4,1,2,4,3,1,2,4,1,3,2,1,4,2,3,4,1,3,2,1]
for q, target in zip(Q, TARGETS):
    answer_text = q['choices'].pop(q['answer']-1)
    q['choices'].insert(target-1, answer_text)
    q['answer'] = target
    for key in ('stem','explanation'):
        q[key]=''.join(chr(ord(ch)-65248) if 65281<=ord(ch)<=65374 else ch for ch in q[key]).replace('I꜀','IC').replace('Iₑ','IE')
    q['choices']=[''.join(chr(ord(ch)-65248) if 65281<=ord(ch)<=65374 else ch for ch in s) for s in q['choices']]
    submap=str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')
    for key in ('stem','explanation'):q[key]=q[key].translate(submap)

def verify():
    assert len(Q) == 25 and Counter(q['difficulty'] for q in Q) == {1:9,2:10,3:5,4:1}
    assert Counter(TARGETS) == {1:7,2:6,3:6,4:6}
    for q in Q:
        assert len(set(q['choices'])) == 4
    # 별도 수치·진리표 검산. 서술형 개념 문항은 정답·오답 보기까지 수동 검토.
    assert math.isclose(1/math.sqrt(.020*2e-6), 5000)
    for a in (0,1):
        for b in (0,1):
            for c in (0,1):
                assert ((4*a+2*b+c) in [1,3,4,5,7]) == bool(c or (a and not b))
    # 부하 연결 원회로 KCL로 최대전력 결과 재검산: RＬ = 2 Ω.
    v = (18/6)/(1/6+1/3+1/2)
    assert math.isclose(v*v/2,4.5)
    assert math.isclose((9.4-2*.7)/2000,.004)
    assert 1+10/2 == 6
    assert math.isclose(-25e3*20e-6*(0-8)/(4-2),2)
    assert math.isclose(12-100*((12-.7)/226e3)*1e3,7)
    # 電流和ゼロ条件を両閾値で直接確認。
    for vin,vout in [(-1,8),(7,-8)]:
        assert abs((vin-2)/20000+(vout-2)/40000)<1e-12
    gm=2*.008/4*(1-(-2)/(-4))
    assert math.isclose(-gm*3000,-6)
    assert math.isclose(.008*(1-.5)**2,.002)
    assert 12-.002*3000 > -2-(-4)
    assert 3/.25*math.sqrt(.25) == 6
    state=0; seq=[]
    for x in [1,0,1,1]:
        state ^= x; seq.append(state)
    assert seq == [1,1,0,1]
    assert math.isclose((100/abs(complex(6,8)))**2*6,600)
    assert math.isclose(.02/(2*50*.001),.2)
    assert (1+12/3)*(-18/6) == -15
    vf=(2*9+4*3)/(2+4)
    assert vf==5 and (2*81+4*9)/2-6*vf*vf/2==24

class Art:
    def __init__(self,page,font): self.p,self.font=page,font
    def line(self,a,b): self.p.draw_line(a,b,width=.75,color=(0,0,0))
    def text(self,x,y,s,size=8):
        s=''.join(chr(ord(ch)-65248) if 65281<=ord(ch)<=65374 else ch for ch in s)
        s=s.translate(str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789'))
        self.p.insert_text((x,y),s,fontname='kr',fontsize=size)
    def node(self,x,y): self.p.draw_circle((x,y),1.6,fill=(0,0,0),color=(0,0,0))
    def ground(self,x,y):
        self.line((x,y),(x,y+5))
        for i,w in enumerate([8,5,2]): self.line((x-w,y+5+i*3),(x+w,y+5+i*3))
    def res(self,x1,y1,x2,y2,label):
        dx,dy=x2-x1,y2-y1; length=math.hypot(dx,dy); ux,uy=dx/length,dy/length
        start=(length-22)/2; last=(x1,y1)
        pts=[(x1+ux*start,y1+uy*start)]
        for i in range(7):
            t=start+i*22/6; off=0 if i in (0,6) else (3 if i%2 else -3)
            pts.append((x1+ux*t-uy*off,y1+uy*t+ux*off))
        pts.extend([(x1+ux*(start+22),y1+uy*(start+22)),(x2,y2)])
        for pt in pts:self.line(last,pt);last=pt
        self.text((x1+x2)/2+(8 if dy else -12),(y1+y2)/2+(-7 if not dy else 0),label)
    def op(self,x,y):
        self.p.draw_polyline([(x,y-18),(x,y+18),(x+34,y),(x,y-18)],color=(0,0,0),width=.8)
        self.text(x+4,y-7,'−');self.text(x+4,y+12,'+')
    def voltage(self,x,y,label):
        self.p.draw_circle((x,y),11,color=(0,0,0),width=.8)
        self.text(x-3,y-2,'+');self.text(x-3,y+8,'−');self.text(x-34,y+3,label)

def diagram(page,x,y,kind,font):
    a=Art(page,font); page.set_rotation(0)
    # 로컬 220 × 120 pt 공간에서 선과 문자 모두 벡터로 그린다.
    def L(p,q):a.line((x+p[0],y+p[1]),(x+q[0],y+q[1]))
    def T(px,py,s):a.text(x+px,y+py,s)
    def R(p,q,s):a.res(x+p[0],y+p[1],x+q[0],y+q[1],s)
    def G(px,py):a.ground(x+px,y+py)
    def O(px,py):a.op(x+px,y+py)
    if kind=='thevenin':
        a.voltage(x+34,y+60,'18 V');L((34,49),(34,24));R((34,24),(124,24),'6 Ω')
        L((124,24),(192,24));R((124,24),(124,103),'3 Ω');R((192,24),(192,103),'RＬ')
        L((34,71),(34,103));L((34,103),(192,103));G(124,103)
    elif kind=='noninv':
        O(100,55);L((90,95),(90,65));L((90,65),(100,65));T(85,110,'Vin')
        L((100,45),(60,45));R((60,45),(60,103),'2 kΩ');G(60,103)
        L((60,45),(60,12));R((60,12),(158,12),'10 kΩ')
        L((158,12),(158,55));L((134,55),(191,55));T(170,46,'Vout')
    elif kind=='diff':
        # 入力波形と微分器を上下に分ける。
        L((12,43),(93,43));L((12,43),(12,6));L((12,43),(47,10));L((47,10),(82,43))
        T(5,55,'0');T(44,55,'2');T(80,55,'4');T(91,45,'t [s]');T(14,9,'8 V');T(38,69,'(가)')
        O(151,41);L((110,31),(123,31));L((127,21),(127,41));L((132,21),(132,41));L((123,31),(127,31));L((132,31),(151,31))
        T(110,15,'20 μF');L((142,31),(142,0));R((142,0),(201,0),'25 kΩ');L((201,0),(201,41));L((185,41),(216,41))
        L((151,51),(140,51));G(140,51);T(192,56,'Vout');T(166,87,'(나)')
    elif kind=='bjt':
        # NPNのベース・コレクタ・エミッタを明示。
        L((35,12),(154,12));T(85,5,'+12 V');R((35,12),(35,70),'226 kΩ');L((35,70),(104,70))
        R((154,12),(154,48),'1 kΩ');L((113,55),(113,84));L((104,70),(113,70))
        L((113,63),(133,51));L((113,77),(133,91));L((133,91),(133,108));G(133,108)
        page.draw_polyline([(x+124,y+90),(x+133,y+91),(x+130,y+83)],color=(0,0,0),fill=(0,0,0))
        # コレクタ経路を接続。
        L((133,51),(154,48));T(158,68,'+');T(158,84,'VＣＥ');T(158,100,'−')
    elif kind=='schmitt':
        # 正入力は下、負入力は上。
        O(112,58);R((22,68),(100,68),'20 kΩ');L((100,68),(112,68));T(2,71,'Vin')
        L((100,68),(100,105));R((100,105),(180,105),'40 kΩ');L((180,105),(180,58));L((146,58),(208,58));T(181,46,'Vout')
        L((112,48),(74,48));T(40,43,'+2 V');T(136,17,'포화 ±8 V')
    elif kind=='fet':
        T(150,6,'+12 V');R((157,12),(157,49),'3 kΩ');L((157,49),(157,57));L((150,57),(157,57));L((150,57),(150,92));L((150,92),(157,92));L((157,92),(157,107));G(157,107)
        L((141,61),(141,88));L((133,74),(141,74));L((133,74),(150,74));L((146,71),(150,74));L((146,77),(150,74))
        L((25,74),(54,74));L((54,64),(54,84));L((59,64),(59,84));L((59,74),(133,74));T(3,70,'Vin');T(40,56,'C')
        R((100,74),(100,111),'1 MΩ');page.draw_circle((x+100,y+111),1.5,color=(0,0,0));T(76,125,'−2 V (DC)');L((157,49),(206,49));T(178,42,'Vout')
    elif kind=='dff':
        # XORを標準の論理式ブロックで表す。帰還はQからXORへ。
        page.draw_rect(fitz.Rect(x+48,y+31,x+88,y+64),color=(0,0,0),width=.8);T(56,51,'XOR')
        page.draw_rect(fitz.Rect(x+126,y+25,x+173,y+89),color=(0,0,0),width=.8)
        T(131,47,'D');T(159,48,'Q');L((88,45),(126,45));L((15,40),(48,40));T(3,37,'x')
        L((173,45),(209,45));T(199,34,'Q');L((190,45),(190,110));L((190,110),(32,110));L((32,110),(32,57));L((32,57),(48,57))
        L((102,76),(126,76));L((126,71),(132,76));L((132,76),(126,81));T(86,88,'CK')
    elif kind=='cascade':
        O(39,50);T(42,106,'Vin');L((37,90),(37,60));L((37,60),(39,60));L((39,40),(20,40));R((20,40),(20,100),'');T(0,84,'3 kΩ');G(20,100)
        L((20,40),(20,11));R((20,11),(84,11),'12 kΩ');L((84,11),(84,50));L((73,50),(84,50))
        R((84,50),(143,50),'6 kΩ');O(143,60);L((143,70),(131,70));G(131,70)
        L((134,50),(134,12));R((134,12),(197,12),'18 kΩ');L((197,12),(197,60));L((177,60),(215,60));T(184,78,'Vout')
    elif kind=='charge':
        L((40,22),(104,22));L((116,22),(181,22));page.draw_circle((x+104,y+22),2,color=(0,0,0));page.draw_circle((x+116,y+22),2,color=(0,0,0));L((104,22),(114,10));T(104,5,'S')
        for px,label,vol in [(40,'C₁ = 2 μF','9 V'),(181,'C₂ = 4 μF','3 V')]:
            L((px,22),(px,53));L((px-12,53),(px+12,53));L((px-12,59),(px+12,59));L((px,59),(px,100));T(px-4,46,'+');T(px-4,74,'−');T(px-21,88,vol);T(px-25,117,label)
        L((40,100),(181,100))

def build():
    verify();OUT.mkdir(parents=True,exist_ok=True)
    labels=''.join(str(q) for q in Q)+'전자공학개론 창작 모의고사 제1회 문제지 정답 및 해설 성명 수험번호 문항 각 점 총 점 시간 분 참고 예상 난도 개념 기본 계산 다단계 심화 별 공식 검산 난도는 실제 정답률 자료가 아닌 풀이 기준 추정치입니다. 전원 출판 기출 원문 출처 표시 없는 신규 문항 출력飽和直流①②③④★ 출題'
    fontbytes=subset_font(Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'),labels)
    font=fitz.Font(fontbuffer=fontbytes)
    def setup(doc):
        p=doc.new_page(width=595.276,height=841.89);p.insert_font(fontname='kr',fontbuffer=fontbytes);return p
    def text(p,x,y,s,size=10):p.insert_text((x,y),s,fontname='kr',fontsize=size)
    def wrap(s,width,size):
        lines=[]
        for para in s.split('\n'):
            line=''
            for ch in re.findall(r'[A-Za-z0-9][A-Za-z0-9_.]*|.',para):
                if font.text_length(line+ch,fontsize=size)>width:
                    lines.append(line);line=ch
                else:line+=ch
            lines.append(line)
        return lines
    def block(p,x,y,s,width,size=10,leading=15):
        for line in wrap(s,width,size):text(p,x,y,line,size);y+=leading
        return y
    doc=fitz.open();placements=[]
    # 左列を上から下へ解き、続いて右列へ。各ページ3+2問、計5ページ。
    for pi in range(5):
        p=setup(doc);text(p,32,31,'전자공학개론 · 창작 모의고사 제1회',14)
        text(p,32,49,'25문항 · 각 4점 · 총 100점 · 권장 시간 30분',8)
        text(p,350,49,'성명: __________  수험번호: __________',8)
        p.draw_line((30,59),(565,59),width=.8);p.draw_line((297.6,70),(297.6,797),width=.4,color=(.6,.6,.6))
        page_questions=Q[pi*5:pi*5+5]
        def height(q):
            return len(wrap(f"{q['number']}. {q['stem']}",249,10))*14.5+(151 if q['diagram'] else 0)+sum(3+len(wrap('① '+s,245,9.5))*13 for s in q['choices'])
        tops={}
        for col,items in [(0,page_questions[:3]),(1,page_questions[3:])]:
            used=sum(height(q) for q in items)
            assert used<710,(pi,col,used)
            gap=(710-used)/len(items)
            next_top=80
            for q in items:
                tops[q['number']]=next_top
                next_top+=height(q)+gap
        for si,q in enumerate(page_questions):
            col=0 if si<3 else 1;row=si if col==0 else si-3
            top=tops[q['number']];bottom=795
            x=33 if col==0 else 313; width=249
            y=block(p,x,top,f"{q['number']}. {q['stem']}",width,size=10,leading=14.5)
            if q['diagram']:
                diagram(p,x+10,y+17,q['diagram'],font);y+=151
            for j,opt in enumerate(q['choices']):y=block(p,x+4,y+3,'①②③④'[j]+' '+opt,width-4,size=9.5,leading=13)
            if y>bottom:raise RuntimeError(f"문항 {q['number']} 영역 넘침: {y:.1f}>{bottom:.1f}")
            placements.append({'number':q['number'],'page':pi+1,'column':col+1,'top':top,'bottom':y})
        text(p,278,822,f'{pi+1} / 5',8)
    doc.set_metadata({'title':'전자공학개론 창작 모의고사 제1회 — 문제지','author':'elec study','subject':'신규 25문항 · A4 세로 2단'})
    doc.save(OUT/'mock_exam_01_questions.pdf',garbage=4,deflate=True);doc.close()
    ans=fitz.open();p=setup(ans);text(p,32,37,'제1회 정답 및 해설',16)
    text(p,32,59,'문제지와 분리된 정답지 · 25문항 / 100점',9)
    for row in range(5):
        y=82+row*24
        for col in range(5):
            q=Q[row*5+col];text(p,35+col*106,y,f"{q['number']:02d}번  {'①②③④'[q['answer']-1]}",11)
    text(p,32,216,'문항별 해설',12);y=242
    for q in Q:
        content=f"{q['number']}. {'①②③④'[q['answer']-1]}  {q['explanation']}"
        h=len(wrap(content,525,10))*15+13
        if y+h>790:
            p=setup(ans);text(p,32,37,'제1회 정답 및 해설',14);y=70
        y=block(p,34,y,content,525,10,15)+13
    p=setup(ans);text(p,32,38,'출제 구성 및 난도 기준',15)
    note='난도는 실제 정답률 자료가 아닌 풀이 과정 기준의 예상치입니다. 최근 지방직 2022~2026년 총 100문항을 검토한 비율(38%, 39%, 19%, 4%, 0%)을 25문항에 맞춰 배분했습니다. 기존 문항의 이미지·보기·회로를 가져오지 않고 문항과 도식을 새로 작성했습니다.'
    y=block(p,32,67,note,525,10,16)+15
    for level,meaning in [(1,'기본 개념·단순 암기'),(2,'표준 공식·기본 계산'),(3,'여러 단계 계산·회로 해석'),(4,'까다로운 조건·심화 해석'),(5,'매우 복잡한 고난도')]:
        nums=[str(q['number']) for q in Q if q['difficulty']==level]
        y=block(p,32,y,f"{'★'*level}  {meaning}: {len(nums)}문항 / "+(', '.join(nums) if nums else '없음'),525,10,17)+10
    text(p,32,y+15,'배점은 난도와 관계없이 각 4점입니다.',10)
    for i,p in enumerate(ans):text(p,278,821,f'{i+1} / {len(ans)}',8)
    ans.set_metadata({'title':'전자공학개론 창작 모의고사 제1회 — 정답 및 해설','author':'elec study'})
    ans.save(OUT/'mock_exam_01_answers.pdf',garbage=4,deflate=True);ans.close()
    (OUT/'questions.json').write_text(json.dumps(Q,ensure_ascii=False,indent=2)+'\n')
    (OUT/'layout.json').write_text(json.dumps(placements,ensure_ascii=False,indent=2)+'\n')
    print('검산 통과. 문제지 5쪽. 정답지',len(fitz.open(OUT/'mock_exam_01_answers.pdf')),'쪽.')

if __name__=='__main__':build()
