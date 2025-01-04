#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import traceback
from time import strftime

import config
import hass
from utils import log_stderr, LEFT, RIGHT, BUTTON
from hass import Service

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
LCD_BL = None
if len(config.GPIO_LCD) > 6:
    LCD_BL = config.GPIO_LCD[6]

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
    # pause \x03
    [0b11011,
     0b11011,
     0b11011,
     0b11011,
     0b11011,
     0b11011,
     0b11011,
     0b00000],
    # play \x04
    [0b10000,
     0b11000,
     0b11100,
     0b11110,
     0b11100,
     0b11000,
     0b10000,
     0b00000],
    # up \x05
    [0b11111,
     0b11111,
     0b00000,
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
     0b00000,
     0b11111,
     0b11111],
    # up+down \x07
    [0b11111,
     0b11111,
     0b00000,
     0b00000,
     0b00000,
     0b00000,
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
    ':': ['&\xA5&',
          '&\xA5&'],
    '\'': ['\xDF',
           ' '],
}

# menu id: [show function, 'Menu desc', button change function, post change menu id, parent menu id, ui_changing]
menu = {
    1: ['show_source', 'Source', 'change_source', 1, -1, False],
    2: ['show_status', 'Snapcast', 'change_status', 2, -1, False],
    3: ['show_volume', 'Volume', None, 31, -1, False],
    31: ['show_volume', 'Volume', 'change_volume', 3, 3, True],
}


