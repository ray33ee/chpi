from gpiozero import RGBLED, Button, DigitalOutputDevice

from better import BetterButton

from datetime import datetime

from diagprint import DiagPrint

from gateway import Gateway

import logging

import json

import os

# Get properties from config file
with open( os.path.join(os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts"), "config"), "r") as fp:
    config = json.load(fp)

class CHFSM:
    
    # Normal operation
    IDLE_COLOUR = (1.5, 1.5, (0,0,0), (1.0, 1.0, 1.0)) # off to White
    CH_ONLY_COLOUR = (1.5, 1.5, (0,0,0), (0, 0.9, 0.4)) # off to Reddy-purple
    HW_ONLY_COLOUR = (1.5, 1.5, (0,0,0), (0.9, 0.0, 0.1)) # off to Greeny-cyan
    CH_AND_HW_COLOUR = (1.5, 1.5, (0,0,0), (0.9, 0.1, 0.0)) # off to Orange
    # INHIBIT_MODE = (1.5, 1.5, (0,0,0), (1, 0, 0.5))  # Off to purple
    
    # Errors
    NO_GATEWAY_CONNECTION = (1.5, 1.5, (1,0,0), (0.9, 0, 0.9)) # Red to purple
    SCHEDULE_MISSING = (1.5, 1.5, (1,0,0), (1, 0.3, 0.0)) # red to yellow/orange
    BAD_SCHEDULE = (1.5, 1.5, (1,0,0), (1, 1, 0)) # red to cyan
    
    # Maintainance mode
    BLUETOOTH_MODE = (1.5, 1.5, (0,0,1), (0, 1, 1)) # blue to cyan
    UPDATING = (1.5, 1.5, (0, 0, 1), (0, 1, 0)) #blue to Green
    
    update_time = config[r"update_time"]
    
    # Update and reboot time (day_of_month, hour, minute, second)
    UPDATE_REBOOT_TIME = (update_time["day_of_month"], update_time["hour"], update_time["minute"], update_time["second"])
    
    PULSE_UP_TIME = 1.5
    PULSE_DOWN_TIME = 1.5
    
    BUTTON_BOUNCE_TIME = None
    
    # The duration of a CH or HW boost, in seconds
    BOOST_DURATION = config["boost_duration"]
    
    def __init__(self, red, green, blue, hw_relay, ch_relay, hw_button, ch_button, rgb_active_high, ch_relay_active_high, hw_relay_active_high):
        
        
        
        # Setup push buttons
        self.ch_button = BetterButton(ch_button, self.chPressed, self.BUTTON_BOUNCE_TIME, None, True)
        self.hw_button = BetterButton(hw_button, self.hwPressed, self.BUTTON_BOUNCE_TIME, None, True)

        # Setup relay
        self.hw_relay = DigitalOutputDevice(hw_relay, hw_relay_active_high)
        self.ch_relay = DigitalOutputDevice(ch_relay, ch_relay_active_high)

        # Setup RGB status LED
        self.status_led = RGBLED(red, green, blue, active_high=rgb_active_high)

        self.commands_file_path = config["commands_path"]
        self.schedule_file_path = config["schedule_path"]
        
        # Setup HW boost objects
        self.hw_boost_start = None
        self.ch_boost_on = False
        
        self.hw_pressed_flag = False
        self.ch_pressed_flag = False
        
        # Load first state
        self.state = IdleState(self)
        self.state.enter()

    def close(self):
        self.status_led.close()
        self.hw_relay.close()
        self.ch_relay.close()
    
    def setState(self, state):
        self.state.leave()
        self.state = state
        logging.debug("State change: %s", type(state))
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
        self.status_led.pulse(colour[0], colour[1], off_color=colour[2], on_color=colour[3])
        
    def parent_folder():
        return os.path.dirname(os.path.dirname(__file__))
        
    
    
class State:
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def buttonProcess(self):
        stateCode = 0
        # Check to see if either buttons have been pressed
        if self.fsm.ch_pressed_flag:
            if not self.fsm.ch_boost_on:
                logging.info("CH boost started (button)")
                stateCode |= 1
            else:
                logging.info("CH boost cancelled (button)")
            self.fsm.ch_boost_on = not self.fsm.ch_boost_on
            self.fsm.ch_pressed_flag = False
         
        if self.fsm.hw_pressed_flag:
            if not self.fsm.hw_boost_start:
                logging.info("HW boost started (button, %f minutes)", self.fsm.BOOST_DURATION / 60.0)
                stateCode |= 2
                self.fsm.hw_boost_start = datetime.now()
            else:
                logging.info("HW boost cancelled (button)")
                self.fsm.hw_boost_start = None
            self.fsm.hw_pressed_flag = False
            
        if self.fsm.ch_boost_on:
            stateCode |= 1
        
        if self.fsm.hw_boost_start:
            diff = datetime.now() - self.fsm.hw_boost_start
            if diff.seconds < self.fsm.BOOST_DURATION:
                stateCode |= 2 
            else:
                logging.info("HW boost expired")
                self.fsm.hw_boost_start = None
                
        return stateCode        
                
    def scheduleProcess(self):
        # Check to see if the CH or HW is on in the schedule
        current_time = datetime.now()
        
        index = (current_time.weekday() * 24 + current_time.hour) * 60 + current_time.minute
        
        fh = open(self.fsm.schedule_file_path, "rb")
        
        fh.seek(index)
        
        entry = int.from_bytes(fh.read(1), byteorder='little')
        
        fh.close()
        

        
        
        
        return entry
    
    def commandProcess(self):
        stateCode = 0
        
        # Check command file to see if either CH or HW commands are present
        fh = open(self.fsm.commands_file_path, "r+")
        
        commands = fh.read()
        
        fh.close()
        
        if len(commands):
            data = json.loads(commands)
            
            fh = open(self.fsm.commands_file_path, "w")
            
            command_keys = data.keys()
            
            logging.info("Commands received %s", commands)
            
            if "update" in command_keys:
                self.fsm.setState(Update(self.fsm))
                return
            if "shutdown" in command_keys:
                logging.info("Shutting down pi...")
                os.system("shutdown -h now")
                pass
            if "reboot" in command_keys:
                logging.info("Rebooting pi...")
                os.system("shutdown -r now")
                pass
            if "exit" in command_keys:
                logging.info("Stopping chpi...")
                self.fsm.hw_relay.off()
                self.fsm.ch_relay.off()
                
                os.system("kill " + str(os.getpid()))
                
                pass
            if "reload" in command_keys:
                logging.info("Reloading chpi...")
                pass
            if "ch" in command_keys:
                if not self.fsm.ch_boost_on:
                    logging.info("CH boost started (command)")
                    stateCode |= 1
                else:
                    logging.info("CH boost cancelled (command)")
                self.fsm.ch_boost_on = not self.fsm.ch_boost_on
            if "hw" in command_keys:
                if not self.fsm.hw_boost_start:
                    logging.info("HW boost started (command, %f minutes)", self.fsm.BOOST_DURATION / 60.0)
                    stateCode |= 2
                    self.fsm.hw_boost_start = datetime.now()
                else:
                    logging.info("HW boost cancelled (command)")
                    self.fsm.hw_boost_start = None
            if "diagnostics" in command_keys:
                DiagPrint.println()
        
            
            
            
        fh.close()
        
        return stateCode
    
    def process(self):
        
        #nextState = State(self.fsm)
        
        # We check to see if we can reach the default gateway
        if not Gateway.pingGateway():
            self.fsm.setState(NoGateway(self.fsm))
            return
        
        # First we check the time to see if we should update
        current_time = datetime.now()

        
        if current_time.day == CHFSM.UPDATE_REBOOT_TIME[0] and current_time.hour == CHFSM.UPDATE_REBOOT_TIME[1] and current_time.minute == CHFSM.UPDATE_REBOOT_TIME[2] and current_time.second == CHFSM.UPDATE_REBOOT_TIME[3]:
            self.fsm.setState(Update(self.fsm))
            return
        
        # We use stateCode to determine which relays should be set, then use this to change state (if needed)
        stateCode = 0
        
        stateCode |= self.buttonProcess()
            
        # Make sure schedule file exists and is valid
        if not os.path.isfile(self.fsm.schedule_file_path):
            self.fsm.setState(NoSchedule(self.fsm))
            return
        
        # If the schedule file exists, make sure it is the right size
        if os.path.getsize(self.fsm.schedule_file_path) != 7 * 24 * 60:
            self.fsm.setState(BadSchedule(self.fsm))
            return
        
        schedule = self.scheduleProcess()
        
        # Fourth bit represents the emergency off state. This will set the current state to idle
        if schedule & 4 and (0 <= current_time.second <= 1):
            self.fsm.ch_boost_on = False
            return
        
        
        stateCode |= schedule & 3
        
        if not os.path.isfile(self.fsm.commands_file_path):
            fh = open(self.fsm.commands_file_path, "wb")
            fh.close()
        
        stateCode |= self.commandProcess()
        
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
            
            # This segment needs more thought - A way of stating in the log file the exact reason for a change in state
            #if CHHW == 0:
            #    logging.info("HW and CH schedule off")
            #if CHHW == 1:
            #    logging.info("CH schedule on")
            #elif CHHW == 2:
            #    logging.info("HW schedule on")
            #elif CHHW == 3:
            #    logging.info("CH and HW schedule on")
        
    
    def leave(self):
        pass
        
    
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
        
    def process(self):
        super().process()
    
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

# Represents a warning or issue with device. Will not look to schedule, but will respond to 
class DeviceIssue:
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def enter(self):
        
        
        # Turn both relays off
        self.fsm.hw_relay.off()
        self.fsm.ch_relay.off()
        
        
    def process(self):
        
        
            
        # Check commands file and buttons as usual
        stateCode = 0
        
        stateCode |= State(self.fsm).buttonProcess()
        stateCode |= State(self.fsm).commandProcess()
        
        if stateCode == 0:
            self.fsm.hw_relay.off()
            self.fsm.ch_relay.off()
        elif stateCode == 1:
            self.fsm.hw_relay.off()
            self.fsm.ch_relay.on()
        elif stateCode == 2:
            self.fsm.hw_relay.on()
            self.fsm.ch_relay.off()
        elif stateCode == 3:
            self.fsm.hw_relay.on()
            self.fsm.ch_relay.on()
        
            
    def leave(self):
        pass
        
        
        
class BadSchedule(DeviceIssue):
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def enter(self):
        logging.debug("Bad Schedule Enter")
        logging.warning("Bad schedule file! Please create a valid schedule file")
        
        # Change status led to inditate idle
        self.fsm.setStatusLed(CHFSM.BAD_SCHEDULE)
        
        super().enter()
        
    def process(self):
        # Check to see if schedule file exists. If it does not, change to noschedule state
        if not os.path.isfile(self.fsm.schedule_file_path):
            self.fsm.setState(NoSchedule(self.fsm))
        else:
            if os.path.getsize(self.fsm.schedule_file_path) == 7 * 24 * 60:
                self.fsm.setState(IdleState(self.fsm))
                logging.info("Valid schedule file found")
        
        super().process()   
        

class NoSchedule(DeviceIssue):
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def enter(self):
        logging.debug("No Schedule Enter")
        logging.warning("Schedule file not found! Please create a schedule file")
        
        # Change status led to inditate idle
        self.fsm.setStatusLed(CHFSM.SCHEDULE_MISSING)
        
        super().enter()
        
    def process(self):
        # Check to see if schedule file exists. If it does, change state to idle
        if os.path.isfile(self.fsm.schedule_file_path):
            self.fsm.setState(IdleState(self.fsm))
            logging.info("Schedule file found")
        
        super().process()

class NoGateway(DeviceIssue):
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def enter(self):
        logging.debug("No Gateway Enter")
        logging.warning("Could not reach default gateway (ping failed)")
        
        # Change status led to inditate idle
        self.fsm.setStatusLed(CHFSM.NO_GATEWAY_CONNECTION)
        
        super().enter()
        
    def process(self):
        # Check to see if schedule file exists. If it does, change state to idle            
        if Gateway.pingGateway():
            self.fsm.setState(IdleState(self.fsm))
            logging.info("Gateway ping succeeded")
        
        super().process()

class Update:
    
    def __init__(self, fsm):
        self.fsm = fsm
        
    def enter(self):
        
        # Change light
        self.fsm.setStatusLed(CHFSM.UPDATING)
        
        # Turn relays off
        self.fsm.hw_relay.off()
        self.fsm.ch_relay.off()
        
        # Update, upgrade and reboot        
        logging.info("Updating pi...")
        os.system("sudo apt update -y")
        
        logging.info("Upgrading pi...")
        os.system("sudo apt full-upgrade -y")
        
        self.fsm.status_led.off()
        
        logging.info("Rebooting pi...")
        os.system("sudo shutdown -r now")
        
    
    def process(self):
        pass
    
    
    
    
    
    
    
    
    
    
    
    
        