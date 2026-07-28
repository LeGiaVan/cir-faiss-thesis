import os
import sys
import argparse
import numpy as np
import torch
import gc
from torch.utils.data import DataLoader

# Fix Unicode print on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Thêm đường dẫn để import các module trong src/
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from extractors.clip4cir_adapter import CLIP4CirAdapter
from extractors.searle_adapter import SearleAdapter
from extractors.pic2word_adapter import Pic2WordAdapter
from data.generic_dataloader import GenericGalleryDataset
from tqdm import tqdm

def pil_collate_fn(batch):
    images = [item[0] for item in batch]
    names = [item[1] for item in batch]
    return images, names

def get_adapter(model_name: str, dataset: str):
    if model_name == "clip4cir":
        adapter = CLIP4CirAdapter(clip_model_name="RN50x4")
        # Checkpoint CLIP4Cir PHẢI khớp đúng dataset đang trích xuất - đây là bug đã sửa
        # (trước đây hard-code luôn checkpoint FashionIQ kể cả khi chạy trên CIRR/CIRCO).
        if dataset == "fashioniq":
            base_ckpt_dir = "checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft"
            clip_ckpt = os.path.join(base_ckpt_dir, "fiq_clip_RN50x4_fullft.pt")
            comb_ckpt = os.path.join(base_ckpt_dir, "fiq_comb_RN50x4_fullft.pt")
        elif dataset == "cirr":
            base_ckpt_dir = "checkpoints/CLIP4Cir/CIRR/RN50x4_fullft"
            clip_ckpt = os.path.join(base_ckpt_dir, "cirr_clip_RN50x4_fullft.pt")
            comb_ckpt = os.path.join(base_ckpt_dir, "cirr_comb_RN50x4_fullft.pt")
        elif dataset == "circo":
            raise ValueError(
                "CLIP4Cir không có checkpoint chính chủ train trên CIRCO (paper gốc chỉ công bố "
                "kết quả trên FashionIQ và CIRR). Theo quyết định học thuật trong "
                "AUDIT_AND_REVISED_PLAN.md, KHÔNG chạy CLIP4Cir trên CIRCO trong bảng so sánh chính "
                "để tránh so sánh không công bằng (supervised checkpoint ngoài miền dữ liệu)."
            )
        else:
            raise ValueError(f"Unknown dataset for clip4cir: {dataset}")

        if os.path.exists(clip_ckpt) and os.path.exists(comb_ckpt):
            adapter.load_model(clip_checkpoint_path=clip_ckpt, combiner_checkpoint_path=comb_ckpt)
        else:
            print(f"[CẢNH BÁO] Không tìm thấy checkpoints CLIP4Cir cho {dataset} ({clip_ckpt}), sẽ dùng pre-trained trắng.")
            adapter.load_model()
        return adapter, 640

    elif model_name == "searle":
        adapter = SearleAdapter()
        adapter.load_model()
        return adapter, 512

    elif model_name == "pic2word":
        adapter = Pic2WordAdapter()
        adapter.load_model()
        return adapter, 768

    else:
        raise ValueError(f"Unknown model: {model_name}")

def main():
    parser = argparse.ArgumentParser(description="Trích xuất đặc trưng hàng loạt")
    parser.add_argument("--model", type=str, required=True, choices=["clip4cir", "searle", "pic2word"], help="Tên mô hình")
    parser.add_argument("--dataset", type=str, required=True, choices=["fashioniq", "circo", "cirr"], help="Tập dữ liệu")
    parser.add_argument("--category", type=str, default=None, choices=["dress", "shirt", "toptee"],
                         help="BẮT BUỘC khi --dataset fashioniq. Gallery FashionIQ phải tách riêng theo category.")
    parser.add_argument("--batch-size", type=int, default=128, help="Kích thước batch")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số ảnh (Dùng để test)")

    args = parser.parse_args()

    if args.dataset == "fashioniq" and args.category is None:
        parser.error("--category là bắt buộc khi --dataset fashioniq (dress|shirt|toptee).")

    tag = f"{args.dataset}_{args.category}" if args.category else args.dataset
    print(f"=== PIPELINE TRÍCH XUẤT ĐẶC TRƯNG TỰ ĐỘNG: {args.model.upper()} trên {tag.upper()} ===")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "embeddings", args.model)
    suffix = f"_{args.limit}" if args.limit else ""
    out_feat_path = os.path.join(out_dir, f"{tag}_gallery{suffix}.npy")
    out_name_path = os.path.join(out_dir, f"{tag}_names{suffix}.npy")

    if os.path.exists(out_feat_path) and os.path.exists(out_name_path):
        print(f"[SKIP] Đặc trưng cho {args.model} trên {tag} đã tồn tại ở {out_feat_path}. Bỏ qua trích xuất!")
        sys.exit(0)

    # 1. Khởi tạo Adapter (checkpoint được chọn đúng theo args.dataset)
    adapter, expected_dim = get_adapter(args.model, args.dataset)

    # 2. Khởi tạo Dataset (đúng phạm vi split/category chính thức, xem generic_dataloader.py)
    dataset = GenericGalleryDataset(dataset_name=args.dataset, limit=args.limit, category=args.category)
    if len(dataset) == 0:
        print(f"[LỖI] Không tìm thấy ảnh nào cho {args.dataset}")
        sys.exit(1)

    # 3. Khởi tạo DataLoader
    # pin_memory=True giúp transfer data sang GPU nhanh hơn, tránh nghẽn I/O
    dataloader = DataLoader(
        dataset, 
        batch_size=args.batch_size, 
        shuffle=False, 
        num_workers=4,
        pin_memory=True if torch.cuda.is_available() else False,
        collate_fn=pil_collate_fn
    )
    
    # 4. Trích xuất
    all_features = []
    all_names = []
    
    print("Đang tiến hành trích xuất...")
    for images, names in tqdm(dataloader, desc=f"Extracting {args.dataset}"):
        with torch.no_grad():
            features = adapter.extract_image_features(images)
            
        all_features.append(features)
        all_names.extend(names)
        
        # Chống OOM: Xóa cache thủ công sau mỗi batch nếu RAM/VRAM yếu
        del images
        del features
        
    print("\nĐang nối các vector thành ma trận (Quá trình này tốn RAM hệ thống)...")
    final_features = np.vstack(all_features)
    final_names = np.array(all_names)
    
    # Dọn dẹp RAM triệt để
    del all_features
    gc.collect()
    torch.cuda.empty_cache()
    
    print(f"[HOÀN TẤT] Đã trích xuất {final_features.shape[0]} vector đặc trưng.")
    print(f"Shape: {final_features.shape} - Dtype: {final_features.dtype}")
    
    assert final_features.shape[1] == expected_dim, f"Shape không chuẩn. Chờ đợi {expected_dim}, nhận được {final_features.shape[1]}"
    
    # 5. Lưu ra ổ cứng
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "embeddings", args.model)
    os.makedirs(out_dir, exist_ok=True)

    print("Đang lưu ra ổ cứng (Vui lòng không tắt máy)...")
    np.save(out_feat_path, final_features)
    np.save(out_name_path, final_names)
    
    print(f"\n[THÀNH CÔNG] File Numpy lưu tại: {out_feat_path}")

if __name__ == "__main__":
    main()
