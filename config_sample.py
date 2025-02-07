#!/usr/bin/env python

# **** Copy me to config.py and modify me as needed ****

from utils import LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR

I2C_BUS = 1  # i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2C_ADDRESS = 0x27
LCD_COLUMNS = 16
LCD_ROWS = 2

MODULE_TEMP = True
TEMP_CORRECTION = 1.036

# LCD modes : NONE = 0, GPIO_CharLCD = 1, I2C = 2
MODULE_LCD = 1
# LCD GPIO [RS, EN, D4, D5, D6, D7, BL] - Backlight is optional
GPIO_LCD = [4, 17, 22, 23, 24, 25, 12]

MODULE_MQTT = True
MQTT_BROKER = 'localhost'
MQTT_PORT = 1883
MQTT_TOPIC = 'zigbee2mqtt/Temp_S'

# DISPLAY_AUTO_DIM: dim display when timeout expires
DISPLAY_AUTO_DIM = False
# DISPLAY_PWM_BACKLIGHT: use PWM to set backlight
DISPLAY_PWM_BACKLIGHT = True
# DISPLAY_[ON|DIM]_BACKLIGHT: backlight levels (on, dimmed)
DISPLAY_ON_BACKLIGHT = 1.0
DISPLAY_DIM_BACKLIGHT = 0.1

# Rotary encoder GPIO [DT, CLK, SW]
GPIO_ROTARY = [9, 10, 11]

HASS_SERVER = 'https://myserver/'
HASS_TOKEN = 'mykey'
HASS_CHECK_SSL_CERT = False
HASS_PLAYER_ENTITY_ID = 'media_player.my_player'

# DEBUGGING
TEST_MODE = False
LOG_LEVEL = LOG_DEBUG
LOG_MUTE_MODULES = []
LOG_GPIO = False

# VARIOUS SETTINGS
