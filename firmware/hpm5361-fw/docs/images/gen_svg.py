#!/usr/bin/env python3
# HPM5361 부팅/메모리 문서용 SVG 다이어그램 생성기
import os, html

OUT = "/Users/hancheol/hdd/git/hpm5300evk/firmware/hpm5361-fw/docs/images"
os.makedirs(OUT, exist_ok=True)

MONO = "ui-monospace,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',sans-serif"

BG      = "#ffffff"
INK     = "#1f2328"
MUTED   = "#6a737d"
LINE    = "#8c959f"

# 팔레트
ROM_F, ROM_S     = "#dbeafe", "#3b82f6"   # BootROM / 부팅 단계
FLASH_F, FLASH_S = "#fef3c7", "#d97706"   # 플래시
RAM_F, RAM_S     = "#dcfce7", "#16a34a"   # RAM
PER_F, PER_S     = "#f3f4f6", "#9ca3af"   # 주변장치 / 기타
WARN_F, WARN_S   = "#fee2e2", "#dc2626"   # 예약 / 주의
GAP_F, GAP_S     = "#fafbfc", "#d0d7de"   # 빈 영역
APP_F, APP_S     = "#ede9fe", "#7c3aed"   # 애플리케이션


class Svg:
    def __init__(self, w, h, title=""):
        self.w, self.h, self.title = w, h, title
        self.p = []

    def rect(self, x, y, w, h, fill=BG, stroke=LINE, rx=5, sw=1.2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                      f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=13, fill=INK, anchor="start", mono=False,
             weight="400", family=None, opacity=None):
        fam = family or (MONO if mono else SANS)
        op = f' opacity="{opacity}"' if opacity else ""
        self.p.append(f'<text xml:space="preserve" x="{x}" y="{y}" font-family="{fam}" '
                      f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
                      f'font-weight="{weight}"{op}>{html.escape(s)}</text>')

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1.2, dash=None, marker=False):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#a)"' if marker else ""
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                      f'stroke-width="{sw}"{d}{m}/>')

    def path(self, d, stroke=LINE, sw=1.2, fill="none", dash=None, marker=False):
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#a)"' if marker else ""
        self.p.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{ds}{m}/>')

    def diamond(self, cx, cy, rw, rh, fill=PER_F, stroke=PER_S, sw=1.2):
        self.p.append(f'<polygon points="{cx},{cy-rh} {cx+rw},{cy} {cx},{cy+rh} {cx-rw},{cy}" '
                      f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def save(self, name):
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{html.escape(self.title)}">\n'
                f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
                f'markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>\n'
                f'<rect width="{self.w}" height="{self.h}" fill="{BG}"/>\n')
        with open(os.path.join(OUT, name), "w") as f:
            f.write(head + "\n".join(self.p) + "\n</svg>\n")
        print("  ", name)


def boxlines(s, x, y, w, lines, dy=19, pad=14, size=12.5, mono=True, fill=INK):
    for i, ln in enumerate(lines):
        s.text(x + pad, y + pad + 12 + i * dy, ln, size=size, mono=mono, fill=fill)


# ────────────────────────────────────────────────────────────── 1. 부팅 개요
def boot_overview():
    s = Svg(1010, 470, "HPM5361 부팅 개요")
    s.text(505, 28, "전원 인가부터 apMain() 까지", size=15, anchor="middle", weight="600")

    cols = [(30, 165, "[1] 전원", "", ""),
            (295, 275, "[2] BootROM", "0x2000_0000 실행", "클럭: RC24M / XTAL24M"),
            (680, 300, "[3] 애플리케이션", "0x8000_3000 실행", "클럭: 24MHz → 480MHz")]
    for x, w, t, a, b in cols:
        s.text(x, 60, t, size=13.5, weight="700")
        if a:
            s.text(x, 78, a, size=11.5, mono=True, fill=MUTED)
            s.text(x, 94, b, size=11.5, fill=MUTED)

    # [1] 전원
    s.rect(30, 108, 165, 86, ROM_F, ROM_S)
    boxlines(s, 30, 108, 165, ["VPMC 3.3V 상승", "(POR)", "", "RESETN ↑ 해제"], mono=False, dy=18)

    # [2] BootROM
    s.rect(295, 108, 275, 300, ROM_F, ROM_S)
    s.line(295, 196, 570, 196, ROM_S, 1)
    s.line(295, 288, 570, 288, ROM_S, 1)
    s.text(309, 128, "① ROM 런타임 초기화", size=12.5, weight="700")
    boxlines(s, 295, 128, 275, ["ROM BSS / RW 초기화", "ROM 클럭 초기화",
                                "BOOT_MODE 핀 샘플링"], dy=18, size=12, mono=False)
    s.text(309, 216, "② 부트 모드 분기", size=12.5, weight="700")
    boxlines(s, 295, 216, 275, ["→ XPI NOR 부팅", "→ 시리얼 / ISP",
                                "→ 저전력 웨이크업"], dy=18, size=12, mono=False)
    s.text(309, 308, "③ XPI NOR 부팅", size=12.5, weight="700")
    boxlines(s, 295, 308, 275, ["0x400  cfg option 읽기", "0x1000 부트 헤더 읽기",
                                "이미지 검증", "DEBUG 포트 개방"], dy=18, size=12, mono=False)

    # [3] 애플리케이션
    s.rect(680, 108, 300, 300, APP_F, APP_S)
    app = ["_start   (start.S)", "   gp / tp / sp 설정, FPU 활성",
           "   I$ / D$ enable", "   c_startup()", "   __libc_init_array()",
           "   _clean_up()", "   mtvec ← 벡터 테이블", "   reset_handler()",
           "      system_init()", "      main()", "         bspInit()",
           "         hwInit()", "         apInit() / apMain()"]
    boxlines(s, 680, 108, 300, app, dy=20, size=12, mono=True)

    # 화살표
    s.line(195, 151, 291, 151, LINE, 1.4, marker=True)
    s.text(243, 143, "전역 리셋", size=11, anchor="middle", fill=MUTED)
    s.line(570, 258, 676, 258, LINE, 1.4, marker=True)
    s.text(623, 250, "entry_point", size=11, anchor="middle", fill=MUTED, mono=True)
    s.text(623, 274, "로 점프", size=11, anchor="middle", fill=MUTED)

    s.text(112, 428, "수 ms", size=11.5, anchor="middle", fill=MUTED)
    s.text(432, 428, "수 ms", size=11.5, anchor="middle", fill=MUTED)
    s.text(830, 428, "여기부터 사용자 코드", size=11.5, anchor="middle", fill=MUTED)
    s.text(505, 456, "BootROM 은 점프 직전에 DEBUG 포트를 연다 — 그래서 디버거는 _start 부터 붙는다 (UM 19.6)",
           size=11, anchor="middle", fill=MUTED)
    s.save("boot-overview.svg")


