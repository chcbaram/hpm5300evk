# hpm5300evk

HPM5300EVK (HPM5361ICB1, Andes D25 RISC-V) 펌웨어 프로젝트.

## 구성

```
firmware/hpm5361-fw/    펌웨어 (독립 빌드 — hpm_sdk 설치 불필요)
hardware/               회로도 (HPM5300EVKREVC.pdf)
```

## 요구사항

| 항목 | 값 |
|---|---|
| 툴체인 | xPack `riscv-none-elf-gcc` 13.4.0-1 (GCC 12 이상, binutils 2.39 이상 권장) |
| 디버거 | HPMicro OpenOCD 0.12.0+dev, 온보드 FT2232 프로브 |
| 벤더링된 hpm_sdk | v1.12.1 (`git describe: v1.12.1-3-g88b01b43900d`) |

hpm_sdk 는 빌드 의존성이 아니다. 필요한 소스만 `src/lib/hpm_sdk/` 아래로 복사해 두었다.

## 환경변수

**`~/.zshrc` 가 아니라 `~/.zshenv` 에 둘 것.** `.zshrc` 는 대화형 셸에서만 읽히는데,
VS Code 는 시작 시 로그인 셸(`zsh -l`)로 환경을 수집하므로 `.zshrc` 의 export 를 보지 못한다.
그 경우 `${env:...}` 가 빈 문자열이 되어 "The value of miDebuggerPath is invalid" 로 실패한다.

```sh
export HPM_RISCV_TOOLCHAIN_DIR="$HOME/hdd/tools/xpack-riscv-none-elf-gcc-13.4.0-1"
export HPM_RISCV_OPENOCD_PATH="$HOME/hdd/tools/hpmicro/openocd/bin"
export HPM_RISCV_GDB="$HOME/hdd/tools/xpack-riscv-none-elf-gcc-12.2.0-3/bin/riscv-none-elf-gdb-py3"
```

빌드용 툴체인과 디버깅용 gdb 가 다른 버전인 것은 의도한 것이다 — 아래 참조.

## 빌드

```sh
cd firmware/hpm5361-fw
cmake -S . -B build && cmake --build build -j
```

산출물: `build/hpm5361-fw.{elf,bin,asm,map}`

## 기록 / 디버깅

```sh
$HPM_RISCV_OPENOCD_PATH/openocd -s tools/openocd -f hpm5361-fw.cfg \
    -c "init; halt; program build/hpm5361-fw.elf verify; reset; exit"
```

VS Code 는 `.vscode/launch.json` 의 **HPM5361 Debug (OpenOCD)** 를 사용한다
(cortex-debug 은 ARM 대상이고 RISC-V 는 공식 지원이 아니라 `cppdbg` + OpenOCD 조합이다).
F5 를 누르면 빌드 → OpenOCD 기동 → 플래시 기록 → `reset halt` 후 `_start` 에서 멈춘다.
이후 브레이크포인트는 에디터에서 F9 로 찍는다.

### gdb 는 12.2.0-3 것을 쓸 것

xpack 이 2025-10 배치로 빌드한 **gdb 16.3 (arm64 macOS)** 은 에러를 던지는 모든 명령에서
`uncaught gdb_exception_error` 로 abort 한다. cppdbg 가 시작 직후 보내는
`set debuginfod enabled on` 에서 바로 죽어 디버깅을 시작할 수 없다
(`GDB exited unexpectedly with exit code 134`).

13.4.0-1 과 15.2.0-1 에서 동일하게 재현했다. gcc 문제가 아니라 gdb 바이너리 문제이며,
같은 배치의 12.5.0-1 / 14.3.0-1 도 같을 가능성이 높다.
2023 년 빌드인 **12.2.0-3 의 gdb 12.1 은 정상**이고, GCC 13/15 가 만든 DWARF 도 문제없이 읽는다.

어떤 gdb 든 아래 한 줄로 판별된다.

```sh
<gdb경로> --batch -ex "print nosuchsymbol" -ex "echo OK\n"
#  "No symbol table is loaded... OK"        -> 정상
#  "libc++abi: terminating... Abort trap: 6" -> 사용 불가
```

콘솔은 UART0 (PA00/PA01) 115200 8N1 이며 온보드 FT2232 의 VCP 로 나온다.

## 확인된 부팅 로그

```
[ Firmware Begin... ]
Booting..Name           : HPM5361-EVK-FW
Booting..Ver            : V260726R1
Booting..Clock          : 480 Mhz
Booting..Addr           : 0x80000000

[  ] moduleInit()
       count : 2
[  ] moduleBegin()
       cli OK
cli#
```
