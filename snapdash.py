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

from tendo import singleton
from utils import log_stderr, os_async_command

sig_command = False
io_status = io_data.Status()
lcd = dashboard.Dashboard()


def main():
    global sig_command

    update_lcd_content()
    while True:
        try:
            # save cycle start time
            cycle_start_time = datetime.datetime.now()

        except (KeyboardInterrupt, SystemExit):
            # cleanup sensors & LCD
            lcd.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
        finally:
            try:
                # update lcd screen to 1 sec approx.
                cycle_duration = (datetime.datetime.now() - cycle_start_time)\
                    .total_seconds()
                for loop in range(4):
                    # catch command "interrupt" (jump to new cycle)
                    #if sig_command:
                    #    break
                    frame_duration = lcd.update(io_status)
                    if frame_duration < .25 and cycle_duration < 1:
                        time.sleep(.25 - frame_duration)
                    cycle_duration += .25

                if sig_command:
                    sig_command = False
                    refreshing = True

            except (KeyboardInterrupt, SystemExit):
                # cleanup sensors & LCD
                lcd.cleanup()
                raise
            except Exception:
                # LCD I/O error: refresh LCD screen
                log_stderr(traceback.format_exc())
                log_stderr('LCD I/O error: trying to recover..')
                time.sleep(1)
                lcd.refresh_display(io_status)

def update_lcd_content(change=False):
    if change:
        lcd.change_dashboard_program(io_status)

    lcd.update_content(io_status, change)
