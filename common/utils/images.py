import numpy as np
import cv2
import os
import base64
from typing import List
from ultralytics import YOLO
from common.types.ObjectDetection import ObjectDetection
from controllers.webots.adapters.lidar import LidarSnapshot

model = YOLO("yolo11n.pt")

def extractColorChannel(image, fn, width, height):
    return np.array([[fn(image, width, i, j) for i in range(width)] for j in range(height)], dtype=np.uint8)

def toBase64Image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer.tobytes()).decode("utf-8")

def saveImage(image, filename, path='./'):
    if not os.path.exists(path):
        os.makedirs(path)
    cv2.imwrite(f"{path}/{filename}", image)

def detectObjects(image):
    results = model(image, verbose=False)
    detections: List[ObjectDetection] = []
    for result in results:
        for box in result.boxes:
            x, y, w, h = box.xywhn[0]
            detections.append(ObjectDetection(
                model.names[int(box.cls.item())], 
                box.conf.item(), 
                x.item(), 
                y.item(), 
                w.item(), 
                h.item())
            )        
    return detections
