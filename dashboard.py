#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import traceback
import math
from time import strftime

import config

from utils import log_stderr

NONE = 0
GPIO_CharLCD = 1
I2C_LCD = 2

DISPLAY_TYPE = NONE
PAUSED = False

try:
    DISPLAY_TYPE = config.MODULE_LCD
except Exception:
    pass

if DISPLAY_TYPE == GPIO_CharLCD:
    from lib.RPiGPIO_CharLCD import RPiGPIO_CharLCD
elif DISPLAY_TYPE == I2C_LCD:
    from lib import I2C_LCD_driver
else:
    DISPLAY_TYPE = NONE

# charsets
CHARSET_SYMBOL = 0
CHARSET_BIGNUM = 1

CURRENT_CHARSET = None
# NEW_CHARSET = CHARSET_SYMBOL # change charset
NEW_CHARSET = CHARSET_BIGNUM

# RPiGPIO_CharLCD pin configuration
LCD_RS = config.GPIO_LCD[0]
LCD_EN = config.GPIO_LCD[1]
LCD_D4 = config.GPIO_LCD[2]
LCD_D5 = config.GPIO_LCD[3]
LCD_D6 = config.GPIO_LCD[4]
LCD_D7 = config.GPIO_LCD[5]

# I2C_LCD configuration
# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
try:
    I2C_BUS = config.I2C_BUS
except Exception:
    I2C_BUS = 1
# LCD Address (0X27 = 16x2)
try:
    I2C_ADDRESS = config.I2C_ADDRESS
except Exception:
    I2C_ADDRESS = 0x27
# LCD COLUMNS
try:
    LCD_COLUMNS = config.LCD_COLUMNS
except Exception:
    LCD_COLUMNS = 16
# LCD COLUMNS
try:
    LCD_ROWS = config.LCD_ROWS
except Exception:
    LCD_ROWS = 2

# global parameters
LCD_LINE_DELAY = 3

BIGNUMDATA = [
    # on icon (flame) /x00
    [0b01000,
     0b01001,
     0b00110,
     0b01011,
     0b10111,
     0b10101,
     0b01110,
     0b00000],
    # warming icon (empty flame) /x01
    [0b01000,
     0b01001,
     0b00110,
     0b01001,
     0b10001,
     0b10001,
     0b01110,
     0b00000],
    # cooling icon (smokey) /x02
    [0b01000,
     0b10000,
     0b01000,
     0b10101,
     0b10101,
     0b10101,
     0b10101,
     0b00000],
    # automatic char /x03
    [0b00000,
     0b00000,
     0b01110,
     0b10101,
     0b10111,
     0b10001,
     0b01110,
     0b00000],
    # manual char /x04
    [0b00100,
     0b01110,
     0b11110,
     0b11111,
     0b10001,
     0b10001,
     0b10001,
     0b10010],
    # up \x05
    [0b11111,
     0b11111,
     0b11111,
     0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b00000],
    # down \x06
    [0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b00000,
     0b11111,
     0b11111,
     0b11111],
    # up+down \x07
    [0b11111,
     0b11111,
     0b11111,
     0b00000,
     0b00000,
     0b11111,
     0b11111,
     0b11111]
]
BIGNUMMATRIX = {
    '0': ['\xFF\x05\xFF ',
          '\xFF\x06\xFF '],
    '1': ['\x06\xFF ',
          ' \xFF '],
    '2': ['\x05\x07\xFF ',
          '\xFF\x06\x06 '],
    '3': ['\x05\x07\xFF ',
          '\x06\x06\xFF '],
    '4': ['\xFF\x06\xFF ',
          '  \xFF '],
    '5': ['\xFF\x07\x05 ',
          '\x06\x06\xFF '],
    '6': ['\xFF\x07\x07 ',
          '\xFF\x06\xFF '],
    '7': ['\x05\x05\xFF ',
          ' \xFF  '],
    '8': ['\xFF\x07\xFF ',
          '\xFF\x06\xFF '],
    '9': ['\xFF\x07\xFF ',
          '\x06\x06\xFF '],
    ' ': [' ',
          ' '],
    '.': [' ',
          '.'],
    ':': ['\xA5',
          '\xA5'],
    '\'': ['\xDF',
           ' '],
}


