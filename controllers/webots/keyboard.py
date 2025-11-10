from concurrent.futures import ThreadPoolExecutor

class KeyboardController:
    def __init__(self):
        self.controls = {}
        self.NO_KEY_HANDLER = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        pass

    def onKey(self, key, handler):
        self.controls[key] = handler
        return self

    def onNoKey(self, handler):
        self.NO_KEY_HANDLER = handler
        return self    

    def execute(self, key):
        if key in self.controls:
            f = self.executor.submit(self.controls[key])
            return f
        elif key == -1 and self.NO_KEY_HANDLER != None:
            self.NO_KEY_HANDLER()
        return False
        