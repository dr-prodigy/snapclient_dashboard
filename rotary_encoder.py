from time import sleep

import config

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
        GPIO.setup(ROTARY_SW, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

        counter = 0
        self.clkLastState = GPIO.input(ROTARY_CLK)

    def scan(self, io_status):
        clkState = GPIO.input(ROTARY_DT)
        dtState = GPIO.input(ROTARY_CLK)
        if clkState != self.clkLastState:
            if dtState != clkState:
                io_status.volume += 5 if io_status.volume < 100 else 0
            else:
                io_status.volume -= 5 if io_status.volume > 0 else 0
        self.clkLastState = clkState

    def cleanup(self):
        GPIO.cleanup()
