#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import time
import datetime
import traceback

import config
import io_data
import dashboard
import rotary_encoder
import key_reader
import sensors
import hass
import mqtt

from utils import log_stderr, os_async_command

io_status = io_data.Status()
dash = dashboard.Dashboard()
rotary = rotary_encoder.Rotary()
sensor = sensors.Sensors()
mqtt = mqtt.MQTT(io_status)

if config.TEST_MODE:
    keyreader = key_reader.KeyReader(block=False)

LCD_REFRESH_TIME = .2
CONTENT_REFRESH_TIME = 1
STATE_REFRESH_TIME_ACTIVE = 10
STATE_REFRESH_TIME_INACTIVE = 120
TEMPERATURE_REFRESH_TIME = 20
TEMPERATURE_MQTT_PUBLISH_TIME = 900 # 15 mins
TEMPERATURE_MQTT_PUBLISH_THRESHOLD = 1
INACTIVE_MENU_SECS = 5
INACTIVE_DISPLAY_SECS = 20

def main():
    # initialize refresh timeouts
    now = lcd_refresh_time = content_refresh_time = state_refresh_time = \
        inactive_time = temperature_mqtt_time = datetime.datetime.now()
    temperature_time = now - datetime.timedelta(seconds=TEMPERATURE_REFRESH_TIME)
    temperature_mqtt_last_published = 0
    hass.get_status(io_status)
    dash.idle_update(True, INACTIVE_DISPLAY_SECS)
    dash.content_update(io_status)
    while True:
        try:
            for loop in range(10):
                now = datetime.datetime.now()
                command = rotary.scan()
                if config.TEST_MODE and command is None:
                    command = keyreader.scan()
                if command is not None:
                    inactive_time = now
                    dash.idle_update(True, INACTIVE_DISPLAY_SECS)
                    if dash.is_active and dash.menu_action(io_status, command):
                        # early refresh (state, lcd)
                        lcd_refresh_time = state_refresh_time = \
                                now - datetime.timedelta(seconds=STATE_REFRESH_TIME_ACTIVE - 1)
                        break
                time.sleep(.01)

            # inactive time reached -> back to default view
            if (now - inactive_time).total_seconds() >= INACTIVE_MENU_SECS:
                dash.default_view(io_status)
            # periodic refresh (longer if inactive)
            refresh_timeout = STATE_REFRESH_TIME_ACTIVE if dash.is_active else STATE_REFRESH_TIME_INACTIVE
            if (now - state_refresh_time).total_seconds() >= refresh_timeout and not io_status.ui_changing:
                hass.get_status(io_status)
                state_refresh_time = now
            # content refresh
            if (now - content_refresh_time).total_seconds() >= CONTENT_REFRESH_TIME:
                dash.content_update(io_status)
                content_refresh_time = now
            # lcd refresh
            if (now - lcd_refresh_time).total_seconds() >= LCD_REFRESH_TIME:
                dash.update()
                lcd_refresh_time = now
            # temperature refresh
            if (now - temperature_time).total_seconds() >= TEMPERATURE_REFRESH_TIME:
                temp = sensor.read_temp()
                if temp:
                    io_status.int_temp_c = temp * config.TEMP_CORRECTION
                    if abs(temperature_mqtt_last_published -
                           io_status.int_temp_c) >= TEMPERATURE_MQTT_PUBLISH_THRESHOLD:
                        # temperature change: update
                        temperature_mqtt_time = now - datetime.timedelta(seconds=TEMPERATURE_MQTT_PUBLISH_TIME)
                temperature_time = now
            # mqtt refresh
            if (now - temperature_mqtt_time).total_seconds() >= TEMPERATURE_MQTT_PUBLISH_TIME:
                if io_status.int_temp_c:
                    mqtt.publish()
                    temperature_mqtt_last_published = io_status.int_temp_c
                    temperature_mqtt_time = now
                else:
                    temperature_mqtt_time += datetime.timedelta(seconds=TEMPERATURE_REFRESH_TIME)
        except (KeyboardInterrupt, SystemExit):
            # cleanup
            dash.cleanup()
            rotary.cleanup()
            sensor.cleanup()
            mqtt.cleanup()
            raise
        except Exception:
            log_stderr(traceback.format_exc())
