import os
import numpy as np
import torch

class BaseAdapter:
    def __init__(self, model_name: str, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.preprocess = None
        
    def load_model(self):
        """Tải weights của model. Cần được implement bởi class con."""
        raise NotImplementedError("Subclasses must implement load_model method")

    def extract_image_features(self, image_list: list) -> np.ndarray:
        """Trích xuất đặc trưng ảnh. Đầu ra phải là numpy array float32 shape (N, D)"""
        raise NotImplementedError("Subclasses must implement extract_image_features method")
        
    def extract_text_features(self, text_list: list) -> np.ndarray:
        """Trích xuất đặc trưng văn bản. Đầu ra phải là numpy array float32 shape (N, D)"""
        raise NotImplementedError("Subclasses must implement extract_text_features method")

    def extract_query_features(self, image_list: list, text_list: list) -> np.ndarray:
        """Trích xuất đặc trưng Truy vấn (Image + Text modifier). Đầu ra phải là numpy array float32 shape (N, D)"""
        raise NotImplementedError("Subclasses must implement extract_query_features method")

    def save_embeddings(self, features: np.ndarray, save_path: str):
        """Lưu đặc trưng thành file .npy với định dạng float32 chuẩn cho FAISS"""
        if not isinstance(features, np.ndarray):
            features = features.cpu().numpy() if torch.is_tensor(features) else np.array(features)
        
        # Bắt buộc ép kiểu về float32 để FAISS có thể đọc tối ưu
        features = features.astype(np.float32)
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        np.save(save_path, features)
        print(f"Saved {features.shape[0]} vectors (dim={features.shape[1]}) to {save_path}")
