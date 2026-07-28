import os
import json
from PIL import Image
from torch.utils.data import Dataset

# Thư mục con CIRR ứng với từng split chính thức - phải khớp với generic_dataloader.py
CIRR_SPLIT_SUBDIR = {"val": "dev", "train": "train", "test1": "test1"}

class GenericQueryDataset(Dataset):
    """
    Dataset dùng để load tập Truy vấn (Queries) từ bộ dữ liệu Validation/Test của FashionIQ, CIRCO, CIRR.
    Trả về: (reference_image, relative_caption, target_image_id, group_members)
    """
    def __init__(self, dataset_name: str, split: str = "val", data_dir: str = "data/raw", limit: int = None,
                 category: str = None):
        self.dataset_name = dataset_name.lower()
        self.split = split
        self.data_dir = data_dir
        self.category = category

        self.queries = []

        if self.dataset_name == "fashioniq":
            if category not in ("dress", "shirt", "toptee"):
                raise ValueError(
                    "FashionIQ bắt buộc phải chỉ định --category ('dress'|'shirt'|'toptee'), "
                    "khớp với gallery đã trích xuất riêng theo category."
                )
            self._load_fashioniq()
        elif self.dataset_name == "circo":
            self._load_circo()
        elif self.dataset_name == "cirr":
            self._load_cirr()
        else:
            raise ValueError(f"Dataset {dataset_name} chưa được hỗ trợ.")
            
        if limit is not None and limit > 0:
            self.queries = self.queries[:limit]
            
        print(f"[{dataset_name.upper()} QUERY] Đã nạp danh sách {len(self.queries)} truy vấn.")

    def _load_fashioniq(self):
        # Chỉ load ĐÚNG 1 category, khớp với gallery riêng của category đó
        # (không được trộn 3 category, xem DATA_EVALUATION_PROTOCOL.md).
        cap_dir = os.path.join("data/annotations", "fashionIQ")
        img_dir = os.path.join(self.data_dir, "fashionIQ", "images")

        cap_file = os.path.join(cap_dir, f"cap.{self.category}.{self.split}.json")
        if not os.path.exists(cap_file):
            print(f"[CẢNH BÁO] Không tìm thấy file {cap_file}.")
            return

        with open(cap_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                ref_img_name = item['candidate']
                target_img_name = item['target']
                relative_caption = " and ".join(item['captions'])

                self.queries.append({
                    "ref_img_path": os.path.join(img_dir, f"{ref_img_name}.png"),
                    "caption": relative_caption,
                    "target_ids": [target_img_name],
                    "group_members": []
                })

    def _load_circo(self):
        img_dir = os.path.join(self.data_dir, "circo", "unlabeled2017")
        anno_file = os.path.join("data/annotations", "circo", f"{self.split}.json")
        
        if not os.path.exists(anno_file):
            print(f"[CẢNH BÁO] Không tìm thấy {anno_file}.")
            return
            
        with open(anno_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for item in data:
            ref_img_name = str(item['reference_img_id']).zfill(12)
            # gt_img_ids trong file JSON là list of ints (ví dụ: [355099, ...]), cần pad thành '000000355099'
            gt_img_ids = [str(gt).zfill(12) for gt in item.get('gt_img_ids', [])]
            gt_img_ids = [gt for gt in gt_img_ids if gt != ""]
            
            self.queries.append({
                "ref_img_path": os.path.join(img_dir, f"{ref_img_name}.jpg"),
                "caption": item['relative_caption'],
                "target_ids": gt_img_ids,
                "group_members": []
            })

    def _load_cirr(self):
        # Dùng os.walk giống gallery để tìm ảnh CIRR - PHẢI trỏ đúng thư mục con của split
        # (val -> dev), không được quét cả train/test1 kẻo ref image bị lẫn ảnh ngoài phạm vi split.
        subdir = CIRR_SPLIT_SUBDIR.get(self.split)
        if subdir is None:
            raise ValueError(f"Split '{self.split}' không hợp lệ cho CIRR. Chọn 1 trong {list(CIRR_SPLIT_SUBDIR)}.")
        img_dir = os.path.join(self.data_dir, "cirr", "img_raw_filtered", subdir)
        cap_file = os.path.join("data/annotations", "cirr", f"cap.rc2.{self.split}.json")
        
        if not os.path.exists(cap_file):
            print(f"[CẢNH BÁO] Không tìm thấy {cap_file}.")
            return
            
        with open(cap_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Nạp trước toàn bộ đường dẫn ảnh thực tế bằng os.walk để search nhanh
        # Thay vì chỉ join với .jpg có thể bị sai folder (test1, dev, train)
        img_paths = {}
        if os.path.exists(img_dir):
            for root, _, files in os.walk(img_dir):
                for fname in files:
                    if fname.endswith(('.jpg', '.png')):
                        name = os.path.splitext(fname)[0]
                        img_paths[name] = os.path.join(root, fname)

        for item in data:
            ref_img_name = item['reference']
            target_img_name = item['target_hard']
            members = item.get('img_set', {}).get('members', [])
            
            ref_path = img_paths.get(ref_img_name, os.path.join(img_dir, f"{ref_img_name}.jpg"))
            
            self.queries.append({
                "ref_img_path": ref_path,
                "caption": item['caption'],
                "target_ids": [target_img_name],
                "group_members": members
            })

    def __len__(self):
        return len(self.queries)

    def __getitem__(self, idx):
        query = self.queries[idx]
        img_path = query["ref_img_path"]
        
        # Nếu path chưa đúng extension, thử .jpg hoặc .png
        if not os.path.exists(img_path):
            if img_path.endswith('.jpg') and os.path.exists(img_path.replace('.jpg', '.png')):
                img_path = img_path.replace('.jpg', '.png')
            elif img_path.endswith('.png') and os.path.exists(img_path.replace('.png', '.jpg')):
                img_path = img_path.replace('.png', '.jpg')
        
        try:
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            # print(f"[LỖI] Không thể đọc ảnh Reference: {img_path} - {e}")
            image = Image.new("RGB", (224, 224), (0, 0, 0))
            
        return image, query["caption"], query["target_ids"], query["group_members"]
