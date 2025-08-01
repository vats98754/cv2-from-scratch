import numpy as np

# Median filter (takes medium of window)
def apply_median_filter(img, kernel=(3,3)):
    kernel_height_halved = int((kernel[1]-1)/2)
    kernel_width_halved = int((kernel[0]-1)/2)
    img = np.pad(img, ((kernel_height_halved, kernel_height_halved), 
                    (kernel_width_halved, kernel_width_halved)), 
                mode='constant', constant_values=0)
    convolution = []
    img_height = img.shape[0]
    img_width = img.shape[1]
    # start at row kernel_height_halved, end at row img_height-kernel_height_halved
    for i in range(kernel_height_halved, img_height-kernel_height_halved):
        lst = []
        # start at col kernel_width_halved, end at col img_width-kernel_height_halved
        for j in range(kernel_width_halved, img_width-kernel_width_halved):
            lst.append(np.median(img[i-kernel_height_halved:i+kernel_height_halved+1,
                            j-kernel_width_halved:j+kernel_width_halved+1]))
        convolution.append(lst)
    return convolution


# Bilateral Filter (smooths the image while respecting edges)
def apply_bilateral_filter(img, kernel=(3,3), sigma_spatial=1, sigma_intensity=1):
    kernel_height_halved = int((kernel[1]-1)/2)
    kernel_width_halved = int((kernel[0]-1)/2)
    img = np.pad(img, ((kernel_height_halved, kernel_height_halved), 
                    (kernel_width_halved, kernel_width_halved)), 
                mode='constant', constant_values=0)
    bilateral = []
    img_height = img.shape[0]
    img_width = img.shape[1]
    # start at row kernel_height_halved, end at row img_height-kernel_height_halved
    for i in range(kernel_height_halved, img_height-kernel_height_halved):
        lst = []
        # start at col kernel_width_halved, end at col img_width-kernel_height_halved
        for j in range(kernel_width_halved, img_width-kernel_width_halved):
            lst.append(denoised_intensity(img,i,j,sigma_spatial,sigma_intensity,
                                          startk=i-kernel_height_halved,
                                          endk=i+kernel_height_halved+1,
                                          startl=j-kernel_width_halved,
                                          endl=j+kernel_width_halved+1))
        bilateral.append(lst)

    return bilateral

# calculate the weighted intensity normalized (i.e. divided by sum of weights)
def denoised_intensity(img, i, j, sigma_spatial, sigma_intensity, startk, endk, startl, endl):
    sum_ij = 0
    sum_weights = 0
    for k in range(startk, endk):
        for l in range(startl, endl):
            weight_kl = weight(img, i, j, k, l, sigma_spatial, sigma_intensity)
            sum_ij += img[k][l] * weight_kl
            sum_weights += weight_kl
    return sum_ij/sum_weights

# weight assigned for pixel (k, l) to denoise pixel (i, j)
def weight(img, i, j, k, l, sigma_spatial, sigma_intensity):
    # is never 0 as you cannot have input -inf
    intensity_diff = img[i][j] - img[k][l]
    spatial_term = -((i - k)**2 + (j - l)**2) / (2 * sigma_spatial**2)
    intensity_term = -(intensity_diff**2) / (2 * sigma_intensity**2)
    return np.exp(spatial_term + intensity_term)
