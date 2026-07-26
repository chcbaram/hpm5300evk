/*
 * uart.c
 *
 * hpm5300evk 콘솔 UART(UART0, PA00=TXD / PA01=RXD) 1채널.
 * 온보드 FT2232 디버거의 VCP 로 그대로 나온다.
 *
 * 템플릿 단계라 폴링 방식이다. 인터럽트 RX(qbuffer 링버퍼)는 필요해질 때 추가한다.
 */

#include "uart.h"


#ifdef _USE_HW_UART

#include "cli.h"
#include "hpm_uart_drv.h"
#include "hpm_clock_drv.h"


typedef struct
{
  bool           is_open;
  uint32_t       baud;
  uint32_t       rx_cnt;
  uint32_t       tx_cnt;
  UART_Type     *p_uart;
  clock_name_t   clock;
  uart_driver_t *p_driver;
} uart_tbl_t;


static void uartInitPins(uint8_t ch);


static bool is_init = false;

static uart_tbl_t uart_tbl[UART_MAX_CH];

#if CLI_USE(HW_UART)
static void cliUart(cli_args_t *args);
#endif




bool uartInit(void)
{
  for (int i=0; i<UART_MAX_CH; i++)
  {
    uart_tbl[i].is_open  = false;
    uart_tbl[i].baud     = 115200;
    uart_tbl[i].rx_cnt   = 0;
    uart_tbl[i].tx_cnt   = 0;
    uart_tbl[i].p_driver = NULL;
  }

  uart_tbl[HW_UART_CH_DEBUG].p_uart = HPM_UART0;
  uart_tbl[HW_UART_CH_DEBUG].clock  = clock_uart0;

  is_init = true;

#if CLI_USE(HW_UART)
  cliAdd("uart", cliUart);
#endif

  return true;
}

bool uartDeInit(void)
{
  return true;
}

bool uartIsInit(void)
{
  return is_init;
}

bool uartOpen(uint8_t ch, uint32_t baud)
{
  uart_config_t config = {0};


  if (ch >= UART_MAX_CH) return false;

  if (uart_tbl[ch].p_driver != NULL)
  {
    uart_tbl[ch].baud    = baud;
    uart_tbl[ch].is_open = uart_tbl[ch].p_driver->open(baud);
    return uart_tbl[ch].is_open;
  }

  /*
   * 순서 주의 : pinmux -> clock -> uart_init.
   * 클럭을 먼저 켜면 RX 핀의 레벨 변화가 스퓨리어스 바이트로 잡힌다.
   */
  uartInitPins(ch);
  clock_add_to_group(uart_tbl[ch].clock, 0);

  uart_default_config(uart_tbl[ch].p_uart, &config);
  config.src_freq_in_hz = clock_get_frequency(uart_tbl[ch].clock);
  config.baudrate       = baud;

  if (uart_init(uart_tbl[ch].p_uart, &config) != status_success)
  {
    return false;
  }

  uart_tbl[ch].baud    = baud;
  uart_tbl[ch].is_open = true;

  return true;
}

void uartInitPins(uint8_t ch)
{
  switch (ch)
  {
    case HW_UART_CH_DEBUG:
      /* UART0 : PA00 = TXD, PA01 = RXD  (온보드 FT2232 VCP) */
      HPM_IOC->PAD[IOC_PAD_PA00].FUNC_CTL = IOC_PA00_FUNC_CTL_UART0_TXD;
      HPM_IOC->PAD[IOC_PAD_PA01].FUNC_CTL = IOC_PA01_FUNC_CTL_UART0_RXD;
      break;

    default:
      break;
  }
}

bool uartIsOpen(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return false;

  return uart_tbl[ch].is_open;
}

bool uartSetDriver(uint8_t ch, uart_driver_t *p_driver)
{
  if (ch >= UART_MAX_CH) return false;

  uart_tbl[ch].p_driver = p_driver;

  return true;
}

bool uartClose(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return false;

  uart_tbl[ch].is_open = false;

  return true;
}

