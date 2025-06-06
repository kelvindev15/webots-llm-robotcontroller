import numpy as np

DOUBLE_EQUALITY_TOLERANCE = 1e-10  # This mimics WbPrecision::DOUBLE_EQUALITY_TOLERANCE

def clamped_acos(value):
    return np.arccos(np.clip(value, -1.0, 1.0))

class WbRotation:
    # This was originally a C++ class in Webots, adapted to Python.
    def __init__(self):
        self.mX = 0.0
        self.mY = 0.0
        self.mZ = 0.0
        self.mAngle = 0.0

    def normalize_axis(self):
        norm = np.linalg.norm([self.mX, self.mY, self.mZ])
        if norm > 0:
            self.mX /= norm
            self.mY /= norm
            self.mZ /= norm

    def from_matrix3(self, M):
        theta = clamped_acos((M[0, 0] + M[1, 1] + M[2, 2] - 1) / 2)

        if theta < DOUBLE_EQUALITY_TOLERANCE:
            self.mX, self.mY, self.mZ, self.mAngle = 1.0, 0.0, 0.0, 0.0
            return
        elif np.pi - theta < DOUBLE_EQUALITY_TOLERANCE:
            if M[0, 0] > M[1, 1] and M[0, 0] > M[2, 2]:
                self.mX = np.sqrt(M[0, 0] - M[1, 1] - M[2, 2] + 1) / 2
                self.mY = M[0, 1] / (2 * self.mX)
                self.mZ = M[0, 2] / (2 * self.mX)
            elif M[1, 1] > M[0, 0] and M[1, 1] > M[2, 2]:
                self.mY = np.sqrt(M[1, 1] - M[0, 0] - M[2, 2] + 1) / 2
                self.mX = M[0, 1] / (2 * self.mY)
                self.mZ = M[1, 2] / (2 * self.mY)
            else:
                self.mZ = np.sqrt(M[2, 2] - M[0, 0] - M[1, 1] + 1) / 2
                self.mX = M[0, 2] / (2 * self.mZ)
                self.mY = M[1, 2] / (2 * self.mZ)
        else:
            self.mX = M[2, 1] - M[1, 2]
            self.mY = M[0, 2] - M[2, 0]
            self.mZ = M[1, 0] - M[0, 1]

        self.mAngle = theta
        self.normalize_axis()

    def __repr__(self):
        return f"WbRotation(x={self.mX}, y={self.mY}, z={self.mZ}, angle={self.mAngle})"    