# ────────────────────────────────────────────────────────────── 2. 리셋 도메인
def reset_domain():
    s = Svg(830, 400, "HPM5361 리셋 도메인")
    s.text(415, 28, "리셋 도메인과 리셋 범위 (UM 9장)", size=15, anchor="middle", weight="600")

    s.rect(130, 55, 470, 120, "#eff6ff", ROM_S)
    s.text(148, 78, "전원 관리 도메인", size=13, weight="700")
    s.rect(148, 92, 120, 44, WARN_F, WARN_S)
    s.text(208, 119, "PDGO", size=13, anchor="middle", weight="700", mono=True)
    s.rect(282, 92, 300, 44, PER_F, PER_S)
    s.text(432, 111, "PCFG / PPOR / PGPIO / PUART", size=11.5, anchor="middle", mono=True)
    s.text(432, 127, "PTMR / PEWDG", size=11.5, anchor="middle", mono=True)

    s.rect(130, 235, 470, 100, "#f0fdf4", RAM_S)
    s.text(148, 258, "시스템 전원 도메인", size=13, weight="700")
    s.rect(148, 272, 434, 48, PER_F, PER_S)
    s.text(365, 291, "CPU0 서브시스템 / 대부분의 주변장치", size=11.5, anchor="middle")
    s.text(365, 308, "OTP 섀도우 레지스터 유지, DEBUG 회로 유지", size=11.5, anchor="middle", fill=MUTED)

    s.line(365, 175, 365, 231, LINE, 1.4, marker=True)
    s.text(375, 208, "냉복위(Cold Reset)", size=11.5, fill=MUTED)

    # 전역 리셋 브래킷
    s.path("M 110,55 L 96,55 L 96,175 L 110,175", WARN_S, 1.4)
    s.text(88, 118, "전역 리셋", size=11.5, anchor="end", fill=WARN_S, weight="600")

    s.rect(630, 55, 175, 280, GAP_F, GAP_S)
    s.text(645, 78, "리셋 트리거", size=12.5, weight="700")
    trig = ["전역 리셋", "  VPMC 상승 (POR)", "  RESETN 핀 로우", "",
            "냉복위", "  VPMC < 약 2.7V", "  디버거 리셋", "  워치독 만료",
            "  보안 위반", "  소프트 리셋", "", "PDGO 까지",
            "  VPMC < 약 2.5V"]
    for i, t in enumerate(trig):
        w = "700" if t and not t.startswith(" ") else "400"
        c = INK if w == "700" else MUTED
        s.text(645, 100 + i * 17, t, size=11, weight=w, fill=c)

    s.text(415, 372, ".noinit 은 냉복위에서 살아남고 전원 차단에서 사라진다",
           size=11, anchor="middle", fill=MUTED)
    s.save("reset-domain.svg")


