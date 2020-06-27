
from datetime import datetime

from gpiozero import PingServer, CPUTemperature, LoadAverage

import logging

from gateway import Gateway

class DiagPrint:
    
    def __init__(self, duration):
        self.start_time = datetime.now()
        self.duration = duration
        
    def process(self):
        if (datetime.now() - self.start_time).total_seconds() >= self.duration:
            # Temperature, ping and load information
            
            gateway = Gateway.gateway()
            
            ping = PingServer(gateway).value
            
            temp = CPUTemperature().temperature
            
            load = LoadAverage().load_average
            
            data = {"ping gateway": gateway, "ping response": ping, "temperature": temp, "average load": load}
            
            logging.debug("Diagnostics: %s", str(data))
            self.start_time = datetime.now()