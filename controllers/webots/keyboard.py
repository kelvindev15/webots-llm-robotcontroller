class KeyboardController:
    def __init__(self):
        self.controls = {}
        self.NO_KEY_HANDLER = None
        pass

    def onKey(self, key, handler):
        self.controls[key] = handler
        return self

    def onNoKey(self, handler):
        self.NO_KEY_HANDLER = handler
        return self    

    def execute(self, key):
        if key in self.controls:
            self.controls[key]()
            return True
        elif key == -1 and self.NO_KEY_HANDLER != None:
            self.NO_KEY_HANDLER()
        return False
        