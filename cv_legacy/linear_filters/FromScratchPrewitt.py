import numpy as np
import matplotlib.pyplot as plt
import cv2
import math

class FromScratchPrewitt():
    def __init__(self, ksize=(3,3), alpha=0, dx=1, dy=0):
        if (alpha != 0):
            self.prewitt_operator = mygetPrewittKernelAlpha(ksize, alpha)
        else:
            self.Gx, self.Gy, self.G_magnitude, self.G_theta = mygetPrewittKernel(ksize)
            self.prewitt_operator = mygetPrewittKernelAlpha(ksize, alpha=np.atan2(dy, dx))

# Prewitt operator, defined for just alpha=0 (x-direction) and alpha=math.pi/2 (y-direction)
def mygetPrewittKernel(ksize=(3,3)):
    """
    Generate Prewitt kernels for x and y directions for any kernel size.
    Following the same mathematical approach as Sobel but with uniform weighting concept.
    """
    center_y = (ksize[0]-1)/2
    center_x = (ksize[1]-1)/2
    Gx = []
    Gy = []
    G_magnitude = []
    G_angle = []
    
    for y in range(ksize[1]):  # Note: using ksize[1] for y range like Sobel
        rowx = []
        rowy = []
        rowmag = []
        rowangle = []
        j = y - center_y
        for x in range(ksize[0]):  # Note: using ksize[0] for x range like Sobel
            i = x - center_x
            dist_squared = i**2 + j**2
            if dist_squared != 0:
                # Prewitt: same gradient calculation as Sobel (uniform weighting is conceptual)
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
def mygetPrewittKernelAlpha(ksize=(3,3), alpha=0):
    """
    Generate Prewitt kernel in a specific direction (alpha) for any kernel size.
    Following the same mathematical approach as Sobel.
    """
    center_y = (ksize[0]-1)/2
    center_x = (ksize[1]-1)/2
    G_alpha = []
    
    for y in range(ksize[1]):  # Note: using ksize[1] for y range like Sobel
        row_alpha = []
        j = y - center_y
        for x in range(ksize[0]):  # Note: using ksize[0] for x range like Sobel
            i = x - center_x
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
    prewitt = FromScratchPrewitt(ksize, alpha)
    print("prewitt_operator", prewitt.prewitt_operator)
    print("mygetPrewittKernelAlpha function call", mygetPrewittKernelAlpha(ksize, alpha))
