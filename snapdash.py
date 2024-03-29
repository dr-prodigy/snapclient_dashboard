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

LCD_REFRESH_TIME = .2
CONTENT_REFRESH_TIME = 1
STATE_REFRESH_TIME_ACTIVE = 10
STATE_REFRESH_TIME_INACTIVE = 120
INACTIVE_MENU_SECS = 5
INACTIVE_DISPLAY_SECS = 20

def main():
    # initialize refresh timeouts
    lcd_refresh_time = datetime.datetime.now()
    content_refresh_time = datetime.datetime.now()
    state_refresh_time = datetime.datetime.now()
    inactive_time = datetime.datetime.now()
    hass.get_state(io_status)
    dash.idle_update(True, INACTIVE_DISPLAY_SECS)
    dash.content_update(io_status)
    while True:
        try:
            command = rotary.scan()
            if config.TEST_MODE and command is None:
                command = keyreader.scan()
            if command is not None:
                if not dash.is_active:
                    command = None
                inactive_time = datetime.datetime.now()
                dash.idle_update(True, INACTIVE_DISPLAY_SECS)
                if dash.menu_action(io_status, command):
                    # anticipated refresh
                    state_refresh_time = datetime.datetime.now() - \
                                         datetime.timedelta(seconds=STATE_REFRESH_TIME_ACTIVE - 1)

            # inactive time reached -> back to default view
            if (datetime.datetime.now() - inactive_time).total_seconds() > INACTIVE_MENU_SECS:
                dash.default_view(io_status)
            # periodic refresh (longer if inactive)
            refresh_timeout = STATE_REFRESH_TIME_ACTIVE if dash.is_active else STATE_REFRESH_TIME_INACTIVE
            if ((datetime.datetime.now() - state_refresh_time).total_seconds() > refresh_timeout
                    and not io_status.ui_changing):
                hass.get_state(io_status)
                state_refresh_time = datetime.datetime.now()
            if (datetime.datetime.now() - content_refresh_time).total_seconds() > CONTENT_REFRESH_TIME:
                dash.content_update(io_status)
                content_refresh_time = datetime.datetime.now()
            if (datetime.datetime.now() - lcd_refresh_time).total_seconds() > LCD_REFRESH_TIME:
                dash.update()
                lcd_refresh_time = datetime.datetime.now()
            time.sleep(.01)
        except (KeyboardInterrupt, SystemExit):
            # cleanup
            dash.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
