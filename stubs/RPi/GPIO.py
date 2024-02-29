# -*- coding: utf-8 -*-
import config

DEBUG_LOG = config.VERBOSE_LOG

# stubs
BOARD = 1
OUT = 'OUT'
IN = 'IN'
HIGH = 'HIGH'
LOW = 'LOW'
BCM = 'BCM'

PUD_NONE = 0
PUD_DOWN = 1
PUD_UP = 2

def setmode(a):
    if DEBUG_LOG:
        print('GPIO.setmode {}'.format(a))


def setup(a, b, pull_up_down=PUD_NONE):
    if DEBUG_LOG:
        print('GPIO.setup {},{},{}'.format(a, b, pull_up_down))

def input(a):
    if DEBUG_LOG:
        print('GPIO.input {}'.format(a))

def output(a, b):
    if DEBUG_LOG:
        print('GPIO.output {},{}'.format(a, b))


def cleanup():
    if DEBUG_LOG:
        print('GPIO.cleanup')


def setwarnings(flag):
    if DEBUG_LOG:
        print('GPIO.setwarnings {}'.format(flag))


class PWM():
    def __init__(self, a, b):
        if DEBUG_LOG:
            print('__GPIO.PWM__ {}'.format(a, b))

    def start(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.start {}'.format(a))

    def ChangeFrequency(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.ChangeFrequency {}'.format(a))

    def ChangeDutyCycle(self, a):
        if DEBUG_LOG:
            print('GPIO.PWM.ChangeDutyCycle {}'.format(a))
