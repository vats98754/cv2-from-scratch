import numpy as np
import matplotlib.pyplot as plt
import cv2
import math

class FromScratchSobel():
    def __init__(self, ksize=(3,3), alpha=0, dx=1, dy=0):
        if (alpha != 0):
            self.sobel_operator = mygetSobelKernelAlpha(ksize, alpha)
        else:
            self.Gx, self.Gy, self.G_magnitude, self.G_theta = mygetSobelKernel(ksize)
            self.sobel_operator = mygetSobelKernelAlpha(ksize, alpha=np.atan2(dy, dx))

# Sobel operator, defined for just alpha=0 (x-direction) and alpha=math.pi/2 (y-direction)
def mygetSobelKernel(ksize=(3,3)):
    center_y = (ksize[0]-1)/2
    center_x = (ksize[1]-1)/2
    Gx = []
    Gy = []
    G_magnitude = []
    G_angle = []
    for y in range(ksize[1]):
        rowx = []
        rowy = []
        rowmag = []
        rowangle = []
        j = y-center_y
        for x in range(ksize[0]):
            i = x-center_x
            dist_squared = i**2 + j**2
            if dist_squared != 0:
                Gx_ij = i/dist_squared
                Gy_ij = j/dist_squared
            else:
                Gx_ij = 0
                Gy_ij = 0
            rowx.append(Gx_ij)
            rowy.append(Gy_ij)
            rowmag.append((Gx_ij**2 + Gy_ij**2)**0.5)
            rowangle.append(np.atan2(Gy_ij, Gx_ij))
        Gx.append(rowx)
        Gy.append(rowy)
        G_magnitude.append(rowmag)
        G_angle.append(rowangle)
    return np.array(Gx), np.array(Gy), np.array(G_magnitude), np.array(G_angle)

# g_alpha = (alpha-unit vector) dot (gx, gy)
#         = (cos a, sin a) dot (gx, gy)
#         = cos a * gx + sin a * gy
#         = (cos a * i + sin a * j)/(i**2 + j**2)
# This overloaded function gives the image gradients in the direction of alpha
def mygetSobelKernelAlpha(ksize=(3,3), alpha=0):
    center_y = (ksize[0]-1)/2
    center_x = (ksize[1]-1)/2
    G_alpha = []
    for y in range(ksize[1]):
        row_alpha = []
        j = y-center_y
        for x in range(ksize[0]):
            i = x-center_x
            dist_squared = i**2 + j**2
            if dist_squared != 0:
                Gij_alpha = (np.cos(alpha) * i + np.sin(alpha) * j)/dist_squared
            else:
                Gij_alpha = 0
            row_alpha.append(Gij_alpha)
        G_alpha.append(row_alpha)
    return np.array(G_alpha)

if __name__ == "__main__":
    alpha = math.pi/3
    ksize = (5,5)
    sobel = FromScratchSobel(ksize, alpha)
    print("sobel_operator", sobel.sobel_operator)
    print("mygetSobelKernelAlpha function call", mygetSobelKernelAlpha(ksize, alpha))