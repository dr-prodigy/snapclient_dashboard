#!/usr/bin/env python

# LCD modes : NONE = 0, GPIO_CharLCD = 1, I2C = 2
MODULE_LCD = 1
I2C_BUS = 1  # i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2C_ADDRESS = 0x27
LCD_COLUMNS = 16
LCD_ROWS = 2

# LCD GPIO [RS, EN, D4, D5, D6, D7]
GPIO_LCD = [4, 17, 22, 23, 24, 25]

# Rotary encoder GPIO
GPIO_ROTARY = [9, 10, 11]

HASS_SERVER = 'https://myserver/'
HASS_TOKEN = 'mykey'
HASS_CHECK_SSL_CERT = False
HASS_PLAYER_ENTITY_ID = 'media_player.my_player'

# DEBUGGING
TEST_MODE = True
DEBUG_LOG = True
VERBOSE_LOG = False

# VARIOUS SETTINGS