"""Render R4 step 0 status using the recorded inventory and comparison."""
from pathlib import Path
import datetime,json
P=Path(__file__).resolve().parent

def main():
    inv=json.loads((P/'inventory.json').read_text(encoding='utf-8'));comp_path=P/'comparison.json';comp=json.loads(comp_path.read_text(encoding='utf-8')) if comp_path.exists() else None
    clean=inv['isolated_snapshot']['status']['exit_code']==0 and not inv['isolated_snapshot']['status']['stdout'];commit=inv['isolated_snapshot']['head']['stdout'];missing=[x['path'] for x in inv['files'] if not x['exists']];changed=[x['path'] for x in inv['files'] if x.get('stage0_byte_match') is False and not x.get('stage0_lf_match',False)]
    lines=['# R4 Bước 0 — Provenance và đối chiếu ID query','',f"Ngày tạo UTC: {datetime.datetime.now(datetime.UTC).isoformat()}",'', '## 1. Phạm vi và trạng thái','', 'Kiểm kê nguồn, dữ liệu và môi trường; trích lại query CIRCO test kèm ID tại thời điểm mã hóa; kiểm tra tương thích cache R2. Ngưỡng đối chiếu đã khóa trong [preflight](./preflight_kiem_dinh.md).','',f"Snapshot mã trích xuất độc lập: commit `{commit}`, working tree {'sạch' if clean else 'chưa sạch hoặc chưa kiểm tra được'}. Snapshot nằm ở `source_snapshot/` và không có data, weights hay package cài ngoài; commit này không đại diện đầy đủ cho mọi mã thực nghiệm R4 tương lai.",'',f"Workspace nguồn: commit `{inv['project']['head']['stdout']}`; trạng thái và submodule lưu trong [inventory.json](./inventory.json). Không sửa hoặc commit các thay đổi sẵn có của workspace nguồn.",'', '## 2. Input và môi trường','',f"Môi trường: {inv['environment']['platform']}; CPU `{inv['environment']['cpu']}`; CPU logic {inv['environment']['logical_cpus']}; CUDA: {inv['environment']['cuda']}; Python `{inv['environment']['python'].split()[0]}`; thư viện và hash được ghi trong manifest.",'']
    if missing:lines += ['Tệp chưa có trong kiểm kê: '+', '.join(f'`{x}`' for x in missing)+'. Không suy diễn hoặc thay thế số liệu thiếu.','']
    if changed:lines += ['Tệp khác hash Chặng 0 ngay cả sau chuẩn hóa xuống dòng: '+', '.join(f'`{x}`' for x in changed)+'. Không dùng chữ ký cũ để khẳng định đây là cùng mã.','']
    lines += ['Các tệp `.py`/YAML có thể khác byte LF/CRLF; inventory ghi cả hash gốc và hash chuẩn hóa. Input, weights, 800 ảnh tham chiếu và mã nguồn có hash; weights/data nằm ngoài commit, cần lưu trữ hoặc khôi phục đúng hash.','', '## 3. Kiểm tra trích xuất và mapping','']
    if comp:
        lines += ['| Model | Query test | Hàng khớp ngưỡng | Cosine nhỏ nhất | Sai số tọa độ lớn nhất | Hàng khó phân biệt |','|---|---:|---:|---:|---:|---:|']
        for m in ['searle','pic2word']:
            v=comp['results'][m];lines.append(f"| {m} | {v['count']} | {v['test_matched_rows']} | {v['min_cosine']:.9f} | {v['max_abs_difference']:.3g} | {v['ambiguous_new_feature_rows']} |")
        lines += ['', 'ID test và reference image ID được ghi cùng batch trích xuất mới. Validation prefix và thứ tự target được kiểm tra với annotation. So sánh vector theo thứ tự annotation với cache cũ; kết quả từng dòng và ngưỡng nằm trong [comparison.json](./comparison.json).','']
        if any(v['test_failed_rows'] for v in comp['results'].values()):lines += ['**Cổng chưa đạt:** có feature vượt tolerance; cần kiểm tra exact top-10 và ảnh hưởng tới retention trước khi kết luận lại R3.','']
        else:lines += ['Không có dòng vượt tolerance đã đăng ký. Đây là bằng chứng cache mới nhất quán theo vị trí với cache cũ, không chứng minh bằng mật mã lịch sử ID cho cache cũ vì cache cũ không lưu ID trực tiếp.','']
    else:lines += ['**Chưa hoàn tất:** chưa có đối chiếu đầy đủ 800 query cho cả hai model; xem nhật ký tiến trình.','']
    lines += ['## 4. Kết luận và cổng confirmatory','', 'Không coi snapshot mã trích xuất là commit xác nhận cho các script R4 chưa được đưa vào snapshot. Mọi lượt chạy confirmatory tiếp theo cần commit sạch bao phủ đúng mã thực thi, dependency/submodule và input hash. Nếu nguồn/feature khác quá ngưỡng, kiểm tra ảnh hưởng và chạy lại kết quả chịu tác động theo kế hoạch.','', 'Output chi tiết: [inventory](./inventory.json), [ngưỡng trước khi chạy](./preflight_kiem_dinh.md), [script đối chiếu](./compare_extractions.py) và dữ liệu local trong `data/` (được ignore).']
    (P/'bao_cao_buoc_0.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
