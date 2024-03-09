#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import traceback
import math
from time import strftime

import config
from utils import log_stderr, LEFT, RIGHT, BUTTON

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

# menu id: [show function, 'Menu desc', button change function, post change menu id, parent menu id],
menu = {
    1: ['show_source', 'Source', 'change_source', 1, -1],
    2: ['show_status', 'Snapcast', 'change_status', 2, -1],
    3: ['show_volume', 'Volume', None, 31, -1],
    31: ['show_volume', 'Volume', 'change_volume', 3, 3],
}

class Dashboard:
    def __init__(self):
        self._current_program = -1
        self._message_timeout = datetime.datetime(9999, 12, 31)
        self.line = [''] * LCD_ROWS
        self.old_line = [''] * LCD_ROWS
        self.lcd = None
        self.refresh_display()
        self.current_menu_item = 2
        self.current_source = 0

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

        # backlight change timeout expired: set backlight with no timeout
        self.lcd.set_backlight(True)

        if CURRENT_CHARSET != NEW_CHARSET:
            CURRENT_CHARSET = NEW_CHARSET
            self.cleanup()
            self._load_charset()

        blink_off = datetime.datetime.now().second % 2 != 0

        tmp_lines = [''] * LCD_ROWS
        for no in range(0, LCD_ROWS):
            tmp_line = ''
            blinked = False
            for ch in self.line[no]:
                if ch == '&':
                    blinked = not blinked
                else:
                    tmp_line += ' ' if blinked and blink_off else ch

            tmp_line = tmp_line.center(LCD_COLUMNS)

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
            replace_chars = ['*', '+', '=', 'A', 'M', '?', '?', '?', '#', 'O']
        else:
            replace_chars = ['*', '+', '=', 'A', 'M', '-', '_', '=', '#', 'O']

        print(' ' * (LCD_COLUMNS + 4))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ')
        for row in range(0, LCD_ROWS):
            count = 0
            cur_row = lines[row]
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\xDB\xFF':
                cur_row = cur_row.replace(char, replace_chars[count])
                count += 1
            print(' |{}| '.format(cur_row))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ')
        print(' ' * int(LCD_COLUMNS + 4))
        # restore cursor pos
        sys.stdout.write("\x1b8")

    # menu id: [show function, 'Menu desc', button change function, post change menu id, parent menu id],
    def menu_update(self, io_status):
        menu_item = menu[self.current_menu_item]
        self.line[0] = menu_item[1]
        if menu_item[0] == 'show_source':
            self.line[1] = '&{}&'.format(io_status.sources[io_status.current_source])
        elif menu_item[0] == 'show_status':
            if io_status.is_muted:
                self.line[1] = '&Mute&'
            else:
                self.line[1] = 'Playing &>&' if io_status.is_playing else 'Idle'
        elif menu_item[0] == 'show_volume':
            vol_blink = '&' if menu_item[2] else ''
            self.line[1] = '{}{}{}{}'.format(vol_blink,
                                             '\xFF' * int(io_status.volume / 100.0 * 14),
                                             vol_blink,
                                             '\xDB' * (14 - int(io_status.volume / 100.0 * 14)))
        else:
            self.line[1] = menu[self.current_menu_item][1]

    def menu_action(self, io_status, command):
        action = menu[self.current_menu_item][2]
        if command == RIGHT:
            if action == 'change_volume':
                io_status.volume += 2 if io_status.volume < 100 else 0
            elif(self.current_menu_item + 1) in menu:
                self.current_menu_item += 1
        elif command == LEFT:
            if action == 'change_volume':
                io_status.volume -= 2 if io_status.volume > 0 else 0
            elif (self.current_menu_item - 1) in menu:
                self.current_menu_item -= 1
        elif command == BUTTON:
            if action == 'change_source':
                if io_status.current_source < len(io_status.sources) - 1:
                    io_status.current_source += 1
                else:
                    io_status.current_source = 0
            elif action == 'change_status':
                io_status.is_muted = not io_status.is_muted
            elif action == 'change_volume':
                pass
            self.current_menu_item = menu[self.current_menu_item][3]

        if command is not None:
            self.menu_update(io_status)