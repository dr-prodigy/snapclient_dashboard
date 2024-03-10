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

from requests import get
from utils import log_stderr
from datetime import datetime, timedelta

if not config.HASS_CHECK_SSL_CERT:
    urllib3.disable_warnings()

next_publish = datetime.now()

STATUS_ENTITY_API_URL = "api/states/"

def get_state(io_status):
    global next_publish

    try:
        url = config.HASS_SERVER + STATUS_ENTITY_API_URL + config.HASS_PLAYER_ENTITY_ID
        headers = {"Authorization": "Bearer " + config.HASS_TOKEN, "content-type": "application/json"}

        if datetime.now() >= next_publish:
            response = get(url, headers=headers, verify=config.HASS_CHECK_SSL_CERT)
            if config.DEBUG_LOG:
                print('*HASS* GET_STATE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, response.text))
            json = response.json()
            io_status.friendly_name = json['attributes']['friendly_name']
            io_status.volume_level = json['attributes']['volume_level']
            io_status.sources = json['attributes']['source_list']
            io_status.source = json['attributes']['source']
            io_status.is_volume_muted = json['attributes']['is_volume_muted']
    except Exception as e:
        log_stderr('*HASS* ERR: GET_STATE ({}): {}'.format(config.HASS_PLAYER_ENTITY_ID, e))
        # exit and delay next publish for 60 secs
        next_publish = datetime.now() + timedelta(seconds=60)
