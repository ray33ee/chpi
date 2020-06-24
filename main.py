
from chfsm import CHFSM
from time import sleep

import logging

# varsious Pi and circuit-specific constants
RGB_ACTIVE_HIGH = False
CH_RELAY_ACTIVE_HIGH = False
HW_RELAY_ACTIVE_HIGH = False

RED_LED_PIN = "J8:32"
GREN_LED_PIN = "J8:35"
BLUE_LED_PIN = "J8:33"

HW_RELAY_PIN = "J8:8"
CH_RELAY_PIN = "J8:10"

HW_SWITCH_PIN = "J8:36"
CH_SWITCH_PIN = "J8:38"

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y-%m-%d %a %H:%M:%S")

logging.info("Application started")

try:
    fsm = CHFSM(RED_LED_PIN, GREN_LED_PIN, BLUE_LED_PIN, HW_RELAY_PIN, CH_RELAY_PIN, HW_SWITCH_PIN, CH_SWITCH_PIN, RGB_ACTIVE_HIGH, CH_RELAY_ACTIVE_HIGH, HW_RELAY_ACTIVE_HIGH)
    while 1:
        fsm.process()
        sleep(0.1)
except Exception as e:
    logging.exception("Unhandled exception - '%s'", str(e))
    # We should shutdown to prevent issues