# ────────────────────────────────────────────────────────────── 3. BootROM 분기
def bootrom_flow():
    s = Svg(880, 680, "BootROM 부팅 흐름도")
    s.text(440, 28, "BootROM 부팅 흐름도 (UM 그림12)", size=15, anchor="middle", weight="600")

    def cbox(cx, y, w, h, lines, fill=ROM_F, stroke=ROM_S, size=12, dy=17):
        s.rect(cx - w / 2, y, w, h, fill, stroke)
        n = len(lines)
        y0 = y + h / 2 - (n - 1) * dy / 2 + 4
        for i, ln in enumerate(lines):
            s.text(cx, y0 + i * dy, ln, size=size, anchor="middle",
                   mono=not any(ord(c) > 0x2FFF for c in ln))

    cbox(250, 50, 210, 44, ["BootROM 진입  0x2000_0000"], ROM_F, ROM_S)
    s.line(250, 94, 250, 116, LINE, 1.3, marker=True)

    s.diamond(250, 148, 118, 32, "#fff7ed", "#ea580c")
    s.text(250, 152, "저전력 웨이크업 이벤트?", size=11.5, anchor="middle")

    # 예 → 오른쪽
    s.line(368, 148, 560, 148, LINE, 1.3, marker=True)
    s.text(462, 140, "예", size=11, anchor="middle", fill=MUTED)
    cbox(680, 124, 210, 48, ["wakeup entry 검증", "(SYSCTL.CPU0_GPR0)"], "#fff7ed", "#ea580c")
    s.line(680, 172, 680, 196, LINE, 1.3, marker=True)
    s.text(690, 190, "유효", size=11, fill=MUTED)
    cbox(680, 196, 210, 40, ["wakeup entry 로 점프"], RAM_F, RAM_S)
    # 무효 → 전체 부팅 흐름으로 되돌아옴
    s.path("M 785,148 L 845,148 L 845,196 L 262,196 L 262,210", LINE, 1.3,
           dash="4 3", marker=True)
    s.text(853, 174, "무효", size=11, fill=MUTED)

    s.line(250, 180, 250, 214, LINE, 1.3, marker=True)
    s.text(240, 209, "아니오", size=11, anchor="end", fill=MUTED)

    cbox(250, 214, 250, 74, ["① ROM BSS / RW 초기화",
                             "② ROM 클럭 초기화",
                             "③ BOOT_MODE 핀 초기화"], ROM_F, ROM_S)
    s.line(250, 288, 250, 320, LINE, 1.3, marker=True)

    cbox(250, 320, 250, 40, ["OTP word16  BOOT_MODE 확인"], "#f5f3ff", APP_S)

    # OTP 값 분기
    s.line(250, 360, 250, 386, LINE, 1.3)
    s.line(96, 386, 790, 386, LINE, 1.3)
    branch = [(96, "값 = 0"), (330, "값 = 1"), (560, "값 = 2"), (790, "값 = 4")]
    for x, lab in branch:
        s.line(x, 386, x, 414, LINE, 1.3, marker=True)
        s.text(x + 6, 402, lab, size=11, fill=MUTED, mono=True)

    cbox(96, 414, 170, 40, ["BOOT_MODE 핀 확인"], "#f5f3ff", APP_S)
    cbox(330, 414, 150, 40, ["XPI NOR 부팅"], RAM_F, RAM_S)
    cbox(560, 414, 150, 40, ["시리얼 부팅"], FLASH_F, FLASH_S)
    cbox(790, 414, 140, 40, ["ISP 모드"], FLASH_F, FLASH_S)

    # 핀 분기 — 전 폭을 써서 한 줄로 펼친다
    s.line(96, 454, 96, 500, LINE, 1.3)
    s.line(96, 500, 660, 500, LINE, 1.3)
    pins = [(96, "00"), (284, "01"), (472, "10"), (660, "11")]
    for x, lab in pins:
        s.line(x, 500, x, 532, LINE, 1.3, marker=True)
        s.text(x + 7, 518, lab, size=11, fill=MUTED, mono=True)
    cbox(96, 532, 150, 46, ["XPI NOR 부팅"], RAM_F, RAM_S)
    cbox(284, 532, 150, 46, ["시리얼 / ISP"], FLASH_F, FLASH_S)
    cbox(472, 532, 150, 46, ["시리얼 / ISP"], FLASH_F, FLASH_S)
    cbox(660, 532, 150, 46, ["while(1) 루프"], WARN_F, WARN_S)
    s.text(96, 600, "정상 동작", size=10.5, anchor="middle", fill=RAM_S, weight="600")
    s.text(660, 600, "예약 — 빠져나오지 못한다", size=10.5, anchor="middle",
           fill=WARN_S, weight="600")

    s.text(440, 646, "[PA03:PA02] = BOOT_MODE[1:0]  ·  OTP word16 = 0 (미퓨징) 이면 핀이 결정한다",
           size=11.5, anchor="middle", fill=MUTED)
    s.save("bootrom-flow.svg")


# ────────────────────────────────────────────────────────────── 4. XPI NOR 부팅
def xpi_nor_flow():
    s = Svg(900, 740, "XPI NOR 부팅 흐름")
    s.text(440, 28, "XPI NOR 부팅 흐름 (UM 그림14)", size=15, anchor="middle", weight="600")

    CX = 340
    def stage(y, h, lines, fill=RAM_F, stroke=RAM_S, w=420):
        s.rect(CX - w / 2, y, w, h, fill, stroke)
        n = len(lines)
        y0 = y + h / 2 - (n - 1) * 17 / 2 + 4
        for i, ln in enumerate(lines):
            s.text(CX, y0 + i * 17, ln, size=12, anchor="middle")

    stage(50, 38, ["XPI NOR 부팅 진입"], ROM_F, ROM_S)
    s.line(CX, 88, CX, 108, LINE, 1.3, marker=True)

    s.diamond(CX, 136, 150, 28, "#fff7ed", "#ea580c")
    s.text(CX, 132, "OTP XPI_NOR_CFG_SRC == 0 ?", size=11, anchor="middle")
    s.text(CX, 147, "(설정을 플래시에서 읽는가)", size=10, anchor="middle", fill=MUTED)

    # 아니오 → 오른쪽 (OTP 경로)
    s.line(CX + 150, 136, 640, 136, LINE, 1.3, marker=True)
    s.text(560, 128, "아니오", size=11, anchor="middle", fill=MUTED)
    s.rect(640, 108, 215, 56, PER_F, PER_S)
    s.text(747, 130, "OTP 의 PROBE_TYPE,", size=11, anchor="middle", mono=True)
    s.text(747, 146, "XPI_FREQ_OPTION 등으로 초기화", size=11, anchor="middle")

    s.line(CX, 164, CX, 190, LINE, 1.3, marker=True)
    s.text(CX + 8, 182, "예", size=11, fill=MUTED)

    stage(190, 56, ["① XPI_DEFAULT_READ (1-1-1, 0x03) 로 XPI 임시 초기화",
                    "② FLASH 0x400 에서 cfg option 16B 읽기"], FLASH_F, FLASH_S)
    s.line(CX, 246, CX, 268, LINE, 1.3, marker=True)

    s.diamond(CX, 294, 140, 26, "#fff7ed", "#ea580c")
    s.text(CX, 298, "tag == 0xfcf90 ?", size=11.5, anchor="middle", mono=True)

    s.line(CX, 320, CX, 344, LINE, 1.3, marker=True)
    s.text(CX + 8, 336, "예", size=11, fill=MUTED)
    stage(344, 40, ["③ 읽은 option 대로 XPI 재초기화 → FLASH 재검출"], FLASH_F, FLASH_S)
    s.line(CX, 384, CX, 406, LINE, 1.3, marker=True)

    s.diamond(CX, 432, 140, 26, "#fff7ed", "#ea580c")
    s.text(CX, 436, "FLASH 정상 인식?", size=11.5, anchor="middle")

    s.line(CX, 458, CX, 482, LINE, 1.3, marker=True)
    s.text(CX + 8, 474, "예", size=11, fill=MUTED)
    stage(482, 62, ["④ FLASH 0x1000 에서 부트 헤더 읽기",
                    "SEC_IMG_OFFSET ≠ 0 이면 두 번째 이미지도 읽어",
                    "sw_version 이 큰 쪽을 최신으로 선택"], FLASH_F, FLASH_S)
    s.line(CX, 544, CX, 566, LINE, 1.3, marker=True)

    s.diamond(CX, 592, 165, 26, "#fff7ed", "#ea580c")
    s.text(CX, 596, "tag==0xBF, version==0x10, FW 유효?", size=10.5, anchor="middle", mono=True)

    s.line(CX, 618, CX, 640, LINE, 1.3, marker=True)
    s.text(CX + 8, 634, "예", size=11, fill=MUTED)
    stage(640, 40, ["⑤ entry_point 로 점프  (0x8000_3000 = _start)"], RAM_F, RAM_S)

    # 실패 경로 → 시리얼 부팅 (세 갈래가 한 줄기로 합쳐진다)
    s.rect(690, 300, 165, 44, WARN_F, WARN_S)
    s.text(772, 320, "시리얼 부팅으로", size=11.5, anchor="middle")
    s.text(772, 336, "하강", size=11.5, anchor="middle")
    s.line(640, 294, 640, 592, WARN_S, 1.2, dash="4 3")
    for y, rw in ((294, 140), (432, 140), (592, 165)):
        s.line(CX + rw, y, 640, y, WARN_S, 1.2, dash="4 3")
        s.text(CX + rw + 10, y - 7, "아니오", size=10, fill=WARN_S)
    s.line(640, 322, 686, 322, WARN_S, 1.2, dash="4 3", marker=True)

    s.text(440, 712, "cfg option 이 깨지면 칩은 자기 플래시를 못 읽고 USB HID 로 뜬다",
           size=11, anchor="middle", fill=MUTED)
    s.save("xpi-nor-boot.svg")


