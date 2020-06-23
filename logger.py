import datetime

class Logger:
    def __init__(self, fsm):
        self.fsm = fsm
        pass
    
    def log(self, message):
        print("Log entry: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f") + " (" + str(type(self.fsm.getState())) + ") " + message)
        pass