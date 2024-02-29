#!/usr/bin/env python
import os
import sys
import datetime


def log_stderr(data):
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write('{} - {}\n'.format(cur_date, data))


def os_async_command(command):
    os.popen(command)