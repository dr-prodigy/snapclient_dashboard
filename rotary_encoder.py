import config
import datetime
from utils import LEFT, RIGHT, BUTTON

try:
    import RPi.GPIO as GPIO
except:
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
        self.clk_last_state = GPIO.input(ROTARY_CLK)
        self.button_last_state = GPIO.input(ROTARY_SW)
        self.last_change = datetime.datetime.now()

    def scan(self):
        command = None
        clk_state = GPIO.input(ROTARY_DT)
        dt_state = GPIO.input(ROTARY_CLK)
        button_state = GPIO.input(ROTARY_SW)
        now = datetime.datetime.now()
        if (button_state != self.button_last_state and
                (now - self.last_change).total_seconds() > .05):
            self.button_last_state = button_state
            self.last_change = now
            if button_state == GPIO.LOW:
                command = BUTTON
        elif clk_state == GPIO.HIGH and self.clk_last_state == GPIO.LOW:
            command = RIGHT if dt_state == GPIO.HIGH else LEFT

        self.clk_last_state = clk_state
        return command

    @staticmethod
    def cleanup():
        GPIO.cleanup()
