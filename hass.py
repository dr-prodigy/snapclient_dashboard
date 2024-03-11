#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import config
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
SERVICE_API_PAUSE = SERVICE_API_URL + "media_pause"
SERVICE_API_STOP = SERVICE_API_URL + "media_stop"
SERVICE_API_SELECT_SOURCE = SERVICE_API_URL + "select_source"

class Service(Enum):
    VOLUME_SET = 0
    VOLUME_MUTE = 1
    PLAY = 2
    PAUSE = 3
    STOP = 4
    SELECT_SOURCE = 5

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
            io_status.state = json['state']
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
        elif service == Service.PLAY:
            url = config.HASS_SERVER + SERVICE_API_PLAY
        elif service == Service.PAUSE:
            url = config.HASS_SERVER + SERVICE_API_PAUSE
        elif service == Service.STOP:
            url = config.HASS_SERVER + SERVICE_API_STOP
        if datetime.now() >= next_publish:
            response = post(url, headers=headers, verify=config.HASS_CHECK_SSL_CERT, json=json)
    except Exception as e:
        log_stderr('*HASS* ERR: SET_MUTE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, e))
        # exit and delay next publish for 60 secs
        next_publish = datetime.now() + timedelta(seconds=60)
