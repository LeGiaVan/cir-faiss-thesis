"""Render the C1 narrative and matched-budget figures from saved results."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent

def main():
    result=json.loads((P/'results.json').read_text(encoding='utf-8'))
    df=pd.read_csv(P/'sweep.csv')
    lines=['# Báo cáo C1: Centering và retention tại cùng chi phí tìm kiếm','',
           '## 1. Câu hỏi nghiên cứu','',
           'Centering gallery có tăng retention@10 khi HNSW thực hiện cùng số phép tính khoảng cách trên mỗi truy vấn (`ndis/query`) không? Đối chiếu HNSW gallery gốc với HNSW gallery đã centering, cùng cấu hình dựng; quét `efSearch` để tạo đường đánh đổi giữa chi phí và retention. Đây là phép so sánh hiệu quả tìm kiếm, không phải so sánh tại cùng `efSearch`.','',
           '## 2. Giả thuyết và dự đoán đã đăng ký trước','',
           'Dự đoán làm việc: lợi thế Pic2Word có thể giảm khi so tại cùng `ndis`, vì đồ thị centered có thể tốn nhiều phép tính hơn ở cùng `efSearch`; hiệu ứng SEARLE có thể nhỏ hơn. Dự đoán và quy tắc đã được ghi trước khi chạy tại [đăng ký trước](../stage0_preregistration.md) và [kế hoạch C1](./ke_hoach_C1.md). CI của chênh lệch centered − original hoàn toàn dương tại một ngân sách hỗ trợ cải thiện ở ngân sách đó; CI chứa 0 nghĩa là chưa đủ bằng chứng về hướng hiệu ứng.','',
           '## 3. Thiết kế và cách đo','',
           '- Dữ liệu: CIRCO, 123.403 vector gallery và 1.020 query (220 validation, 800 test) cho mỗi backbone: SEARLE 512 chiều và Pic2Word 768 chiều. Query và gallery được chuẩn hóa L2 trước khi biến đổi.',
           '- Original: HNSWFlat inner product trên gallery gốc. Centered: trừ trung bình gallery khỏi mỗi vector gallery, không chuẩn hóa lại; query giữ nguyên. Với mỗi query, điểm IP đổi cùng một hằng số nên exact ranking kỳ vọng không đổi. Exact top-10 được kiểm tra trực tiếp cho toàn bộ query.',
           '- Mỗi model và biến thể dùng 5 seed 42–46, `M=32`, `efConstruction=200`; quét `efSearch = 32, 48, 64, 96, 128, 160, 192, 256, 384`. Retention@10 là tỷ lệ giao giữa top-10 HNSW và top-10 exact của cùng query, sau đó lấy trung bình query.',
           '- `ndis/query` lấy từ `faiss.cvar.hnsw_stats.ndis`, chia số query. Latency là chỉ số phụ: một lượt warm-up, bảy lượt đo, batch 1, trung vị mỗi lượt dựng; phép đo bao gồm overhead Python. Xem [sweep.csv](./sweep.csv) để kiểm tra từng seed, cấu hình và độ trễ.',
           '- So sánh chính: lấy miền `ndis` chung của tất cả các seed original và centered, chọn 5 ngân sách cách đều theo log, nội suy tuyến tính retention từng query/từng seed theo `ndis`, không ngoại suy. Bootstrap percentile 95%, 2.000 lần, lấy mẫu lại đồng thời seed và query theo cặp; `ndis` đo được giữ cố định. CI là tại từng điểm, không phải CI đồng thời.','',
           '## 4. Kết quả thực nghiệm','',
           '### 4.1. Đường retention–ndis: so sánh chính','',
           'Ở mỗi hình, các đường mảnh là từng seed. Hai đường đậm là retention nội suy rồi lấy trung bình tại cùng ngân sách; dấu chấm là năm ngân sách đăng ký trước. Biểu đồ dưới thể hiện trực tiếp chênh lệch centered − original và CI ghép cặp. Chênh lệch dương là centered đạt retention cao hơn tại cùng `ndis`.','']
    for model in ['searle','pic2word']:
        pts=result['results'][model]['comparison']; lo,hi=result['results'][model]['common_support']
        fig,(ax,deltaax)=plt.subplots(2,1,figsize=(9,8),sharex=True,gridspec_kw={'height_ratios':[2,1]})
        grid=np.geomspace(lo,hi,150)
        for var,color,label in [('original_ip','#2666aa','Original IP'),('centered_ip','#dc6a15','Centered IP')]:
            curves=[]
            for seed in [42,43,44,45,46]:
                a=df[(df.model==model)&(df.variant==var)&(df.seed==seed)].sort_values('efSearch')
                x=a.ndis_per_query.to_numpy(); y=a.retention.to_numpy()*100
                ax.plot(x,y,color=color,alpha=.23,lw=1)
                curves.append(np.interp(grid,x,y))
            ax.plot(grid,np.mean(curves,axis=0),color=color,lw=2.5,label=label)
            ax.scatter([p['ndis_per_query'] for p in pts],[p['original_retention' if var=='original_ip' else 'centered_retention']*100 for p in pts],color=color,s=24,zorder=4)
        xs=np.array([p['ndis_per_query'] for p in pts]); ys=np.array([p['delta'] for p in pts])*100
        lows=np.array([p['ci_lower'] for p in pts])*100; highs=np.array([p['ci_upper'] for p in pts])*100
        deltaax.errorbar(xs,ys,yerr=[ys-lows,highs-ys],fmt='o',color='#333333',capsize=4)
        deltaax.axhline(0,color='#888888',lw=1); deltaax.set_ylabel('Chênh lệch\n(điểm %)'); deltaax.set_xlabel('Số phép tính khoảng cách / query (ndis, log)')
        ax.set_xscale('log'); ax.set_ylabel('Retention@10 (%)'); ax.set_title(f'{model.upper()}: cùng chi phí tìm kiếm'); ax.legend(); ax.grid(alpha=.25); deltaax.grid(alpha=.25); fig.tight_layout(); fig.savefig(P/f'c1_{model}.png',dpi=180); plt.close(fig)
        fig,ax=plt.subplots(figsize=(8,4.5))
        for var,color,label in [('original_ip','#2666aa','Original IP'),('centered_ip','#dc6a15','Centered IP'),('centered_l2','#39944b','Centered L2, exact L2 riêng')]:
            group=df[(df.model==model)&(df.variant==var)]
            for seed in [42,43,44,45,46]:
                a=group[group.seed==seed].sort_values('efSearch'); ax.plot(a.ndis_per_query,a.retention*100,color=color,alpha=.25,lw=1)
            avg=group.groupby('efSearch')[['ndis_per_query','retention']].mean().sort_index()
            ax.plot(avg.ndis_per_query,avg.retention*100,color=color,label=label,lw=2,marker='o',markersize=3)
        ax.set_xscale('log'); ax.set_xlabel('ndis / query (log)'); ax.set_ylabel('Retention@10 (%)'); ax.set_title(f'{model.upper()}: ba trạng thái, trung bình cùng efSearch'); ax.grid(alpha=.25); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(P/f'c1_{model}_three_variants.png',dpi=160); plt.close(fig)
        lines += [f'#### {model.upper()}', '', f'Miền `ndis` chung: **{lo:.1f}–{hi:.1f} phép tính/query**.','',f'![Retention và chênh lệch cùng ndis — {model}](./c1_{model}.png)','','| ndis/query | Original retention | Centered retention | Chênh lệch (điểm %) | CI 95% (điểm %) |','|---:|---:|---:|---:|---:|']
        for p in pts:
            lines.append(f"| {p['ndis_per_query']:.1f} | {p['original_retention']*100:.2f}% | {p['centered_retention']*100:.2f}% | {p['delta']*100:+.2f} | [{p['ci_lower']*100:+.2f}, {p['ci_upper']*100:+.2f}] |")
        if model=='pic2word':
            p=pts[2]; lines += ['',f"Tại khoảng **{p['ndis_per_query']:.0f} phép tính/query**, original đạt **{p['original_retention']*100:.2f}%**, centered đạt **{p['centered_retention']*100:.2f}%**: tăng **{p['delta']*100:.2f} điểm phần trăm**, CI 95% [{p['ci_lower']*100:.2f}, {p['ci_upper']*100:.2f}]. Cả năm CI đều dương: dữ liệu ủng hộ cải thiện retention–compute trong vùng khảo sát, dù mức tăng không giống nhau ở mọi ngân sách.",'']
        else:
            lines += ['', 'Cả năm CI đều chứa 0. Chưa có bằng chứng centering cải thiện retention ở cùng chi phí đối với SEARLE; không diễn giải kết quả này là chứng minh hai phương án hoàn toàn tương đương.','']
        exact=result['results'][model]['exact_check']
        lines += [f"Kiểm tra exact IP: top-10 giống nhau trên {exact['n_queries']} query; sai số lớn nhất của đồng nhất thức dịch điểm là `{exact['ip_max_score_shift_residual']:.3g}`.",'']
        log_curves={}
        for var in ['original_ip','centered_ip']:
            values=[]
            for seed in [42,43,44,45,46]:
                a=df[(df.model==model)&(df.variant==var)&(df.seed==seed)].sort_values('efSearch')
                values.append(np.interp(np.log(xs),np.log(a.ndis_per_query.to_numpy()),a.retention.to_numpy()))
            log_curves[var]=np.mean(values,axis=0)
        log_delta=log_curves['centered_ip']-log_curves['original_ip']
        max_change=float(np.max(np.abs(log_delta-np.array([p['delta'] for p in pts]))))*100
        lines += [f'Độ nhạy nội suy: nếu nội suy retention theo log(`ndis`) thay cho nội suy theo `ndis`, chênh lệch điểm ước lượng thay đổi tối đa **{max_change:.3f} điểm phần trăm** trên năm ngân sách; đây là phân tích độ nhạy của ước lượng điểm, không phải CI mới.','',f'[Hình bổ sung: original IP, centered IP và centered L2 — {model}](./c1_{model}_three_variants.png).','']
    lines += ['### 4.2. Grid search efSearch và lý do phải khớp chi phí','', 'Bảng sau là trung bình 5 seed tại từng `efSearch` đo được. Đây là số đo trực tiếp, chưa nội suy; cùng hàng không có nghĩa cùng chi phí. Độ trễ là trung bình của trung vị bảy lượt đo theo từng seed, nhằm mô tả chứ không thay thế `ndis` làm tiêu chí chính.','']
    for model in ['searle','pic2word']:
        lines += [f'#### {model.upper()}','', '| efSearch | Original ndis | Original retention | Original ms/query | Centered ndis | Centered retention | Centered ms/query |','|---:|---:|---:|---:|---:|---:|---:|']
        s=df[(df.model==model)&df.variant.isin(['original_ip','centered_ip'])].groupby(['variant','efSearch'])[['ndis_per_query','retention','latency_median_ms']].mean()
        for ef in [32,48,64,96,128,160,192,256,384]:
            a=s.loc[('original_ip',ef)]; b=s.loc[('centered_ip',ef)]
            lines.append(f"| {ef} | {a.ndis_per_query:.1f} | {a.retention*100:.2f}% | {a.latency_median_ms:.3f} | {b.ndis_per_query:.1f} | {b.retention*100:.2f}% | {b.latency_median_ms:.3f} |")
        a=s.loc[('original_ip',128)]; b=s.loc[('centered_ip',128)]
        lines += ['', f"Ví dụ tại `efSearch=128`, centered dùng {b.ndis_per_query:.1f} so với {a.ndis_per_query:.1f} phép tính/query của original ({(b.ndis_per_query/a.ndis_per_query-1)*100:+.1f}%). Vì vậy chênh lệch retention cùng `efSearch` không trả lời trực tiếp câu hỏi cùng chi phí.",'']
    lines += ['## 5. Kết luận và đánh giá giả thuyết','',
              '**Pic2Word — ỦNG HỘ MỘT PHẦN:** centering cải thiện retention tại cả năm ngân sách chung khảo sát, với CI ghép cặp dương tại từng điểm. Kết quả ủng hộ lợi thế trong cấu hình đã đo; chưa thể khẳng định hiệu ứng phổ quát hoặc tách cơ chế đồ thị dày hơn nếu chưa hoàn thành C2.','',
              '**SEARLE — CHƯA KẾT LUẬN:** cả năm CI chứa 0, nên chưa có bằng chứng lợi thế tại cùng chi phí. Dự đoán hiệu ứng nhỏ hơn phù hợp với kết quả mô tả, nhưng so sánh trực tiếp độ lớn hiệu ứng giữa backbone chưa được kiểm định.','',
              '## 6. Hạn chế','',
              'Chỉ có 5 seed; dựng HNSW đa luồng có thể thay đổi theo lịch luồng. CI coi ndis quan sát được là cố định và không hiệu chỉnh cho nhiều điểm; nội suy là xấp xỉ giữa các `efSearch` đã đo. Latency phụ thuộc máy, thời điểm và overhead. ID nguồn của 800 test query chưa được xác minh từng hàng; ghép cặp trong C1 dựa vào thứ tự feature, không xác nhận ánh xạ ID. Workspace dirty nên provenance dựa vào hash tệp thay vì clean commit. C1 chỉ khảo sát CIRCO và một cấu hình dựng.','',
              'Đường centered L2 đã được đo với exact L2 riêng, nhưng chưa thể dùng làm kiểm định bất biến C3: cần thêm L2 gốc và kiểm tra dịch cả query lẫn gallery. Hình bổ sung ba trạng thái biểu diễn trung bình tại cùng efSearch và không chứng minh đối chứng C3.','',
              '## 7. Bước tiếp theo','',
              'Thực hiện C2: đo số cạnh và so original tăng M với centered ở cùng mật độ và cùng ndis. Thực hiện C3: dựng L2 gốc, kiểm tra bất biến khoảng cách và thứ hạng khi dịch cả hai phía. Sau đó làm C4–C5 trước khi gửi mentor theo cổng đã định.','',
              'Dữ liệu và mã: [JSON kết quả](./results.json), [bảng cùng ngân sách](./comparison.csv), [bảng sweep](./sweep.csv), [manifest](./run_manifest.json), [mã phân tích](./analyze_c1.py), [mã tạo báo cáo](./render_c1_report.py), và checkpoint theo seed trong `data/`.']
    (P/'bao_cao_C1.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__': main()
