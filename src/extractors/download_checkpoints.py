import os
import subprocess
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def install_gdown():
    try:
        import gdown
    except ImportError:
        print("Installing gdown...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "gdown"])

def download_checkpoints():
    install_gdown()
    import gdown
    
    base_dir = "checkpoints"
    os.makedirs(base_dir, exist_ok=True)
    
    print("=== Tải Checkpoints cho Pic2Word ===")
    pic2word_out = os.path.join(base_dir, "pic2word_vit_l_14.pt")
    if not os.path.exists(pic2word_out):
        print("Đang tải Pic2Word weights từ HuggingFace (do link Google Drive gốc đã chết)...")
        hf_url = "https://huggingface.co/flashingtt/pic2word/resolve/main/pic2word_model.pt"
        try:
            import urllib.request
            urllib.request.urlretrieve(hf_url, pic2word_out)
            print("[+] Tải Pic2Word checkpoint thành công!")
        except Exception as e:
            print(f"\n[LỖI] Không thể tải Pic2Word: {e}")
    else:
        print("Pic2Word checkpoint đã tồn tại.")

    print("\n=== Tải Checkpoints cho CLIP4Cir ===")
    # CLIP4Cir tác giả share nguyên folder, ta dùng lệnh gdown --folder để kéo về
    clip4cir_id = "1ny2hhzP8HZBnXhjvDEni8P8G4_inCNTv"
    clip4cir_out_dir = os.path.join(base_dir, "CLIP4Cir")
    if not os.path.exists(clip4cir_out_dir):
        os.makedirs(clip4cir_out_dir, exist_ok=True)
        print("Đang tải folder CLIP4Cir, việc này có thể mất vài phút...")
        try:
            subprocess.run(["gdown", "--folder", clip4cir_id, "-O", clip4cir_out_dir], check=True)
        except Exception as e:
            print("\n[LỖI] Không thể tải tự động thư mục từ Google Drive.")
            print("Vui lòng tải thủ công theo link sau và giải nén vào thư mục 'checkpoints/CLIP4Cir':")
            print(f"👉 https://drive.google.com/drive/folders/{clip4cir_id}")
    else:
        print("CLIP4Cir checkpoints đã tồn tại.")
        
    print("\n[LƯU Ý] SEARLE không cần tải vì nó sẽ tự tải thông qua torch.hub khi code chạy!")
    print("HOÀN TẤT TẢI CHECKPOINTS.")

if __name__ == "__main__":
    download_checkpoints()
