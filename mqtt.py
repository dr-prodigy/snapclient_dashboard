#!/usr/bin/env python
# -*- coding: utf-8 -*-

import config
import re
import time

from datetime import datetime, timedelta
from utils import LOG_INFO, log_stdout, log_stderr, LOG_DEBUG, LOG_WARN
from paho.mqtt import client as mqtt_client
from paho.mqtt.enums import CallbackAPIVersion

CONNECT_TIMEOUT_SECS = 5
RETRY_MINUTES = 2
publish_time = datetime.now()

class MQTT:
    def __init__(self, io_status):
        self.__connected = False
        self.__io_status = io_status
        self.__client = None

    def __connect(self):
        global publish_time
        # lazy MQTT server connection
        if not self.__client or not self.__connected:
            try:
                self.__client = self.__connect_mqtt()
            except Exception as e:
                log_stderr('*MQTT* - Failed to connect: {} -> delaying {} mins'.format(e, RETRY_MINUTES))
                publish_time = datetime.now() + timedelta(minutes=RETRY_MINUTES)
        return self.__connected

    def __connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc, properties):
            if flags.session_present:
                pass
            if rc == 0:
                log_stdout('MQTT', 'Connected to broker {}:{}'
                           .format(config.MQTT_BROKER, config.MQTT_PORT), LOG_INFO)
                self.__connected = True
            else:
                log_stderr('*MQTT* - Failed to connect to broker {}:{}: {}'.
                           format(config.MQTT_BROKER, config.MQTT_PORT, rc))

        def on_disconnect(client, userdata, flags, rc, properties):
            if rc == 0:
                # successful disconnect
                log_stdout('MQTT', 'Disconnected: ok', LOG_INFO)
            else:
                # error processing
                log_stderr('*MQTT* - Failed to disconnect: {}'.format(rc))
            self.__connected = False

        self.__connected = False
        _client = mqtt_client.Client(CallbackAPIVersion.VERSION2)
        # client.username_pw_set(username, password)
        _client.on_connect = on_connect
        _client.on_disconnect = on_disconnect
        _client.connect(config.MQTT_BROKER, config.MQTT_PORT)
        _client.loop_start()

        start_time = datetime.now()
        while not self.__connected and \
            (datetime.now() - start_time).total_seconds() < CONNECT_TIMEOUT_SECS:
            time.sleep(.1)

        if config.LOG_LEVEL == LOG_DEBUG:
            _client.subscribe("$SYS/broker/log/#")
        return _client

    def publish(self):
        self.__connect()

        topic = '{}'.format(config.MQTT_TOPIC)
        payload = ("{" + "\"temperature\": {:04.1f}".format(self.__io_status.int_temp_c) + "}")
        if self.__connected:
            self.__client.publish(topic, payload)
            log_stdout('MQTT', 'Topic: {} - Publish: {}'.format(config.MQTT_TOPIC, payload), LOG_INFO)
        else:
            log_stdout('MQTT', 'Not connected - Publish SKIPPED {} -> ({})'.
                        format(payload, topic), LOG_WARN)

    def cleanup(self):
        log_stdout('MQTT', 'Cleanup', LOG_INFO)
        if self.__client:
            self.__client.loop_stop()
            self.__client.disconnect()
