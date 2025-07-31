import numpy as np

def apply_transform(img, mat = [[1, 0], [0, 1]], center = (img.shape[0]/2, img.shape[1]/2)):
    center_y = center[0]
    center_x = center[1]
    new_img = np.zeros(img.shape, dtype=img.dtype)
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            new_x = int(mat[0][0] * (x - center_x) + mat[1][0] * (y - center_y) + center_x)
            new_y = int(mat[0][1] * (x - center_x) + mat[1][1] * (y - center_y) + center_y)

            if new_x >= img.shape[1] or new_x <= 0 or new_y >= img.shape[0] or new_y <= 0:
                continue

            new_img[new_y][new_x] = img[y][x]

    return new_img

def rotate(img, angle = 0, center = (img.shape[0]/2, img.shape[1]/2)):
    rotation_mat = [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
    return apply_transform(img, rotation_mat, center)

def shear(img, shear_x_vec = [1, 0], shear_y_vec = [0, 1], center = (img.shape[0]/2, img.shape[1]/2)):
    shear_x_magnitude = (shear_x_vec[0] ** 2 + shear_y_vec[0] ** 2) ** 0.5
    shear_y_magnitude = (shear_x_vec[1] ** 2 + shear_y_vec[1] ** 2) ** 0.5
    shear_mat = [[shear_x_vec[0]/shear_x_magnitude, shear_y_vec[0]/shear_y_magnitude],
                 [shear_x_vec[1]/shear_x_magnitude, shear_y_vec[1]/shear_y_magnitude]]
    return apply_transform(img, shear_mat, center)

def scale(img, scale = 1, center = (img.shape[0]/2, img.shape[1]/2)):
    scale_mat = [[scale, 0], [0, scale]]
    return apply_transform(img, scale_mat, center)