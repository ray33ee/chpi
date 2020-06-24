from gpiozero import RGBLED, Button, DigitalOutputDevice

from datetime import datetime
import logging

import json

class CHFSM:
    
    IDLE_COLOUR = (1.0, 1.0, 1.0) # White
    CH_ONLY_COLOUR = (0, 0.9, 0.4) # Reddy-purple
    HW_ONLY_COLOUR = (0.9, 0.0, 0.1) # Greeny-cyan
    CH_AND_HW_COLOUR = (0.9, 0.1, 0.0) # Orange
    NO_WIFI_CONNECTION = ()
    BLUETOOTH_MODE = ()
    # INHIBIT_MODE = ()
    
    PULSE_UP_TIME = 1.5
    PULSE_DOWN_TIME = 1.5
    
    BUTTON_BOUNCE_TIME = None
    
    # The duration of a CH or HW boost, in seconds
    BOOST_DURATION = 10
    
    def __init__(self, red, green, blue, hw_relay, ch_relay, hw_button, ch_button, rgb_active_high, ch_relay_active_high, hw_relay_active_high):
        
        # Setup push buttons
        self.ch_button = Button(ch_button, bounce_time=self.BUTTON_BOUNCE_TIME)
        self.hw_button = Button(hw_button, bounce_time=self.BUTTON_BOUNCE_TIME)

        # Setup relay
        self.hw_relay = DigitalOutputDevice(hw_relay, hw_relay_active_high)
        self.ch_relay = DigitalOutputDevice(ch_relay, ch_relay_active_high)

        # Setup RGB status LED
        self.status_led = RGBLED(red, green, blue, active_high=rgb_active_high)
        
        # Connect button press events 
        self.ch_button.when_pressed = self.chPressed
        self.hw_button.when_pressed = self.hwPressed
        
        # Setup CH and HW boost objects
        self.ch_boost_start = None
        self.hw_boost_start = None
        
        self.hw_pressed_flag = False
        self.ch_pressed_flag = False
        
        # Load first state
        self.state = IdleState(self)
        self.state.enter()

        
    
    def setState(self, state):
        self.state.leave()
        self.state = state
        self.state.enter()
        
    def process(self):
        self.state.process()
    
    def getState(self):
        return self.state
    
    def chPressed(self):
        logging.debug("CH button press")
        self.ch_pressed_flag = True
    
    def hwPressed(self):
        logging.debug("HW button press")
        self.hw_pressed_flag = True
        
    def setStatusLed(self, colour):
        self.status_led.pulse(CHFSM.PULSE_UP_TIME, CHFSM.PULSE_DOWN_TIME, on_color=colour)
        
    
class State:
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    
    def process(self):
        print(".", end='')
        
        nextState = IdleState(self)
        
        # We use stateCode to determine which relays should be set, then use this to change state (if needed)
        stateCode = 0
        
        # Check to see if either buttons have been pressed
        if self.fsm.ch_pressed_flag:
            if not self.fsm.ch_boost_start: # IF there is no timer set, set one
                logging.info("CH boost started (%f minutes)", self.fsm.BOOST_DURATION)
                stateCode |= 1
                self.fsm.ch_boost_start = datetime.now()
            else: # If a timer is already set, cancel it
                logging.info("CH boost cancelled")
                self.fsm.ch_boost_start = None
            self.fsm.ch_pressed_flag = False
         
        if self.fsm.hw_pressed_flag:
            if not self.fsm.hw_boost_start:
                logging.info("HW boost started (%f minutes)", self.fsm.BOOST_DURATION)
                stateCode |= 2
                self.fsm.hw_boost_start = datetime.now()
            else:
                logging.info("HW boost cancelled")
                self.fsm.hw_boost_start = None
            self.fsm.hw_pressed_flag = False
        
        # If we are within the boost time, update stateCode accordingly
        if self.fsm.ch_boost_start: # If a start time is set
            diff = datetime.now() - self.fsm.ch_boost_start
            if diff.seconds < self.fsm.BOOST_DURATION: # If we are within the boost time
                stateCode |= 1
            else:
                logging.info("CH boost expired")
                self.fsm.ch_boost_start = None
        
        if self.fsm.hw_boost_start:
            diff = datetime.now() - self.fsm.hw_boost_start
            if diff.seconds < self.fsm.BOOST_DURATION:
                stateCode |= 2 
            else:
                logging.info("HW boost expired")
                self.fsm.hw_boost_start = None
            
        
        # Check to see if the CH or HW is on in the schedule
        current_time = datetime.now()
        
        index = (current_time.weekday() * 24 + current_time.hour) * 60 + current_time.minute
        
        fh = open("schedule", "rb")
        
        fh.seek(index)
        
        entry = int.from_bytes(fh.read(1), byteorder='little')
        
        fh.close()
        
        CHHW = entry & 3
        
        stateCode |= CHHW
        
        
            
        
        # Check command file to see if either CH or HW commands are present
        fh = open("commands", "r+")
        
        commands = fh.read()
        
        if len(commands):
            data = json.loads(commands)
            
            print(json.dumps(commands, indent=4))
            
            fh.close()
        
            fh = open("commands", "w")
            
            logging.info("Commands received %s", commands)
            
        fh.close()
        
        # Translate state code into an FSM state
        if stateCode == 0:
            nextState = IdleState(self.fsm)
        elif stateCode == 1:
            nextState = CHState(self.fsm)
        elif stateCode == 2:
            nextState = HWState(self.fsm)
        elif stateCode == 3:
            nextState = BothState(self.fsm)
        
        # Only set state if it has changed
        if type(nextState) != type(self.fsm.getState()):
            self.fsm.setState(nextState)
            
            if CHHW == 1:
                logging.info("CH schedule on")
            elif CHHW == 2:
                logging.info("HW schedule on")
            elif CHHW == 3:
                logging.info("CH and HW schedule on")
        
    
    def leave(self):
        print("State Leave")
        
    
class IdleState(State):
    
    def __init__(self, fsm):
        self.fsm = fsm
    
    def enter(self):
        logging.debug("Idle Enter")
        
        # Turn both relays off
        self.fsm.hw_relay.off()
        self.fsm.ch_relay.off()
        
        # Change status led to inditate idle
        self.fsm.setStatusLed(CHFSM.IDLE_COLOUR)
        
    
class CHState(State):
    
    def __init__(self, fsm):
        self.fsm = fsm
    
    def enter(self):
        logging.debug("CH Enter")
        
        # Turn CH relay on and HW relay off
        self.fsm.hw_relay.off()
        self.fsm.ch_relay.on()
        
        # Change status led to inditate CH on 
        self.fsm.setStatusLed(CHFSM.CH_ONLY_COLOUR)
        
    
class HWState(State):
    
    def __init__(self, fsm):
        self.fsm = fsm
        pass
    
    def enter(self):
        logging.debug("HW Enter")
        
        # Turn both CH off and HW relay on
        self.fsm.hw_relay.on()
        self.fsm.ch_relay.off()
        
        # Change status led to inditate HW on
        self.fsm.setStatusLed(CHFSM.HW_ONLY_COLOUR)
        
    
class BothState(State):
    
    def __init__(self, fsm):
        self.fsm = fsm
    
    def enter(self):
        logging.debug("HW and CH Enter")
        
        # Turn both relays on
        self.fsm.hw_relay.on()
        self.fsm.ch_relay.on()
        
        # Change status led to inditate HW and CH are on
        self.fsm.setStatusLed(CHFSM.CH_AND_HW_COLOUR)
    
    