import os
import sys
import torch
import torch.nn.functional as F
import numpy as np
from typing import List
from PIL import Image

# Add SEARLE to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SEARLE_SRC = os.path.join(CURRENT_DIR, "../../third_party/SEARLE/src")
sys.path.append(SEARLE_SRC)

try:
    import clip
except ImportError:
    print("Vui lòng cài đặt CLIP: pip install git+https://github.com/openai/CLIP.git")
    raise

from .base_adapter import BaseAdapter
from encode_with_pseudo_tokens import encode_with_pseudo_tokens

class SearleAdapter(BaseAdapter):
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        super().__init__(model_name="searle_vitb32", device=device)
        self.phi = None
        self.clip_model = None

    def load_model(self):
        """
        Tải mô hình SEARLE và CLIP (ViT-B/32) thông qua torch.hub
        """
        print(f"Loading SEARLE model and CLIP ViT-B/32 on {self.device}...")
        
        # Phi is the textual inversion network
        self.phi, _ = torch.hub.load(
            repo_or_dir='miccunifi/SEARLE', 
            model='searle', 
            backbone='ViT-B/32',
            source='github',
            force_reload=False
        )
        
        # Tải mô hình CLIP tiêu chuẩn
        self.clip_model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
        self.phi = self.phi.to(self.device)
        self.phi.eval()
        self.phi.requires_grad_(False)
        
        self.clip_model = self.clip_model.float().eval().requires_grad_(False)
        self.clip_model = self.clip_model.to(self.device)

        print("[OK] SEARLE Adapter loaded successfully!")

    def extract_image_features(self, image_list: List[Image.Image]) -> np.ndarray:
        """
        Trích xuất đặc trưng ảnh tham chiếu (Gallery Images)
        Chú ý: FAISS gallery cho SEARLE chỉ dùng bộ tính năng hình ảnh của CLIP RN50x4
        """
        if not image_list:
            return np.array([])
            
        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.encode_image(processed_images)
            # L2 Normalize
            image_features = F.normalize(image_features, p=2, dim=-1)
            
        return image_features.cpu().numpy().astype(np.float32)

    def extract_text_features(self, text_list: List[str]) -> np.ndarray:
        """
        Trích xuất đặc trưng văn bản (Ít dùng trong Composed Retrieval)
        """
        if not text_list:
            return np.array([])
            
        text_tokens = clip.tokenize(text_list, context_length=77, truncate=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = F.normalize(text_features, p=2, dim=-1)
            
        return text_features.cpu().numpy().astype(np.float32)

    def extract_query_features(self, image_list: List[Image.Image], text_list: List[str]) -> np.ndarray:
        """
        Trích xuất đặc trưng Truy vấn (Image + Text) bằng Textual Inversion.
        SEARLE sẽ ánh xạ hình ảnh thành token $ và thay thế nó vào trong câu text.
        """
        assert len(image_list) == len(text_list), "Số lượng ảnh và text phải bằng nhau!"
        if not image_list:
            return np.array([])

        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        
        # Replace the target with the dummy token $ for SEARLE text template
        # Usually text_list contains modifier like "change color to blue"
        # We wrap it inside: "a photo of $ that change color to blue"
        input_captions = [f"a photo of $ that {caption}" for caption in text_list]
        tokenized_input_captions = clip.tokenize(input_captions, context_length=77, truncate=True).to(self.device)
        
        with torch.no_grad():
            # 1. Trích xuất pseudo-tokens (S*) từ reference images thông qua mạng Phi
            image_features = self.clip_model.encode_image(processed_images)
            pseudo_tokens = self.phi(image_features.float())
            
            # 2. Thay thế token '$' trong câu văn bằng pseudo-tokens và đưa qua CLIP text encoder
            # Shape of pseudo_tokens requires to be unsqueezed as expected by encode_with_pseudo_tokens
            # We reshape it implicitly by iterating or just passing it if encode_with_pseudo_tokens handles it.
            # encode_with_pseudo_tokens expects pseudo_tokens of shape [B, 1, D] if num_tokens=1
            # actually it expects [B, D] and unsqueezes inside if len(shape) == 2.
            query_features = encode_with_pseudo_tokens(
                self.clip_model, 
                tokenized_input_captions, 
                pseudo_tokens
            )
            
            # L2 Normalize
            query_features = F.normalize(query_features, p=2, dim=-1)
            
        return query_features.cpu().numpy().astype(np.float32)
