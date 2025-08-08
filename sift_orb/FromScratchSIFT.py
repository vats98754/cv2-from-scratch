import numpy as np
import cv2
import matplotlib.pyplot as plt

class FromScratchSIFT:
    def __init__(self, num_scales=5, sigma=1.6):
        self.num_scales = num_scales
        self.sigma = sigma
    
    def build_dog_pyramid(self, image):
        """Build Difference of Gaussians pyramid"""
        gaussians = []
        dogs = []
        k = np.sqrt(2)

        for i in range(self.num_scales + 1):
            sigma_i = self.sigma * (k ** i)
            blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma_i)
            gaussians.append(blurred)

        for i in range(self.num_scales):
            dogs.append(gaussians[i+1] - gaussians[i])

        return np.stack(dogs, axis=-1)
    
    def is_extremum(self, D, x, y, s):
        """Check if point is local extremum in 3D"""
        patch = D[x-1:x+2, y-1:y+2, s-1:s+2]
        center = D[x, y, s]
        return (center == patch.max()) or (center == patch.min())
    
    def assign_orientation(self, image, x, y):
        """Assign dominant orientation to keypoint"""
        radius = 8
        H, W = image.shape
        x, y = int(round(x)), int(round(y))
        
        x0, x1 = max(0, x - radius), min(H, x + radius + 1)
        y0, y1 = max(0, y - radius), min(W, y + radius + 1)
        patch = image[x0:x1, y0:y1]

        gx = cv2.Sobel(patch, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(patch, cv2.CV_32F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        angle = (np.arctan2(gy, gx) * 180 / np.pi) % 360

        hist, _ = np.histogram(angle, bins=36, range=(0, 360), weights=mag)
        dominant_angle = np.argmax(hist) * 10

        return dominant_angle
    
    def compute_descriptor(self, image, x, y, angle):
        """Compute 128-dimensional SIFT descriptor"""
        # Simplified descriptor computation
        patch_size = 16
        half = patch_size // 2
        
        # Extract rotated patch
        angle_rad = -np.deg2rad(angle)
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        patch = np.zeros((patch_size, patch_size), dtype=np.float32)
        
        for i in range(patch_size):
            for j in range(patch_size):
                xi = int(x + (i - half) * cos_a - (j - half) * sin_a)
                yj = int(y + (i - half) * sin_a + (j - half) * cos_a)
                
                if 0 <= xi < image.shape[0] and 0 <= yj < image.shape[1]:
                    patch[i, j] = image[xi, yj]
        
        # Compute gradients and descriptor
        gx = cv2.Sobel(patch, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(patch, cv2.CV_32F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        ori = (np.arctan2(gy, gx) * 180 / np.pi - angle) % 360
        
        descriptor = []
        cell_size = 4
        bins = 8
        
        for i in range(0, patch_size, cell_size):
            for j in range(0, patch_size, cell_size):
                cell_mag = mag[i:i+cell_size, j:j+cell_size]
                cell_ori = ori[i:i+cell_size, j:j+cell_size]
                
                hist = np.zeros(bins)
                for m in range(cell_mag.shape[0]):
                    for n in range(cell_mag.shape[1]):
                        bin_idx = int(cell_ori[m, n] * bins / 360.0) % bins
                        hist[bin_idx] += cell_mag[m, n]
                
                descriptor.extend(hist)
        
        descriptor = np.array(descriptor)
        descriptor = descriptor / (np.linalg.norm(descriptor) + 1e-7)
        descriptor = np.clip(descriptor, 0, 0.2)
        descriptor = descriptor / (np.linalg.norm(descriptor) + 1e-7)
        
        return descriptor
    
    def detect_and_compute(self, image):
        """Main SIFT pipeline"""
        image = cv2.resize(image, (256, 256))
        D = self.build_dog_pyramid(image)
        
        keypoints = []
        H, W, S = D.shape
        
        for s in range(1, S-1):
            for x in range(1, H-1):
                for y in range(1, W-1):
                    if self.is_extremum(D, x, y, s):
                        sigma = self.sigma * (np.sqrt(2) ** s)
                        blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=sigma)
                        angle = self.assign_orientation(blurred, x, y)
                        descriptor = self.compute_descriptor(blurred, x, y, angle)
                        
                        keypoints.append({
                            'x': x, 'y': y, 'scale': s, 'angle': angle,
                            'descriptor': descriptor
                        })
        
        return keypoints

if __name__ == "__main__":
    # Test both algorithms
    img = cv2.imread("../cat.png", cv2.IMREAD_GRAYSCALE)
    if img is None:
        img = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    
    # Test SIFT
    sift = FromScratchSIFT()
    sift_features = sift.detect_and_compute(img)
    print(f"SIFT detected {len(sift_features)} keypoints")
