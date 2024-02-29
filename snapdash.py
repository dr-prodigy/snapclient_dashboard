#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import sys
import time
import datetime
import traceback
import os

import config
import io_data
import dashboard
import rotary_encoder

from tendo import singleton
from utils import log_stderr, os_async_command

io_status = io_data.Status()
lcd = dashboard.Dashboard()
rotary = rotary_encoder.Rotary()

def main():
    refresh_start_time = datetime.datetime.now()
    while True:
        # save refresh start time
        try:
            rotary.scan(io_status)
            if (datetime.datetime.now() - refresh_start_time).total_seconds() > .2:
                lcd.update(io_status)
                refresh_start_time = datetime.datetime.now()
            else:
                time.sleep(.01)
        except (KeyboardInterrupt, SystemExit):
            # cleanup
            lcd.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
