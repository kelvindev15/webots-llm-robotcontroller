from controller.camera import Camera
from controller.device import Device
import cv2

import numpy as np

class WBCamera():
    def __init__(self, camera: Camera, timeStep: int):
        self.camera: Camera = camera
        self.camera.enable(timeStep)

    def getImage(self):
        image_data = np.array(list(self.camera.getImage()), dtype=np.uint8)
        image_data = image_data.reshape((self.camera.getHeight(), self.camera.getWidth(), 4))
        output_image = cv2.cvtColor(image_data, cv2.COLOR_BGRA2BGR)
        return output_image    
