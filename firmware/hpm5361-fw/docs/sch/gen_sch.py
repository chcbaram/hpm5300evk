#!/usr/bin/env python3
# HPM5361 keyboard power/clock schematic SVG generator
import os

FONT = "Helvetica, Arial, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif"
STROKE = "#1a1a1a"
NETC = "#0b5cad"
ACC = "#b3261e"
GRAY = "#666"


class Sheet:
    def __init__(self, w, h, title, sub=""):
        self.w, self.h = w, h
        self.o = []
        self.o.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>')
        self.o.append(f'<rect x="10" y="10" width="{w-20}" height="{h-20}" fill="none" stroke="#bbb" stroke-width="2"/>')
        self.text(38, 52, title, 26, weight="bold")
        if sub:
            self.text(38, 78, sub, 14, color=GRAY)

    # ---------- primitives ----------
    def line(self, x1, y1, x2, y2, w=2.2, color=STROKE, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ''
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}/>')

    def wire(self, *pts, color=STROKE, w=2.2):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], w, color)

    def text(self, x, y, s, size=13, anchor="start", weight="normal", color=STROKE, style="normal"):
        s = (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        self.o.append(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'font-style="{style}" fill="{color}" text-anchor="{anchor}">{s}</text>')

    def rect(self, x, y, w, h, fill="#ffffff", stroke=STROKE, sw=2.2, rx=0):
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def dot(self, x, y, r=4.2):
        self.o.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{STROKE}"/>')

    # ---------- symbols ----------
    def gnd(self, x, y, label=None):
        """ground symbol; node is at (x,y), symbol drawn below"""
        self.line(x, y, x, y + 12)
        self.line(x - 15, y + 12, x + 15, y + 12, 2.6)
        self.line(x - 9, y + 18, x + 9, y + 18, 2.6)
        self.line(x - 3, y + 24, x + 3, y + 24, 2.6)
        if label:
            self.text(x + 20, y + 22, label, 11, color=GRAY)

    def cap(self, x, y, name, value, gnd=True, lab_dx=17, sub=None):
        """vertical cap, node at top (x,y). returns bottom node y"""
        self.line(x, y, x, y + 17)
        self.line(x - 13, y + 17, x + 13, y + 17, 2.6)
        self.line(x - 13, y + 25, x + 13, y + 25, 2.6)
        self.line(x, y + 25, x, y + 38)
        self.text(x + lab_dx, y + 19, name, 12.5, weight="bold")
        self.text(x + lab_dx, y + 33, value, 12)
        if sub:
            self.text(x + lab_dx, y + 46, sub, 10.5, color=GRAY)
        if gnd:
            self.gnd(x, y + 38)
        return y + 38

    def res_v(self, x, y, name, value, lab_dx=17):
        """vertical resistor from (x,y) to (x,y+56)"""
        self.line(x, y, x, y + 11)
        self.rect(x - 9, y + 11, 18, 34)
        self.line(x, y + 45, x, y + 56)
        self.text(x + lab_dx, y + 26, name, 12.5, weight="bold")
        self.text(x + lab_dx, y + 40, value, 12)
        return (x, y + 56)

    def res_h(self, x, y, name, value, up=True):
        """horizontal resistor from (x,y) to (x+56,y)"""
        self.line(x, y, x + 11, y)
        self.rect(x + 11, y - 9, 34, 18)
        self.line(x + 45, y, x + 56, y)
        if up:
            self.text(x + 28, y - 16, name, 12.5, anchor="middle", weight="bold")
            self.text(x + 28, y + 28, value, 12, anchor="middle")
        else:
            self.text(x + 28, y + 26, f"{name}  {value}", 12, anchor="middle")
        return (x + 56, y)

    def ind_h(self, x, y, name, value):
        """horizontal inductor from (x,y) to (x+70,y)"""
        self.line(x, y, x + 10, y)
        for i in range(4):
            cx = x + 17.5 + i * 15
            self.o.append(f'<path d="M {cx-7.5} {y} A 7.5 7.5 0 0 1 {cx+7.5} {y}" fill="none" stroke="{STROKE}" stroke-width="2.4"/>')
        self.line(x + 60, y, x + 70, y)
        self.text(x + 35, y - 16, name, 12.5, anchor="middle", weight="bold")
        self.text(x + 35, y + 26, value, 12, anchor="middle")
        return (x + 70, y)

    def bead_h(self, x, y, name, value):
        self.line(x, y, x + 12, y)
        self.rect(x + 12, y - 9, 36, 18, fill="#eeeeee")
        self.line(x + 48, y, x + 60, y)
        self.text(x + 30, y - 16, name, 12.5, anchor="middle", weight="bold")
        self.text(x + 30, y + 27, value, 11.5, anchor="middle")
        return (x + 60, y)

    def xtal(self, x, y, name, value):
        """horizontal crystal from (x,y) to (x+70,y)"""
        self.line(x, y, x + 18, y)
        self.line(x + 18, y - 18, x + 18, y + 18, 2.6)
        self.rect(x + 24, y - 15, 22, 30)
        self.line(x + 52, y - 18, x + 52, y + 18, 2.6)
        self.line(x + 52, y, x + 70, y)
        self.text(x + 35, y - 28, name, 12.5, anchor="middle", weight="bold")
        self.text(x + 35, y + 40, value, 12, anchor="middle")
        return (x + 70, y)

    def netflag(self, x, y, label, side="right", color=NETC):
        """net label flag; wire attaches at (x,y)"""
        wpx = 9 * len(label) + 22
        if side == "right":
            pts = f"{x},{y} {x+12},{y-13} {x+wpx},{y-13} {x+wpx},{y+13} {x+12},{y+13}"
            self.o.append(f'<polygon points="{pts}" fill="#eaf2fb" stroke="{color}" stroke-width="1.8"/>')
            self.text(x + 20, y + 5, label, 13.5, weight="bold", color=color)
        else:
            pts = f"{x},{y} {x-12},{y-13} {x-wpx},{y-13} {x-wpx},{y+13} {x-12},{y+13}"
            self.o.append(f'<polygon points="{pts}" fill="#eaf2fb" stroke="{color}" stroke-width="1.8"/>')
            self.text(x - 20, y + 5, label, 13.5, weight="bold", color=color, anchor="end")

    def ic(self, x, y, w, h, ref, part, pkg=None, fill="#fbfbf7"):
        self.rect(x, y, w, h, fill=fill)
        self.text(x + w / 2, y - 38, ref, 16, anchor="middle", weight="bold")
        self.text(x + w / 2, y - 16, part, 13.5, anchor="middle", weight="bold")
        if pkg:
            self.text(x + w / 2, y + h + 62, pkg, 12, anchor="middle", color=GRAY)

    def pin_l(self, x, y, num, name, length=34):
        """pin sticking out to the LEFT of box edge at (x,y)"""
        self.line(x - length, y, x, y)
        self.text(x + 9, y + 5, name, 13)
        self.text(x - length / 2, y - 7, str(num), 11, anchor="middle", color=ACC)
        return (x - length, y)

    def pin_r(self, x, y, num, name, length=34):
        self.line(x, y, x + length, y)
        self.text(x - 9, y + 5, name, 13, anchor="end")
        self.text(x + length / 2, y - 7, str(num), 11, anchor="middle", color=ACC)
        return (x + length, y)

    def note(self, x, y, lines, w=None, title=None):
        h = 22 * len(lines) + (26 if title else 8) + 14
        w = w or 420
        self.rect(x, y, w, h, fill="#fffdf0", stroke="#c9a227", sw=1.8, rx=6)
        yy = y + 24
        if title:
            self.text(x + 14, yy, title, 13.5, weight="bold", color="#8a6d00")
            yy += 26
        for ln in lines:
            self.text(x + 14, yy, ln, 12.5)
            yy += 22

    def save(self, path):
        body = "\n".join(self.o)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}">\n{body}\n</svg>\n')
        open(path, "w").write(svg)
        print("wrote", path, len(svg), "bytes")


