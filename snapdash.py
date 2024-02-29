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
        # save refresh start time
        refresh_start_time = datetime.datetime.now()
        try:
            rotary.scan(io_status)

        except (KeyboardInterrupt, SystemExit):
            # cleanup
            lcd.cleanup()
            rotary.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
        finally:
            try:
                if (datetime.datetime.now() - refresh_start_time).total_seconds() > .2:
                    lcd.update_content(io_status)
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
                # LCD I/O error: refresh LCD screen
                log_stderr(traceback.format_exc())
                log_stderr('LCD I/O error: trying to recover..')
                time.sleep(1)
                lcd.refresh_display(io_status)
