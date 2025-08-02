import numpy as np
import matplotlib.pyplot as plt
import cv2
from scipy.signal import convolve2d
from linear_filters.FromScratchGaussianBlur import FromScratchGaussianBlur
from linear_filters.FromScratchSobel import FromScratchSobel
from convolution_and_gpu.FromScratchConvolve2d import myconvolve2d

class FromScratchHarrisCorners():
    def __init__(self, img, ksize_sobel=(3,3), ksize_gaussian=(0,0), sigmaX=1, alpha=0, threshold=0):
        self.img = img
        self.corner_img = img
        self.ksize_sobel = ksize_sobel
        self.ksize_gaussian = ksize_gaussian
        self.sigmaX = sigmaX
        self.alpha = alpha
        self.threshold = threshold
        self.corners = self.getCorners()
        if threshold != 0:
            self.corners = self.apply_threshold()

    def getCorners(self):
        gaussian_blur = FromScratchGaussianBlur(self.ksize_gaussian, self.sigmaX)
        sobel = FromScratchSobel(self.ksize_sobel, self.alpha)
        print("sobel_x", sobel.Gx)
        print("sobel_y", sobel.Gy)

        convolved_img_sobel_x = myconvolve2d(self.img, sobel.Gx)
        convolved_img_sobel_y = myconvolve2d(self.img, sobel.Gy)

        print("I_x", convolved_img_sobel_x)
        print("I_y", convolved_img_sobel_y)

        # Squared Gaussian blur of I_x * I_y
        corners_supressed_squared = myconvolve2d(convolved_img_sobel_x * convolved_img_sobel_y, gaussian_blur.kernel) ** 2
        # Gaussian blur of I_x ** 2
        I_x_squared_blur = myconvolve2d(convolved_img_sobel_x ** 2, gaussian_blur.kernel)
        # Gaussian blur of I_y ** 2
        I_y_squared_blur = myconvolve2d(convolved_img_sobel_y ** 2, gaussian_blur.kernel)

        print("corners_supressed_squared", corners_supressed_squared)
        print("I_x_squared_blur", I_x_squared_blur)
        print("I_y_squared_blur", I_y_squared_blur)

        self.corners = I_x_squared_blur * I_y_squared_blur - corners_supressed_squared
        print("self.corners", self.corners)
        return self.corners

    def show_corners(self):
        img = cv2.cvtColor(self.img, cv2.COLOR_GRAY2RGB)
        for i in range(self.img.shape[0]):
            for j in range(self.img.shape[1]):
                if self.corners[i][j] == 255:
                    cv2.circle(img, (j, i), radius=2, color=(255, 0, 0), thickness=-1)
        plt.imsave("corners_image.png", img)

    def apply_threshold(self):
        self.corners[self.corners < self.corners.max() * (1-self.threshold)] = 0
        self.corners[self.corners != 0] = 255
        return self.corners

if __name__ == "__main__":
    img = cv2.imread("/Users/anvay-coder/cv2-from-scratch/cat.png", cv2.IMREAD_GRAYSCALE)
    ksize_sobel = (3,3)
    ksize_gaussian = (3,3)
    sigmaX = 1
    alpha = 0
    threshold = 0.2

    hc = FromScratchHarrisCorners(img, ksize_sobel, ksize_gaussian, sigmaX, alpha, threshold)
    corners = hc.corners
    hc.show_corners()