OUT = "/Users/hancheol/hdd/git/hpm5300evk/firmware/hpm5361-fw/docs/sch"
os.makedirs(OUT, exist_ok=True)

# =====================================================================
# SHEET 1 - power distribution
# =====================================================================
s = Sheet(1900, 1180, "1 / 3   전원 분배  —  USB 5V → 3.3V (아날로그 / 디지털 분리)",
          "HPM5361ICB1 홀 키보드 · 부품 JLCPCB 조회 완료 · 핀번호는 데이터시트 확인분")

# ---- VBUS input (analog) ----
s.netflag(60, 170, "VBUS 5V", "right")
s.wire((175, 170), (340, 170))
s.text(60, 138, "USB Type-C VBUS", 12, color=GRAY)
s.dot(250, 170)
s.cap(250, 170, "C40", "22uF/25V", sub="0805")

# ---- U2 : analog LDO ----
s.ic(340, 128, 190, 96, "U2", "AP2114H-3.3TRG1", "SOT-223 · 1A · TAB = VOUT")
s.text(435, 168, "LDO", 16, anchor="middle", weight="bold")
s.text(435, 192, "아날로그", 12.5, anchor="middle", color=GRAY)
s.line(306, 170, 340, 170)
s.text(350, 175, "VIN", 12.5)
s.text(323, 162, "3", 11, anchor="middle", color=ACC)
s.line(530, 170, 564, 170)
s.text(520, 175, "VOUT", 12.5, anchor="end")
s.text(547, 162, "2", 11, anchor="middle", color=ACC)
s.line(435, 224, 435, 240)
s.gnd(435, 240)
s.text(452, 238, "1  GND", 11.5, color=ACC)

