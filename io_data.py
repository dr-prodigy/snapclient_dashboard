#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime

import config

class Input:
    def __init__(self):
        self.last_update = datetime.datetime.now().isoformat()


class Status:
    def __init__(self):
        # general
        self.last_update = datetime.datetime.now().isoformat()
        self.last_change = datetime.datetime.now().isoformat()
        self.hide_message_time = datetime.datetime.now()
        # gui
        self.message = ''
        self.state = ''
        self.volume_level = .5
        self.is_volume_muted = False
        self.is_playing = False
        self.friendly_name = 'Snapcast'
        self.sources = ['Media', 'Spotify']
        self.source = 'Media'
        self.ui_changing = False

    def get_output(self):
        return json.dumps(self.__dict__, indent=0)

    def update(self, current_time):
        if self.message != '' and self.hide_message_time <= current_time:
            self.message = ''
            self.last_change == current_time.isoformat()

    def send_message(self, message):
        self.message = message.encode('utf-8')
        self.last_change = datetime.datetime.now().isoformat()
        self.hide_message_time = datetime.datetime.now() + datetime.timedelta(seconds=40)

    def reset_message(self):
        self.message = ''
        self.last_change = datetime.datetime.now().isoformat()
        self.hide_message_time = datetime.datetime.now()