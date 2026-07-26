/*
 * board.c
 *
 * hpm_sdk boards/hpm5300evk/board.c 에서 본 프로젝트에 필요한 부분만 추린 것이다.
 * 콘솔 초기화(board_init_console)는 제거했다 — UART0 은 src/hw/driver/uart.c 가 단독으로 소유한다.
 *
 * Copyright (c) 2023-2026 HPMicro
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include "board.h"

#include "hpm_clock_drv.h"
#include "hpm_sysctl_drv.h"
#include "hpm_pllctlv2_drv.h"
#include "hpm_pcfg_drv.h"


/**
 * @brief FLASH configuration option definitions:
 * option[0]:
 *    [31:16] 0xfcf9 - FLASH configuration option tag
 *    [15:4]  0 - Reserved
 *    [3:0]   option words (exclude option[0])
 * option[1]:
 *    [31:28] Flash probe type
 *    [27:24] Command Pads after Power-on Reset
 *    [23:20] Command Pads after Configuring FLASH
 *    [19:16] Quad Enable Sequence
 *    [15:8]  Dummy cycles
 *    [7:4]   Misc.
 *    [3:0]   Frequency option
 * option[2]:
 *    [19:16] IO voltage
 *    [15:12] Pin group
 *    [11:8]  Connection selection
 *    [7:0]   Drive Strength
 *
 * ROM 부트로더가 0x80000400 에서 이 값을 읽어 XPI0 를 설정한다. 없으면 부팅하지 못한다.
 */
#if defined(FLASH_XIP) && FLASH_XIP
__attribute__ ((section(".nor_cfg_option"), used)) const uint32_t option[4] = {0xfcf90002, 0x00000005, 0x1000, 0x0};
#endif




/*
 * PY 패드는 IOC 뿐 아니라 PIOC 도 함께 설정해야 SoC 기능이 연결된다.
 * 특정 주변장치에 속하지 않는 칩 레벨 설정이라 보드 계층에 둔다.
 */
static void board_init_py_pins(void)
{
    HPM_PIOC->PAD[IOC_PAD_PY00].FUNC_CTL = PIOC_PY00_FUNC_CTL_PGPIO_Y_00;
    HPM_PIOC->PAD[IOC_PAD_PY01].FUNC_CTL = PIOC_PY01_FUNC_CTL_PGPIO_Y_01;
    HPM_PIOC->PAD[IOC_PAD_PY02].FUNC_CTL = PIOC_PY02_FUNC_CTL_PGPIO_Y_02;
    HPM_PIOC->PAD[IOC_PAD_PY03].FUNC_CTL = PIOC_PY03_FUNC_CTL_PGPIO_Y_03;
    HPM_PIOC->PAD[IOC_PAD_PY04].FUNC_CTL = PIOC_PY04_FUNC_CTL_PGPIO_Y_04;
    HPM_PIOC->PAD[IOC_PAD_PY05].FUNC_CTL = PIOC_PY05_FUNC_CTL_PGPIO_Y_05;
}

/* 클럭 그룹0 에 항상 필요한 것만 등록한다. 주변장치별 클럭은 각 드라이버가 직접 켠다. */
static void board_init_clock_group(void)
{
    clock_add_to_group(clock_cpu0,    0);
    clock_add_to_group(clock_ahb,     0);
    clock_add_to_group(clock_lmm0,    0);
    clock_add_to_group(clock_mchtmr0, 0);
    clock_add_to_group(clock_rom,     0);
    clock_add_to_group(clock_gpio,    0);
    clock_add_to_group(clock_hdma,    0);
    clock_add_to_group(clock_xpi0,    0);
}

static void board_init_clock_source(void)
{
    /* PLL0 960MHz */
    pllctlv2_init_pll_with_freq(HPM_PLLCTLV2, PLLCTLV2_PLL_PLL0, 960000000);

    pllctlv2_set_postdiv(HPM_PLLCTLV2, PLLCTLV2_PLL_PLL0, pllctlv2_clk0, pllctlv2_div_1p0);  /* 960MHz */
    pllctlv2_set_postdiv(HPM_PLLCTLV2, PLLCTLV2_PLL_PLL0, pllctlv2_clk1, pllctlv2_div_1p6);  /* 600MHz */
    pllctlv2_set_postdiv(HPM_PLLCTLV2, PLLCTLV2_PLL_PLL0, pllctlv2_clk2, pllctlv2_div_2p4);  /* 400MHz */

    /* mchtmr = 24MHz */
    clock_set_source_divider(clock_mchtmr0, clk_src_osc24m, 1);
}


void board_init(void)
{
    board_init_py_pins();

    board_init_clock();
    board_init_pmp();
}

void board_init_clock(void)
{
    uint32_t cpu0_freq = clock_get_frequency(clock_cpu0);

    if (cpu0_freq == PLLCTL_SOC_PLL_REFCLK_FREQ) {
        /* Configure the External OSC ramp-up time: ~9ms */
        pllctlv2_xtal_set_rampup_time(HPM_PLLCTLV2, 32UL * 1000UL * 9U);

        /* Select clock setting preset1 */
        sysctl_clock_set_preset(HPM_SYSCTL, 2);
    }

    /* group0[0] */
    board_init_clock_group();

    /* Connect Group0 to CPU0 */
    clock_connect_group_to_cpu(0, 0);

    /* Note: When using an external DCDC, don't set the internal DCDC voltage.
     * The following call of pcfg_dcdc_set_voltage() function should be commented out. */
    /* Bump up DCDC voltage to 1275mv */
    pcfg_dcdc_set_voltage(HPM_PCFG, 1275);

    /* Configure CPU to 480MHz, AXI/AHB to 160MHz */
    sysctl_config_cpu0_domain_clock(HPM_SYSCTL, clock_source_pll0_clk0, 2, 3);

    /* PLL0    : 960MHz
     * PLL0CLK0: 960MHz / PLL0CLK1: 600MHz / PLL0CLK2: 400MHz
     * mchtmr  : 24MHz  */
    board_init_clock_source();

    clock_update_core_clock();
}

void board_init_pmp(void)
{
}

void board_ungate_mchtmr_at_lp_mode(void)
{
    /* Keep cpu clock on wfi, so that mchtmr irq can still work after wfi */
    sysctl_set_cpu_lp_mode(HPM_SYSCTL, BOARD_RUNNING_CORE, cpu_lp_mode_ungate_cpu_clock);
}

void board_delay_us(uint32_t us)
{
    clock_cpu_delay_us(us);
}

void board_delay_ms(uint32_t ms)
{
    clock_cpu_delay_ms(ms);
}