s.wire((564, 170), (770, 170))
s.dot(630, 170)
s.cap(630, 170, "C41", "22uF/25V", sub="0805")
s.dot(710, 170)
s.cap(710, 170, "C42", "100nF", sub="0402")

# ---- +3V3A rail ----
s.netflag(770, 170, "+3V3A", "right")
s.wire((865, 170), (1320, 170))
s.text(880, 142, "아날로그 3.3V — 센서 96 + MUX + VREFH + VANA", 13, color=NETC, weight="bold")

# R6 -> VREF_3V3
s.dot(940, 170)
s.res_v(940, 170, "R6", "0Ω")
s.wire((940, 226), (940, 280), (1700, 280))
s.netflag(940, 280, "VREF_3V3", "left")
s.dot(1120, 280)
s.cap(1120, 280, "C31", "10uF", sub="0603")
s.dot(1230, 280)
s.cap(1230, 280, "C32", "100nF", sub="0402")

# sensor branch
s.dot(1020, 280)
s.wire((1020, 280), (1020, 370))
s.netflag(1020, 380, "→ 센서 96 + MUX  약 250mA", "right", color="#0a7d33")

# FB1 -> VANA
s.dot(1320, 170)
s.wire((1320, 170), (1320, 450))
x, y = s.bead_h(1320, 450, "FB1", "600Ω@100MHz")
s.wire((x, y), (1700, y))
s.netflag(1420, 450, "+3V3ANA", "right")
s.dot(1600, 450)
s.cap(1600, 450, "C29", "4.7uF", sub="0603")

# ---- U1A ----
s.rect(1700, 240, 150, 320, fill="#f4f7fb")
s.text(1775, 228, "U1A", 16, anchor="middle", weight="bold")
s.text(1775, 582, "HPM5361ICB1", 12.5, anchor="middle", weight="bold")

s.text(1708, 285, "VREFH", 12.5)
s.text(1682, 268, "65", 11, anchor="middle", color=ACC)
s.text(1708, 455, "VANA", 12.5)
s.text(1682, 438, "67", 11, anchor="middle", color=ACC)
s.wire((1600, 520), (1700, 520))
s.text(1708, 525, "VREFL", 12.5)
s.text(1682, 508, "64", 11, anchor="middle", color=ACC)
s.gnd(1600, 520, "GNDA")

