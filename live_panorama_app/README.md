# Live Panorama Stitching App

This directory contains a live panorama stitching application that demonstrates the concepts learned from SIFT and ORB feature detection.

## Files

1. **live_panorama_stitcher.py** - Main live panorama app using OpenCV's optimized ORB
2. **fromscratch_panorama_stitcher.py** - Demo using our from-scratch ORB implementation
3. **requirements.txt** - Required packages

## Features

- Real-time camera feed
- Live panorama stitching
- Interactive controls
- Save final panorama

## Usage

### Standard Version (Recommended)
```bash
python live_panorama_stitcher.py
```

### From-Scratch Version (Educational)
```bash
python fromscratch_panorama_stitcher.py
```

## Controls

- **SPACE**: Capture current frame and add to panorama
- **'r'**: Reset panorama and start over
- **'q'**: Quit application

## How It Works

1. **Feature Detection**: Uses ORB (Oriented FAST and Rotated BRIEF) to detect keypoints
2. **Feature Matching**: Matches features between consecutive frames using Hamming distance
3. **Homography Estimation**: Finds geometric transformation between images using RANSAC
4. **Image Warping**: Transforms and combines images into panorama
5. **Blending**: Simple overlay blending for seamless panorama

## Tips for Best Results

1. **Overlap**: Ensure 20-30% overlap between consecutive frames
2. **Slow Movement**: Move camera slowly and steadily
3. **Good Lighting**: Use well-lit environments for better feature detection
4. **Stable Camera**: Keep camera as stable as possible
5. **Feature-Rich Scenes**: Point camera at textured surfaces with distinct features

## Panorama Techniques Used

- **ORB Feature Detection**: Fast corner detection + binary descriptors
- **RANSAC Homography**: Robust estimation of geometric transformation
- **Perspective Warping**: Transform images to common coordinate system
- **Simple Blending**: Overlay images with basic blending

This application demonstrates practical computer vision concepts in real-time!
