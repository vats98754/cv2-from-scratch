import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class FromScratchHOG:
    def __init__(self, cell_size=8, block_size=2, num_bins=9):
        self.cell_size = cell_size
        self.block_size = block_size
        self.num_bins = num_bins
        self.scaler = StandardScaler()
        self.classifier = LinearSVC()
    
    def compute_hog(self, img):
        gx = cv2.Sobel(img, ddepth=cv2.CV_32F, dx=1, dy=0)
        gy = cv2.Sobel(img, ddepth=cv2.CV_32F, dx=0, dy=1)

        magnitude = np.sqrt(gx**2 + gy**2)
        angle = np.rad2deg(np.atan2(gy, gx)) % 180
        bin_partition_size = 180 / self.num_bins

        H, W = img.shape
        n_cells_x = W // self.cell_size
        n_cells_y = H // self.cell_size
        
        hist = np.zeros((n_cells_y, n_cells_x, self.num_bins))

        for i in range(n_cells_y):
            for j in range(n_cells_x):
                mag = magnitude[i*self.cell_size:(i+1)*self.cell_size, 
                               j*self.cell_size:(j+1)*self.cell_size]
                ang = angle[i*self.cell_size:(i+1)*self.cell_size, 
                           j*self.cell_size:(j+1)*self.cell_size]

                for m in range(self.cell_size):
                    for n in range(self.cell_size):
                        bin_idx = int(ang[m, n] / bin_partition_size)
                        hist[i, j, bin_idx] += mag[m, n]

        blocks = []
        for i in range(n_cells_y - self.block_size + 1):
            for j in range(n_cells_x - self.block_size + 1):
                block = hist[i:i+self.block_size, j:j+self.block_size, :].flatten()
                norm = np.linalg.norm(block) + 1e-6
                blocks.append(block / norm)

        return np.concatenate(blocks)
    
    def load_dataset(self, dataset_path, standard_size=(256, 256)):
        images_0 = []
        images_1 = []
        
        for label in ["0", "1"]:
            folder_path = os.path.join(dataset_path, label)
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, standard_size)
                if label == "0":
                    images_0.append(img)
                else:
                    images_1.append(img)
        
        data = [(self.compute_hog(img), 0) for img in images_0] + \
               [(self.compute_hog(img), 1) for img in images_1]
        
        X = np.array([x for x, _ in data])
        y = np.array([y for _, y in data])
        
        return X, y
    
    def train_classifier(self, X, y):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        X_train = self.scaler.fit_transform(X_train)
        X_test = self.scaler.transform(X_test)
        
        self.classifier.fit(X_train, y_train)
        
        y_test_pred = self.classifier.predict(X_test)
        print("Test accuracy:", accuracy_score(y_test, y_test_pred))
        
        return X_test, y_test
    
    def plot_det_curve(self, X_test, y_test):
        scores = self.classifier.decision_function(X_test)
        labels = y_test
        
        sorted_idx = np.argsort(-scores)
        scores = scores[sorted_idx]
        labels = labels[sorted_idx]
        
        total_neg = np.sum(labels == 0)
        miss_rates = []
        fppw = []
        
        tp = 0
        fp = 0
        fn = np.sum(labels == 1)
        
        for i in range(len(scores)):
            if labels[i] == 1:
                tp += 1
                fn -= 1
            else:
                fp += 1
            
            miss_rate = fn / (tp + fn + 1e-9)
            fppw_val = fp / (total_neg + 1e-9)
            
            miss_rates.append(miss_rate)
            fppw.append(fppw_val)
        
        plt.figure(figsize=(6, 5))
        plt.loglog(fppw, miss_rates, label="HOG Detector")
        plt.xlabel("False Positives Per Window (FPPW)")
        plt.ylabel("Miss Rate")
        plt.grid(True, which="both", linestyle="--")
        plt.legend()
        plt.title("DET Curve")
        plt.show()

if __name__ == "__main__":
    # Initialize HOG detector
    hog = FromScratchHOG(cell_size=8, block_size=2, num_bins=9)
    
    # Load dataset and train
    dataset_path = "/Users/anvay-coder/Downloads/human-detection-dataset/"
    X, y = hog.load_dataset(dataset_path)
    X_test, y_test = hog.train_classifier(X, y)
    
    # Plot DET curve
    hog.plot_det_curve(X_test, y_test)