# ---- U3 : digital LDO ----
s.netflag(60, 700, "VBUS 5V", "right")
s.wire((175, 700), (340, 700))
s.dot(250, 700)
s.cap(250, 700, "C43", "10uF", sub="0603")

s.ic(340, 658, 190, 96, "U3", "AP2114H-3.3TRG1", "SOT-223 (U2와 동일 품번)")
s.text(435, 698, "LDO", 16, anchor="middle", weight="bold")
s.text(435, 722, "디지털", 12.5, anchor="middle", color=GRAY)
s.line(306, 700, 340, 700)
s.text(350, 705, "VIN", 12.5)
s.text(323, 692, "3", 11, anchor="middle", color=ACC)
s.line(530, 700, 564, 700)
s.text(520, 705, "VOUT", 12.5, anchor="end")
s.text(547, 692, "2", 11, anchor="middle", color=ACC)
s.line(435, 754, 435, 770)
s.gnd(435, 770)
s.text(452, 768, "1  GND", 11.5, color=ACC)

s.wire((564, 700), (770, 700))
s.dot(630, 700)
s.cap(630, 700, "C44", "10uF", sub="0603")
s.dot(710, 700)
s.cap(710, 700, "C45", "100nF", sub="0402")

s.netflag(770, 700, "+3V3D", "right")
s.wire((865, 700), (1380, 700))
s.text(900, 672, "디지털 3.3V — MCU 전용 (약 100mA)", 13, color=NETC, weight="bold")

s.wire((1380, 700), (1380, 1020))
rows = [
    (700, "9, 15, 85, 96", "VIO_B00", "C13~C16  100nF x4 (핀별) + C19 10uF"),
    (780, "42, 55", "VIO_B01", "C17,C18  100nF x2 + C20 10uF   ← ADC 뱅크"),
    (860, "31", "VPMC", "C21 100nF + C22 10uF   ← PY 뱅크 IO 전원 겸용"),
    (940, "71", "VPLL", "C23 100nF + C24 10uF"),
    (1020, "30", "DCDC_IN", "C4 10uF + C37 100nF   → 시트 2"),
]
s.rect(1620, 660, 230, 400, fill="#f4f7fb")
s.text(1735, 648, "U1B", 16, anchor="middle", weight="bold")
s.text(1735, 1082, "HPM5361ICB1", 12.5, anchor="middle", weight="bold")
for (yy, nums, lbl, capnote) in rows:
    if yy != 700:
        s.dot(1380, yy)
    s.wire((1380, yy), (1620, yy))
    if yy == 700:
        s.text(1360, yy - 16, capnote, 11.5, color=GRAY, anchor="end")
    else:
        s.text(1360, yy + 5, capnote, 11.5, color=GRAY, anchor="end")
    s.text(1628, yy + 5, lbl, 13)
    s.text(1600, yy - 12, nums, 10.5, anchor="end", color=ACC)
    s.dot(1480, yy)
    s.line(1480, yy, 1480, yy + 14)
    s.line(1467, yy + 14, 1493, yy + 14, 2.4)
    s.line(1467, yy + 21, 1493, yy + 21, 2.4)
    s.line(1480, yy + 21, 1480, yy + 32)
    s.gnd(1480, yy + 32)

