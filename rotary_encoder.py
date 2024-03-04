from time import sleep
import keyboard

import config

try:
    import RPi.GPIO as GPIO
except ImportError:
    print('WARN: RPi.GPIO missing - loading stub library')
    import stubs.RPi.GPIO as GPIO

ROTARY_DT = config.GPIO_ROTARY[0]
ROTARY_CLK = config.GPIO_ROTARY[1]
ROTARY_SW = config.GPIO_ROTARY[2]

LEFT = 0
RIGHT = 1
BUTTON = 2

class Rotary:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ROTARY_CLK, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(ROTARY_DT, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(ROTARY_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        counter = 0
        self.clk_last_state = GPIO.input(ROTARY_CLK)
        self.button_last_state = GPIO.input(ROTARY_SW)

    def scan(self):
        clk_state = GPIO.input(ROTARY_DT)
        dt_state = GPIO.input(ROTARY_CLK)
        if clk_state != self.clk_last_state and clk_state == GPIO.HIGH:
            self.clk_last_state = clk_state
            if dt_state == GPIO.HIGH:
                return RIGHT
            else:
                return LEFT

        button_state = GPIO.input(ROTARY_SW)
        if button_state != self.button_last_state:
            self.button_last_state = button_state
            if button_state == GPIO.LOW:
                return BUTTON

        if keyboard.is_pressed("a"):
            return LEFT
        if keyboard.is_pressed("d"):
            return RIGHT
        if keyboard.is_pressed(" "):
            return BUTTON
        return None

    def cleanup(self):
        GPIO.cleanup()
