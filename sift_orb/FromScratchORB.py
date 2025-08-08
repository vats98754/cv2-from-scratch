import numpy as np
import cv2
import matplotlib.pyplot as plt

class FromScratchORB:
    def __init__(self, brief_len=256, patch_size=31):
        self.brief_len = brief_len
        self.patch_size = patch_size
        self.pairs = self._generate_brief_pairs()
    
    def _generate_brief_pairs(self):
        """Generate random BRIEF test pairs"""
        n = self.brief_len
        r = self.patch_size // 2
        coords = np.random.randint(-r, r, size=(n, 2, 2))
        return coords
    
    def fast_keypoints(self, img, threshold=20, N=12):
        """FAST corner detection"""
        radius = 3
        circle_idx = [
            (0, -radius), (radius // 2, -radius), (radius, -radius // 2), (radius, 0),
            (radius, radius // 2), (radius // 2, radius), (0, radius), (-radius // 2, radius),
            (-radius, radius // 2), (-radius, 0), (-radius, -radius // 2), (-radius // 2, -radius)
        ]
        
        H, W = img.shape
        keypoints = []
        
        for y in range(radius, H - radius):
            for x in range(radius, W - radius):
                p = img[y, x]
                brighter = 0
                darker = 0
                for dx, dy in circle_idx:
                    val = img[y + dy, x + dx]
                    if val > p + threshold:
                        brighter += 1
                    elif val < p - threshold:
                        darker += 1
                if brighter >= N or darker >= N:
                    keypoints.append((x, y))
        
        return keypoints
    
    def compute_orientation(self, img, x, y):
        """Compute orientation using intensity centroid"""
        r = self.patch_size // 2
        x0, x1 = x - r, x + r + 1
        y0, y1 = y - r, y + r + 1
        
        if x0 < 0 or y0 < 0 or x1 > img.shape[1] or y1 > img.shape[0]:
            return None
        
        patch = img[y0:y1, x0:x1]
        cy, cx = np.mgrid[-r:r+1, -r:r+1]
        m10 = np.sum(cx * patch)
        m01 = np.sum(cy * patch)
        angle = np.arctan2(m01, m10)
        
        return angle
    
    def compute_brief_descriptor(self, img, x, y, angle):
        """Compute rotated BRIEF descriptor"""
        H, W = img.shape
        desc = []
        
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)
        
        for (p1, p2) in self.pairs:
            # Rotate points
            dx1 = int(round(cos_a * p1[0] - sin_a * p1[1]))
            dy1 = int(round(sin_a * p1[0] + cos_a * p1[1]))
            dx2 = int(round(cos_a * p2[0] - sin_a * p2[1]))
            dy2 = int(round(sin_a * p2[0] + cos_a * p2[1]))
            
            x1, y1 = x + dx1, y + dy1
            x2, y2 = x + dx2, y + dy2
            
            if not (0 <= x1 < W and 0 <= y1 < H and 0 <= x2 < W and 0 <= y2 < H):
                desc.append(0)
            else:
                desc.append(1 if img[y1, x1] < img[y2, x2] else 0)
        
        return np.array(desc, dtype=np.uint8)
    
    def detect_and_compute(self, img):
        """Main ORB pipeline"""
        img = cv2.GaussianBlur(img, (3, 3), 0)
        keypoints_xy = self.fast_keypoints(img)
        orb_features = []
        
        for (x, y) in keypoints_xy:
            angle = self.compute_orientation(img, x, y)
            if angle is None:
                continue
            desc = self.compute_brief_descriptor(img, x, y, angle)
            orb_features.append({
                'x': x, 'y': y, 'angle': angle, 'descriptor': desc
            })
        
        return orb_features

# Utility functions for matching
def hamming_distance(desc1, desc2):
    """Compute Hamming distance between binary descriptors"""
    return np.count_nonzero(desc1 != desc2)

def match_features(features1, features2, max_dist=30):
    """Match features between two images"""
    matches = []
    for i, f1 in enumerate(features1):
        best_match = None
        best_score = float('inf')
        for j, f2 in enumerate(features2):
            if 'descriptor' in f1 and 'descriptor' in f2:
                if len(f1['descriptor']) == len(f2['descriptor']):
                    d = hamming_distance(f1['descriptor'], f2['descriptor'])
                    if d < best_score:
                        best_score = d
                        best_match = (i, j)
        if best_score < max_dist:
            matches.append(best_match)
    return matches

if __name__ == "__main__":
    # Test both algorithms
    img = cv2.imread("../cat.png", cv2.IMREAD_GRAYSCALE)
    if img is None:
        img = np.random.randint(0, 255, (256, 256), dtype=np.uint8)
    
    # Test ORB
    orb = FromScratchORB()
    orb_features = orb.detect_and_compute(img)
    print(f"ORB detected {len(orb_features)} keypoints")
