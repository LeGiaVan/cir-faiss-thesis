import os
import sys
import argparse
import pickle
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
from data.generic_query_dataloader import GenericQueryDataset
from tqdm import tqdm

def query_collate_fn(batch):
    images = [item[0] for item in batch]
    captions = [item[1] for item in batch]
    target_ids = [item[2] for item in batch]
    group_members = [item[3] for item in batch]
    return images, captions, target_ids, group_members

def get_adapter(model_name: str):
    if model_name == "clip4cir":
        adapter = CLIP4CirAdapter(clip_model_name="RN50x4")
        base_ckpt_dir = "checkpoints/CLIP4Cir/FashionIQ/RN50x4_fullft"
        clip_ckpt = os.path.join(base_ckpt_dir, "fiq_clip_RN50x4_fullft.pt")
        comb_ckpt = os.path.join(base_ckpt_dir, "fiq_comb_RN50x4_fullft.pt")
        if os.path.exists(clip_ckpt) and os.path.exists(comb_ckpt):
            adapter.load_model(clip_checkpoint_path=clip_ckpt, combiner_checkpoint_path=comb_ckpt)
        else:
            print("[CẢNH BÁO] Không tìm thấy checkpoints CLIP4Cir, sẽ dùng pre-trained trắng.")
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
    parser = argparse.ArgumentParser(description="Trích xuất Query hàng loạt")
    parser.add_argument("--model", type=str, required=True, choices=["clip4cir", "searle", "pic2word"], help="Tên mô hình")
    parser.add_argument("--dataset", type=str, required=True, choices=["fashioniq", "circo", "cirr"], help="Tập dữ liệu")
    parser.add_argument("--batch-size", type=int, default=64, help="Kích thước batch")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số lượng truy vấn")
    
    args = parser.parse_args()
    
    print(f"=== PIPELINE TRÍCH XUẤT QUERY: {args.model.upper()} trên {args.dataset.upper()} ===")
    
    adapter, expected_dim = get_adapter(args.model)
        
    dataset = GenericQueryDataset(dataset_name=args.dataset, split="val", limit=args.limit)
    if len(dataset) == 0:
        print(f"[LỖI] Không tìm thấy câu truy vấn nào cho {args.dataset}")
        sys.exit(1)

    dataloader = DataLoader(
        dataset, 
        batch_size=args.batch_size, 
        shuffle=False, 
        num_workers=2 if sys.platform != 'win32' else 0,
        pin_memory=True if torch.cuda.is_available() else False,
        collate_fn=query_collate_fn
    )
    
    all_features = []
    all_target_ids = []
    all_group_members = []
    
    print("Đang tiến hành trích xuất...")
    for images, captions, target_ids, group_members in tqdm(dataloader, desc=f"Extracting Queries"):
        with torch.no_grad():
            features = adapter.extract_query_features(images, captions)
            
        all_features.append(features)
        all_target_ids.extend(target_ids)
        all_group_members.extend(group_members)
        
        del images
        del features
        
    print("\nĐang nối các vector thành ma trận...")
    final_features = np.vstack(all_features)
    
    del all_features
    gc.collect()
    torch.cuda.empty_cache()
    
    print(f"[HOÀN TẤT] Đã trích xuất {final_features.shape[0]} query vectors.")
    assert final_features.shape[1] == expected_dim, f"Shape không chuẩn. Chờ đợi {expected_dim}"
    
    out_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "queries", args.model)
    os.makedirs(out_dir, exist_ok=True)
    
    suffix = f"_{args.limit}" if args.limit else ""
    out_path = os.path.join(out_dir, f"{args.dataset}_queries{suffix}.pkl")
    
    export_data = {
        "query_features": final_features,
        "target_ids": all_target_ids,
        "group_members": all_group_members
    }
    
    with open(out_path, 'wb') as f:
        pickle.dump(export_data, f)
    
    print(f"\n[THÀNH CÔNG] File Pickle lưu tại: {out_path}")

if __name__ == "__main__":
    main()
