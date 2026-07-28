import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

URLS_FILE = "data/raw/fashionIQ/metadata/needed_val_urls.json"
OUT_DIR = "data/raw/fashionIQ/images_highres"
LOG_FAILED = "data/raw/fashionIQ/metadata/download_failed.json"
LOG_OK = "data/raw/fashionIQ/metadata/download_ok.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def download_one(asin, url, timeout=10, retries=2):
    ext = os.path.splitext(url.split("?")[0])[1]
    if ext.lower() not in (".jpg", ".jpeg", ".png"):
        ext = ".jpg"
    out_path = os.path.join(OUT_DIR, f"{asin}{ext}")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 500:
        return asin, True, "already_exists"
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=timeout)
            if r.status_code == 200 and len(r.content) > 500:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return asin, True, "ok"
        except Exception as e:
            last_err = str(e)
            continue
    return asin, False, f"failed status/exception"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(URLS_FILE, encoding="utf-8") as f:
        asin2url = json.load(f)

    items = list(asin2url.items())
    print(f"Tong so anh can tai: {len(items)}", flush=True)

    ok_list = []
    failed_list = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=24) as ex:
        futures = {ex.submit(download_one, asin, url): asin for asin, url in items}
        done = 0
        for fut in as_completed(futures):
            asin, ok, msg = fut.result()
            if ok:
                ok_list.append(asin)
            else:
                failed_list.append(asin)
            done += 1
            if done % 500 == 0 or done == len(items):
                elapsed = time.time() - t0
                print(f"[{done}/{len(items)}] ok={len(ok_list)} failed={len(failed_list)} elapsed={elapsed:.0f}s", flush=True)

    with open(LOG_OK, "w", encoding="utf-8") as f:
        json.dump(ok_list, f)
    with open(LOG_FAILED, "w", encoding="utf-8") as f:
        json.dump(failed_list, f)

    print(f"HOAN TAT. Thanh cong: {len(ok_list)}  That bai: {len(failed_list)}", flush=True)


if __name__ == "__main__":
    main()
