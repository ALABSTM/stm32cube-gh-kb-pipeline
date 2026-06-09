"""
Generate a quality test suite (Question, Answer, Tags)
for all MCU series and export as Excel (.xlsx).

Covers: F4, H5, H7, U5, WL, C0

Usage:
    python pipeline_Automation/test_suites/generate_quality_test_suite.py
"""

from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
except ImportError:
    print("Install openpyxl: pip install openpyxl")
    raise SystemExit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "datasets" / "07_delivery" / "st_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
XLSX_PATH = OUTPUT_DIR / "quality_test_suite_all_series.xlsx"

# ============================================================
# TEST QUESTIONS DATABASE
# ============================================================

QUESTIONS = [
    # ======================== STM32H7 ========================
    {
        "question": "My STM32H743 project crashes with a hard fault as soon as I enable DMA for SPI. I've checked the clock config and it seems fine. The SPI works in polling mode. What could be wrong?",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "I migrated my STM32H747I-DISCO Ethernet project from CubeH7 v1.9 to v1.11 and now LwIP doesn't get an IP address anymore. The PHY link is up but no DHCP response. Any idea?",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "I need to pass data between CM7 and CM4 cores on my STM32H745 custom board. I tried shared memory but I get random corruption. What's the recommended approach?",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "USB CDC on STM32H750B-DK works for about 30 seconds then the PC says 'USB device not recognized'. I have to unplug and replug. The same code works fine on F4.",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "I'm trying to execute code from external QSPI flash on STM32H735G-DK in memory-mapped mode but I get a bus fault. The flash ID reads correctly in indirect mode.",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "My ADC readings on STM32H743 Nucleo-144 jump around by 200 LSBs even with a stable DC voltage input. I tried averaging in software but it's still noisy. What am I doing wrong?",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "I configured I2C1 as slave on STM32H743I-EVAL but the address match interrupt never fires. The master sees NACK. Pull-ups are present on the bus.",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "How do I set up SAI with BDMA on STM32H7 for audio playback? The DMA transfer complete callback never triggers. Regular DMA1/DMA2 works but BDMA doesn't.",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "FreeRTOS crashes with a hard fault when I try to read SD card via SDMMC1 on STM32H7B3I-DK. It works fine in bare metal. Stack overflow detection doesn't trigger.",
        "answer": "",
        "tags": "H7",
    },
    {
        "question": "FDCAN on my STM32H753 receives frames fine but some messages with specific IDs are dropped even though my filter should accept them. Is there a known issue with FDCAN filters?",
        "answer": "",
        "tags": "H7",
    },
    # ======================== STM32F4 ========================
    {
        "question": "HAL_UART_Receive_IT on STM32F446RE only gives me the first character then stops. I have to call it again in the callback. Is this expected behavior or a bug?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "I just got an STM32F4 Discovery board and the accelerometer doesn't respond. SPI MISO stays low. I'm using the BSP driver from the Cube package. What should I check?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "I need exactly 1ms timer interrupt on STM32F411 Nucleo but my timing is off by about 5%. The system clock is 100MHz from HSE. What's the correct TIM2 prescaler and period?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "ADC with DMA in scan mode on STM32F429 gives me the same value in all buffer positions. I configured 4 channels but the buffer fills with channel 0 data repeated.",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "I'm implementing USB MSC on STM32F469I-EVAL to expose the SD card to PC but Windows says 'device not recognized' at enumeration. The same descriptor works on F407.",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "I want to receive only CAN messages with IDs 0x100-0x1FF on STM32F4. How do I configure the filter bank to accept this range and reject everything else?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "After a slave sends NACK, my I2C1 on STM32F401 gets permanently stuck with BUSY flag set. HAL_I2C_Init doesn't fix it. Only a full chip reset clears it. How to recover?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "HAL_Delay() hangs forever when I integrate FreeRTOS on my STM32F4 project. It worked before adding the RTOS. SysTick is still running.",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "TIM1 CH1 PWM output on STM32F407 stays low no matter what duty cycle I set. TIM2 PWM works fine with the same config approach. What's different about TIM1?",
        "answer": "",
        "tags": "F4",
    },
    {
        "question": "What breaking changes should I be aware of when updating from STM32CubeF4 v1.26 to v1.28? My project uses USB, Ethernet, and FreeRTOS.",
        "answer": "",
        "tags": "F4",
    },
    # ======================== STM32H5 ========================
    {
        "question": "After enabling TrustZone on STM32H573I-Discovery, I can't toggle LEDs from non-secure code anymore. The GPIO init returns HAL_OK but nothing happens on the pin.",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "I get a hard fault when enabling ICACHE on STM32H563 after configuring OSPI in memory-mapped mode. Without ICACHE it runs fine but too slow. Is there a conflict?",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "I want my STM32H5 Nucleo to wake up from STOP mode on LPUART character reception. The wake-up from EXTI works but LPUART wake-up doesn't. What's the clock source issue?",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "SPI DMA transfers on STM32H563 work most of the time but randomly return corrupted data (about 1 in 50 transfers). The same code on F4 with regular DMA is rock solid.",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "I need continuous ADC conversion with DMA on STM32H5 using the new GPDMA. The examples show linked-list mode. Is there a simpler way like on F4, or is linked-list mandatory?",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "RTC alarm A interrupt wakes the STM32H573 from STOP1 but not from STOP2. The alarm flag is set but the wake-up doesn't happen. What additional config is needed for STOP2?",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "USB device on STM32H5F5J-Discovery enumerates as 'Unknown Device' on Windows. I'm using the CDC class from STM32 USB Device Library. HSI48 with CRS is configured.",
        "answer": "",
        "tags": "H5",
    },
    {
        "question": "What BSP examples come with the STM32H573I-Discovery board package? I'm looking for audio and display demos to test the hardware.",
        "answer": "",
        "tags": "H5",
    },
    # ======================== STM32U5 ========================
    {
        "question": "I set up LPDMA to transfer ADC results to SRAM4 in STOP2 mode on STM32U585 but the transfer never starts. In Run mode it works. The SmartRun domain should keep LPDMA alive, right?",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "How do I configure the ADF peripheral to capture audio from the onboard digital microphone on B-U585I-IOT02A? The BSP audio driver returns errors.",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "TouchGFX screen on STM32U5G9J-DK2 shows garbage after I updated the Cube package. The LTDC init looks correct. Display was working before the update.",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "After enabling TrustZone (TZEN=1) on STM32U5, my application no longer boots. I get stuck in secure fault handler. How do I recover the board and fix the configuration?",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "I need to achieve under 5uA in STOP3 on STM32U575 but I measure 50uA. All GPIOs are set to analog. What else should I disable? Is there a checklist for ultra-low-power?",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "I2C4 works in Run mode on STM32U5 but after wake-up from STOP2, the I2C peripheral doesn't respond. HAL_I2C_GetState returns RESET. Do I need to reinitialize after wake-up?",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "Accessing HyperRAM via OSPI in memory-mapped mode on STM32U5A9J-DK causes a bus fault at certain addresses. First 1MB works fine but beyond that it faults.",
        "answer": "",
        "tags": "U5",
    },
    {
        "question": "What sensors and connectivity are available on the B-U585I-IOT02A board? I want to build a demo that uses WiFi and environmental sensors.",
        "answer": "",
        "tags": "U5",
    },
    # ======================== STM32WL ========================
    {
        "question": "My STM32WL Nucleo sends LoRa join requests but never gets a join accept back. The gateway log shows the request arriving. DevEUI and AppKey are double-checked. What else could block the join?",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "The B-WL5M-SUBG1 module has both sub-GHz and BLE. How do I switch the RF path between them? Is it an antenna switch GPIO or is it automatic?",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "My STM32WL55 outputs only +10dBm TX power even though I configured +22dBm with the HP PA. The radio config looks correct according to the datasheet. What am I missing?",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "On my STM32WL dual-core board, only CPU1 (CM4) runs. CPU2 (CM0+) never starts. I set C2BOOT in option bytes but it stays in reset. How to properly start the second core?",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "I need to send LoRa packets every 30 seconds using LPTIM to wake from STOP2 on STM32WL. The LPTIM interrupt fires in Run mode but doesn't wake from STOP2.",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "How to configure LoRaWAN Class C on STM32WL? I need the device to receive downlinks at any time, not just after uplinks. The stack examples only show Class A.",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "What's the realistic communication range I can expect with STM32WL LoRa in an urban environment? I'm getting only 500m but the datasheet mentions several km.",
        "answer": "",
        "tags": "WL",
    },
    {
        "question": "When I write to internal flash on STM32WL during radio RX, I lose incoming packets. Is there a way to write flash without disrupting the radio? Or do I need to pause RX first?",
        "answer": "",
        "tags": "WL",
    },
    # ======================== STM32C0 ========================
    {
        "question": "GPIO pin on STM32C011 stays in input mode after HAL_GPIO_Init(). I'm setting it as push-pull output but nothing changes. The pin is not mapped to anything else in CubeMX.",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "USART1 on STM32C0 Nucleo transmits garbage characters. I'm targeting 115200 baud with HSI 48MHz. The receiver shows random bytes instead of my string.",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "I need my STM32C031 battery sensor to last 2 years on a CR2032. What's the lowest power mode I can use while still waking on a GPIO edge? Current draw target is under 2uA.",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "ADC on STM32C011 always returns 0 for all channels. I verified the input pin has 1.5V with a multimeter. The ADC clock is enabled. What am I missing in the init sequence?",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "I2C slave mode on STM32C0: the address match interrupt never fires. Master scanner shows the device doesn't ACK its address. The I2C init completes without error.",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "I'm new to STM32C0. What example projects are included in the STM32CubeC0 package? I need a starting point for UART + ADC + low power.",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "TIM3 PWM on STM32C0 outputs 500Hz instead of the 10kHz I calculated. Prescaler is 0, ARR is 4799, clock should be 48MHz. Where's my error?",
        "answer": "",
        "tags": "C0",
    },
    {
        "question": "Flash page erase on STM32C011 never returns — the function hangs. I call HAL_FLASH_Unlock() first and it returns HAL_OK. Is there a known issue with flash operations on C0?",
        "answer": "",
        "tags": "C0",
    },
]


def main():
    wb = Workbook()
    ws = wb.active
    ws.title = "Quality Test Suite"

    # Styles
    header_fill = PatternFill(start_color="1A2382", end_color="1A2382", fill_type="solid")
    header_font = Font(bold=True, size=11, color="FFFFFF")
    wrap_align = Alignment(wrap_text=True, vertical="top")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    # Headers: Question, Answer, Tags
    headers = ["Question", "Answer", "Tags"]
    col_widths = [80, 60, 12]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
        ws.column_dimensions[chr(64 + col_idx)].width = width

    # Data rows
    for row_idx, q in enumerate(QUESTIONS, start=2):
        row_data = [q["question"], q["answer"], q["tags"]]
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = wrap_align
            cell.border = thin_border
            cell.font = Font(size=10)

    # Freeze header + auto-filter
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:C{len(QUESTIONS) + 1}"

    # Save
    wb.save(XLSX_PATH)
    print(f"Generated: {XLSX_PATH}")
    print(f"Total questions: {len(QUESTIONS)}")


if __name__ == "__main__":
    main()
