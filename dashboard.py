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

# RPiGPIO_CharLCD pin configuration:
LCD_RS = 4  # Note this might need to be changed to 21 for older revision Pi's
LCD_EN = 17
LCD_D4 = 22
LCD_D5 = 23
LCD_D6 = 24
LCD_D7 = 25
LCD_BACKLIGHT = 26  # NOT USED

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
        self._is_backlit = True
        self._backlight_change = datetime.datetime(9999, 12, 31)
        self._command = ''
        self._message_timeout = datetime.datetime(9999, 12, 31)
        self.line = [''] * LCD_ROWS
        self.old_line = [''] * LCD_ROWS
        self.position = [-LCD_LINE_DELAY] * LCD_ROWS
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

    def refresh_display(self, io_status = None):
        global PAUSED
        try:
            PAUSED = False
            if DISPLAY_TYPE == GPIO_CharLCD:
                # initialize display
                self.lcd = RPiGPIO_CharLCD(LCD_RS, LCD_EN, LCD_D4, LCD_D5,
                                           LCD_D6, LCD_D7,
                                           LCD_COLUMNS, LCD_ROWS,
                                           LCD_BACKLIGHT)
            elif DISPLAY_TYPE == I2C_LCD:
                # initialize display
                self.lcd = I2C_LCD_driver.lcd(I2C_ADDRESS, I2C_BUS)
            # load symbol font data
            self._load_charset()

            if io_status:
                # force lines refresh
                self.old_line = [''] * LCD_ROWS
                self.update(io_status)
        except KeyboardInterrupt:
            raise
        except Exception:
            log_stderr(traceback.format_exc())
            log_stderr('ERR: LCD init failed: PAUSED')
            PAUSED = True

    def set_charset(self, charset=CHARSET_SYMBOL):
        global NEW_CHARSET
        NEW_CHARSET = charset

    def update_content(self, io_status, change=True):
        if not config.MODULE_LCD or PAUSED:
            return

        # bignum view
        if config.TEST_MODE == 2:
            # bignum test mode
            clock = '0123456789\''
        else:
            clock = strftime("%H:%M")

        main_temp1 = main_temp2 = ''
        for char in clock:
            try:
                if char == '.' \
                        or char == ':' \
                        or char == '\'':
                    main_temp1 = main_temp1[:-1]
                    main_temp2 = main_temp2[:-1]
                main_temp1 += BIGNUMMATRIX[char][0]
                main_temp2 += BIGNUMMATRIX[char][1]
            except Exception:
                traceback.print_exc()
                pass

        if False and io_status.message == '':
            # +----------------+
            # |_ XXX XXX XXX°  |
            # |M XXX XXX.XXX   |
            # +----------------+
            self.set_charset(CHARSET_BIGNUM)

            if self._current_program % 4 == 0:
                self.line[0] = '{} {}'.format(heating_icon,
                                              main_temp1.center(14))
                self.line[1] = '{} {}'.format(mode_icon,
                                              main_temp2.center(14))
            else:
                self.line[0] = main_temp1.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
                self.line[1] = main_temp2.center(LCD_COLUMNS + 1)[0:LCD_COLUMNS]
        else:
            # +----------------+
            # |     Play >     |
            # | ______________ |
            # +----------------+
            # self.set_charset(CHARSET_SYMBOL) # change charset
            self.line[0] = '     Play >     '
            if io_status.message != '':
                self.line[1] = ' \xA5 \xA5 \xA5 ' + \
                               io_status.message + ' \xA5 \xA5 \xA5'
            else:
                self.line[1] = ' ______________ '

        # if program is changed, reset positions
        if change:
            self.position = [-LCD_LINE_DELAY] * LCD_ROWS

    def update(self, refresh_requested=False, draw=True):
        global CURRENT_CHARSET, NEW_CHARSET
        if DISPLAY_TYPE == NONE or PAUSED:
            return 0

        start_time = datetime.datetime.now()
        tmp_lines = [''] * LCD_ROWS

        # backlight change timeout expired: set backlight with no timeout
        if datetime.datetime.now() > self._backlight_change:
            self.set_backlight(not self._is_backlit)

        if draw and (self._is_backlit or refresh_requested):
            if CURRENT_CHARSET != NEW_CHARSET:
                CURRENT_CHARSET = NEW_CHARSET
                self.cleanup()
                self._load_charset()

        blink_off = datetime.datetime.now().second % 2 != 0

        # lines update
        if datetime.datetime.now() >= self._message_timeout:
            self._command = ''

        for no in range(0, LCD_ROWS):
            if self._command:
                if no == int(LCD_ROWS / 2):
                    tmp_lines[no] = self._command.center(LCD_COLUMNS)
                else:
                    tmp_lines[no] = ' ' * LCD_COLUMNS
            else:
                if len(self.line[no]) > LCD_COLUMNS:
                    self.position[no] += 1
                    if self.position[no] > len(
                            self.line[no]) - LCD_COLUMNS + LCD_LINE_DELAY:
                        self.position[no] = -LCD_LINE_DELAY
                position = 0 if self.position[no] < 0 else \
                    len(self.line[no]) - LCD_COLUMNS if self.position[no] > \
                    len(self.line[no]) - LCD_COLUMNS else \
                    self.position[no]
                cur_line = self.line[no][position:len(self.line[no])].ljust(
                    LCD_COLUMNS)[0:LCD_COLUMNS]
                tmp_lines[no] = cur_line

            if blink_off:
                tmp_lines[no] = tmp_lines[no].replace('\xA5', ' ')
                tmp_lines[no] = tmp_lines[no].replace('^', ' ')
                tmp_lines[no] = tmp_lines[no].replace('@', ' ')
                tmp_lines[no] = tmp_lines[no].replace('¶', ' ')
            else:
                tmp_lines[no] = tmp_lines[no].replace('^', ':')
                tmp_lines[no] = tmp_lines[no].replace('@', '<')
                tmp_lines[no] = tmp_lines[no].replace('¶', '>')

            if draw and (self._is_backlit or refresh_requested):
                if self.old_line[no] != tmp_lines[no]:
                    self.old_line[no] = tmp_lines[no]
                    self.lcd.lcd_display_string(tmp_lines[no], no)

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

    def set_backlight(self, state, timeout=datetime.datetime(9999, 12, 31)):
        global CURRENT_CHARSET, NEW_CHARSET

        if DISPLAY_TYPE == NONE or PAUSED:
            return

        # set backlight and re-initialize LCD screen text on backlight on
        if state and not self._is_backlit:
            if CURRENT_CHARSET != NEW_CHARSET:
                CURRENT_CHARSET = NEW_CHARSET
                self.cleanup()
                self._load_charset()

            for row in range(0, LCD_ROWS):
                self.lcd.lcd_display_string(self.line[row], row)
        self.lcd.set_backlight(state)

        self._is_backlit = state
        self._backlight_change = timeout

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
        print(' +' +
              ('-' * LCD_COLUMNS) + '+ ' if self._is_backlit else
              ' +' + '- ' * int(LCD_COLUMNS / 2) + '+ ')
        for row in range(0, LCD_ROWS):
            count = 0
            cur_row = lines[row]
            for char in '\x00\x01\x02\x03\x04\x05\x06\x07\x7E\xDF\xFF\xA5':
                cur_row = cur_row.replace(char, replace_chars[count])
                count += 1
            print(' |{}| '.format(cur_row))
        print(' +' + ('-' * LCD_COLUMNS) + '+ ' if self._is_backlit
              else ' +' + '- ' * int(
            LCD_COLUMNS / 2) + '+ ')
        print(' ' * int(LCD_COLUMNS + 4))
        # restore cursor pos
        sys.stdout.write("\x1b8")
