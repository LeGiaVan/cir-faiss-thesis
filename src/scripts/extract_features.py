import os
import sys
import numpy as np
import torch
from torch.utils.data import DataLoader

# Fix Unicode print on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from extractors.clip4cir_adapter import CLIP4CirAdapter
from data.generic_dataloader import GenericGalleryDataset
from tqdm import tqdm

def pil_collate_fn(batch):
    """
    Hàm gom nhóm (collate) tùy chỉnh cho DataLoader.
    Vì adapter nhận vào một danh sách (List) các PIL Image, ta không thể dùng hàm gom nhóm mặc định của PyTorch
    (mặc định sẽ cố gắng stack thành Tensor).
    """
    images = [item[0] for item in batch]
    names = [item[1] for item in batch]
    return images, names

def main():
    print("=== PIPELINE TRÍCH XUẤT ĐẶC TRƯNG TỰ ĐỘNG ===")
    
    # 1. Khởi tạo Adapter
    adapter = CLIP4CirAdapter(clip_model_name="RN50x4")
    
    # Load weights giả định người dùng đã tải thư mục RN50x4_fullft
    base_ckpt_dir = "checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft"
    clip_ckpt = os.path.join(base_ckpt_dir, "fiq_clip_RN50x4_fullft.pt")
    comb_ckpt = os.path.join(base_ckpt_dir, "fiq_comb_RN50x4_fullft.pt")
    
    if os.path.exists(clip_ckpt) and os.path.exists(comb_ckpt):
        adapter.load_model(clip_checkpoint_path=clip_ckpt, combiner_checkpoint_path=comb_ckpt)
    else:
        print(f"[CẢNH BÁO] Không tìm thấy checkpoints tại {base_ckpt_dir}.")
        print("Sẽ dùng mô hình CLIP trắng (chưa fine-tune) để chạy test pipeline.")
        adapter.load_model()
        
    # 2. Khởi tạo Dataset (Test Mode - Chỉ lấy 50 ảnh đầu tiên)
    dataset = GenericGalleryDataset(dataset_name="fashioniq", limit=50)
    
    if len(dataset) == 0:
        print("[LỖI] Không tìm thấy ảnh nào. Vui lòng kiểm tra thư mục data/raw/fashionIQ/images")
        return

    # 3. Khởi tạo Băng chuyền (DataLoader)
    batch_size = 16
    dataloader = DataLoader(
        dataset, 
        batch_size=batch_size, 
        shuffle=False, 
        num_workers=4 if sys.platform != 'win32' else 0, # Windows thường kén multiprocessing
        collate_fn=pil_collate_fn
    )
    
    # 4. Trích xuất
    all_features = []
    all_names = []
    
    print("Đang tiến hành trích xuất...")
    for images, names in tqdm(dataloader, desc="Extracting Gallery"):
        # Trích xuất 1 batch
        features = adapter.extract_image_features(images) # Trả về numpy array
        
        all_features.append(features)
        all_names.extend(names)
        
    # Gộp tất cả các mảng numpy nhỏ thành 1 mảng lớn
    final_features = np.vstack(all_features)
    final_names = np.array(all_names)
    
    print(f"\n[HOÀN TẤT] Đã trích xuất {final_features.shape[0]} vector đặc trưng.")
    print(f"Shape: {final_features.shape} - Dtype: {final_features.dtype}")
    
    # Kiểm tra tính đúng đắn (Sanity check)
    assert final_features.shape == (50, 640), "Shape không chuẩn (50, 640) của RN50x4"
    assert final_features.dtype == np.float32, "Kiểu dữ liệu phải là float32 cho FAISS"
    
    # 5. Lưu ra ổ cứng
    out_feat_path = "data/embeddings/test_gallery_50.npy"
    out_name_path = "data/embeddings/test_gallery_names_50.npy"
    
    os.makedirs(os.path.dirname(out_feat_path), exist_ok=True)
    np.save(out_feat_path, final_features)
    np.save(out_name_path, final_names)
    
    print(f"\n[THÀNH CÔNG] File Numpy lưu tại: {out_feat_path}")
    print("PIPELINE SẴN SÀNG CHO ĐỢT RUN CHÍNH THỨC HÀNG TRĂM NGÀN ẢNH!")

if __name__ == "__main__":
    main()
