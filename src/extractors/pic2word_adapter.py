import os
import sys
import torch
import torch.nn.functional as F
import numpy as np
from typing import List
from PIL import Image

# Add Pic2Word source code to path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PIC2WORD_SRC = os.path.join(CURRENT_DIR, "../../third_party/composed_image_retrieval")
sys.path.append(PIC2WORD_SRC)

try:
    from model.clip import load as load_clip, tokenize
    from model.model import IM2TEXT
    from third_party.open_clip.clip import _transform
except ImportError as e:
    print(f"Error loading Pic2Word dependencies: {e}")
    raise

from .base_adapter import BaseAdapter

class Pic2WordAdapter(BaseAdapter):
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        # The checkpoint pic2word_vit_l_14.pt means it's based on ViT-L/14
        super().__init__(model_name="pic2word_vit_l_14", device=device)
        self.clip_model = None
        self.img2text = None

    def load_model(self, checkpoint_path: str = None):
        """
        Tải mô hình CLIP (ViT-L/14) và mạng MLP IM2TEXT
        """
        if not checkpoint_path:
            checkpoint_path = os.path.join(CURRENT_DIR, "../../checkpoints/pic2word_vit_l_14.pt")
            
        print(f"Loading Pic2Word model from {checkpoint_path} on {self.device}...")
        
        # 1. Khởi tạo backbone CLIP ViT-L/14
        self.clip_model, _, self.preprocess = load_clip("ViT-L/14", jit=False)
        
        # 2. Khởi tạo mạng IM2TEXT (MLP)
        self.img2text = IM2TEXT(
            embed_dim=self.clip_model.embed_dim, 
            middle_dim=512, # default in Pic2Word
            output_dim=self.clip_model.token_embedding.weight.shape[1],
            n_layer=2       # default in Pic2Word
        )
        
        # 3. Load weights
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        sd = checkpoint["state_dict"]
        sd_img2text = checkpoint["state_dict_img2text"]
        
        # Xử lý prefix 'module.' nếu checkpoint được train bằng DataParallel
        if next(iter(sd.items()))[0].startswith('module.'):
            sd = {k[len('module.'):]: v for k, v in sd.items()}
        if next(iter(sd_img2text.items()))[0].startswith('module.'):
            sd_img2text = {k[len('module.'):]: v for k, v in sd_img2text.items()}
            
        self.clip_model.load_state_dict(sd)
        self.img2text.load_state_dict(sd_img2text)
        
        self.clip_model = self.clip_model.float().to(self.device).eval().requires_grad_(False)
        self.img2text = self.img2text.float().to(self.device).eval().requires_grad_(False)
        
        print("[OK] Pic2Word Adapter loaded successfully!")

    def extract_image_features(self, image_list: List[Image.Image]) -> np.ndarray:
        """
        Trích xuất đặc trưng ảnh tham chiếu (Gallery Images)
        Đầu ra là numpy array L2-normalized float32
        """
        if not image_list:
            return np.array([])
            
        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.encode_image(processed_images)
            # FAISS yêu cầu chuẩn hóa L2 để Inner Product thành Cosine Similarity
            image_features = F.normalize(image_features, p=2, dim=-1)
            
        return image_features.cpu().numpy().astype(np.float32)

    def extract_text_features(self, text_list: List[str]) -> np.ndarray:
        if not text_list:
            return np.array([])
            
        text_tokens = tokenize(text_list).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.encode_text(text_tokens)
            text_features = F.normalize(text_features, p=2, dim=-1)
            
        return text_features.cpu().numpy().astype(np.float32)

    def extract_query_features(self, image_list: List[Image.Image], text_list: List[str]) -> np.ndarray:
        """
        Trích xuất đặc trưng Truy vấn gồm (Image + Text).
        Pic2Word thay thế token '*' trong text bằng pseudo-token ảnh ánh xạ qua IM2TEXT.
        """
        assert len(image_list) == len(text_list), "Số lượng ảnh và text phải bằng nhau!"
        if not image_list:
            return np.array([])

        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        
        # Thay thế target image = dummy token '*' trong câu text
        # Vd: "a photo of * that change color to blue"
        input_captions = [f"a photo of * that {caption}" for caption in text_list]
        text_tokens = tokenize(input_captions).to(self.device)
        id_split = tokenize(["*"])[0][1] # Lấy ID của ký tự '*' để model biết chỗ mà chèn vector vào
        
        with torch.no_grad():
            # 1. Trích xuất visual token từ ảnh tham chiếu
            img_feature = self.clip_model.encode_image(processed_images)
            
            # 2. Ánh xạ visual token sang không gian chữ bằng IM2TEXT
            query_img_feature = self.img2text(img_feature)
            
            # 3. Kết hợp pseudo-word vào câu text
            # Dùng encode_text_img_retrieval (repeat=False) - đúng theo eval_utils.py gốc cho
            # trường hợp N ảnh tham chiếu + N câu độc lập trong cùng batch. encode_text_img_vis
            # chỉ đúng khi batch_size=1 (không index theo batch), dùng nhầm sẽ crash/sai với batch>1.
            query_features = self.clip_model.encode_text_img_retrieval(
                text_tokens,
                query_img_feature,
                split_ind=id_split,
                repeat=False
            )
            
            # 4. Chuẩn hóa L2
            query_features = F.normalize(query_features, p=2, dim=-1)
            
        return query_features.cpu().numpy().astype(np.float32)
