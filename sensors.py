#!/usr/bin/env python
# -*- coding: utf-8 -*-

import glob
import codecs
import time
import config

reader = codecs.getreader("utf-8")

class Sensors:
    device_file = ''

    def __init__(self):
        # DS18B20 thermometer: initialize device file
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
        if device_folders:
            self.device_file = device_folders[0] + '/w1_slave'
        else:
            self.device_file = None

    # temperature sensor
    def _read_temp_raw(self):
        if self.device_file:
            try:
                f = open(self.device_file, 'r')
                lines = f.readlines()
                f.close()
                return lines
            except Exception:
                # in case of a temp sensor issue, return None
                return None
        else:
            return None

    def read_temp(self):
        lines = self._read_temp_raw()
        if lines:
            retries = 0
            while (not lines or lines[0].strip()[-3:] != 'YES') \
                    and retries < 5:
                time.sleep(0.2)
                lines = self._read_temp_raw()
                retries += 1
            if lines and len(lines) > 1:
                equals_pos = lines[1].find('t=')
                if equals_pos != -1:
                    temp_string = lines[1][equals_pos + 2:]
                    temp_c = float(temp_string) / 1000.0
                    return temp_c * config.TEMP_CORRECTION
        return None

    def cleanup(self):
        pass