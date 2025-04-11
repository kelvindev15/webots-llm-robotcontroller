import numpy as np
import math


def rotateVector(vector, angle):
    rotation_matrix = np.array(
        [[np.cos(angle), -np.sin(angle)],
         [np.sin(angle), np.cos(angle)]])
    return np.dot(rotation_matrix, vector)


def angleBetweenVectors(v1, v2):
    return np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


def gaussian(x, a, b, c):
    return a*math.exp(- (x - b)**2/(2*(c**2)))


def calculateDistanceAccuracy(distance, a=1, b=2, c=1.5):
    return gaussian(distance, a, b, c)


def normalizeVector(vector):
    return vector / np.linalg.norm(vector)


def calculateDirectionAccuracy(direction, a=1, b=0, c=0.157):
    return gaussian(direction, a, b, c)


def calculateAccuracy(distance, direction):
    return calculateDistanceAccuracy(distance) * calculateDirectionAccuracy(direction)