uint32_t uartAvailable(uint8_t ch)
{
  uint32_t ret = 0;


  if (ch >= UART_MAX_CH) return 0;
  if (uart_tbl[ch].is_open == false) return 0;

  if (uart_tbl[ch].p_driver != NULL)
  {
    return uart_tbl[ch].p_driver->available();
  }

  if (uart_check_status(uart_tbl[ch].p_uart, uart_stat_data_ready))
  {
    ret = 1;
  }

  return ret;
}

bool uartFlush(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return false;

  if (uart_tbl[ch].p_driver != NULL)
  {
    return uart_tbl[ch].p_driver->flush();
  }

  while (uartAvailable(ch) > 0)
  {
    uartRead(ch);
  }

  return true;
}

uint8_t uartRead(uint8_t ch)
{
  uint8_t ret = 0;


  if (ch >= UART_MAX_CH) return 0;
  if (uart_tbl[ch].is_open == false) return 0;

  if (uart_tbl[ch].p_driver != NULL)
  {
    return uart_tbl[ch].p_driver->read();
  }

  if (uart_receive_byte(uart_tbl[ch].p_uart, &ret) == status_success)
  {
    uart_tbl[ch].rx_cnt++;
  }

  return ret;
}

uint32_t uartWrite(uint8_t ch, uint8_t *p_data, uint32_t length)
{
  uint32_t ret = 0;


  if (ch >= UART_MAX_CH) return 0;
  if (uart_tbl[ch].is_open == false) return 0;

  if (uart_tbl[ch].p_driver != NULL)
  {
    return uart_tbl[ch].p_driver->write(p_data, length);
  }

  for (uint32_t i=0; i<length; i++)
  {
    if (uart_send_byte(uart_tbl[ch].p_uart, p_data[i]) != status_success)
    {
      break;
    }
    ret++;
  }

  uart_tbl[ch].tx_cnt += ret;

  return ret;
}

uint32_t uartPrintf(uint8_t ch, const char *fmt, ...)
{
  char buf[256];
  va_list args;
  int len;
  uint32_t ret;


  va_start(args, fmt);
  len = vsnprintf(buf, 256, fmt, args);
  va_end(args);

  if (len < 0) return 0;

  ret = uartWrite(ch, (uint8_t *)buf, (uint32_t)len);

  return ret;
}

uint32_t uartGetBaud(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return 0;

  return uart_tbl[ch].baud;
}

uint32_t uartGetRxCnt(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return 0;

  return uart_tbl[ch].rx_cnt;
}

uint32_t uartGetTxCnt(uint8_t ch)
{
  if (ch >= UART_MAX_CH) return 0;

  return uart_tbl[ch].tx_cnt;
}


#if CLI_USE(HW_UART)
void cliUart(cli_args_t *args)
{
  bool ret = false;


  if (args->argc == 1 && args->isStr(0, "info"))
  {
    for (int i=0; i<UART_MAX_CH; i++)
    {
      cliPrintf("uart ch%d : %d bps, open %d, rx %d, tx %d\n",
                i,
                (int)uart_tbl[i].baud,
                uart_tbl[i].is_open,
                (int)uart_tbl[i].rx_cnt,
                (int)uart_tbl[i].tx_cnt);
    }
    ret = true;
  }

  if (args->argc == 2 && args->isStr(0, "test"))
  {
    uint8_t ch;

    ch = (uint8_t)args->getData(1);

    if (ch >= UART_MAX_CH)
    {
      cliPrintf("ch %d is over max %d\n", ch, UART_MAX_CH);
      return;
    }

    while (cliKeepLoop())
    {
      if (uartAvailable(ch) > 0)
      {
        uint8_t rx_data;

        rx_data = uartRead(ch);
        cliPrintf("%c", rx_data);
      }
    }
    ret = true;
  }

  if (ret == false)
  {
    cliPrintf("uart info\n");
    cliPrintf("uart test ch[0~%d]\n", UART_MAX_CH-1);
  }
}
#endif

#endif