s.note(60, 850, [
    "· 스위칭 레귤레이터를 쓰지 않는다. 12bit ADC 보드에 1~2MHz 스위칭 노이즈를 들이지 않는 쪽이 이득.",
    "· 비율계측(센서 VCC = VREFH) 덕분에 LDO 노이즈/PSRR은 상당 부분 상쇄된다 → 전류·열·안정성이 선정 기준.",
    "· 손실: 아날로그 0.25A x 1.7V = 0.43W (θJA 128℃/W → 약 54℃ 상승), 디지털 0.1A x 1.7V = 0.17W (22℃).",
    "· TAB = VOUT 이므로 방열 동박은 출력 네트로 깐다. 100mm² 이상 권장.",
    "· 아날로그 레일은 반드시 하나. 둘로 쪼개면 VREFH가 한쪽만 따라가 비율계측이 깨진다.",
    "· AP2114H를 고른 이유: 출력 커패시턴스 상한 규정이 없다. 센서 96개 바이패스 9.6uF + 벌크가 붙는 레일이다.",
], w=900, title="설계 판단")

s.save(f"{OUT}/sch-1-power.svg")

# =====================================================================
# SHEET 2 — 코어 DCDC + 내부 LDO 캡
# =====================================================================
s = Sheet(1560, 900, "2 / 3   코어 전원  —  내장 DCDC (VDD_SOC)",
          "데이터시트 Rev0.11 표7: L1 = 2.2~10uH (typ 4.7uH), C1 = 33~66uF")

s.netflag(60, 180, "+3V3D", "right")
s.wire((160, 180), (420, 180))
s.dot(250, 180)
s.cap(250, 180, "C4", "10uF/10V", sub="0603")
s.dot(330, 180)
s.cap(330, 180, "C37", "100nF", sub="0402")

# MCU DCDC block
s.rect(420, 130, 240, 340, fill="#f4f7fb")
s.text(540, 118, "U1C", 15, anchor="middle", weight="bold")
s.text(540, 492, "HPM5361ICB1", 13, anchor="middle", weight="bold")
s.text(540, 300, "내장 DCDC", 14, anchor="middle", color=GRAY)

for (yy, num, nm, side) in [(180, 30, "DCDC_IN", "l"), (250, 29, "DCDC_LP", "r"),
                            (330, 21, "DCDC_SNS", "r"), (420, 28, "DCDC_GND", "l")]:
    if side == "l":
        s.text(430, yy + 5, nm, 13)
        s.text(402, yy - 8, str(num), 11, anchor="middle", color=ACC)
    else:
        s.text(650, yy + 5, nm, 13, anchor="end")
        s.text(678, yy - 8, str(num), 11, anchor="middle", color=ACC)

# DCDC_GND
s.wire((420, 420), (350, 420))
s.gnd(350, 420, "단일점")

# DCDC_LP -> L1 -> VDD_SOC
s.wire((660, 250), (740, 250))
x, y = s.ind_h(740, 250, "L1", "4.7uH  C6807738")
s.wire((x, y), (900, y))
s.dot(900, 250)
s.netflag(900, 250, "VDD_SOC", "right")

# VDD_SOC bus
s.wire((900, 250), (900, 330))
s.wire((900, 330), (1460, 330))
# DCDC_SNS kelvin
s.wire((660, 330), (900, 330))
s.dot(900, 330)
s.text(700, 318, "켈빈 감지선 (전류 경로 아님)", 11.5, color=ACC)

for i, (xx, nm, val, sub) in enumerate([
        (980, "C1", "22uF/6.3V", "0603"), (1080, "C2", "22uF/6.3V", "0603"),
        (1180, "C3", "22uF/6.3V", "0603")]):
    s.dot(xx, 330)
    s.cap(xx, 330, nm, val, sub=sub)

s.dot(1330, 330)
s.cap(1330, 330, "C5~C12", "100nF x8", sub="VDD_SOC 8핀 각각")

# VDD_SOC pins box
s.rect(1460, 250, 90, 170, fill="#f4f7fb")
s.text(1505, 238, "U1C", 14, anchor="middle", weight="bold")
s.text(1505, 442, "VDD_SOC 8핀", 12.5, anchor="middle", weight="bold")
s.text(1505, 306, "7, 17, 20, 44", 11, anchor="middle", color=ACC)
s.text(1505, 322, "57, 69, 83, 94", 11, anchor="middle", color=ACC)
s.text(1505, 360, "전부 연결", 11, anchor="middle", color=GRAY)