# ────────────────────────────────────────────────────────────── 5. 플래시 레이아웃
def flash_layout():
    segs = [
        ("0x8000_0000", 28, "(미사용)",                       "1,024 B",   GAP_F,   GAP_S,   False),
        ("0x8000_0400", 34, ".nor_cfg_option",                "16 B",      ROM_F,   ROM_S,   True),
        (None,          22, "(미사용)",                       "",          GAP_F,   GAP_S,   False),
        ("0x8000_1000", 40, ".boot_header",                   "144 B",     ROM_F,   ROM_S,   True),
        (None,          22, "(미사용)",                       "",          GAP_F,   GAP_S,   False),
        ("0x8000_2000", 30, ".version   (firm_ver)",          "72 B",      PER_F,   PER_S,   False),
        (None,          22, "(미사용)",                       "",          GAP_F,   GAP_S,   False),
        ("0x8000_3000", 32, ".start        ← entry_point",    "80 B",      FLASH_F, FLASH_S, False),
        ("0x8000_3050", 32, ".vectors LMA  → ILM 0x0 복사",   "952 B",     FLASH_F, FLASH_S, False),
        ("0x8000_3408", 58, ".text + .rodata   ← XIP 실행",   "77,552 B",  FLASH_F, FLASH_S, False),
        ("0x8001_62F8", 26, ".eh_frame",                      "40 B",      FLASH_F, FLASH_S, False),
        ("0x8001_6320", 30, ".data LMA     → DLM 복사",       "600 B",     FLASH_F, FLASH_S, False),
        ("0x8001_6578", 66, "미사용",                          "956,040 B", GAP_F,   GAP_S,   False),
    ]
    top, X, W = 76, 190, 420
    h = top + sum(x[1] for x in segs) + 90
    s = Svg(820, h, "플래시 레이아웃")
    s.text(410, 28, "플래시 레이아웃 — 내장 1MB NOR (XPI0)", size=15, anchor="middle", weight="600")
    s.text(410, 48, "본 프로젝트 실측값 · build/hpm5361-fw.bin", size=11.5, anchor="middle", fill=MUTED)

    y = top
    fw_top = fw_bot = None
    for addr, hh, label, size_s, fill, stroke, rom in segs:
        s.rect(X, y, W, hh, fill, stroke, rx=0, sw=1.1)
        if addr:
            s.text(X - 10, y + 13, addr, size=11.5, anchor="end", mono=True)
        s.text(X + 14, y + hh / 2 + 4, label, size=12,
               mono=not any(ord(c) > 0x2FFF for c in label))
        if size_s:
            s.text(X + W - 14, y + hh / 2 + 4, size_s, size=11.5, anchor="end",
                   mono=True, fill=MUTED)
        if rom:
            s.text(X + W + 16, y + hh / 2 + 4, "← ROM 이 읽는다", size=11, fill=ROM_S, weight="600")
        if addr == "0x8000_3000":
            fw_top = y
        if addr == "0x8001_6578":
            fw_bot = y
        y += hh
    s.text(X - 10, y + 13, "0x8010_0000", size=11.5, anchor="end", mono=True)
    s.line(X, y, X + W, y, GAP_S, 1.1)

    # FW Info Table 커버리지 브래킷
    bx = X + W + 30
    s.path(f"M {bx},{fw_top} L {bx+12},{fw_top} L {bx+12},{fw_bot} L {bx},{fw_bot}", FLASH_S, 1.6)
    s.text(bx + 20, (fw_top + fw_bot) / 2 - 6, "FW Info Table", size=11, fill=FLASH_S, weight="600")
    s.text(bx + 20, (fw_top + fw_bot) / 2 + 9, "size = 79,224 B", size=11, fill=FLASH_S, mono=True)

    s.text(410, h - 44, "기록되는 총 바이트  90,488 B  (0x8000_0400 ~ 0x8001_6578)  ·  1MB 중 8.6%",
           size=11.5, anchor="middle", fill=MUTED)
    s.text(410, h - 24, "페이지 256 B / 4096 페이지 · 소거 단위 1K, 4K, 32K, 64K, 전체 (DS 4.2절)",
           size=11, anchor="middle", fill=MUTED)
    s.save("flash-layout.svg")


