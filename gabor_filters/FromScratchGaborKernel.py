import numpy as np
import matplotlib.pyplot as plt
import cv2
import math

class FromScratchGaborKernel():
    def __init__(self, theta=0, lambd=8, sigma=4.0, gamma=0.5, psi=0, size=31):
        self.theta = theta
        self.lambd = lambd
        self.sigma = sigma
        self.gamma = gamma
        self.psi = psi
        self.size = size
        self.kernel = mygetGaborKernel(theta, lambd, sigma, gamma, psi, size)

# Gabor kernel implementation
def mygetGaborKernel(theta, lambd, sigma=4.0, gamma=0.5, psi=0, size=31):
    half = size // 2
    y, x = np.meshgrid(np.arange(-half, half+1), np.arange(-half, half+1))

    # Rotate coordinates according to theta
    x_theta = x * np.cos(theta) + y * np.sin(theta)
    y_theta = -x * np.sin(theta) + y * np.cos(theta)

    # Gaussian envelope
    exp_term = np.exp(-(x_theta**2 + (gamma**2) * y_theta**2) / (2 * sigma**2))
    
    # Sinusoidal component
    cos_term = np.cos(2 * np.pi * x_theta / lambd + psi)

    return exp_term * cos_term

if __name__ == "__main__":
    # Test the Gabor kernel
    theta = np.pi/4  # 45 degrees
    lambd = 8
    sigma = 4.0
    gamma = 0.5
    psi = 0
    size = 31
    
    gabor = FromScratchGaborKernel(theta, lambd, sigma, gamma, psi, size)
    print("Gabor kernel shape:", gabor.kernel.shape)
    print("Gabor kernel (first 5x5 corner):")
    print(gabor.kernel[:5, :5])
    print("mygetGaborKernel function call result shape:", mygetGaborKernel(theta, lambd, sigma, gamma, psi, size).shape)