# internal LDO caps
s.rect(420, 590, 240, 200, fill="#f4f7fb")
s.text(540, 578, "U1C", 15, anchor="middle", weight="bold")
s.text(540, 812, "내부 LDO 출력 — 외부 급전 금지", 12.5, anchor="middle", weight="bold", color=ACC)
for (yy, num, nm) in [(650, 33, "VDD_PMCCAP"), (740, 23, "VDD_OTPCAP")]:
    s.text(650, yy + 5, nm, 13, anchor="end")
    s.text(678, yy - 8, str(num), 11, anchor="middle", color=ACC)
    s.wire((660, yy), (800, yy))
    s.dot(800, yy)

s.cap(800, 650, "C25", "4.7uF", sub="0603")
s.wire((800, 650), (900, 650))
s.cap(900, 650, "C26", "100nF", sub="0402")
s.cap(800, 740, "C27", "4.7uF", sub="0603")
s.wire((800, 740), (900, 740))
s.cap(900, 740, "C28", "100nF", sub="0402")

s.note(1000, 590, [
    "전류 (표19): 480/160MHz 전주변장치 ON → IDD 59.9mA @3.3V",
    "DCDC 출력 ≈ 139mA @1.275V,  리플 83mA p-p (fsw 2MHz 가정)",
    "→ 인덕터 Isat 요구 0.4A. 선정품 2.2A로 5배 여유.",
    "",
    "C1~C3 유효용량 (최악): 22 x 0.8 x 0.85 x 0.85 = 12.7uF x3 = 38uF",
    "→ 규격 33~66uF 만족. 0805 22uF 2개(29uF)는 미달.",
], w=520, title="수치 근거")

s.save(f"{OUT}/sch-2-core.svg")

# =====================================================================
# SHEET 3 - clock / reset / boot / vbus
# =====================================================================
s = Sheet(1700, 1060, "3 / 3   클럭 · 리셋 · 부트 · VBUS 감지",
          "LQFP100은 내부 RC 부팅 미지원 → 24MHz 크리스털은 필수 부품")


def mcubox(sh, x, y, w, h, ref, pins):
    """pins: list of (ypos, pinnum, name). wire exits to the right at x+w."""
    sh.rect(x, y, w, h, fill="#f4f7fb")
    sh.text(x + w / 2, y - 12, ref, 15, anchor="middle", weight="bold")
    sh.text(x + w / 2, y + h + 22, "HPM5361ICB1", 12, anchor="middle", weight="bold")
    for (yy, num, nm) in pins:
        sh.text(x + 12, yy + 5, nm, 13)
        sh.line(x + w, yy, x + w + 40, yy)
        sh.text(x + w + 20, yy - 8, str(num), 11, anchor="middle", color=ACC)


def xtal_v(sh, x, y1, y2, name, lines):
    """vertical crystal between (x,y1) and (x,y2)"""
    mid = (y1 + y2) / 2
    sh.line(x, y1, x, mid - 35)
    sh.line(x - 20, mid - 35, x + 20, mid - 35, 2.6)
    sh.rect(x - 15, mid - 28, 30, 56)
    sh.line(x - 20, mid + 35, x + 20, mid + 35, 2.6)
    sh.line(x, mid + 35, x, y2)
    sh.text(x + 32, mid - 12, name, 13.5, weight="bold")
    for i, ln in enumerate(lines):
        sh.text(x + 32, mid + 6 + i * 17, ln, 12, color=GRAY)


# ---- crystal ----
mcubox(s, 120, 130, 180, 260, "U1D", [(190, 74, "XTALI"), (330, 75, "XTALO")])
s.wire((340, 190), (470, 190))
s.wire((340, 330), (470, 330))
s.dot(390, 190)
s.cap(390, 190, "C33", "12pF", sub="C0G 0402")
s.dot(390, 330)
s.cap(390, 330, "C34", "12pF", sub="C0G 0402")
xtal_v(s, 470, 190, 330, "X1", ["24MHz · CL 10pF", "±10ppm · ESR 50Ω", "C70583 (Basic)", "패드 2,4 = GND"])

