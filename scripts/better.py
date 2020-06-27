from gpiozero import Button

from datetime import datetime

# We make our own custom Button class to prevent the user from activating the button too frequently
class BetterButton(Button):
    
    # The minimum time between any two valid button presses
    BUTTON_DELAY = 0.5
    
    
    def __init__(self, pin, function, bounce, pullup, activestate):
        self.func = function
        self.press_time = None
        
        super().__init__(pin, bounce_time=bounce, pull_up=pullup, active_state=activestate)
        self.when_pressed = self.pressed
        
        
    def pressed(self):
        
        if self.press_time:
            delta = datetime.now() - self.press_time
            if delta.total_seconds() > self.BUTTON_DELAY:
                self.press_time = datetime.now()
                self.func()
        else:
            self.press_time = datetime.now()
            self.func()
        
    