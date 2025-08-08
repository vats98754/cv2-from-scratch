import numpy as np
import cv2

class SimplePanoramaStitcher:
    def __init__(self):
        self.orb = cv2.ORB_create()
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.panorama = None
        self.is_first_frame = True
    
    def detect_and_match(self, img1, img2):
        """Detect keypoints and match between two images"""
        kp1, des1 = self.orb.detectAndCompute(img1, None)
        kp2, des2 = self.orb.detectAndCompute(img2, None)
        
        if des1 is None or des2 is None:
            return None, None, None
        
        matches = self.matcher.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)
        
        return kp1, kp2, matches
    
    def find_homography(self, kp1, kp2, matches, min_matches=10):
        """Find homography matrix using RANSAC"""
        if len(matches) < min_matches:
            return None
        
        # Extract matched keypoints
        src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        
        # Find homography
        H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
        return H
    
    def stitch_images(self, img1, img2):
        """Stitch two images together"""
        # Detect and match features
        kp1, kp2, matches = self.detect_and_match(img1, img2)
        
        if matches is None or len(matches) < 10:
            return img2  # Return current frame if no good matches
        
        # Find homography
        H = self.find_homography(kp1, kp2, matches)
        
        if H is None:
            return img2
        
        # Get image dimensions
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # Transform corners of img1
        corners1 = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]]).reshape(-1, 1, 2)
        corners1_transformed = cv2.perspectiveTransform(corners1, H)
        
        # Find bounding box for the result
        all_corners = np.concatenate([corners1_transformed, 
                                     np.float32([[0, 0], [w2, 0], [w2, h2], [0, h2]]).reshape(-1, 1, 2)])
        
        min_x = int(np.min(all_corners[:, 0, 0]))
        max_x = int(np.max(all_corners[:, 0, 0]))
        min_y = int(np.min(all_corners[:, 0, 1]))
        max_y = int(np.max(all_corners[:, 0, 1]))
        
        # Adjust homography for translation
        translation = np.array([[1, 0, -min_x], [0, 1, -min_y], [0, 0, 1]])
        H_adjusted = translation @ H
        
        # Create result image
        result_width = max_x - min_x
        result_height = max_y - min_y
        
        # Warp img1
        warped1 = cv2.warpPerspective(img1, H_adjusted, (result_width, result_height))
        
        # Create result and place img2
        result = warped1.copy()
        img2_x = -min_x
        img2_y = -min_y
        
        if img2_x >= 0 and img2_y >= 0:
            result[img2_y:img2_y+h2, img2_x:img2_x+w2] = img2
        
        return result
    
    def add_frame(self, frame):
        """Add a new frame to the panorama"""
        if self.is_first_frame:
            self.panorama = frame.copy()
            self.is_first_frame = False
            return self.panorama
        
        # Stitch with existing panorama
        self.panorama = self.stitch_images(self.panorama, frame)
        return self.panorama

def main():
    """Main live panorama stitching application"""
    print("Live Panorama Stitcher")
    print("Controls:")
    print("- SPACE: Capture frame for panorama")
    print("- 'r': Reset panorama")
    print("- 'q': Quit")
    
    cap = cv2.VideoCapture(0)
    stitcher = SimplePanoramaStitcher()
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to grayscale for processing
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Display current frame
        cv2.imshow('Camera Feed (Press SPACE to add to panorama)', frame)
        
        # Display current panorama if it exists
        if stitcher.panorama is not None:
            # Resize panorama for display if too large
            pano_display = stitcher.panorama.copy()
            if pano_display.shape[1] > 1200:
                scale = 1200 / pano_display.shape[1]
                new_width = int(pano_display.shape[1] * scale)
                new_height = int(pano_display.shape[0] * scale)
                pano_display = cv2.resize(pano_display, (new_width, new_height))
            
            cv2.imshow('Panorama', pano_display)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(' '):  # Space key - capture frame
            print("Adding frame to panorama...")
            result = stitcher.add_frame(gray)
            print(f"Panorama size: {result.shape}")
        
        elif key == ord('r'):  # Reset panorama
            print("Resetting panorama...")
            stitcher.panorama = None
            stitcher.is_first_frame = True
            cv2.destroyWindow('Panorama')
        
        elif key == ord('q'):  # Quit
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Save final panorama if it exists
    if stitcher.panorama is not None:
        cv2.imwrite('final_panorama.jpg', stitcher.panorama)
        print("Final panorama saved as 'final_panorama.jpg'")

if __name__ == "__main__":
    main()