# ────────────────────────────────────────────────────────────── 6. 시스템 메모리 맵
def system_memory_map():
    segs = [
        ("0x0000_0000", "CPU0 ILM   명령 로컬 메모리",       "128 K", RAM_F,   RAM_S),
        ("0x0006_0000", "ILM 별칭",                           "128 K", GAP_F,   GAP_S),
        ("0x0008_0000", "CPU0 DLM   데이터 로컬 메모리",     "128 K", RAM_F,   RAM_S),
        ("0x000A_0000", "DLM 별칭",                           "128 K", GAP_F,   GAP_S),
        ("0x000C_0000", "FGPIO   CPU 로컬 버스 GPIO",         "256 K", PER_F,   PER_S),
        ("0x0104_0000", "ILM 미러",                           "128 K", GAP_F,   GAP_S),
        ("0x0106_0000", "DLM 미러",                           "128 K", GAP_F,   GAP_S),
        ("0x2000_0000", "BOOT ROM   부팅 코드 + ROM API",     "128 K", ROM_F,   ROM_S),
        ("0x3000_0000", "DM   디버그 모듈",                   "1 M",   PER_F,   PER_S),
        ("0x8000_0000", "XPI0 창   내장 1MB NOR (XIP)",       "255 M", FLASH_F, FLASH_S),
        ("0xE400_0000", "PLIC   플랫폼 인터럽트 컨트롤러",    "4 M",   PER_F,   PER_S),
        ("0xE600_0000", "MCHTMR   머신 타이머 (1ms 틱)",      "1 M",   PER_F,   PER_S),
        ("0xE640_0000", "PLICSW   소프트웨어 인터럽트",       "4 M",   PER_F,   PER_S),
    ]
    apb1 = ["GPTMR0~3 / UART0~7 / I2C0~3 / SPI0~3",
            "CRC / TSNS / MBX / EWDG0,1 / MISC",
            "DMAMUX / HDMA / GPIO0 / GPIOM",
            "MCAN0~3 / PTPC / QEI / QEO / MMC",
            "PWM / RDC / PLB / SYNT / SEI / TRGM0"]
    apb2 = ["XPI0 / USB0 / SDP / SEC / MON / RNG",
            "OTP / KEYM / ADC0,1 / DAC0,1",
            "OPAMP0,1 / ACMP"]
    pmc = ["PPOR / PCFG / PGPR0,1 / PIOC / PGPIO",
           "PTMR / PUART / PEWDG / PDGO"]

    top, X, W, HH = 76, 190, 430, 30
    h = top + len(segs) * HH + 5 * 30 + 3 * 30 + 3 * 30 + 3 * 30 + 120
    s = Svg(830, h, "시스템 메모리 맵")
    s.text(415, 28, "시스템 메모리 맵 (UM 표29)", size=15, anchor="middle", weight="600")
    s.text(415, 48, "32비트 주소 공간 전체 · 비례 축척 아님", size=11.5, anchor="middle", fill=MUTED)

    y = top
    for addr, label, size_s, fill, stroke in segs:
        s.rect(X, y, W, HH, fill, stroke, rx=0, sw=1.1)
        s.text(X - 10, y + 19, addr, size=11.5, anchor="end", mono=True)
        s.text(X + 14, y + 19, label, size=12)
        s.text(X + W - 14, y + 19, size_s, size=11.5, anchor="end", mono=True, fill=MUTED)
        y += HH

    def block(addr, title, lines, fill, stroke):
        nonlocal y
        hh = 22 + len(lines) * 16
        s.rect(X, y, W, hh, fill, stroke, rx=0, sw=1.1)
        s.text(X - 10, y + 17, addr, size=11.5, anchor="end", mono=True)
        s.text(X + 14, y + 17, title, size=12, weight="600")
        for i, ln in enumerate(lines):
            s.text(X + 26, y + 34 + i * 16, ln, size=10.5, mono=True, fill=MUTED)
        y += hh

    block("0xF000_0000", "APB 주변장치 ①", apb1, PER_F, PER_S)
    s.rect(X, y, W, HH, RAM_F, RAM_S, rx=0, sw=1.1)
    s.text(X - 10, y + 19, "0xF040_0000", size=11.5, anchor="end", mono=True)
    s.text(X + 14, y + 19, "AHB SRAM (HRAM)", size=12)
    s.text(X + W - 14, y + 19, "32 K", size=11.5, anchor="end", mono=True, fill=MUTED)
    y += HH
    block("0xF300_0000", "APB 주변장치 ②", apb2, PER_F, PER_S)
    for a, t, sz in [("0xF400_0000", "SYSCTL   시스템 제어", "256 K"),
                     ("0xF404_0000", "IOC   IO 컨트롤러", "256 K"),
                     ("0xF40C_0000", "PLLCTLV2   PLL 컨트롤러", "256 K")]:
        s.rect(X, y, W, HH, PER_F, PER_S, rx=0, sw=1.1)
        s.text(X - 10, y + 19, a, size=11.5, anchor="end", mono=True)
        s.text(X + 14, y + 19, t, size=12)
        s.text(X + W - 14, y + 19, sz, size=11.5, anchor="end", mono=True, fill=MUTED)
        y += HH
    block("0xF410_0000", "전원 관리 도메인", pmc, "#eff6ff", ROM_S)
    s.line(X, y, X + W, y, GAP_S, 1.1)
    s.text(X - 10, y + 13, "0xF413_8000", size=11.5, anchor="end", mono=True)

    s.text(415, y + 48, "온칩 SRAM 288KB = ILM 128K + DLM 128K + AHB SRAM 32K (DS 1절)",
           size=11.5, anchor="middle", fill=MUTED)
    s.text(415, y + 68, "ILM/DLM 은 로컬 주소 · 시스템 버스 별칭 · 미러 세 곳에서 보인다",
           size=11, anchor="middle", fill=MUTED)
    s.h = y + 92
    s.save("system-memory-map.svg")


