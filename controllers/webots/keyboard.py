from concurrent.futures import ThreadPoolExecutor

class KeyboardController:
    def __init__(self):
        self.controls = {}
        self.NO_KEY_HANDLER = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        pass

    def onKey(self, key, handler):
        self.controls[key] = handler
        return self

    def onNoKey(self, handler):
        self.NO_KEY_HANDLER = handler
        return self    

    def execute(self, key):
        if key in self.controls:
            try:
                f = self.executor.submit(self.controls[key])
                return f
            except Exception as e:
                print(f"KeyboardController: Error executing handler for key {key}: {str(e)}")
                raise e
        elif key == -1 and self.NO_KEY_HANDLER != None:
            self.NO_KEY_HANDLER()
        return False
        