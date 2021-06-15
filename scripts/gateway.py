
import subprocess

import sys

import os

import csv

from gpiozero import PingServer

tmp_path = os.path.join(os.path.join(os.path.dirname(__file__), "tmp.txt"))

class Gateway:
    
    def gateway():
        
        
        os.system("route > " + tmp_path)
        
        res = subprocess.run(["awk '/default/{print $2}' " + tmp_path], capture_output=True, shell=True)
        
        #os.remove(tmp_path)
        
        output = str(res.stdout.decode('utf-8'))
        
        output = output.replace("\n", "")
        
        
        return output
    
    def pingGateway():
        return PingServer(Gateway.gateway()).value
                