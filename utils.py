#!/usr/bin/env python
import os
import sys
import datetime

import os
import sys
import datetime
import config

LOG_GPIO = 0
LOG_DEBUG = 1
LOG_INFO = 2
LOG_WARN = 3
LOG_ERROR = 4

LEFT = 0
RIGHT = 1
BUTTON = 2

def log_stdout(module, data, log_level=LOG_DEBUG):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if log_level >= config.LOG_LEVEL and module not in config.LOG_MUTE_MODULES or \
        log_level > config.LOG_INFO:
        sys.stdout.write("{} - *{}* - {}\n".format(cur_date, module, data))

def log_stderr(data):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write('{} - {}\n'.format(cur_date, data))

def os_async_command(command):
    os.popen(command)