# ────────────────────────────────────────────────────────────── 7. 내장 메모리 상세
def internal_memory():
    s = Svg(900, 660, "내장 메모리 실제 배치")
    s.text(450, 28, "내장 메모리 실제 배치 — build/hpm5361-fw.elf 실측", size=15,
           anchor="middle", weight="600")

    # ILM (왼쪽)
    X1, W1, T = 120, 200, 70
    s.text(X1 + W1 / 2, 60, "ILM   128 KB", size=13, anchor="middle", weight="700")
    ilm = [("0x0000_0000", 34, ".vectors", "952 B", RAM_F, RAM_S),
           ("0x0000_03B8", 30, ".fast   (비어 있음)", "0 B", GAP_F, GAP_S),
           (None, 262, "미사용   약 127 KB", "", GAP_F, GAP_S)]
    y = T
    for addr, hh, label, sz, f, st in ilm:
        s.rect(X1, y, W1, hh, f, st, rx=0, sw=1.1)
        if addr:
            s.text(X1 - 8, y + 13, addr, size=10.5, anchor="end", mono=True)
        s.text(X1 + 10, y + hh / 2 + 4, label, size=11,
               mono=not any(ord(c) > 0x2FFF for c in label))
        if sz:
            s.text(X1 + W1 - 10, y + hh / 2 + 4, sz, size=10.5, anchor="end",
                   mono=True, fill=MUTED)
        y += hh
    s.text(X1 - 8, y + 13, "0x0002_0000", size=10.5, anchor="end", mono=True)
    s.line(X1, y, X1 + W1, y, GAP_S, 1.1)
    s.text(X1 + W1 / 2, y + 34, "벡터 테이블만 산다", size=10.5, anchor="middle", fill=MUTED)
    s.text(X1 + W1 / 2, y + 50, "99.3% 비어 있음", size=10.5, anchor="middle", fill=RAM_S,
           weight="600")

    # DLM (가운데)
    X2, W2 = 460, 250
    s.text(X2 + W2 / 2, 60, "DLM   128 KB", size=13, anchor="middle", weight="700")
    dlm = [("0x0008_0000", 30, "예약", "768 B", WARN_F, WARN_S),
           ("0x0008_0300", 30, ".data", "600 B", RAM_F, RAM_S),
           ("0x0008_0558", 46, ".bss", "19,624 B", RAM_F, RAM_S),
           ("0x0008_5200", 28, ".noinit   ← 리셋 후 보존", "24 B", "#fef9c3", "#ca8a04"),
           ("0x0008_5218", 24, ".tdata / .tbss / .framebuffer", "0 B", GAP_F, GAP_S),
           ("0x0008_5800", 40, ".noncacheable   USB DMA", "9,224 B", RAM_F, RAM_S),
           ("0x0008_7C08", 36, ".heap", "16,384 B", RAM_F, RAM_S),
           ("0x0008_BC08", 36, ".stack", "16,384 B", RAM_F, RAM_S),
           ("0x0008_FC10", 74, "미사용", "66,544 B", GAP_F, GAP_S),
           ("0x0009_7000", 44, "BootROM BSS / RW / 스택", "36 KB", "#fee2e2", WARN_S)]
    y = T
    stack_top = None
    for addr, hh, label, sz, f, st in dlm:
        s.rect(X2, y, W2, hh, f, st, rx=0, sw=1.1)
        s.text(X2 - 8, y + 13, addr, size=10.5, anchor="end", mono=True)
        s.text(X2 + 10, y + hh / 2 + 4, label, size=11,
               mono=not any(ord(c) > 0x2FFF for c in label))
        s.text(X2 + W2 - 10, y + hh / 2 + 4, sz, size=10.5, anchor="end", mono=True, fill=MUTED)
        if addr == "0x0008_FC10":
            stack_top = y
        y += hh
    s.text(X2 - 8, y + 13, "0x000A_0000", size=10.5, anchor="end", mono=True)
    s.line(X2, y, X2 + W2, y, GAP_S, 1.1)
    s.text(X2 + W2 + 12, stack_top + 4, "← _stack", size=10.5, fill=RAM_S, weight="600")
    s.text(X2 + W2 + 12, stack_top + 20, "여유 29,680 B", size=10.5, fill=MUTED)
    s.text(X2 + W2 + 12, y - 22, "ROM API 호출 시", size=10.5, fill=WARN_S)
    s.text(X2 + W2 + 12, y - 8, "겹칠 수 있다", size=10.5, fill=WARN_S)

    # AHB SRAM (오른쪽)
    X3, W3 = 762, 120
    s.text(X3 + W3 / 2, 60, "AHB SRAM  32 KB", size=13, anchor="middle", weight="700")
    s.text(X3, 86, "0xF040_0000", size=10.5, mono=True)
    s.rect(X3, 94, W3, 120, GAP_F, GAP_S, rx=0, sw=1.1)
    s.text(X3 + W3 / 2, 150, ".ahb_sram", size=11, anchor="middle", mono=True)
    s.text(X3 + W3 / 2, 166, "0 B", size=10.5, anchor="middle", fill=MUTED, mono=True)
    s.text(X3 + W3 / 2, 236, "전부 비어 있음", size=10.5, anchor="middle", fill=RAM_S, weight="600")
    s.text(X3 + W3 / 2, 252, "DMA 버퍼 후보", size=10.5, anchor="middle", fill=MUTED)

    s.text(450, 520, ".fast(ILM) 와 AHB SRAM 이 통째로 비어 있다 — 지연에 민감한 루프를 옮길 자리",
           size=11, anchor="middle", fill=MUTED)
    s.h = 548
    s.save("internal-memory.svg")


