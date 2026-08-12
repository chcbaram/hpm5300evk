# 디버그 프로브 · 툴체인 · 복구 절차

HPM5361 보드에 붙는 프로브와 OpenOCD 조합, 그리고 플래시 덤프/기록/복구 절차를 정리한다.
**전부 실측으로 검증한 내용**이다.

---

## 1. 핵심 — 프로브별로 할 수 있는 일이 다르다

| | jlink 드라이버 | ftdi 드라이버 | `hpm_xpi` 플래시 |
|---|---|---|---|
| **HPMicro OpenOCD** (`~/hdd/tools/hpmicro/openocd/bin`) | ❌ | ✅ | ✅ |
| **homebrew OpenOCD** (`/opt/homebrew/bin`) | ✅ | ✅ | ❌ |

> `strings <openocd> | grep -ix 'jlink\|hpm_xpi'` 로 확인할 수 있다.

**결론: 플래시를 기록하려면 FT2232(EVK 온보드 디버거) + HPMicro OpenOCD 조합이어야 한다.**
J-Link 은 읽기·디버깅 전용이다. 둘 다 필요하면 HPMicro OpenOCD 소스를 `--enable-jlink` 로
직접 빌드해야 한다.

### SEGGER 순정 경로는 쓸 수 없다

DLL 에 HPM5361 지원이 **실제로 들어 있다** — 디바이스명 `HPM5361xCBx` / `xCFx` / `xEGx`,
OpenFlashloader 가 `0x80000000` · 섹터 4KB 로 등록돼 있고 진입점(`Init`/`EraseSector`/
`ProgramPage`/`SEGGER_OPEN_Program` 등)도 전부 존재한다.

그런데도 연결이 안 된다. TAP 감지 → RISC-V DTM 협상 → `Detected: RV32 core` 까지 가고
`0xFFFFFEFA` 로 실패하는데, 원인은 **보유 프로브가 J-Link 클론**이라 DLL 이 의도적으로
차단하기 때문이다(`The connected probe appears to be a J-Link clone.` 다이얼로그).

- 디바이스명을 `HPM5361` 로 주면 거부된다. 정확한 이름은 `HPM5361xCBx` (LQFP100 = CB).
- **클론 프로브에 SEGGER 툴을 쓰지 말 것.** 펌웨어 업데이트를 승인하면 벽돌이 되는 사례가 많다.
- OpenOCD 는 libjlink(jaylink)로 직접 붙어 클론 검사를 하지 않으므로 **경고창이 뜨지 않는다.**

---

## 2. 주의 — 앱이 JTAG 핀을 뺏는다 (상용 보드)

HPM5361 의 JTAG 는 **PA04(TDO) / PA05(TDI) / PA06(TCK) / PA07(TMS) / PA08(TRST)** 이다
(`hpm_iomux.h`, ALT24).

상용 보드의 앱 펌웨어는 **PA05·PA06 을 ALT0(GPIO) 출력으로 리먹싱**한다. 그래서 앱이
도는 동안에는 어떤 프로브로도 붙지 않는다:

```
Error: JTAG scan chain interrogation failed: all zeroes
Error: dtmcontrol is 0. Check JTAG connectivity/board power.
```

- 속도를 바꿔도(100/500/1000 kHz) 항상 동일하게 `all zeroes` 다.
  접촉 불량이면 `all ones` / `all zeroes` 가 **실행마다 바뀐다** — 구분 기준이 된다.
- 이 상태로 오래 두지 말 것. J-Link 의 TCK/TDI 드라이버와 MCU 의 GPIO 출력이 서로 밀고 있다.
- **IAP 부트로더 모드에서는 리먹싱이 없어 정상적으로 붙는다.**
  USB 제품 문자열로 앱 모드인지 IAP 모드인지 구분할 수 있다.

우리가 만드는 펌웨어는 PA04~PA08 을 건드리지 않으므로 이 문제가 없다.

---

## 3. 검증된 명령

### 3.1 J-Link + homebrew OpenOCD — 읽기 전용

```sh
openocd -s tools/openocd -f hpm5361-jlink-ro.cfg -c "init; scan_chain; targets; exit"
```

정상이면 IDCODE `0x1000563d` (Andes Technology) · `XLEN=32, misa=0x4090112f` 가 나온다.

1MB 덤프(러닝 상태 그대로, halt 불필요):

```sh
openocd -s tools/openocd -f hpm5361-jlink-ro.cfg \
        -c "init" -c "riscv set_mem_access sysbus progbuf abstract" \
        -c "dump_image flash_dump.bin 0x80000000 0x100000" -c "exit"
```

### 3.2 FT2232 + HPMicro OpenOCD — 읽기 전용

`hpm5361-fw.cfg` 는 플래시 뱅크를 선언하므로, 타겟을 건드리고 싶지 않을 때는 아래 설정을 쓴다.
(`docs/analysis/ft2232-ro.cfg` 에 사본이 있다.)

```tcl
source [find probes/ft2232.cfg]
adapter speed 1000

set _CHIP hpm5361
jtag newtap $_CHIP cpu -irlen 5 -expected-id 0x1000563D
target create $_CHIP.cpu0 riscv -chain-position $_CHIP.cpu -coreid 0
targets $_CHIP.cpu0
reset_config none
```

