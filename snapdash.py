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
    while True:
        try:
            # save cycle start time
            cycle_start_time = datetime.datetime.now()
            rotary.scan(io_status)
            lcd.update_content(io_status)

        except (KeyboardInterrupt, SystemExit):
            # cleanup
            lcd.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
        finally:
            try:
                cycle_duration = (datetime.datetime.now() - cycle_start_time)\
                    .total_seconds() + lcd.update(io_status)
                if cycle_duration < .05:
                    time.sleep(.05 - cycle_duration)

            except (KeyboardInterrupt, SystemExit):
                # cleanup
                lcd.cleanup()
                rotary.cleanup()
                raise
            except Exception:
                # LCD I/O error: refresh LCD screen
                log_stderr(traceback.format_exc())
                log_stderr('LCD I/O error: trying to recover..')
                time.sleep(1)
                lcd.refresh_display(io_status)
