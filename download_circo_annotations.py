import os
import urllib.request

def download_circo_annotations(base_dir="data/annotations/circo"):
    os.makedirs(base_dir, exist_ok=True)
    
    base_url = "https://raw.githubusercontent.com/miccunifi/CIRCO/main/annotations/"
    files = ["val.json", "test.json"]
    
    print("Downloading official CIRCO annotations...")
    
    for file_name in files:
        try:
            res = urllib.request.urlopen(base_url + file_name)
            if res.getcode() == 200:
                with open(os.path.join(base_dir, file_name), "w", encoding="utf-8") as f:
                    f.write(res.read().decode("utf-8"))
                print(f"  [+] Downloaded: {file_name}")
        except Exception as e:
            print(f"  [-] Failed to download {file_name}: {e}")

if __name__ == "__main__":
    download_circo_annotations()
    print("Finished downloading CIRCO annotations!")
