import os
import subprocess
import sys

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
    pic2word_id = "1IxRi2Cj81RxMu0ViT4q4nkfyjbSHm1dF"
    pic2word_out = os.path.join(base_dir, "pic2word_vit_l_14.pt")
    if not os.path.exists(pic2word_out):
        try:
            gdown.download(id=pic2word_id, output=pic2word_out, quiet=False)
        except Exception as e:
            print("\n[LỖI] Google Drive từ chối tải tự động (thường do quá tải hoặc giới hạn quyền).")
            print("Vui lòng tải thủ công theo link sau và đặt vào thư mục 'checkpoints':")
            print(f"👉 https://drive.google.com/file/d/{pic2word_id}/view")
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
