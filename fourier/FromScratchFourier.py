import numpy as np
import cv2
import matplotlib.pyplot as plt

class FromScratchFourier:
    def __init__(self):
        pass
    
    def dft2d(self, img):
        """Discrete Fourier Transform in 2D - O(N^2 * M^2)"""
        M, N = img.shape
        freqs = np.zeros((M, N), dtype=np.complex128)
        for u in range(M):
            for v in range(N):
                sum = 0
                for x in range(M):
                    for y in range(N):
                        angle = -2j * np.pi * ((u * x / M) + (v * y / N))
                        sum += img[x, y] * np.exp(angle)
                freqs[u, v] = sum
        return freqs
    
    def fft1d(self, x):
        """Cooley-Tukey Fast Fourier Transform in 1D - O(N * log N)"""
        N = len(x)
        if N <= 1:
            return x
        
        even = self.fft1d(x[::2])
        odd = self.fft1d(x[1::2])

        X = [0] * N
        for k in range(N // 2):
            twiddle_factor = np.exp(-2j * np.pi * k / N)
            X[k] = even[k] + twiddle_factor * odd[k]
            X[k + N // 2] = even[k] - twiddle_factor * odd[k]

        return X
    
    def fft2d(self, img):
        """2D FFT by applying 1D FFT to rows then columns - O(MN * log MN)"""
        # Apply 1D FFT on rows
        fft_rows = [self.fft1d(row) for row in img]
        fft_rows = np.array(fft_rows).T  # transpose

        # Apply 1D FFT on columns
        fft_cols = [self.fft1d(col) for col in fft_rows]
        return np.array(fft_cols).T  # transpose
    
    def low_pass_filter(self, img, cutoff=30):
        """Apply low-pass filter to keep only low frequencies"""
        H, W = img.shape
        Y, X = np.ogrid[:H, :W]
        cy, cx = H // 2, W // 2
        dist = np.sqrt((Y - cy)**2 + (X - cx)**2)
        mask = dist < cutoff
        
        F = np.fft.fft2(img)
        F_shifted = np.fft.fftshift(F)
        F_filtered = F_shifted * mask
        return np.fft.ifft2(np.fft.ifftshift(F_filtered)).real
    
    def high_pass_filter(self, img, cutoff=30):
        """Apply high-pass filter to keep only high frequencies"""
        H, W = img.shape
        Y, X = np.ogrid[:H, :W]
        cy, cx = H // 2, W // 2
        dist = np.sqrt((Y - cy)**2 + (X - cx)**2)
        mask = dist >= cutoff
        
        F = np.fft.fft2(img)
        F_shifted = np.fft.fftshift(F)
        F_filtered = F_shifted * mask
        return np.fft.ifft2(np.fft.ifftshift(F_filtered)).real
    
    def band_pass_filter(self, img, low=30, high=70):
        """Apply band-pass filter to keep only mid-range frequencies"""
        H, W = img.shape
        Y, X = np.ogrid[:H, :W]
        cy, cx = H // 2, W // 2
        dist = np.sqrt((Y - cy)**2 + (X - cx)**2)
        mask = (dist > low) & (dist < high)
        
        F = np.fft.fft2(img)
        F_shifted = np.fft.fftshift(F)
        F_filtered = F_shifted * mask
        return np.fft.ifft2(np.fft.ifftshift(F_filtered)).real
    
    def show_magnitude_spectrum(self, img, title="Magnitude Spectrum"):
        """Display magnitude spectrum of image"""
        F = np.fft.fft2(img)
        F_shifted = np.fft.fftshift(F)
        magnitude = np.log(np.abs(F_shifted) + 1)
        
        plt.figure(figsize=(8, 6))
        plt.imshow(magnitude, cmap='gray')
        plt.title(title)
        plt.colorbar()
        plt.show()

if __name__ == "__main__":
    # Test the Fourier transform implementations
    fourier = FromScratchFourier()
    
    # Load test image
    img = cv2.imread("../cat.png", cv2.IMREAD_GRAYSCALE)
    if img is None:
        # Create dummy image if file not found
        img = np.random.randint(0, 255, (64, 64), dtype=np.uint8)
    
    print("Testing Fourier Transform implementations...")
    
    # Test DFT (slow for large images)
    if img.shape[0] <= 64 and img.shape[1] <= 64:
        print("Computing DFT (slow)...")
        dft_result = fourier.dft2d(img)
        print(f"DFT result shape: {dft_result.shape}")
    
    # Test FFT
    print("Computing FFT...")
    fft_result = fourier.fft2d(img)
    print(f"FFT result shape: {fft_result.shape}")
    
    # Show magnitude spectrum
    fourier.show_magnitude_spectrum(img, "Original Image Spectrum")
    
    # Test filters
    print("Applying filters...")
    low_passed = fourier.low_pass_filter(img, cutoff=30)
    high_passed = fourier.high_pass_filter(img, cutoff=30)
    band_passed = fourier.band_pass_filter(img, low=30, high=70)
    
    # Display results
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    axes[0, 0].imshow(img, cmap='gray')
    axes[0, 0].set_title('Original')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(low_passed, cmap='gray')
    axes[0, 1].set_title('Low-pass Filtered')
    axes[0, 1].axis('off')
    
    axes[1, 0].imshow(high_passed, cmap='gray')
    axes[1, 0].set_title('High-pass Filtered')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(band_passed, cmap='gray')
    axes[1, 1].set_title('Band-pass Filtered')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.show()