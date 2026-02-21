---
name: atmega4809-xplained-pro
description: ATmega4809 Xplained Pro board reference including pin mapping, extension headers, power configuration, EDBG debugger, UART bridge, crystal config, programming commands, and common gotchas. Use when writing code for or configuring the ATmega4809 Xplained Pro development board.
---



# Board Overview

-   MCU: ATmega4809 (48KB Flash, 6KB SRAM, 256B EEPROM)
-   Operating Voltage: Selectable 3.3V or 5.0V via J105 jumper
-   Default Clock: 3.33 MHz (internal 20 MHz / 6 prescaler)
-   Debugger: On-board EDBG via UPDI
-   USB: Micro-B (J400) for power, programming, debug, and virtual COM
-   Crystal: 32.768 kHz on PF0/PF1 for RTC


# Pin Assignments


## User LED and Buttons

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">Name</th>
<th scope="col" class="org-left">Pin</th>
<th scope="col" class="org-left">Function</th>
<th scope="col" class="org-left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-left">LED0</td>
<td class="org-left">PB5</td>
<td class="org-left">Active low</td>
<td class="org-left">Shared with EXT2, DGI GPIO3</td>
</tr>

<tr>
<td class="org-left">SW0</td>
<td class="org-left">PB2</td>
<td class="org-left">Active low</td>
<td class="org-left">Enable internal pullup. Shared with EXT2, DGI GPIO0</td>
</tr>

<tr>
<td class="org-left">SW1/RESET</td>
<td class="org-left">PF6</td>
<td class="org-left">Active low</td>
<td class="org-left">GPIO by default, configurable as RESET via fuse</td>
</tr>
</tbody>
</table>


## UART Bridge (Virtual COM Port)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">Signal</th>
<th scope="col" class="org-left">Pin</th>
<th scope="col" class="org-left">Peripheral</th>
<th scope="col" class="org-left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-left">TX</td>
<td class="org-left">PC0</td>
<td class="org-left">USART1 TX</td>
<td class="org-left">MCU to PC</td>
</tr>

<tr>
<td class="org-left">RX</td>
<td class="org-left">PC1</td>
<td class="org-left">USART1 RX</td>
<td class="org-left">PC to MCU</td>
</tr>
</tbody>
</table>


## Shared Buses

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">Bus</th>
<th scope="col" class="org-left">Pins</th>
<th scope="col" class="org-left">Peripheral</th>
<th scope="col" class="org-left">Shared Across</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-left">I2C</td>
<td class="org-left">PC2/PC3</td>
<td class="org-left">TWI0</td>
<td class="org-left">EXT1, EXT2, EXT3, mikroBUS, ATECC508A (0x60)</td>
</tr>

<tr>
<td class="org-left">SPI</td>
<td class="org-left">PA4/PA5/PA6</td>
<td class="org-left">SPI0</td>
<td class="org-left">EXT1, EXT2, EXT3, mikroBUS, DGI</td>
</tr>
</tbody>
</table>


## Extension Header EXT1 (J200)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-right" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-right">Pin</th>
<th scope="col" class="org-left">Name</th>
<th scope="col" class="org-left">MCU Pin</th>
<th scope="col" class="org-left">Function</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-right">3</td>
<td class="org-left">ADC(+)</td>
<td class="org-left">PD2</td>
<td class="org-left">ADC0 AIN2</td>
</tr>

<tr>
<td class="org-right">4</td>
<td class="org-left">ADC(-)</td>
<td class="org-left">PD3</td>
<td class="org-left">ADC0 AIN3</td>
</tr>

<tr>
<td class="org-right">5</td>
<td class="org-left">GPIO1</td>
<td class="org-left">PA2</td>
<td class="org-left">USART0 XCK</td>
</tr>

<tr>
<td class="org-right">6</td>
<td class="org-left">GPIO2</td>
<td class="org-left">PA3</td>
<td class="org-left">USART0 XDIR</td>
</tr>

