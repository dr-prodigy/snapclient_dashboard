from time import sleep

import config
from utils import LEFT, RIGHT, BUTTON

try:
    import RPi.GPIO as GPIO
except ImportError:
    print('WARN: RPi.GPIO missing - loading stub library')
    import stubs.RPi.GPIO as GPIO

ROTARY_DT = config.GPIO_ROTARY[0]
ROTARY_CLK = config.GPIO_ROTARY[1]
ROTARY_SW = config.GPIO_ROTARY[2]

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
        command = None
        clk_state = GPIO.input(ROTARY_DT)
        dt_state = GPIO.input(ROTARY_CLK)
        button_state = GPIO.input(ROTARY_SW)
        if clk_state != self.clk_last_state and clk_state == GPIO.HIGH:
            if dt_state == GPIO.HIGH:
                command = RIGHT
            else:
                command = LEFT
        if button_state != self.button_last_state:
            self.button_last_state = button_state
            if button_state == GPIO.LOW:
                command = BUTTON
        sleep(0.01)
        self.clk_last_state = clk_state
        return command

    def cleanup(self):
        GPIO.cleanup()
