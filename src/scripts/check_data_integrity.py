import os
import sys
import argparse
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_integrity(file_path: str, expected_dim: int = None):
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
        
    try:
        logging.info(f"Checking {file_path}...")
        data = np.load(file_path)
        
        # 1. Type Check (Must be float32 for FAISS)
        if data.dtype != np.float32:
            logging.error(f"Data type mismatch. Expected float32, got {data.dtype}")
            return False
            
        # 2. NaN/Inf Check (Causes FAISS to crash)
        if np.isnan(data).any():
            logging.error("Data contains NaN values!")
            return False
            
        if np.isinf(data).any():
            logging.error("Data contains Infinity values!")
            return False
            
        # 3. Dimension Check
        if expected_dim is not None and data.shape[1] != expected_dim:
            logging.error(f"Dimension mismatch. Expected {expected_dim}, got {data.shape[1]}")
            return False
            
        # 4. L2 Normalization Check (Norm should be close to 1)
        # We check a random sample of 100 vectors to save time
        sample_size = min(100, data.shape[0])
        sample = data[np.random.choice(data.shape[0], sample_size, replace=False)]
        norms = np.linalg.norm(sample, axis=1)
        if not np.allclose(norms, 1.0, atol=1e-3):
            logging.error("Vectors are NOT L2-normalized! FAISS Inner Product will be wrong.")
            return False
            
        logging.info(f"[PASS] {file_path} (Shape: {data.shape}, Size: {data.nbytes / (1024*1024):.2f} MB)")
        return True
        
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check integrity of extracted .npy vectors")
    parser.add_argument("--file", type=str, required=True, help="Path to .npy file")
    parser.add_argument("--dim", type=int, default=None, help="Expected embedding dimension")
    
    args = parser.parse_args()
    
    success = check_integrity(args.file, args.dim)
    sys.exit(0 if success else 1)
