from gpiozero import RGBLED, DigitalOutputDevice

from chfsm import CHFSM
from time import sleep

import logging

from datetime import datetime

from diagprint import DiagPrint

from gateway import Gateway

import os

######## MUST BE STARTED WITH SUDO

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

# Time, in seconds, between diag print calls
DIAG_PRINT_DELAY = 5 * 60

# Time, in seconds, between infinite loop ticks
TICK_DURATION = 0.1

log_filename = os.path.join(os.path.join(CHFSM.parent_folder(), "logs"), datetime.now().strftime("%Y-%m") + ".log")

logging.basicConfig(filename=log_filename, level=logging.DEBUG, format="%(asctime)s [%(levelname)s]: %(message)s", datefmt="%Y-%m-%d %a %H:%M:%S")

logging.info("Application started")

fsm = CHFSM(RED_LED_PIN, GREN_LED_PIN, BLUE_LED_PIN, HW_RELAY_PIN, CH_RELAY_PIN, HW_SWITCH_PIN, CH_SWITCH_PIN, RGB_ACTIVE_HIGH, CH_RELAY_ACTIVE_HIGH, HW_RELAY_ACTIVE_HIGH)

try:
    
    diag = DiagPrint(DIAG_PRINT_DELAY) # Setup DiagPrint to print diagnostics to log file every 5 minutes
    
    
    while 1:
        
        current_time = datetime.now()
        
        fsm.process()
        
        diag.process()
        
        if current_time.day == 1 and current_time.hour == 0 and current_time.minute == 0 and current_time.second == 0:
            # At the very first day of the month we update, reboot, and (as a result of the reboot) start a new log file. (though not necessarily in that order)
            
            logging.info("Updating pi...")
            os.system("sudo apt update -y")
            
            logging.info("Upgrading pi...")
            os.system("sudo apt full-upgrade -y")
            
            logging.info("Rebooting pi...")
            os.system("sudo shutdown -r now")
        
        sleep(TICK_DURATION)
        
        
        
except Exception as e:
    logging.exception("Unhandled exception - '%s'", str(e))
    
    # Close all previous GPIO devices
    fsm.close()
    
    # Turn relays off
    hw = DigitalOutputDevice(HW_RELAY_PIN, HW_RELAY_ACTIVE_HIGH)
    ch = DigitalOutputDevice(CH_RELAY_PIN, CH_RELAY_ACTIVE_HIGH)
    
    hw.off()
    ch.off()
    
    # Put RGB LED on pulsing red
    rgb_led = RGBLED(RED_LED_PIN, GREN_LED_PIN, BLUE_LED_PIN, active_high=RGB_ACTIVE_HIGH)
    
    rgb_led.pulse(1.5, 1.5, on_color=(1, 0,0))
    




