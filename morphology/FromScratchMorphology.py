import numpy as np

# 1. Erosion (each center pixel stays only if the structuring element completely lies in white pixels)
def erode(img, structuring_element=[[0,1,0],[1,1,1],[0,1,0]]):
    H, W = img.shape
    se_h, se_w = len(structuring_element), len(structuring_element[0])
    pad_h, pad_w = se_h // 2, se_w // 2

    # Pad the image to handle border pixels
    padded_img = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant', constant_values=0)
    eroded_img = np.zeros_like(img)

    for i in range(H):
        for j in range(W):
            # Extract the region of interest
            roi = padded_img[i:i+se_h, j:j+se_w]
            # Apply erosion: check if structuring element fits completely
            if np.array_equal(roi & structuring_element, structuring_element):
                eroded_img[i, j] = 255  # Set pixel to white
            else:
                eroded_img[i, j] = 0  # Set pixel to black

    return eroded_img

# 2. Dilation (each center pixel stays only if the structuring element intersects a white pixel)
def dilate(img, structuring_element=[[0,1,0],[1,1,1],[0,1,0]]):
    H, W = img.shape
    se_h, se_w = len(structuring_element), len(structuring_element[0])
    pad_h, pad_w = se_h // 2, se_w // 2

    # Pad the image to handle border pixels
    padded_img = np.pad(img, ((pad_h, pad_h), (pad_w, pad_w)), mode='constant', constant_values=0)
    dilated_img = np.zeros_like(img)

    for i in range(H):
        for j in range(W):
            # Extract the region of interest
            roi = padded_img[i:i+se_h, j:j+se_w]
            # Apply dilation: check if structuring element intersects
            if np.any(roi & structuring_element):
                dilated_img[i, j] = 255  # Set pixel to white
            else:
                dilated_img[i, j] = 0  # Set pixel to black

    return dilated_img

# Opening removes noise but keeps the general shape by applying erosion then dilation
def opening(img, structuring_element=[[1,1,1],[1,1,1],[1,1,1]]):
    return dilate(erode(img, structuring_element), structuring_element)

# Closing closes small gaps or holes by applying dilation then erosion
def closing(img, structuring_element=[[1,1,1],[1,1,1],[1,1,1]]):
    return erode(dilate(img, structuring_element), structuring_element)