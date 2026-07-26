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
```

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
(cortex-debug 은 ARM 전용이라 쓸 수 없어 `cppdbg` + OpenOCD 조합이다).

> gdb 는 반드시 **`riscv-none-elf-gdb-py3`** 를 써야 한다.
> xpack 의 `riscv-none-elf-gdb` 는 Python 없이 빌드되어 있어, cppdbg 가 보내는 python 명령을
> 받으면 에러 대신 abort 로 죽는다 (`GDB exited unexpectedly with exit code 134`).

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
