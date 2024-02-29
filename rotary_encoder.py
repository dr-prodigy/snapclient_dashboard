from RPi import GPIO
from time import sleep

import config

dt = 9
clk = 10
sw = 11

GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

counter = 0
clkLastState = GPIO.input(clk)

try:
    while True:
        clkState = GPIO.input(config.GPIO_ROTARY[0])
        dtState = GPIO.input(config.GPIO_ROTARY[1])
        if clkState != clkLastState:
            if dtState != clkState:
                counter += 1
            else:
                counter -= 1
        print(counter)
        clkLastState = clkState
        sleep(0.01)
finally:
    GPIO.cleanup()
