import numpy as np
import cv2
import os
import base64


def extractColorChannel(image, fn, width, height):
    return np.array([[fn(image, width, i, j) for i in range(width)] for j in range(height)], dtype=np.uint8)


def toBase64Image(image):
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer.tobytes()).decode("utf-8")


def saveImage(image, filename, path='./'):
    if not os.path.exists(path):
        os.makedirs(path)
    cv2.imwrite(f"{path}/{filename}", image)
