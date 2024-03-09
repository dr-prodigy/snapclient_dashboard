#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime

import config

hide_message_time = None


class Input:
    def __init__(self):
        self.last_update = datetime.datetime.now().isoformat()


class Status:
    def __init__(self):
        global hide_message_time
        # general
        self.last_update = datetime.datetime.now().isoformat()
        self.last_change = datetime.datetime.now().isoformat()
        # gui
        self.message = ''
        self.volume = 50
        self.is_muted = False
        hide_message_time = datetime.datetime.now()

        self.sources = ['Media', 'Spotify']
        self.current_source = 0

    def get_output(self):
        return json.dumps(self.__dict__, indent=0)

    def update(self, current_time):
        if self.message != '' and hide_message_time <= current_time:
            self.message = ''
            self.last_change == current_time.isoformat()

    def send_message(self, message):
        global hide_message_time

        self.message = message.encode('utf-8')
        self.last_change = datetime.datetime.now().isoformat()
        hide_message_time = datetime.datetime.now() + datetime.timedelta(seconds=40)

    def reset_message(self):
        global hide_message_time

        self.message = ''
        self.last_change = datetime.datetime.now().isoformat()
        hide_message_time = datetime.datetime.now()