<tr>
<td class="org-right">7</td>
<td class="org-left">PWM(+)</td>
<td class="org-left">PC4</td>
<td class="org-left">TCA0 WO4</td>
</tr>

<tr>
<td class="org-right">8</td>
<td class="org-left">PWM(-)</td>
<td class="org-left">PC5</td>
<td class="org-left">TCA0 WO5</td>
</tr>

<tr>
<td class="org-right">9</td>
<td class="org-left">IRQ</td>
<td class="org-left">PC6</td>
<td class="org-left">GPIO</td>
</tr>

<tr>
<td class="org-right">10</td>
<td class="org-left">SPI<sub>SS</sub><sub>B</sub></td>
<td class="org-left">PC7</td>
<td class="org-left">GPIO</td>
</tr>

<tr>
<td class="org-right">13</td>
<td class="org-left">UART<sub>RX</sub></td>
<td class="org-left">PA1</td>
<td class="org-left">USART0 RxD</td>
</tr>

<tr>
<td class="org-right">14</td>
<td class="org-left">UART<sub>TX</sub></td>
<td class="org-left">PA0</td>
<td class="org-left">USART0 TxD</td>
</tr>

<tr>
<td class="org-right">15</td>
<td class="org-left">SPI<sub>SS</sub><sub>A</sub></td>
<td class="org-left">PA7</td>
<td class="org-left">SPI0 SS</td>
</tr>
</tbody>
</table>


## Extension Header EXT2 (J201)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-right" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-right">Pin</th>
<th scope="col" class="org-left">Name</th>
<th scope="col" class="org-left">MCU Pin</th>
<th scope="col" class="org-left">Function</th>
<th scope="col" class="org-left">Shared With</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-right">3</td>
<td class="org-left">ADC(+)</td>
<td class="org-left">PD4</td>
<td class="org-left">ADC0 AIN4</td>
<td class="org-left">&#xa0;</td>
</tr>

<tr>
<td class="org-right">4</td>
<td class="org-left">ADC(-)</td>
<td class="org-left">PD5</td>
<td class="org-left">ADC0 AIN5</td>
<td class="org-left">&#xa0;</td>
</tr>

<tr>
<td class="org-right">5</td>
<td class="org-left">GPIO1</td>
<td class="org-left">PE0</td>
<td class="org-left">GPIO</td>
<td class="org-left">&#xa0;</td>
</tr>

<tr>
<td class="org-right">6</td>
<td class="org-left">GPIO2</td>
<td class="org-left">PF6</td>
<td class="org-left">GPIO/RESET</td>
<td class="org-left">SW1, DEBUG</td>
</tr>

<tr>
<td class="org-right">7</td>
<td class="org-left">PWM(+)</td>
<td class="org-left">PB4</td>
<td class="org-left">TCA0 WO4</td>
<td class="org-left">DGI GPIO2</td>
</tr>

<tr>
<td class="org-right">8</td>
<td class="org-left">PWM(-)</td>
<td class="org-left">PB5</td>
<td class="org-left">TCA0 WO5</td>
<td class="org-left">LED0, DGI GPIO3</td>
</tr>

<tr>
<td class="org-right">9</td>
<td class="org-left">IRQ</td>
<td class="org-left">PB2</td>
<td class="org-left">GPIO</td>
<td class="org-left">SW0, DGI GPIO0</td>
</tr>

<tr>
<td class="org-right">10</td>
<td class="org-left">SPI<sub>SS</sub><sub>B</sub></td>
<td class="org-left">PB3</td>
<td class="org-left">GPIO</td>
<td class="org-left">DGI GPIO1</td>
</tr>

<tr>
<td class="org-right">13</td>
<td class="org-left">UART<sub>RX</sub></td>
<td class="org-left">PC1</td>
<td class="org-left">USART1 RxD</td>
<td class="org-left">Virtual COM</td>
</tr>