# ────────────────────────────────────────────────────────────── 8. LMA → VMA
def lma_vma():
    s = Svg(880, 420, "c_startup() 이 옮기는 것들")
    s.text(440, 28, "c_startup() — 플래시에서 RAM 으로", size=15, anchor="middle", weight="600")

    s.text(150, 60, "플래시 (LMA)", size=12.5, anchor="middle", weight="700", fill=FLASH_S)
    s.text(700, 60, "RAM (VMA)", size=12.5, anchor="middle", weight="700", fill=RAM_S)

    rows = [
        ("0x8000_3050", ".vectors   952 B", "복사", "ILM  0x0000_0000", ".vectors", True),
        (None,          None,               "0 으로", "DLM  0x0008_0558", ".bss   19,624 B", False),
        (None,          None,               "0 으로", "DLM  0x0008_5800", ".noncacheable.bss", False),
        ("0x8001_6320", ".data      600 B", "복사", "DLM  0x0008_0300", ".data", True),
        ("0x8001_6578", ".fast        0 B", "복사", "ILM  0x0000_03B8", ".fast", True),
    ]
    y = 88
    for laddr, llabel, op, raddr, rlabel, has_src in rows:
        if has_src:
            s.rect(40, y, 230, 34, FLASH_F, FLASH_S, rx=3, sw=1.1)
            s.text(52, y + 15, laddr, size=10.5, mono=True, fill=MUTED)
            s.text(52, y + 29, llabel, size=11, mono=True)
        s.rect(560, y, 250, 34, RAM_F if op == "복사" else PER_F,
               RAM_S if op == "복사" else PER_S, rx=3, sw=1.1)
        s.text(572, y + 15, raddr, size=10.5, mono=True, fill=MUTED)
        s.text(572, y + 29, rlabel, size=11, mono=True)
        x0 = 270 if has_src else 400
        s.line(x0 + 10, y + 17, 556, y + 17, LINE, 1.3, marker=True, dash=None if has_src else "4 3")
        s.text((x0 + 556) / 2, y + 11, op, size=10.5, anchor="middle", fill=MUTED)
        y += 50

    s.rect(40, y + 12, 770, 56, "#fef9c3", "#ca8a04", rx=4)
    s.text(56, y + 34, ".noinit  (DLM 0x0008_5200, 24 B) 은 이 목록에 없다", size=12, weight="600")
    s.text(56, y + 54, "그래서 리셋 후에도 내용이 유지된다 — 링커가 .bss 바깥에 배치한 이유",
           size=11.5, fill=MUTED)

    s.text(440, y + 100, ".text 는 복사하지 않는다 — XIP, 플래시에서 직접 실행",
           size=11, anchor="middle", fill=MUTED)
    s.h = y + 126
    s.save("lma-vma.svg")


# ────────────────────────────────────────────────────────────── 9. 클럭 트리
def clock_tree():
    s = Svg(880, 400, "클럭 트리")
    s.text(440, 28, "클럭 트리 — board_init_clock() 이후", size=15, anchor="middle", weight="600")

    s.rect(40, 70, 150, 44, ROM_F, ROM_S)
    s.text(115, 88, "XTAL24M", size=12.5, anchor="middle", weight="700", mono=True)
    s.text(115, 104, "24 MHz", size=11, anchor="middle", fill=MUTED, mono=True)

    s.rect(40, 150, 150, 44, ROM_F, ROM_S)
    s.text(115, 168, "PLL0", size=12.5, anchor="middle", weight="700", mono=True)
    s.text(115, 184, "960 MHz", size=11, anchor="middle", fill=MUTED, mono=True)
    s.line(115, 114, 115, 146, LINE, 1.3, marker=True)
    s.text(124, 136, "참조", size=10.5, fill=MUTED)

    outs = [(150, "CLK0  (÷1.0)", "960 MHz", True),
            (222, "CLK1  (÷1.6)", "600 MHz", False),
            (282, "CLK2  (÷2.4)", "400 MHz", False)]
    for y, lab, freq, hot in outs:
        s.rect(280, y, 165, 40, RAM_F if hot else PER_F, RAM_S if hot else PER_S)
        s.text(292, y + 17, lab, size=11.5, mono=True)
        s.text(433, y + 17, freq, size=11.5, anchor="end", mono=True, weight="700")
        s.text(292, y + 32, "PLL0 포스트 분주", size=10, fill=MUTED)
        s.path(f"M 190,172 L 235,172 L 235,{y+20} L 276,{y+20}", LINE, 1.3, marker=True)

    s.rect(560, 128, 280, 44, RAM_F, RAM_S)
    s.text(575, 146, "CPU0 / ILM / DLM / FGPIO", size=11.5)
    s.text(825, 146, "480 MHz", size=13, anchor="end", weight="700", mono=True, fill=RAM_S)
    s.text(575, 163, "PLL0CLK0 ÷ 2", size=10.5, fill=MUTED, mono=True)
    s.path("M 445,170 L 510,170 L 510,150 L 556,150", LINE, 1.4, marker=True)

    s.rect(560, 190, 280, 44, RAM_F, RAM_S)
    s.text(575, 208, "AXI / AHB   주변장치 버스", size=11.5)
    s.text(825, 208, "160 MHz", size=13, anchor="end", weight="700", mono=True, fill=RAM_S)
    s.text(575, 225, "PLL0CLK0 ÷ 3   HDMA / GPIO / ADC", size=10.5, fill=MUTED, mono=True)
    s.path("M 445,170 L 510,170 L 510,212 L 556,212", LINE, 1.4, marker=True)

    s.rect(560, 252, 280, 40, PER_F, PER_S)
    s.text(575, 270, "mchtmr0   1 ms 틱", size=11.5)
    s.text(825, 270, "24 MHz", size=12.5, anchor="end", weight="700", mono=True)
    s.text(575, 286, "osc24m 직결 (itInit)", size=10.5, fill=MUTED, mono=True)
    s.path("M 190,92 L 520,92 L 520,272 L 556,272", LINE, 1.3, marker=True, dash="4 3")

    s.rect(40, 330, 800, 46, "#fff7ed", "#ea580c", rx=4)
    s.text(56, 350, "리셋 직후 ~ main() 진입까지는 24MHz 다. 480MHz 는 board_init_clock() 이 만든다.",
           size=12, weight="600")
    s.text(56, 368, "DCDC 를 1.275V 로 올린 뒤 주파수를 올린다 — 순서를 뒤집으면 저전압 고주파 구간이 생긴다.",
           size=11.5, fill=MUTED)
    s.save("clock-tree.svg")


print("생성:")
boot_overview()
reset_domain()
bootrom_flow()
xpi_nor_flow()
flash_layout()
system_memory_map()
internal_memory()
lma_vma()
clock_tree()


