
from datetime import datetime

from gpiozero import PingServer, CPUTemperature, LoadAverage

import logging

from gateway import Gateway

import os

class DiagPrint:
    
    def __init__(self, duration):
        self.start_time = datetime.now()
        self.duration = duration
        
    def println():
        gateway = Gateway.gateway()
            
        ping = Gateway.pingGateway()
        
        temp = CPUTemperature().temperature
        
        load = LoadAverage().load_average
        
        pid = os.getpid()
        
        ppid = os.getppid()
        
        data = {
            "pid": pid,
            "parent pid": ppid,
            "ping gateway": gateway,
            "ping response": ping,
            "temperature": temp,
            "average load": load
            }
        
        logging.debug("Diagnostics: %s", str(data))
        
    def process(self):
        if (datetime.now() - self.start_time).total_seconds() >= self.duration:
            # Temperature, ping and load information
            
            DiagPrint.println()
            self.start_time = datetime.now()
            
            
            
            
            