import os
import sys
import numpy as np
import torch

# Add root project dir to path so we can import src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.extractors.base_adapter import BaseAdapter

class DummyAdapter(BaseAdapter):
    def __init__(self, output_dim=512):
        super().__init__(model_name="dummy_model")
        self.output_dim = output_dim
        
    def load_model(self):
        print("[Dummy] Model weights loaded (fake).")
        
    def extract_image_features(self, image_list: list) -> np.ndarray:
        # Giả lập việc trích xuất đặc trưng của N bức ảnh thành mảng NxD
        N = len(image_list)
        # Sinh mảng random float 64bit để test ép kiểu về 32bit của BaseAdapter
        fake_features = np.random.rand(N, self.output_dim).astype(np.float64) 
        
        # Có thể giả vờ biến thành Pytorch Tensor để kiểm tra tính đa hình
        return torch.tensor(fake_features)

    def extract_text_features(self, text_list: list) -> np.ndarray:
        N = len(text_list)
        fake_features = np.random.rand(N, self.output_dim).astype(np.float64)
        return torch.tensor(fake_features)

def test_pipeline():
    print("=== STARTING TEST BASE ADAPTER ===")
    adapter = DummyAdapter(output_dim=512)
    adapter.load_model()
    
    # 1. Sinh 50 ảnh giả
    dummy_images = [np.zeros((224, 224, 3)) for _ in range(50)]
    print(f"Prepared {len(dummy_images)} fake images.")
    
    # 2. Chạy hàm trích xuất
    features = adapter.extract_image_features(dummy_images)
    
    # 3. Lưu xuống ổ cứng
    save_path = "data/embeddings/test_dummy_50.npy"
    adapter.save_embeddings(features, save_path)
    
    # 4. Kiểm tra lại từ ổ cứng
    loaded_features = np.load(save_path)
    
    shape = loaded_features.shape
    dtype = loaded_features.dtype
    
    print("\n=== ASSERTIONS RESULT ===")
    print(f"Shape: {shape}")
    print(f"Dtype: {dtype}")
    
    assert shape == (50, 512), f"ERROR: Expected shape (50, 512), but got {shape}"
    assert dtype == np.float32, f"ERROR: Expected dtype float32, but got {dtype}"
    
    print("[SUCCESS] Pipeline Adapter is working perfectly! Ready for FAISS.")

if __name__ == "__main__":
    test_pipeline()