# ──────────────────────────────────────────── 10. 보드 부트로더/펌웨어 메모리 맵
def board_flash_map():
    # (주소, 높이, 라벨, 크기, 채움, 테두리, 우측 주석)
    segs = [
        ("0x8000_0000", 24, "(미사용)",              "1,024 B",   GAP_F,   GAP_S,   ""),
        ("0x8000_0400", 30, "nor_cfg_option",        "16 B",      ROM_F,   ROM_S,   "① ROM 이 읽어 XPI0 설정"),
        (None,          18, "(미사용)",              "",          GAP_F,   GAP_S,   ""),
        ("0x8000_1000", 32, "부트 헤더  tag=0xBF",   "144 B",     ROM_F,   ROM_S,   "② ROM 이 읽는다 (offset 0x2000)"),
        (None,          18, "(미사용)",              "",          GAP_F,   GAP_S,   ""),
        ("0x8000_3000", 54, "IAP 부트로더",          "75,888 B",  APP_F,   APP_S,   "③ ROM 이 여기로 점프"),
        ("0x8001_5870", 24, "예약 / 공백",           "~42 KB",    GAP_F,   GAP_S,   ""),
        ("0x8001_B000", 20, "테스트 패턴",           "16 B",      GAP_F,   GAP_S,   ""),
        ("0x8001_D000", 32, "업데이트 플래그",       "4 B",       WARN_F,  WARN_S,  "앱이 쓰고 IAP 가 읽는다"),
        ("0x8001_E000", 22, "시리얼 문자열",         "16 B",      PER_F,   PER_S,   ""),
        ("0x8002_0000", 26, "매직  \"HPM\\n\"",      "4 B",       WARN_F,  WARN_S,  "④ IAP 가 검사하는 유일한 조건"),
        ("0x8002_0004", 58, "앱 펌웨어",             "159,788 B", FLASH_F, FLASH_S, "⑤ IAP 가 여기로 점프"),
        ("0x8004_7030", 28, "미사용",                "230 KB",    GAP_F,   GAP_S,   ""),
        ("0x8008_0000", 38, "EEPROM 에뮬레이션",     "90,112 B",  RAM_F,   RAM_S,   "키맵 · 캘리브레이션"),
        ("0x8009_FE90", 20, "뱅크 디스크립터",       "368 B",     RAM_F,   RAM_S,   ""),
        ("0x800B_FFF0", 18, "마커 KS / CMPH",        "16 B",      PER_F,   PER_S,   ""),
        ("0x800C_0000", 32, "미사용 (0xFF)",         "256 KB",    GAP_F,   GAP_S,   ""),
    ]
    top, X, W = 82, 262, 360
    h = top + sum(x[1] for x in segs) + 104
    s = Svg(1200, h, "보드 부트로더 / 펌웨어 메모리 맵")
    s.text(600, 28, "보드 부트로더 / 펌웨어 메모리 맵", size=15, anchor="middle", weight="600")
    s.text(600, 48, "보드 실측 · flash_dump.bin (1MB SiP 내장 NOR, XPI0 2번 핀그룹)",
           size=11.5, anchor="middle", fill=MUTED)
    s.text(600, 66, "ROM → 부트 헤더 → IAP → 매직 검사 → 앱",
           size=11.5, anchor="middle", fill=ROM_S, weight="600")

    y = top
    keep_top = keep_bot = own_top = own_bot = None
    for addr, hh, label, size_s, fill, stroke, note in segs:
        s.rect(X, y, W, hh, fill, stroke, rx=0, sw=1.1)
        if addr:
            s.text(X - 10, y + 13, addr, size=11.5, anchor="end", mono=True)
        s.text(X + 13, y + hh / 2 + 4, label, size=12,
               mono=not any(ord(c) > 0x2FFF for c in label))
        if size_s:
            s.text(X + W - 12, y + hh / 2 + 4, size_s, size=11, anchor="end",
                   mono=True, fill=MUTED)
        if note:
            s.text(X + W + 16, y + hh / 2 + 4, note, size=11,
                   fill=stroke if stroke != GAP_S else MUTED, weight="600")
        if addr == "0x8000_0400":
            keep_top = y
        if addr == "0x8001_E000":
            keep_bot = y + hh
        if addr == "0x8002_0000":
            own_top = y
        if addr == "0x8004_7030":
            own_bot = y + hh
        y += hh
    s.text(X - 10, y + 13, "0x8010_0000", size=11.5, anchor="end", mono=True)
    s.line(X, y, X + W, y, GAP_S, 1.1)

    # 좌측 브래킷 — 보존 필수 / 자체 펌웨어 영역
    def bracket(x, y0, y1, color, l1, l2):
        s.path(f"M {x+12},{y0} L {x},{y0} L {x},{y1} L {x+12},{y1}", color, 1.8)
        cy = (y0 + y1) / 2
        s.text(x - 8, cy - 5, l1, size=11, anchor="end", fill=color, weight="600")
        s.text(x - 8, cy + 10, l2, size=10.5, anchor="end", fill=MUTED)

    bracket(152, keep_top, keep_bot, ROM_S, "보존 필수", "건드리면 부팅 불가")
    bracket(152, own_top, own_bot, FLASH_S, "자체 펌웨어", "384 KB 가용")

    s.rect(40, h - 84, 1120, 64, "#fff7ed", "#ea580c", rx=4)
    s.text(56, h - 64, "자체 펌웨어 조건 — 0x8002_0000 에 매직 \"HPM\\n\" 4바이트, 0x8002_0004 가 진입점. "
                       "CRC·서명·길이 검사는 없다.", size=11.5, weight="600")
    s.text(56, h - 46, "링커 FLASH 를 ORIGIN=0x8002_0000 / LENGTH=0x60000 으로 묶으면 EEPROM(0x8008_0000~) 을 "
                       "침범하지 않아 벤더 펌웨어를 완전 복원할 수 있다.", size=11, fill=MUTED)
    s.text(56, h - 29, "업데이트 모드 진입 = 매직 없음  또는  PA09 = LOW  또는  0x8001_D000 != 0xFFFF_FFFF",
           size=11, fill=MUTED)
    s.save("board-flash-map.svg")


board_flash_map()
