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
        GPIO.setup(ROTARY_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        counter = 0
        self.clkLastState = GPIO.input(ROTARY_CLK)
        self.buttonLastState = GPIO.input(ROTARY_SW)

    def scan(self, io_status):
        clkState = GPIO.input(ROTARY_DT)
        dtState = GPIO.input(ROTARY_CLK)
        if clkState != self.clkLastState:
            if dtState == clkState:
                io_status.volume += 2 if io_status.volume < 100 else 0
            else:
                io_status.volume -= 2 if io_status.volume > 0 else 0
        self.clkLastState = clkState

        buttonState = GPIO.input(ROTARY_SW)
        if buttonState != self.buttonLastState:
            if buttonState == GPIO.LOW:
                io_status.is_muted = not io_status.is_muted
            self.buttonLastState = buttonState

    def cleanup(self):
        GPIO.cleanup()
