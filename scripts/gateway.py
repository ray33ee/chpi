
import subprocess

import sys

import os

import csv

class Gateway:
    
    def gateway():
        
        os.system("route > tmp")
        
        res = subprocess.run(["awk '/default/{print $2}' tmp"], capture_output=True, shell=True)
        
        output = str(res.stdout.decode('utf-8'))
        
        return output
                