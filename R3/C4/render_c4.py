"""Create a report from C4 numerical artifacts."""
from pathlib import Path
import json,csv
P=Path(__file__).resolve().parent

def main():
    r=json.loads((P/'results.json').read_text(encoding='utf-8')); d=json.loads((P/'decomposition.json').read_text(encoding='utf-8'))
    with (P/'degree_groups.csv').open(encoding='utf-8-sig',newline='') as f: groups=list(csv.DictReader(f))
    lines=['# C4 — Hình học gallery và phân bố bậc vào khi centering','','## 1. Câu hỏi nghiên cứu','','Centering làm thay đổi MCS, N10 phía gallery, bậc vào HNSW và miss rate của exact neighbor như thế nào? Xem [kế hoạch](./ke_hoach_C4.md).','','## 2. Giả thuyết trước khi chạy','','Dự đoán Pic2Word có MCS gốc cao hơn SEARLE; không định trước hướng thay đổi N10 hoặc in-degree. Phân biệt chuyển nhóm bậc vào với thay đổi miss trong cùng nhóm; không suy ra quan hệ nhân quả.','','## 3. Thiết kế','','CIRCO, 123.403 gallery, 1.020 query/model, hai backbone, 5 seed HNSW IP M=32 efConstruction=200 efSearch=128. Dữ liệu đồ thị R2 được tái sử dụng sau kiểm tra chữ ký đầy đủ: in-degree và trạng thái tìm thấy lấy cùng checkpoint. N10 gallery tìm exact IP giữa ảnh gallery, loại self theo ID, k=10; centered không chuẩn hóa lại khi tìm. MCS centered đo cosine trên bản sao đã chuẩn hóa. Bin bậc vào dùng quintile gộp trước/sau, ngưỡng trùng được gộp. Bootstrap ghép seed/query 2.000 lần; xem kế hoạch và manifest.','','## 4. Kết quả','','### 4.1. Hình học và N10 gallery','','| Model | ||μ|| gốc | ||μ|| centered | MCS gốc | MCS centered | Skew N10 gốc | Skew N10 centered | N10=0 gốc | N10=0 centered |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for model in ['searle','pic2word']:
        x=r['models'][model];g=x['geometry'];b=x['n10']['before'];a=x['n10']['after']
        lines.append(f"| {model} | {g['mean_norm_original']:.5f} | {g['mean_norm_centered']:.3g} | {g['mcs_original_unit_formula']:.5f} | {g['mcs_centered_cosine']:.5f} | {b['skewness']:.3f} | {a['skewness']:.3f} | {b['zero_ratio']*100:.2f}% | {a['zero_ratio']*100:.2f}% |")
    lines += ['', '### 4.2. Bậc vào và miss','','Bảng điều kiện theo nhóm trước/sau dùng các tập neighbor có thể khác nhau. Chênh lệch cùng nhóm chỉ xét các occurrence giữ nguyên nhóm, không phải hiệu ứng nhân quả.','']
    for model in ['searle','pic2word']:
        x=r['models'][model]; lines += [f'#### {model.upper()}','',f"Ngưỡng nhóm: {x['degree_bins']}. Miss toàn bộ: gốc {x['overall_miss']['before']*100:.2f}%, centered {x['overall_miss']['after']*100:.2f}%.",'',f'![Miss theo bậc vào](./c4_{model}_miss.png)','','| Nhóm | Dòng gốc/sau | Ảnh khác nhau gốc/sau | Miss gốc/sau | Chênh lệch miss cùng nhóm (điểm %) | CI 95% |','|---:|---:|---:|---:|---:|---:|']
        for a in [z for z in groups if z['model']==model]:
            def pct(k):return float(a[k])*100 if a[k] else float('nan')
            lines.append(f"| {a['bin']} | {a['before_rows']}/{a['after_rows']} | {a['before_images']}/{a['after_images']} | {pct('before_miss_rate'):.2f}% / {pct('after_miss_rate'):.2f}% | {pct('same_group_delta_miss'):+.2f} | [{pct('same_group_ci_low'):+.2f}, {pct('same_group_ci_high'):+.2f}] |")
        lines += ['',f'[Bảng chi tiết và CI theo nhóm](./degree_groups.csv); [bảng chuyển nhóm](./degree_transitions.csv).','']
    p=d['point'];lines += ['### 4.3. Phân rã mô tả chênh lệch giữa hai model','',f"Ở đồ thị original seed {d['seed']}, chênh lệch miss Pic2Word − SEARLE là {p['gap']*100:+.2f} điểm %. Dùng hệ số SEARLE: phần theo đặc trưng {p['forward_explained']*100:+.2f}, phần còn lại {p['forward_unexplained']*100:+.2f} điểm %. Dùng hệ số Pic2Word: tương ứng {p['reverse_explained']*100:+.2f} và {p['reverse_unexplained']*100:+.2f} điểm %. Bootstrap: {d['bootstrap_success']}/{d['bootstrap_attempts']} lần fit thành công. Kết quả hai thứ tự, CI và miền giá trị predictor nằm trong [decomposition.json](./decomposition.json).",'', 'Đây là phân rã mô tả phụ thuộc mô hình và cách ghép hàng/rank khi thay nhóm đặc trưng; các hàng hỗn hợp có thể không thực tế. Nó không phải phân rã nhân quả của hiệu ứng centering.','', '## 5. Đánh giá','',f"MCS gốc Pic2Word {'cao hơn' if r['models']['pic2word']['geometry']['mcs_original_unit_formula']>r['models']['searle']['geometry']['mcs_original_unit_formula'] else 'không cao hơn'} SEARLE trong dữ liệu này. Tham khảo bảng và CI khi đánh giá chuyển nhóm và miss trong nhóm; không suy ra MCS gây ra thay đổi retention từ so sánh hai backbone.",'', '## 6. Hạn chế','','Bootstrap query chưa xử lý đầy đủ phụ thuộc do ảnh xuất hiện ở nhiều query; chỉ có năm seed. Decomposition dùng seed 42 và ghép hàng/rank mô tả, nhạy với overlap và mô hình; không dùng làm mediation. ID test theo thứ tự feature chưa được xác minh độc lập từng hàng. C2 chưa khớp mật độ trong 2%; cấu hình reference không kiểm soát ndis khi so miss. Workspace dirty được ghi bằng hash.','', '## 7. Bước tiếp theo','','Đánh giá độ nhạy theo cụm ảnh và vùng overlap trước khi suy luận mạnh; tiếp tục C5 theo kế hoạch.','', '[Kết quả JSON](./results.json) · [phân rã](./decomposition.json) · [manifest](./run_manifest.json) · [bảng nhóm](./degree_groups.csv) · [bảng chuyển nhóm](./degree_transitions.csv).']
    # Expand the decomposition from the saved data, preserving reproducible numbers.
    point=d['point']; ci=d['bootstrap_ci_95']
    def pp(value): return f'{value*100:+.2f}'
    def interval(key): return f'[{pp(ci[key][0])}, {pp(ci[key][1])}]'
    start=lines.index('### 4.3. Phân rã mô tả chênh lệch giữa hai model')
    end=lines.index('## 5. Đánh giá')
    detailed=['### 4.3. Phân rã mô tả chênh lệch giữa hai model','',
        '**Câu hỏi.** Trên hai đồ thị gốc ở seed 42, các đặc trưng của exact neighbor và query có thể mô tả bao nhiêu chênh lệch miss giữa Pic2Word và SEARLE theo hai mô hình logistic? Phép phân rã này so sánh **hai model trước centering**; nó không phân rã tác động của centering và không chứng minh cơ chế HNSW.','',
        '**Đơn vị và mô hình.** Một quan sát là một cặp query–ảnh thuộc exact top-10; biến đích là ảnh đó có bị HNSW bỏ sót hay không. Với mỗi model có 1.020 query × 10 neighbor = 10.200 dòng, từ một đồ thị seed 42. Hai mô hình logistic không điều chuẩn được khớp riêng; các biến được chuẩn hóa bằng trung bình và độ lệch chuẩn của dữ liệu gộp. Nhóm đặc trưng **neighbor** gồm rank, `log1p(in-degree)` và `log1p(N10_gallery)`; nhóm **query** gồm điểm exact `s1` và `s100`.','',
        '**Cách đọc phép phân rã.** Gọi `S` và `P` là miss quan sát của SEARLE và Pic2Word; `fS(X)` và `fP(X)` là miss dự đoán trung bình theo hệ số logistic của từng model khi đưa vào bộ đặc trưng `X`. Chênh lệch quan sát `P − S` được viết theo hai cách:','',
        '- **Mốc SEARLE:** phần theo đặc trưng `fS(XP) − S`; phần còn lại `P − fS(XP)`. Hình dung: đưa đặc trưng Pic2Word vào mô hình của SEARLE, rồi so dự đoán với miss thực của Pic2Word.',
        '- **Mốc Pic2Word:** phần theo đặc trưng `P − fP(XS)`; phần còn lại `fP(XS) − S`. Hình dung: đưa đặc trưng SEARLE vào mô hình của Pic2Word, rồi so dự đoán với miss thực của SEARLE.','',
        'Hai phép tính dùng hệ số tham chiếu khác nhau nên không cần cho cùng một kết quả. Mỗi phần là chênh lệch trên **thang xác suất**, trình bày bằng điểm phần trăm.','',
        '| Đại lượng | Ước lượng (điểm %) | CI 95% bootstrap (điểm %) |','|---|---:|---:|',
        f"| Chênh lệch miss quan sát: Pic2Word − SEARLE | {pp(point['gap'])} | {interval('gap')} |",
        f"| Mốc SEARLE: phần theo đặc trưng | {pp(point['forward_explained'])} | {interval('forward_explained')} |",
        f"| Mốc SEARLE: phần còn lại | {pp(point['forward_unexplained'])} | {interval('forward_unexplained')} |",
        f"| Mốc Pic2Word: phần theo đặc trưng | {pp(point['reverse_explained'])} | {interval('reverse_explained')} |",
        f"| Mốc Pic2Word: phần còn lại | {pp(point['reverse_unexplained'])} | {interval('reverse_unexplained')} |",'',
        f"Theo mốc SEARLE, {pp(point['forward_explained'])} cộng {pp(point['forward_unexplained'])} xấp xỉ {pp(point['gap'])} điểm % sau làm tròn. Phần theo đặc trưng lớn hơn chênh lệch quan sát vì phần còn lại âm; không diễn giải điều này là đặc trưng gây ra hơn 100% chênh lệch. Hai CI của phần còn lại đều chứa 0, nên dữ liệu chưa xác định rõ dấu của phần này trong hai mô hình.",'',
        '**Độ nhạy với thứ tự thay nhóm đặc trưng.** Để mô tả phần theo đặc trưng, mô hình tạo một bảng trung gian: thay nhóm neighbor trước rồi nhóm query, hoặc thay nhóm query trước rồi nhóm neighbor. Trong bảng dưới, cột neighbor luôn là đóng góp của nhóm `(rank, in-degree, N10_gallery)` và cột query luôn là đóng góp của `(s1, s100)`, bất kể nhóm nào được thay trước.','',
        '| Hệ số tham chiếu | Thứ tự thay | Neighbor (điểm %; CI 95%) | Query (điểm %; CI 95%) |','|---|---|---:|---:|']
    for direction,label in [('forward','SEARLE'),('reverse','Pic2Word')]:
        group=point[direction+'_groups']
        for order,short,display in [('node_then_query','node_first','Neighbor → query'),('query_then_node','query_first','Query → neighbor')]:
            neighbor,query=group[order]
            detailed.append(f'| {label} | {display} | {pp(neighbor)} {interval(direction+"_"+short+"_node")} | {pp(query)} {interval(direction+"_"+short+"_query")} |')
    detailed += ['',
        'Hai thành phần theo từng thứ tự cộng xấp xỉ phần theo đặc trưng của cùng mốc; sai lệch nhỏ có thể xuất hiện do làm tròn và sai số khớp mô hình. Sự thay đổi khi đổi thứ tự cho thấy không có một cách chia duy nhất giữa hai nhóm. Mỗi bảng trung gian ghép đặc trưng theo cùng vị trí hàng query/rank giữa hai model; một hàng lai có thể không mô tả query thực tế. Vì vậy không xem các con số trong bảng là mức miss do riêng một nhóm biến gây ra.','',
        f"**Độ bất định và hạn chế.** Dùng bootstrap percentile theo query, lấy mẫu query độc lập trong từng model và giữ 10 neighbor của mỗi query; số lần fit thành công {d['bootstrap_success']}/{d['bootstrap_attempts']}. Chỉ có một seed đồ thị cho phân rã này; bootstrap không bao gồm biến thiên giữa seed, không điều chỉnh phụ thuộc do cùng một ảnh xuất hiện trong nhiều query và không điều chỉnh cho nhiều phép so sánh. Kiểm tra khoảng min–max của từng predictor chỉ cho thấy giao nhau theo từng biến, không bảo đảm hai model có vùng hỗ trợ chung theo tổ hợp đặc trưng; không giả định `s1` hoặc `s100` có cùng ý nghĩa hình học giữa backbone. Miền giá trị từng biến và kết quả chi tiết nằm trong [decomposition.json](./decomposition.json).",'',
        '**Kết luận của mục 4.3:** mô hình cho thấy việc thay phân phối các đặc trưng đi kèm chênh lệch miss dự đoán, nhưng cách chia phụ thuộc hệ số tham chiếu, thứ tự và cách ghép hàng. Đây là phân tích mô tả bổ sung, không phải bằng chứng nhân quả và không phải kết luận chính về cơ chế centering.','']
    lines[start:end]=detailed
    (P/'bao_cao_C4.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
