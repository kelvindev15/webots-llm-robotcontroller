import numpy as np
import cv2
import os
import base64
from typing import List
from ultralytics import YOLO
from common.types.ObjectDetection import ObjectDetection

model = YOLO("yolov8n.pt")

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

def plotDetections(image):
    results = model(image, verbose=False)
    if len(results) == 0:
        return image
    return results[0].plot()