s.note(700, 140, [
    "발진기가 보는 부하 = 12pF ∥ 12pF + stray 3.5pF ≈ 9.5pF",
    "크리스털 규격 10pF 대비 +11ppm   (USB HS 요구 ±500ppm)",
    "ESR 50Ω ≤ 데이터시트 규격 40~80Ω (표13)",
    "배선 5mm 이내 · 하부 통 GND · 주변 디지털 신호 금지",
    "이 회로가 죽으면 칩이 부팅되지 않는다 (표44)",
], w=560, title="24MHz 수치 근거")

# ---- reset ----
mcubox(s, 120, 500, 180, 120, "U1D", [(560, 26, "RESETN")])
s.wire((340, 560), (620, 560))
s.dot(430, 560)
s.cap(430, 560, "C35", "100nF", sub="0402")
s.dot(540, 560)
s.res_v(540, 460, "R1", "10k")
s.wire((540, 516), (540, 560))
s.wire((540, 460), (540, 440))
s.netflag(540, 440, "+3V3D", "right")
s.rect(620, 540, 76, 40)
s.text(658, 565, "SW1", 12.5, anchor="middle", weight="bold")
s.wire((696, 560), (750, 560))
s.gnd(750, 560)
s.text(620, 606, "리셋 버튼 (옵션)", 11.5, color=GRAY)
s.text(120, 672, "RESET_N 저레벨 요구 ≥ 300us (표12)  →  10k x 100nF = 1ms 로 충족", 12.5, color=ACC)

# ---- boot ----
mcubox(s, 120, 760, 180, 190, "U1D", [(820, 18, "PA03 / BOOT1"), (910, 19, "PA02 / BOOT0")])
s.wire((340, 820), (440, 820))
s.res_v(440, 820, "R2", "10k")
s.gnd(440, 876)
s.wire((340, 910), (620, 910))
s.dot(440, 910)
s.res_v(440, 910, "R3", "10k")
s.gnd(440, 966)
s.rect(620, 890, 76, 40)
s.text(658, 915, "SW2", 12.5, anchor="middle", weight="bold")
s.wire((696, 910), (770, 910))
s.netflag(770, 910, "+3V3D", "right")
s.text(560, 968, "누른 채 전원 인가 = USB DFU 진입 (패드 필수)", 12, color=ACC)

s.note(900, 770, [
    "BOOT_MODE[1:0] = [PA03 : PA02]   (표4)",
    "0 0 → XPI NOR 부팅  (정상 동작)",
    "0 1 → ISP / 시리얼 부팅  ← LQFP100은 USB0 사용 가능",
    "1 0 → ISP / 시리얼 부팅",
    "1 1 → 예약",
], w=520, title="부트 모드")

# ---- wakeup / usbvbus ----
mcubox(s, 1150, 440, 180, 200, "U1D", [(500, 27, "WAKEUP"), (600, 68, "USBVBUS")])
s.wire((1370, 500), (1560, 500))
s.res_v(1560, 500, "R4", "10k")
s.gnd(1560, 556)
s.text(1150, 700, "WAKEUP 극성은 데이터시트 미기재 →", 11.5, color=GRAY)
s.text(1150, 718, "패드만 남기고 확정 레벨로 고정", 11.5, color=GRAY)

s.wire((1370, 600), (1420, 600))
s.dot(1420, 600)
s.cap(1420, 600, "C36", "100nF", sub="0402", lab_dx=-62)
x, y = s.res_h(1450, 600, "R5", "1k")
s.wire((x, y), (1560, y))
s.netflag(1560, 600, "VBUS 5V", "right")
s.text(1150, 752, "USBVBUS 최대 5.5V 허용 (표8) → VBUS 직결 가능", 11.5, color=GRAY)

s.save(f"{OUT}/sch-3-clock.svg")