```sh
~/hdd/tools/hpmicro/openocd/bin/openocd -s tools/openocd -s <위 cfg 디렉토리> \
        -f ft2232-ro.cfg -c "adapter speed 4000" -c "init" \
        -c "riscv set_mem_access sysbus progbuf abstract" \
        -c "dump_image flash_dump.bin 0x80000000 0x100000" -c "exit"
```

> `probes/ft2232.cfg` 의 기본 속도는 10MHz 다. 플라잉 리드 연결에는 빠를 수 있으니
> `adapter speed` 로 낮춰서 시작할 것. 4MHz 에서 1MB 덤프가 **22.8 초** 걸렸다.

> `libusb_detach_kernel_driver() failed with LIBUSB_ERROR_ACCESS` 경고는 macOS 에서
> 항상 뜨며 동작에 영향이 없다.

### 3.3 FT2232 + HPMicro OpenOCD — 플래시 기록

```sh
~/hdd/tools/hpmicro/openocd/bin/openocd -s tools/openocd -f hpm5361-fw.cfg \
  -c "adapter speed 4000" -c "init" -c "halt" -c "flash probe 0" \
  -c "flash write_image erase <이미지>.bin <주소> bin" \
  -c "verify_image <이미지>.bin <주소> bin" -c "exit"
```

`flash probe 0` 이 성공하면 아래처럼 뜬다 — **선언값은 32MB 지만 실제 1MB 로 프로브된다.**

```
flash 'hpm_xpi' found at 0x80000000
#0 : hpm_xpi at 0x80000000, size 0x00100000, buswidth 1, chipwidth 1
     4kB 섹터 256 개, 전부 not protected
```

> `verify_image` 직후의 `verified ... in 0.07s` 는 **타겟측 CRC 비교**다. 바이트 단위로
> 확인하려면 다시 덤프해서 `cmp` 하는 편이 확실하다.

> `flash probe` 는 타겟 ILM(`0x0`~`0x20000`)을 작업 영역으로 쓰고 `work-area-backup 0`
> 이므로 **실행 중이던 코드의 RAM 상태가 깨진다.** 끝나면 리셋하거나 전원을 다시 넣는다.

---

## 4. 되쓰기 실증 결과

상용 보드에서 1MB 전체 소거 + 기록 + 검증을 실제로 수행해 확인했다.

```
wrote    1048576 bytes in 8.94s  (114.5 KiB/s)   [auto erase enabled]
verified 1048576 bytes                            (타겟 CRC)
재덤프   1048576 bytes in 22.84s
대조     SHA-256 일치 / 차이 0 바이트             ← 바이트 단위 독립 검증
```

**소거→기록→검증 경로가 실제로 동작한다.** 되쓰기 전 덤프와 되쓰기 후 덤프가
원본 파일과 모두 동일했다.

---

## 5. 복구 전략

### 5.1 자체 펌웨어를 올릴 때 — IAP 를 보존하면 3중망이 된다

[board-iap.md](board-iap.md) 참조. `0x20000` 부터만 기록하고 IAP 를 남기면:

| # | 경로 | 조건 |
|---|---|---|
| 1 | **JTAG** | 항상. 자체 펌웨어는 PA05/PA06 을 안 건드리므로 늘 붙는다 |
| 2 | **IAP USB 업데이트** | 앱 매직이 없으면 자동으로 업데이트 모드 |
| 3 | **PA09 강제 진입** | PA09 를 LOW 로 잡고 전원 인가 |

IAP 의 업데이트 명령은 기록 주소를 `0x80020000` 으로 하드코딩하므로
**호스트가 IAP 자신을 덮어쓸 수 없다.**

### 5.2 벤더 펌웨어로 원상 복구

```sh
~/hdd/tools/hpmicro/openocd/bin/openocd -s tools/openocd -f hpm5361-fw.cfg \
  -c "adapter speed 4000" -c "init" -c "halt" -c "flash probe 0" \
  -c "flash write_image erase docs/flash_dump.bin 0x80000000 bin" \
  -c "verify_image docs/flash_dump.bin 0x80000000 bin" -c "exit"
```

시리얼(`0x1E000`)과 EEPROM 캘리브레이션(`0x80000`~)까지 덤프 시점 상태로 돌아간다.

> `flash_dump.bin` 은 `.gitignore` 대상이라 clone 으로는 따라오지 않는다.
> **이 보드의 유일한 원상복구 수단이므로 별도로 백업해 둘 것.**

### 5.3 앱만 교체 (IAP·EEPROM 보존)

```sh
... -c "flash write_image erase <app>.bin 0x80020000 bin" ...
```

---

## 6. 참고 — 덤프 디스어셈블

**프로젝트 툴체인**(`~/hdd/tools/xpack-riscv-none-elf-gcc-13.4.0-1`)을 써야 한다.
Zephyr SDK 의 `riscv64-zephyr-elf-objdump` 는 Andes 확장 명령(`bseti` 등)을 `.4byte` 로
흘려서 오독한다. 절차는 [analysis/README.md](analysis/README.md) 에 있다.
