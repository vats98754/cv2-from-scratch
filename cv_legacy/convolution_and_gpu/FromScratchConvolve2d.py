import numpy as np
import matplotlib.pyplot as plt
import cv2
import kagglehub
from FromScratchGaussianBlur import FromScratchGaussianBlur

def myconvolve2d(img, kernel):
    kernel_height = kernel.shape[0]
    kernel_height_halved = int((kernel_height-1)/2)
    kernel_width = kernel.shape[1]
    kernel_width_halved = int((kernel_width-1)/2)
    img = np.pad(img, ((kernel_height_halved, kernel_height_halved), 
                    (kernel_width_halved, kernel_width_halved)), 
                mode='constant', constant_values=0)
    img_height = img.shape[0]
    img_width = img.shape[1]
    convolution = []
    # start at row kernel_height_halved, end at row img_height-kernel_height_halved
    for i in range(kernel_height_halved, img_height-kernel_height_halved):
        lst = []
        # start at col kernel_width_halved, end at col img_width-kernel_height_halved
        for j in range(kernel_width_halved, img_width-kernel_width_halved):
            lst.append((img[i-kernel_height_halved:i+kernel_height_halved+1,
                            j-kernel_width_halved:j+kernel_width_halved+1] * kernel).sum().item())
        convolution.append(lst)
    return np.array(convolution)

if __name__ == "__main__":
    path = kagglehub.dataset_download("joosthazelzet/lego-brick-images")
    IMG_DIR = path + "/LEGO brick images v1/2357 Brick corner 1x2x2/"
    img = plt.imread(IMG_DIR + "/201706171206-0243.png", cv2.IMREAD_GRAYSCALE)
    ksize = (3,3)
    # Gaussian kernel
    sigmaX = 2.0
    gb = FromScratchGaussianBlur(ksize, sigmaX)
    print("Gaussian Blur")
    plt.imsave("gaussian_blur.png", myconvolve2d(img, gb.kernel))