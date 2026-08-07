import os
import sys
import torch
import torch.nn.functional as F
import numpy as np
from typing import List
from PIL import Image

# Thêm đường dẫn tới source code gốc của CLIP4Cir vào sys.path để import dễ dàng
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIP4CIR_SRC = os.path.join(CURRENT_DIR, "../../third_party/CLIP4Cir/src")
sys.path.append(CLIP4CIR_SRC)

try:
    import clip
except ImportError:
    print("Vui lòng cài đặt CLIP: pip install git+https://github.com/openai/CLIP.git")
    raise

from combiner import Combiner
from .base_adapter import BaseAdapter

class CLIP4CirAdapter(BaseAdapter):
    def __init__(self, clip_model_name: str, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        super().__init__(model_name=f"clip4cir_{clip_model_name.replace('/', '')}", device=device)
        self.clip_model_name = clip_model_name
        self.combiner = None

    def load_model(self, clip_checkpoint_path: str = None, combiner_checkpoint_path: str = None):
        """
        Tải mô hình CLIP đã fine-tune và mô hình Combiner.
        :param clip_checkpoint_path: Đường dẫn tới file weights của CLIP (vd: cirr_clip_RN50x4_fullft.pt)
        :param combiner_checkpoint_path: Đường dẫn tới file weights của Combiner (vd: cirr_comb_RN50x4_fullft.pt)
        """
        from data_utils import targetpad_transform
        
        print(f"Loading CLIP model {self.clip_model_name}...")
        self.model, _ = clip.load(self.clip_model_name, device=self.device, jit=False)
        # Bắt buộc sử dụng TargetPad vì mô hình CLIP4Cir được fine-tune với phép biến đổi này
        self.preprocess = targetpad_transform(target_ratio=1.25, dim=self.model.visual.input_resolution)
        self.model.eval()

        if clip_checkpoint_path:
            print(f"Loading Fine-tuned CLIP weights from {clip_checkpoint_path}...")
            # Load the state dict and account for potential DataParallel prefix "module."
            checkpoint = torch.load(clip_checkpoint_path, map_location=self.device)
            state_dict = checkpoint["CLIP"] if "CLIP" in checkpoint else checkpoint
            
            if next(iter(state_dict.keys())).startswith("module."):
                state_dict = {k[len("module."):]: v for k, v in state_dict.items()}
            self.model.load_state_dict(state_dict)

        feature_dim = self.model.visual.output_dim
        
        # Khởi tạo Combiner network theo thông số mặc định của CLIP4Cir
        projection_dim = 2560
        hidden_dim = 5120
        self.combiner = Combiner(clip_feature_dim=feature_dim, projection_dim=projection_dim, hidden_dim=hidden_dim).to(self.device)
        self.combiner.eval()

        if combiner_checkpoint_path:
            print(f"Loading Combiner weights from {combiner_checkpoint_path}...")
            comb_ckpt = torch.load(combiner_checkpoint_path, map_location=self.device)
            comb_state_dict = comb_ckpt["Combiner"] if "Combiner" in comb_ckpt else comb_ckpt
            self.combiner.load_state_dict(comb_state_dict)

        print("[OK] CLIP4Cir Adapter loaded successfully!")

    def extract_image_features(self, image_list: List[Image.Image]) -> np.ndarray:
        """
        Trích xuất đặc trưng ảnh tham chiếu (Reference/Gallery Images)
        """
        if not image_list:
            return np.array([])
            
        import numpy as np
        
        # Tiền xử lý ảnh
        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(processed_images)
            # CLIP4Cir khuyến cáo luôn L2-normalize các vector trước khi tính cosine
            image_features = F.normalize(image_features, dim=-1)
            
        return image_features.cpu().numpy().astype(np.float32)

    def extract_text_features(self, text_list: List[str]) -> np.ndarray:
        """
        Trích xuất đặc trưng văn bản thuần túy (Chỉ dùng nội bộ hoặc debug)
        """
        if not text_list:
            return np.array([])
            
        import numpy as np
        
        text_tokens = clip.tokenize(text_list, context_length=77, truncate=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_tokens)
            text_features = F.normalize(text_features, dim=-1)
            
        return text_features.cpu().numpy().astype(np.float32)

    def extract_query_features(self, image_list: List[Image.Image], text_list: List[str]) -> np.ndarray:
        """
        Trích xuất đặc trưng Truy vấn (Image + Text) bằng Combiner.
        CLIP4Cir kết hợp hình ảnh tham chiếu và văn bản điều chỉnh để tạo ra vector truy vấn cuối cùng.
        """
        import numpy as np
        
        assert len(image_list) == len(text_list), "Số lượng ảnh và text phải bằng nhau!"
        
        # 1. Trích xuất đặc trưng ảnh riêng lẻ
        processed_images = torch.stack([self.preprocess(img) for img in image_list]).to(self.device)
        text_tokens = clip.tokenize(text_list, context_length=77, truncate=True).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(processed_images)
            text_features = self.model.encode_text(text_tokens)

            # QUAN TRỌNG: Mạng Combiner của CLIP4Cir được huấn luyện và đánh giá trên 
            # vector thô (unnormalized) của cả ẢNH và TEXT (xem combiner_train.py và validate.py).
            # Việc normalize image_features ở đây sẽ phá hỏng độ lớn (magnitude) gốc 
            # khiến tỷ lệ cổng residual bên trong Combiner bị sai lệch nghiêm trọng.
            # (Hàm combine_features bên trong Combiner sẽ tự động L2-normalize đầu ra cuối cùng)
            image_features = image_features.float()
            text_features = text_features.float()

            # 2. Dùng Combiner network để dung hợp 2 đặc trưng
            query_features = self.combiner.combine_features(image_features, text_features)
            
            # (Hàm combine_features bên trong lớp Combiner đã gọi F.normalize ở đầu ra rồi)
            
        return query_features.cpu().numpy().astype(np.float32)