<tr>
<td class="org-right">14</td>
<td class="org-left">UART<sub>TX</sub></td>
<td class="org-left">PC0</td>
<td class="org-left">USART1 TxD</td>
<td class="org-left">Virtual COM</td>
</tr>

<tr>
<td class="org-right">15</td>
<td class="org-left">SPI<sub>SS</sub><sub>A</sub></td>
<td class="org-left">PE1</td>
<td class="org-left">GPIO</td>
<td class="org-left">&#xa0;</td>
</tr>
</tbody>
</table>


## Extension Header EXT3 (J203)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-right" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-right">Pin</th>
<th scope="col" class="org-left">Name</th>
<th scope="col" class="org-left">MCU Pin</th>
<th scope="col" class="org-left">Function</th>
<th scope="col" class="org-left">Shared With</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-right">3</td>
<td class="org-left">ADC(+)</td>
<td class="org-left">PD6</td>
<td class="org-left">ADC0 AIN6</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">4</td>
<td class="org-left">ADC(-)</td>
<td class="org-left">PD7</td>
<td class="org-left">ADC0 AIN7</td>
<td class="org-left">&#xa0;</td>
</tr>

<tr>
<td class="org-right">5</td>
<td class="org-left">GPIO1</td>
<td class="org-left">PD0</td>
<td class="org-left">GPIO</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">6</td>
<td class="org-left">GPIO2</td>
<td class="org-left">PD1</td>
<td class="org-left">GPIO</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">7</td>
<td class="org-left">PWM(+)</td>
<td class="org-left">PF4</td>
<td class="org-left">TCB0 WO</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">8</td>
<td class="org-left">PWM(-)</td>
<td class="org-left">PF5</td>
<td class="org-left">TCB1 WO</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">9</td>
<td class="org-left">IRQ</td>
<td class="org-left">PE2</td>
<td class="org-left">GPIO</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">10</td>
<td class="org-left">SPI<sub>SS</sub><sub>B</sub></td>
<td class="org-left">PE3</td>
<td class="org-left">GPIO</td>
<td class="org-left">&#xa0;</td>
</tr>

<tr>
<td class="org-right">13</td>
<td class="org-left">UART<sub>RX</sub></td>
<td class="org-left">PB1</td>
<td class="org-left">USART3 RxD</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">14</td>
<td class="org-left">UART<sub>TX</sub></td>
<td class="org-left">PB0</td>
<td class="org-left">USART3 TxD</td>
<td class="org-left">mikroBUS</td>
</tr>

<tr>
<td class="org-right">15</td>
<td class="org-left">SPI<sub>SS</sub><sub>A</sub></td>
<td class="org-left">PF2</td>
<td class="org-left">GPIO</td>
<td class="org-left">mikroBUS</td>
</tr>
</tbody>
</table>


## mikroBUS Socket (J205/J206)

<table border="2" cellspacing="0" cellpadding="6" rules="groups" frame="hsides">


<colgroup>
<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />

<col  class="org-left" />
</colgroup>
<thead>
<tr>
<th scope="col" class="org-left">mikroBUS Pin</th>
<th scope="col" class="org-left">Function</th>
<th scope="col" class="org-left">MCU Pin</th>
<th scope="col" class="org-left">Notes</th>
</tr>
</thead>
<tbody>
<tr>
<td class="org-left">AN</td>
<td class="org-left">ADC</td>
<td class="org-left">PD6</td>
<td class="org-left">ADC0 AIN6</td>
</tr>

<tr>
<td class="org-left">RST</td>
<td class="org-left">Reset</td>
<td class="org-left">PD0</td>
<td class="org-left">GPIO</td>
</tr>

<tr>
<td class="org-left">CS</td>
<td class="org-left">SPI SS</td>
<td class="org-left">PF2</td>
<td class="org-left">GPIO</td>
</tr>

<tr>
<td class="org-left">SCK</td>
<td class="org-left">SPI CLK</td>
<td class="org-left">PA6</td>
<td class="org-left">Shared SPI bus</td>
</tr>