class Dashboard:
    def __init__(self):
        self._current_program = -1
        self._message_timeout = datetime.datetime(9999, 12, 31)
        self.line = [''] * LCD_ROWS
        self.old_line = [''] * LCD_ROWS
        self.lcd = None
        self.refresh_display()

    def _load_charset(self):
        if PAUSED:
            return

        if CURRENT_CHARSET == CHARSET_SYMBOL:
            if DISPLAY_TYPE == GPIO_CharLCD:
                for font_count in range(0, 4):
                    self.lcd.create_char(font_count, SYMBOLDATA[font_count])
            elif DISPLAY_TYPE == I2C_LCD:
                self.lcd.lcd_load_custom_chars(SYMBOLDATA)
        elif CURRENT_CHARSET == CHARSET_BIGNUM:
            if DISPLAY_TYPE == GPIO_CharLCD:
                for font_count in range(0, 8):
                    self.lcd.create_char(font_count, BIGNUMDATA[font_count])
            elif DISPLAY_TYPE == I2C_LCD:
                self.lcd.lcd_load_custom_chars(BIGNUMDATA)

    def refresh_display(self, io_status=None):
        global PAUSED
        try:
            PAUSED = False
            if DISPLAY_TYPE == GPIO_CharLCD:
                # initialize display
                if self.lcd is None:
                    self.lcd = RPiGPIO_CharLCD(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7, LCD_COLUMNS, LCD_ROWS)
            elif DISPLAY_TYPE == I2C_LCD:
                # initialize display
                self.lcd = I2C_LCD_driver.lcd(I2C_ADDRESS, I2C_BUS)
            # load symbol font data
            self._load_charset()

            if io_status:
                # force lines refresh
                self.old_line = [''] * LCD_ROWS
                self.update()
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('ERR: LCD init failed: PAUSED')
            PAUSED = True

    def set_charset(self, charset=CHARSET_SYMBOL):
        global NEW_CHARSET
        NEW_CHARSET = charset

    def update(self, io_status):
        global CURRENT_CHARSET, NEW_CHARSET
        if DISPLAY_TYPE == NONE or PAUSED:
            return 0

        start_time = datetime.datetime.now()

        # +----------------+
        # |     Play >     |
        # | ______________ |
        # +----------------+
        status = 'Play ¶'
        vol_full_char = '\xFF'
        vol_empty_char = '_'
        if io_status.is_muted:
            status = ' Mute '
            vol_full_char = '#'
            vol_empty_char = '^'
        self.line[0] = '     {}     '.format(status)
        self.line[1] = ' {}{} '.format(vol_full_char * int(io_status.volume / 100.0 * 14),
                                       vol_empty_char * 14 - int(io_status.volume / 100.0 * 14))

        # backlight change timeout expired: set backlight with no timeout
        self.lcd.set_backlight(True)

        if CURRENT_CHARSET != NEW_CHARSET:
            CURRENT_CHARSET = NEW_CHARSET
            self.cleanup()
            self._load_charset()

        blink_off = datetime.datetime.now().second % 2 != 0

        tmp_lines = [''] * LCD_ROWS
        for no in range(0, LCD_ROWS):
            tmp_line = self.line[no]
            if blink_off:
                tmp_line = (tmp_line.replace('\xA5', ' ')
                            .replace('^', ' ')
                            .replace('#', ' ')
                            .replace('¶', ' '))
            else:
                tmp_line = (tmp_line.replace('^', '_')
                            .replace('#', '\xFF')
                            .replace('¶', '>'))
            if self.old_line[no] != tmp_line:
                self.old_line[no] = tmp_line
                self.lcd.lcd_display_string(tmp_line, no)
            tmp_lines[no] = tmp_line

        self.echo_display(tmp_lines)
        return (datetime.datetime.now() - start_time).total_seconds()

    def cleanup(self):
        if DISPLAY_TYPE == NONE or PAUSED:
            return

        if DISPLAY_TYPE == I2C_LCD:
            self.lcd.lcd_clear()
        else:
            # on RPiGPIO lcd_clear breaks..
            for row in range(0, LCD_ROWS):
                self.lcd.lcd_display_string(' ' * LCD_COLUMNS, row)
        self.echo_display([' ' * LCD_COLUMNS] * LCD_ROWS)


    def echo_display(self, lines):
        # move cursor home
        sys.stdout.write("\x1b[H")
        if CURRENT_CHARSET == CHARSET_SYMBOL:
            replace_chars = ['*', '+', '=', 'A', 'M', '?', '?', '?', '>', '°',
                             '?', '.']
        else:
            replace_chars = ['*', '+', '=', 'A', 'M', '-', '_', '=', '>', '°',
                             '0', '.']

        print(' ' * (LCD_COLUMNS + 4))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ')
        for row in range(0, LCD_ROWS):
            count = 0
            cur_row = lines[row]
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\x7E\xDF\xFF\xA5':
                cur_row = cur_row.replace(char, replace_chars[count])
                count += 1
            print(' |{}| '.format(cur_row))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ')
        print(' ' * int(LCD_COLUMNS + 4))
        # restore cursor pos
        sys.stdout.write("\x1b8")
