import numpy as np

class KalmanFilter:
    def __init__(self, F, B, H, Q, R, x0, P0):
        # State transition model
        self.F = F
        self.B = B
        self.H = H
        self.Q = Q
        self.R = R
        self.x = x0
        self.P = P0

    def predict(self, u):
        # x = F*x + B*u
        self.x = np.dot(self.F, self.x) + np.dot(self.B, u)
        # P = F*P*F^T + Q
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self.x

    def update(self, z):
        # calculate Kalman gain
        # S = H*P*H^T + R
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        # K = P*H^T*S^-1
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        # update state estimate and cov matrix
        # y = z - H*x
        y = z - np.dot(self.H, self.x)
        # x = x + K*y
        self.x = self.x + np.dot(K, y)
        # get identity matrix of dim(P)
        I = np.eye(self.P.shape[0])
        # P = ((I - K*H) * P) * (I - (K*H)^T) + K*R*K^T
        self.P = np.dot(np.dot(I - np.dot(K, self.H), self.P), 
                        (I - np.dot(K, self.H)).T) + np.dot(np.dot(K, self.R), K.T)
        return self.x