class Dashboard:
    def __init__(self):
        self._current_program = -1
        self._line = [''] * LCD_ROWS
        self._old_line = [''] * LCD_ROWS
        self.lcd = None
        self.refresh_display()
        self.current_menu_item = 2
        self.is_active = False
        self._inactive_time = datetime.datetime(9999, 12, 31)

    def _load_charset(self):
        if PAUSED: return
        if CURRENT_CHARSET == CHARSET_BIGNUM:
            if DISPLAY_TYPE == GPIO_CharLCD:
                for font_count in range(3, 8):
                    self.lcd.create_char(font_count, BIGNUMDATA[font_count - 3])
            elif DISPLAY_TYPE == I2C_LCD:
                self.lcd.lcd_load_custom_chars(BIGNUMDATA)

    def refresh_display(self, io_status=None):
        global PAUSED
        try:
            PAUSED = False
            if DISPLAY_TYPE == GPIO_CharLCD:
                # initialize display
                if self.lcd is None:
                    self.lcd = RPiGPIO_CharLCD(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7,
                                               LCD_COLUMNS, LCD_ROWS,
                                               LCD_BL, enable_pwm=config.DISPLAY_PWM_BACKLIGHT)
            elif DISPLAY_TYPE == I2C_LCD:
                # initialize display
                self.lcd = I2C_LCD_driver.lcd(I2C_ADDRESS, I2C_BUS)
            # load symbol font data
            self._load_charset()

            if io_status:
                # force lines refresh
                self._old_line = [''] * LCD_ROWS
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

    def idle_update(self, wakeup=False, secs_to_inactive=3600):
        global CURRENT_CHARSET, NEW_CHARSET
        if PAUSED: return

        # set backlight and re-initialize LCD screen text on backlight on
        if wakeup:
            self._inactive_time = datetime.datetime.now() + datetime.timedelta(seconds=secs_to_inactive)
            if not self.is_active:
                self.is_active = True
                if DISPLAY_TYPE != NONE and config.DISPLAY_AUTO_DIM:
                    self.lcd.set_backlight(config.DISPLAY_ON_BACKLIGHT if config.DISPLAY_PWM_BACKLIGHT else True)
                self.update()
        elif datetime.datetime.now() >= self._inactive_time and self.is_active:
            self.is_active = False
            if DISPLAY_TYPE != NONE and config.DISPLAY_AUTO_DIM:
                self.lcd.set_backlight(config.DISPLAY_DIM_BACKLIGHT if config.DISPLAY_PWM_BACKLIGHT else False)

    def default_view(self, io_status):
        self.current_menu_item = 2
        self.content_update(io_status)

    def update(self):
        global CURRENT_CHARSET, NEW_CHARSET
        if PAUSED: return 0

        start_time = datetime.datetime.now()
        self.idle_update()

        if CURRENT_CHARSET != NEW_CHARSET:
            CURRENT_CHARSET = NEW_CHARSET
            self.cleanup()
            self._load_charset()

        blink_off = datetime.datetime.now().microsecond < 300000

        tmp_lines = [''] * LCD_ROWS
        for no in range(0, LCD_ROWS):
            tmp_line = ''
            blinked = False
            for ch in self._line[no]:
                if ch == '&':
                    blinked = not blinked
                else:
                    tmp_line += ' ' if blinked and blink_off else ch

            tmp_line = tmp_line.center(LCD_COLUMNS)

            if self._old_line[no] != tmp_line:
                self._old_line[no] = tmp_line
                if DISPLAY_TYPE != NONE: self.lcd.lcd_display_string(tmp_line, no)
            tmp_lines[no] = tmp_line

        self.echo_display(tmp_lines)
        return (datetime.datetime.now() - start_time).total_seconds()

    def cleanup(self):
        if PAUSED: return

        if DISPLAY_TYPE == I2C_LCD:
            self.lcd.lcd_clear()
        elif DISPLAY_TYPE == GPIO_CharLCD:
            # on RPiGPIO lcd_clear breaks..
            for row in range(0, LCD_ROWS):
                self.lcd.lcd_display_string(' ' * LCD_COLUMNS, row)
        self.echo_display([' ' * LCD_COLUMNS] * LCD_ROWS)

    def echo_display(self, lines):
        # move cursor home
        sys.stdout.write("\x1b[H")
        if CURRENT_CHARSET == CHARSET_SYMBOL:
            replace_chars = ['?', '?', '?', '?', '?', '>', '°', '#', '?', '.']
        else:
            replace_chars = ['"', '>', '-', '_', '=', '>', '°', '#', '0', '.']

        horz_char = '-'
        vert_char = '|'
        if not self.is_active and config.DISPLAY_AUTO_DIM:
            horz_char = vert_char = '.'

        print(' ' * (LCD_COLUMNS + 4))
        print(' +' + (horz_char * LCD_COLUMNS) + '+ ')
        for row in range(0, LCD_ROWS):
            count = 0
            cur_row = lines[row]
            for char in '\x03\x04\x05\x06\x07\x7E\xDF\xDB\xFF\xA5':
                cur_row = cur_row.replace(char, replace_chars[count])
                count += 1
            print(' {}{}{} '.format(vert_char, cur_row, vert_char))
        print(' +' + (horz_char * LCD_COLUMNS) + '+ ')
        print(' ' * (LCD_COLUMNS + 4))
        # restore cursor pos
        sys.stdout.write("\x1b8")

    # menu id: [show function, 'Menu desc', button change function, post change menu id, parent menu id, ui_changing]
    def content_update(self, io_status):
        if self.is_active:
            menu_item = menu[self.current_menu_item]
            self._line[0] = menu_item[1]
            if menu_item[0] == 'show_source':
                self._line[1] = '&{}&'.format(io_status.source)
            elif menu_item[0] == 'show_status':
                self._line[0] = io_status.friendly_name
                if io_status.is_volume_muted:
                    self._line[1] = '&Mute&'
                else:
                    self._line[1] = 'Playing &\x04&' if io_status.state == 'playing' else (
                        '{} \x03'.format(io_status.state.capitalize()))
            elif menu_item[0] == 'show_volume':
                vol_blink = '&' if menu_item[2] else ''
                if io_status.is_volume_muted:
                    self._line[1] = '{}Mute{}'.format(vol_blink, vol_blink)
                else:
                    self._line[1] = '{}{}{}{}'.format(vol_blink,
                                                     '\xFF' * int(io_status.volume_level * 14),
                                                      vol_blink,
                                                     '\xDB' * (14 - int(io_status.volume_level * 14)))
            else:
                self._line[1] = menu[self.current_menu_item][1]
            io_status.ui_changing = menu_item[5]
        else:
            time = strftime("%H:%M")
            # add leading space
            time1 = time2 = ' '
            for char in time:
                try:
                    if char == '.' or char == ':' or char == '\'':
                        time1 = time1[:-1]
                        time2 = time2[:-1]
                    time1 += BIGNUMMATRIX[char][0]
                    time2 += BIGNUMMATRIX[char][1]
                except Exception:
                    traceback.print_exc()
                    pass
            # remove last space, then center
            self._line[0] = time1[:-1].center(LCD_COLUMNS)
            self._line[1] = time2[:-1].center(LCD_COLUMNS)
            # add playing icon
            if io_status.state == 'playing':
                self._line[1] = "&\x04&" + self._line[1][1:]

    def menu_action(self, io_status, command):
        state_refresh = False
        action = menu[self.current_menu_item][2]
        if command == RIGHT:
            if action == 'change_volume':
                if io_status.is_volume_muted:
                    io_status.is_volume_muted = False
                io_status.volume_level += .05
                if io_status.volume_level > 1:
                    io_status.volume_level = 1
            elif (self.current_menu_item + 1) in menu:
                self.current_menu_item += 1
        elif command == LEFT:
            if action == 'change_volume':
                io_status.volume_level -= .05
                if io_status.volume_level < 0.05:
                    io_status.volume_level = 0.05
                    io_status.is_volume_muted = True
            elif (self.current_menu_item - 1) in menu:
                self.current_menu_item -= 1
        elif command == BUTTON:
            if action == 'change_source':
                if len(io_status.sources) > 0:
                    source_index = -1
                    if io_status.source in io_status.sources:
                        source_index = io_status.sources.index(io_status.source)
                    if source_index < len(io_status.sources) - 1:
                        source_index += 1
                    else:
                        source_index = 0
                    io_status.source = io_status.sources[source_index]
                else:
                    io_status.source = ''
                hass.set_service(io_status, Service.SELECT_SOURCE)
                state_refresh = True
            elif action == 'change_status':
                if io_status.is_volume_muted:
                    io_status.is_volume_muted = False
                    hass.set_service(io_status, Service.VOLUME_MUTE)
                elif io_status.state == 'playing':
                    hass.set_service(io_status, Service.PAUSE)
                elif io_status.state == 'idle':
                    hass.set_service(io_status, Service.PLAY)
                state_refresh = True
            elif action == 'change_volume':
                if io_status.is_volume_muted:
                    hass.set_service(io_status, Service.VOLUME_MUTE)
                else:
                    hass.set_service(io_status, Service.VOLUME_MUTE)
                    hass.set_service(io_status, Service.VOLUME_SET)
            self.current_menu_item = menu[self.current_menu_item][3]

        if command is not None:
            # if state_refresh:
            #     hass.get_state(io_status)
            self.content_update(io_status)

        return state_refresh
