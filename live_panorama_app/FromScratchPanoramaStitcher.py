import sys
import os

# Add the parent directory to path for importing sift_orb package
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sift_orb import FromScratchORB, match_features
import numpy as np
import cv2


class FromScratchPanoramaStitcher:
    def __init__(self):
        self.orb = FromScratchORB()
        self.panorama = None
        self.is_first_frame = True
    
    def simple_homography(self, matches, kp1, kp2):
        """Simple homography estimation using least squares"""
        if len(matches) < 4:
            return None
        
        # Get matched points
        src_pts = []
        dst_pts = []
        
        for i, j in matches[:20]:  # Use best 20 matches
            src_pts.append([kp1[i]['x'], kp1[i]['y']])
            dst_pts.append([kp2[j]['x'], kp2[j]['y']])
        
        src_pts = np.array(src_pts, dtype=np.float32)
        dst_pts = np.array(dst_pts, dtype=np.float32)
        
        # Use OpenCV's homography for simplicity
        if len(src_pts) >= 4:
            H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC)
            return H
        
        return None
    
    def stitch_images(self, img1, img2):
        """Stitch two images using from-scratch ORB"""
        # Detect features
        kp1 = self.orb.detect_and_compute(img1)
        kp2 = self.orb.detect_and_compute(img2)
        
        if len(kp1) < 10 or len(kp2) < 10:
            return img2
        
        # Match features
        matches = match_features(kp1, kp2, max_dist=40)
        
        if len(matches) < 4:
            return img2
        
        # Find homography
        H = self.simple_homography(matches, kp1, kp2)
        
        if H is None:
            return img2
        
        # Warp and combine images
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # Simple side-by-side stitching for demonstration
        result_width = w1 + w2
        result_height = max(h1, h2)
        result = np.zeros((result_height, result_width), dtype=np.uint8)
        
        # Place images side by side with some overlap
        overlap = min(w1 // 4, w2 // 4)
        result[:h1, :w1] = img1
        result[:h2, w1-overlap:w1-overlap+w2] = img2
        
        return result
    
    def add_frame(self, frame):
        """Add frame to panorama"""
        if self.is_first_frame:
            self.panorama = frame.copy()
            self.is_first_frame = False
            return self.panorama
        
        self.panorama = self.stitch_images(self.panorama, frame)
        return self.panorama

def main():
    """From-scratch panorama stitcher demo"""
    print("From-Scratch Panorama Stitcher")
    print("Using our own ORB implementation!")
    print("Controls:")
    print("- SPACE: Capture frame for panorama")
    print("- 'r': Reset panorama")
    print("- 'q': Quit")
    
    cap = cv2.VideoCapture(0)
    stitcher = FromScratchPanoramaStitcher()
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale and resize
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (320, 240))  # Smaller for faster processing
        
        # Display current frame
        cv2.imshow('Camera Feed', gray)
        
        # Display panorama
        if stitcher.panorama is not None:
            pano_display = stitcher.panorama.copy()
            if pano_display.shape[1] > 800:
                scale = 800 / pano_display.shape[1]
                new_width = int(pano_display.shape[1] * scale)
                new_height = int(pano_display.shape[0] * scale)
                pano_display = cv2.resize(pano_display, (new_width, new_height))
            
            cv2.imshow('From-Scratch Panorama', pano_display)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):
            print("Processing frame with from-scratch ORB...")
            result = stitcher.add_frame(gray)
            print(f"Panorama size: {result.shape}")
        
        elif key == ord('r'):
            print("Resetting panorama...")
            stitcher.panorama = None
            stitcher.is_first_frame = True
            cv2.destroyWindow('From-Scratch Panorama')
        
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if stitcher.panorama is not None:
        cv2.imwrite('fromscratch_panorama.jpg', stitcher.panorama)
        print("From-scratch panorama saved!")

if __name__ == "__main__":
    main()
