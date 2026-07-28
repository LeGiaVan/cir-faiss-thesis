import os
import json
from PIL import Image
from torch.utils.data import Dataset

# Thư mục con CIRR ứng với từng split chính thức (ảnh đã được ban tổ chức chia sẵn theo split)
CIRR_SPLIT_SUBDIR = {"val": "dev", "train": "train", "test1": "test1"}

class GenericGalleryDataset(Dataset):
    """
    Dataset dùng chung để load ảnh Gallery của một bộ dữ liệu (FashionIQ, CIRR, CIRCO)
    ĐÚNG theo phạm vi đánh giá chính thức của từng benchmark (không phải toàn bộ ảnh có trên đĩa).
    Chỉ dùng để trích xuất đặc trưng ảnh (Build FAISS Index), không chứa query text.
    """
    def __init__(self, dataset_name: str, data_dir: str = "data/raw", limit: int = None,
                 category: str = None, split: str = "val", anno_dir: str = "data/annotations"):
        """
        :param dataset_name: Tên bộ dữ liệu (vd: 'fashioniq', 'circo', 'cirr')
        :param data_dir: Thư mục chứa thư mục con của các bộ dữ liệu
        :param limit: Chế độ test, chỉ load một số lượng ảnh nhất định
        :param category: BẮT BUỘC với FashionIQ ('dress'|'shirt'|'toptee') - gallery phải tách riêng
                          theo category, không được trộn chung (xem DATA_EVALUATION_PROTOCOL.md).
        :param split: Split đánh giá chính thức ('val' mặc định). Với CIRR quyết định thư mục con
                      ảnh sẽ dùng (val -> 'dev'), với FashionIQ quyết định file split.{category}.{split}.json
        """
        self.dataset_name = dataset_name.lower()
        self.category = category
        self.split = split
        self.image_paths = []
        self.image_names = []
        allowed_ids = None

        # Xác định đường dẫn thư mục ảnh tùy theo cấu trúc của từng Dataset
        if self.dataset_name == "fashioniq":
            if category not in ("dress", "shirt", "toptee"):
                raise ValueError(
                    "FashionIQ bắt buộc phải chỉ định --category ('dress'|'shirt'|'toptee'). "
                    "Gallery không được trộn 3 category chung 1 index (xem DATA_EVALUATION_PROTOCOL.md)."
                )
            img_dir = os.path.join(data_dir, "fashionIQ", "images")
            split_file = os.path.join(anno_dir, "fashionIQ", f"split.{category}.{split}.json")
            if not os.path.exists(split_file):
                raise FileNotFoundError(f"Không tìm thấy file split chính thức: {split_file}")
            with open(split_file, "r", encoding="utf-8") as f:
                allowed_ids = set(json.load(f))
        elif self.dataset_name == "circo":
            # CIRCO chủ đích dùng toàn bộ pool COCO2017 unlabeled làm gallery -> không lọc theo split.
            img_dir = os.path.join(data_dir, "circo", "unlabeled2017")
        elif self.dataset_name == "cirr":
            subdir = CIRR_SPLIT_SUBDIR.get(split)
            if subdir is None:
                raise ValueError(f"Split '{split}' không hợp lệ cho CIRR. Chọn 1 trong {list(CIRR_SPLIT_SUBDIR)}.")
            img_dir = os.path.join(data_dir, "cirr", "img_raw_filtered", subdir)
        else:
            raise ValueError(f"Dataset {dataset_name} chưa được hỗ trợ.")

        if not os.path.exists(img_dir):
            raise FileNotFoundError(f"Không tìm thấy thư mục: {img_dir}. Vui lòng giải nén dữ liệu đúng cấu trúc!")

        print(f"[{dataset_name.upper()}] Đang quét danh sách ảnh tại {img_dir}...")

        # Lọc ra các file ảnh
        valid_extensions = {".jpg", ".jpeg", ".png"}
        for root, _, files in os.walk(img_dir):
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in valid_extensions:
                    name = os.path.splitext(fname)[0]
                    if allowed_ids is not None and name not in allowed_ids:
                        continue
                    self.image_paths.append(os.path.join(root, fname))
                    # Đối với dataset lồng nhau, cần giữ cấu trúc nếu cần, nhưng
                    # để đơn giản ta có thể lấy tên file bỏ đuôi hoặc relative path.
                    # Tạm thời cứ lấy tên file bỏ đuôi (giả định tên file unique)
                    self.image_names.append(name)

        if allowed_ids is not None and len(self.image_names) != len(allowed_ids):
            print(f"[CẢNH BÁO] Split file liệt kê {len(allowed_ids)} ảnh nhưng chỉ tìm thấy "
                  f"{len(self.image_names)} ảnh thực tế trên đĩa cho {dataset_name}/{category}.")

        # Sắp xếp để đảm bảo tính nhất quán giữa các lần chạy
        sorted_pairs = sorted(zip(self.image_names, self.image_paths))
        if sorted_pairs:
            self.image_names, self.image_paths = zip(*sorted_pairs)
        else:
            self.image_names, self.image_paths = [], []

        if limit is not None and limit > 0:
            self.image_paths = self.image_paths[:limit]
            self.image_names = self.image_names[:limit]
            
        print(f"[{dataset_name.upper()}] Đã nạp danh sách {len(self.image_paths)} bức ảnh (Gallery).")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        img_name = self.image_names[idx]
        
        try:
            # Mở ảnh bằng PIL và convert sang RGB (quan trọng cho CLIP)
            image = Image.open(img_path).convert("RGB")
        except Exception as e:
            print(f"Lỗi khi đọc ảnh {img_path}: {e}")
            # Nếu lỗi, trả về một ảnh đen để không làm vỡ batch
            image = Image.new("RGB", (224, 224), (0, 0, 0))
            
        return image, img_name
