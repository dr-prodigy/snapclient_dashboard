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
keyreader = key_reader.KeyReader(block=False)

def main():
    refresh_start_time = datetime.datetime.now()
    command = None
    hass.get_state(io_status)
    dash.menu_update(io_status)
    while True:
        # save refresh start time
        try:
            command = rotary.scan()
            if command is None:
                command = keyreader.scan()
            if command is not None:
                dash.menu_action(io_status, command)

            if (datetime.datetime.now() - refresh_start_time).total_seconds() > .2:
                dash.update(io_status)
                refresh_start_time = datetime.datetime.now()
            else:
                time.sleep(.01)
        except (KeyboardInterrupt, SystemExit):
            # cleanup
            dash.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
