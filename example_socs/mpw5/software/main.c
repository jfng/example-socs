#include <stdint.h>

#include "drivers/uart.h"
#include "drivers/soc_id.h"
#include "drivers/spiflash.h"

static volatile uart_regs_t *const UART0 = (volatile uart_regs_t*)0xb2000000;
static volatile soc_id_regs_t *const SOC_ID = (volatile soc_id_regs_t*)0xb4000000;
static volatile spiflash_regs_t *const FLASH_CTRL = (volatile spiflash_regs_t*)0xb0000000;

void main() {
	uart_puts(UART0, "🐱: nyaa~!\n");

	uart_puts(UART0, "SoC type: ");
	uart_puthex(UART0, SOC_ID->type);
	uart_puts(UART0, "\n");

	uart_puts(UART0, "SoC version: ");
	uart_puthex(UART0, SOC_ID->version);
	uart_puts(UART0, "\n");

	uart_puts(UART0, "Flash ID: ");
	uart_puthex(UART0, spiflash_read_id(FLASH_CTRL));
	uart_puts(UART0, "\n");

	while(1) {};
}