<tr>
<td class="org-left">MISO</td>
<td class="org-left">SPI MISO</td>
<td class="org-left">PA5</td>
<td class="org-left">Shared SPI bus</td>
</tr>

<tr>
<td class="org-left">MOSI</td>
<td class="org-left">SPI MOSI</td>
<td class="org-left">PA4</td>
<td class="org-left">Shared SPI bus</td>
</tr>

<tr>
<td class="org-left">PWM</td>
<td class="org-left">PWM</td>
<td class="org-left">PF4</td>
<td class="org-left">TCB0 WO</td>
</tr>

<tr>
<td class="org-left">INT</td>
<td class="org-left">Interrupt</td>
<td class="org-left">PE2</td>
<td class="org-left">GPIO</td>
</tr>

<tr>
<td class="org-left">RX</td>
<td class="org-left">UART RX</td>
<td class="org-left">PB1</td>
<td class="org-left">USART3 RxD</td>
</tr>

<tr>
<td class="org-left">TX</td>
<td class="org-left">UART TX</td>
<td class="org-left">PB0</td>
<td class="org-left">USART3 TxD</td>
</tr>

<tr>
<td class="org-left">SCL</td>
<td class="org-left">I2C CLK</td>
<td class="org-left">PC3</td>
<td class="org-left">Shared I2C bus</td>
</tr>

<tr>
<td class="org-left">SDA</td>
<td class="org-left">I2C DATA</td>
<td class="org-left">PC2</td>
<td class="org-left">Shared I2C bus</td>
</tr>
</tbody>
</table>


# Power Configuration

-   J105 pins 1-2: 3.3V (default)
-   J105 pins 2-3: 5.0V
-   J106 cut-strap: Break for current measurement between VCC<sub>TARGET</sub> and VCC<sub>MCU</sub>
-   USB provides up to 500mA. Use external 5V on J100 pin 1 for higher current (up to 2A)


# Clock Configuration

-   Default: Internal 20 MHz with /6 prescaler = 3.33 MHz
-   To run at 20 MHz: Clear prescaler enable bit in CLKCTRL.MCLKCTRLB
-   External 32.768 kHz crystal on PF0/PF1 for RTC (7pF load)
-   Set F<sub>CPU</sub> accordingly: 3333333UL (default) or 20000000UL


# Programming Quick Reference

    # Program with pymcuprog
    pymcuprog write -f main.hex -d atmega4809 -t uart -u /dev/ttyACM0
    
    # Erase
    pymcuprog erase -d atmega4809 -t uart -u /dev/ttyACM0
    
    # Verify connection
    pymcuprog ping -d atmega4809 -t uart -u /dev/ttyACM0
    
    # Compile
    avr-gcc -mmcu=atmega4809 -DF_CPU=3333333UL -Os main.c -o main.elf
    avr-objcopy -O ihex main.elf main.hex


# Critical Gotchas

-   UPDI is the only programming interface (not ISP or JTAG)
-   Register names use AVR-0/1 style, not classic AVR
-   PORT registers use VPORT for atomic bit manipulation
-   Pin multiplexing is configured via PORTMUX register
-   Virtual COM port requires DTR enabled in terminal software
-   PB2/PB3/PB4/PB5 are shared with EDBG DGI (330Ω series resistors protect against conflicts)
-   I2C bus shared with ATECC508A at address 0x60 — avoid address collision
-   SPI bus shared with EDBG DGI — use unique SS lines per device
-   EXT2 UART pins (PC0/PC1) are also the virtual COM port — cannot use both simultaneously
-   Rev 3 boards have SPI MISO/MOSI crossed for DGI — use I2C mode for DGI or upgrade to rev 4+


# Additional Resources

-   For detailed toolchain setup, Makefile examples, and IDE configuration, see [toolchain-reference.md](toolchain-reference.md)
-   For complete troubleshooting and hardware revision notes, see [troubleshooting.md](troubleshooting.md)

