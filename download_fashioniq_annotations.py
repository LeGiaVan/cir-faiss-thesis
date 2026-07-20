import os
import urllib.request

def download_fashioniq_annotations(base_dir="data/annotations/fashionIQ"):
    os.makedirs(base_dir, exist_ok=True)
    
    base_url_captions = "https://raw.githubusercontent.com/XiaoxiaoGuo/fashion-iq/master/captions/"
    base_url_splits = "https://raw.githubusercontent.com/XiaoxiaoGuo/fashion-iq/master/image_splits/"
    
    categories = ["dress", "shirt", "toptee"]
    splits = ["train", "val", "test"]
    
    print("Downloading official FashionIQ annotations...")
    
    for cat in categories:
        for split in splits:
            # Tải captions
            cap_file = f"cap.{cat}.{split}.json"
            try:
                res = urllib.request.urlopen(base_url_captions + cap_file)
                if res.getcode() == 200:
                    with open(os.path.join(base_dir, cap_file), "w", encoding="utf-8") as f:
                        f.write(res.read().decode("utf-8"))
                    print(f"  [+] Downloaded: {cap_file}")
            except Exception as e:
                pass
            
            # Tải image splits
            split_file = f"split.{cat}.{split}.json"
            try:
                res = urllib.request.urlopen(base_url_splits + split_file)
                if res.getcode() == 200:
                    with open(os.path.join(base_dir, split_file), "w", encoding="utf-8") as f:
                        f.write(res.read().decode("utf-8"))
                    print(f"  [+] Downloaded: {split_file}")
            except Exception as e:
                pass

if __name__ == "__main__":
    download_fashioniq_annotations()
    print("Finished downloading official annotations!")
