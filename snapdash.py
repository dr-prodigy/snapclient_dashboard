#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import sys
import time
import datetime
import traceback
import os

import config
import utils
import io_data
import dashboard
import rotary_encoder
import key_reader
import hass

from tendo import singleton
from utils import log_stderr, os_async_command

io_status = io_data.Status()
dash = dashboard.Dashboard()
rotary = rotary_encoder.Rotary()
if config.TEST_MODE:
    keyreader = key_reader.KeyReader(block=False)

STATE_REFRESH_TIME = 10
INACTIVE_TIME = 20
LCD_REFRESH_TIME = .2

def main():
    # initialize refresh timeouts
    lcd_refresh_time = datetime.datetime.now()
    state_refresh_time = datetime.datetime.now()
    inactive_time = datetime.datetime.now()
    command = None
    hass.get_state(io_status)
    dash.menu_update(io_status)
    while True:
        try:
            command = rotary.scan()
            if config.TEST_MODE and command is None:
                command = keyreader.scan()
            if command is not None:
                inactive_time = datetime.datetime.now()
                if dash.menu_action(io_status, command):
                    # anticipated refresh
                    state_refresh_time = datetime.datetime.now() - datetime.timedelta(seconds=STATE_REFRESH_TIME - 1)

            if (datetime.datetime.now() - inactive_time).total_seconds() > INACTIVE_TIME:
                dash.default_view(io_status)
            if ((datetime.datetime.now() - state_refresh_time).total_seconds() > STATE_REFRESH_TIME
                    and not io_status.ui_changing):
                hass.get_state(io_status)
                dash.menu_update(io_status)
                state_refresh_time = datetime.datetime.now()
            if (datetime.datetime.now() - lcd_refresh_time).total_seconds() > LCD_REFRESH_TIME:
                dash.update()
                lcd_refresh_time = datetime.datetime.now()
        except (KeyboardInterrupt, SystemExit):
            # cleanup
            dash.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
