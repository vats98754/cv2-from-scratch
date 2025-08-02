import math
import numpy as np
import matplotlib.pyplot as plt
import cv2

class FromScratchGaussianBlur():
    def __init__(self, ksize=(3,3), sigmaX=1.0):
        self.ksize = ksize
        self.sigmaX = sigmaX
        self.kernel = myGaussianKernel(self.ksize, self.sigmaX)
    
def gaussian(x, sigmaX=1, mu=0):
    return (1 / (sigmaX * (2*math.pi)**0.5) * math.e ** (-0.5 * ((x-mu)/sigmaX)**2))

def mygetGaussianKernel(dim=1, sigmaX=1.0):
    sum_x = 0 # for normalization
    center_x = (dim-1)/2 # get the center of the 1D kernel
    op = []
    for x in range(dim):
        delta_x = abs(x-center_x)
        gaussian_x = gaussian(delta_x, sigmaX)
        sum_x += gaussian_x
        op.append(gaussian_x)
    return np.array(op, dtype=float)/sum_x

def myGaussianKernel(ksize=(3,3), sigmaX=1.0):    
    # OPTIMIZED approach, using outer product of computer 1D Gaussian kernels in x and y directions
    return np.outer(mygetGaussianKernel(ksize[0], sigmaX),
                    mygetGaussianKernel(ksize[1], sigmaX))

    # NAIVE approach, not optimized
    # kernel = []
    # # get the center of the 2D kernel
    # center_y = (ksize[0]-1)/2; center_x = (ksize[1]-1)/2
    # sum = 0 # for normalization
    # for y in range(ksize[0]):
    #     row = []
    #     for x in range(ksize[1]):
    #         delta_y = y - center_y
    #         delta_x = x - center_x
    #         gaussian_x_y = gaussian((delta_x**2 + delta_y**2)**0.5, sigmaX)
    #         sum += gaussian_x_y
    #         row.append(gaussian_x_y)
    #     kernel.append(row)
    # kernel_np = np.array(kernel, dtype=float)
    # return kernel_np/sum
    
if __name__ == "__main__":
    kernel_height = 5
    kernel_width = 5
    sigmaX = 2.0
    gb = FromScratchGaussianBlur(ksize=(kernel_height, kernel_width), sigmaX=sigmaX)
    gk_height = cv2.getGaussianKernel(kernel_height, sigmaX)
    gk_width = cv2.getGaussianKernel(kernel_width, sigmaX)
    rgb = np.outer(gk_height, gk_width)
    print(gb.kernel)
    print(rgb)
    print("diff", gb.kernel-rgb)