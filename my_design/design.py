# SPDX-License-Identifier: BSD-2-Clause

from chipflow_lib.platforms.sim import SimPlatform
from chipflow_lib.software.soft_gen import SoftwareGenerator

from amaranth import *

from amaranth_soc import wishbone

from amaranth_vexriscv.vexriscv import VexRiscv

from amaranth_orchard.base.gpio import GPIOPeripheral
from amaranth_orchard.memory.spimemio import SPIMemIO
from amaranth_orchard.io.uart import UARTPeripheral
from amaranth_orchard.memory.sram import SRAMPeripheral
from amaranth_orchard.base.platform_timer import PlatformTimer
from amaranth_orchard.base.soc_id import SoCID


class MySoC(Elaboratable):
    def __init__(self):
        super().__init__()

        # Memory regions
        self.spi_base = 0x00000000
        self.sram_base = 0x10000000
        self.sram_size = 8*1024  # 8KiB

        # CSR regions
        self.spi_ctrl_base = 0xb0000000
        self.led_gpio_base = 0xb1000000
        self.uart_base = 0xb2000000
        self.timer_base = 0xb3000000
        self.soc_id_base = 0xb4000000
        # self.btn_gpio_base = 0xb5000000

    def elaborate(self, platform):
        m = Module()

        m.submodules.clock_reset_provider = platform.providers.ClockResetProvider()

        self._arbiter = wishbone.Arbiter(
            addr_width=30,
            data_width=32,
            granularity=8
        )
        self._decoder = wishbone.Decoder(
            addr_width=30,
            data_width=32,
            granularity=8
        )

        self.cpu = VexRiscv(config="LiteDebug", reset_vector=0x00100000)
        self._arbiter.add(self.cpu.ibus)
        self._arbiter.add(self.cpu.dbus)

        m.submodules.rom_provider = rom_provider = platform.providers.QSPIFlashProvider()
        self.rom = SPIMemIO(
            flash=rom_provider.pins
        )
        self._decoder.add(self.rom.data_bus, addr=self.spi_base)
        self._decoder.add(self.rom.ctrl_bus, addr=self.spi_ctrl_base)

        self.sram = SRAMPeripheral(size=self.sram_size)
        self._decoder.add(self.sram.bus, addr=self.sram_base)

        m.submodules.led_gpio_provider = led_gpio_provider = platform.providers.LEDGPIOProvider()
        self.gpio = GPIOPeripheral(
            pins=led_gpio_provider.pins
        )
        self._decoder.add(self.gpio.bus, addr=self.led_gpio_base)

        m.submodules.uart_provider = uart_provider = platform.providers.UARTProvider()
        self.uart = UARTPeripheral(
            init_divisor=(25000000//115200),
            pins=uart_provider.pins
        )
        self._decoder.add(self.uart.bus, addr=self.uart_base)

        self.timer = PlatformTimer(width=48)
        self._decoder.add(self.timer.bus, addr=self.timer_base)

        soc_type = 0xCA7F100F
        self.soc_id = SoCID(type_id=soc_type)
        self._decoder.add(self.soc_id.bus, addr=self.soc_id_base)

        # self.btn = GPIOPeripheral(
        #     pins=platform.providers.ButtonGPIO(platform).add(m)
        # )
        # self._decoder.add(self.btn.bus, addr=self.btn_gpio_base)

        m.submodules.arbiter = self._arbiter
        m.submodules.cpu = self.cpu
        m.submodules.decoder = self._decoder
        m.submodules.rom = self.rom
        m.submodules.sram = self.sram
        m.submodules.gpio = self.gpio
        m.submodules.uart = self.uart
        m.submodules.timer = self.timer
        m.submodules.soc_id = self.soc_id
        # m.submodules.btn = self.btn

        m.d.comb += [
            self._arbiter.bus.connect(self._decoder.bus),
            self.cpu.software_irq.eq(0),
            self.cpu.timer_irq.eq(self.timer.timer_irq),
        ]

        m.submodules.jtag_provider = platform.providers.JTAGProvider(self.cpu)

        if isinstance(platform, SimPlatform):
            m.submodules.bus_mon = platform.add_monitor(
                "wb_mon",
                self._decoder.bus
            )

        sw = SoftwareGenerator(
            # place BIOS at 1MB so room for bitstream
            rom_start=self.spi_base + 0x00100000, rom_size=0x00100000,
            ram_start=self.sram_base, ram_size=self.sram_size,  # place BIOS data in SRAM
        )

        sw.add_periph("spiflash", "FLASH_CTRL", self.spi_ctrl_base)
        sw.add_periph("gpio", "LED_GPIO", self.led_gpio_base)
        sw.add_periph("uart", "UART0", self.uart_base)
        sw.add_periph("plat_timer", "TIMER0", self.timer_base)
        sw.add_periph("soc_id", "SOC_ID", self.soc_id_base)
        # sw.add_periph("gpio", "BTN_GPIO", self.btn_gpio_base)

        sw.generate("build/software/generated")

        return m
