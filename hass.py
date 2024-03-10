#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
# Copyright (C)2018-24 Maurizio Montel (dr-prodigy) <maurizio.montel@gmail.com>
# This file is part of hompi <https://github.com/dr-prodigy/hompi>.
#
# hompi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hompi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hompi.  If not, see <http://www.gnu.org/licenses/>.

import config
import traceback
import urllib3

from enum import Enum
from requests import get, post
from utils import log_stderr
from datetime import datetime, timedelta

if not config.HASS_CHECK_SSL_CERT:
    urllib3.disable_warnings()

headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}
next_publish = datetime.now()

STATE_API_URL = "api/states/"

SERVICE_API_URL = "api/services/media_player/"
SERVICE_API_VOLUME_SET = SERVICE_API_URL + "volume_set"
SERVICE_API_VOLUME_MUTE = SERVICE_API_URL + "volume_mute"
SERVICE_API_PLAY = SERVICE_API_URL + "media_play"
SERVICE_API_STOP = SERVICE_API_URL + "media_stop"
SERVICE_API_SELECT_SOURCE = SERVICE_API_URL + "select_source"

class Service(Enum):
    VOLUME_SET = 0
    VOLUME_MUTE = 1
    PLAY = 2
    STOP = 3
    SELECT_SOURCE = 4

def get_state(io_status):
    global next_publish
    try:
        url = config.HASS_SERVER + STATE_API_URL + config.HASS_PLAYER_ENTITY_ID

        if datetime.now() >= next_publish:
            response = get(url, headers=headers, verify=config.HASS_CHECK_SSL_CERT)
            if config.DEBUG_LOG:
                print('*HASS* GET_STATE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, response.text))
            json = response.json()
            io_status.friendly_name = json['attributes']['friendly_name']
            io_status.state = json['state'].capitalize()
            io_status.volume_level = json['attributes']['volume_level']
            io_status.sources = json['attributes']['source_list']
            io_status.source = json['attributes']['source']
            io_status.is_volume_muted = json['attributes']['is_volume_muted']
    except Exception as e:
        log_stderr('*HASS* ERR: GET_STATE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, e))
        # exit and delay next publish for 60 secs
        next_publish = datetime.now() + timedelta(seconds=60)

def set_service(io_status, service):
    global next_publish
    try:
        json = {"entity_id": config.HASS_PLAYER_ENTITY_ID}
        if service == Service.VOLUME_MUTE:
            url = config.HASS_SERVER + SERVICE_API_VOLUME_MUTE
            json.update({"is_volume_muted": io_status.is_volume_muted})
        elif service == Service.VOLUME_SET:
            url = config.HASS_SERVER + SERVICE_API_VOLUME_SET
            json.update({"volume_level": io_status.volume_level})
        elif service == Service.SELECT_SOURCE:
            url = config.HASS_SERVER + SERVICE_API_SELECT_SOURCE
            json.update({"source": io_status.source})
        if datetime.now() >= next_publish:
            response = post(url, headers=headers, verify=config.HASS_CHECK_SSL_CERT, json = json)
    except Exception as e:
        log_stderr('*HASS* ERR: SET_MUTE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, e))
        # exit and delay next publish for 60 secs
        next_publish = datetime.now() + timedelta(seconds=60)
