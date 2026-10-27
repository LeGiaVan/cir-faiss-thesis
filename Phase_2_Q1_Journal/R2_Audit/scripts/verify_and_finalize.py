"""Validate numerical artifacts and publish truthful P0/P1/P2b completion notes."""
from pathlib import Path
import sys
import ast
import json
import re
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import config,metadata,write_json,sha256,setup

AUDIT=ROOT/'Phase_2_Q1_Journal/R2_Audit'
MODULE=AUDIT/'module_a1_revision'


def main():
    cfg=setup();checks=[]
    for base in [ROOT/'src/phase2',AUDIT/'scripts',MODULE/'scripts']:
        for p in base.rglob('*.py'):
            ast.parse(p.read_text(encoding='utf-8-sig'))
    checks.append('active Python syntax')
    steps={n:json.loads((MODULE/'results'/name).read_text(encoding='utf-8')) for n,name in {
        1:'step1_hnsw_indegree.json',2:'step2_bootstrap_ci.json',3:'step3_nested_logit.json',4:'step4_centering.json'}.items()}
    required=['config_sha256','source_tree_sha256','inputs','resolved_config','hardware','git_commit','git_dirty','versions','num_queries','gallery_size','model','index_config']
    p1_files=sorted((AUDIT/'p1_reference/results').glob('*.json'))
    expected={'a2_searle','a2_pic2word','a3_searle','a3_pic2word','a4_anchor_searle','a4_anchor_pic2word'}
    legacy=json.loads((ROOT/'data/results/phase2_stageA/json/module_a5_geometry_power.json').read_text(encoding='utf-8'))
    expected.update(f"a5_geometry_{r['model']}_{r['dataset']}" for r in legacy['records'])
    assert expected<={p.stem for p in p1_files},expected-{p.stem for p in p1_files}
    artifacts=list(steps.values())+[json.loads(p.read_text(encoding='utf-8')) for p in p1_files]
    for data in artifacts:
        m=data['metadata'];assert all(k in m for k in required)
        assert m['config_sha256']==sha256(ROOT/'configs/reference.yaml')
        assert m['hardware']['threads']==cfg['execution']['num_threads']
        for p in m['inputs']:
            assert sha256(ROOT/p['path'])==p['sha256'],p['path']
    checks.append(f'metadata, config hash, input hashes and actual FAISS threads: {len(artifacts)} artifacts')
    frame=pd.read_parquet(MODULE/'data/neighbor_level_data.parquet')
    assert len(frame)==20400
    assert frame.groupby(['model','query_id']).size().eq(10).all()
    for model in ['searle','pic2word']:
        sub=frame[frame.model==model]
        assert sub.query_id.nunique()==1020
        assert abs((1-sub.missed.mean())-steps[1]['results'][model]['retention_at_10'])<1e-12
        for label,row in steps[2]['results'][model].items():
            if row:assert row['n_missed']<=row['n_observations'] and 0<=row['ci_lower']<=row['ci_upper']<=1
        for row in steps[2]['indegree_results'][model].values():
            if row:assert row['n_missed']<=row['n_observations'] and 0<=row['ci_lower']<=row['ci_upper']<=1
    checks.append('20400 neighbor rows, 1020 paired query IDs, 10 neighbors each; counts and CI bounds')
    per_query=pd.read_parquet(MODULE/'data/centering_per_query.parquet')
    assert len(per_query)==2*5*2*1020
    for model,res in steps[4]['results'].items():
        assert res['rank_invariance_verified'] and res['rank_check_queries']==1020
        assert len(res['builds'])==10 and len(res['per_seed_delta'])==5
        sub=per_query[per_query.model==model]
        for variant in ['before','after']:
            mean=float(sub[sub.variant==variant].retention.mean())
            assert abs(mean-res[variant]['retention_at_10'])<1e-12
        assert abs(res['delta_retention']-(res['after']['retention_at_10']-res['before']['retention_at_10']))<1e-12
        for build in res['builds']:
            assert len(build['latency']['runs_ms'])==7
            ck=np.load(MODULE/f"data/reference_{model}_{build['seed']}_{build['variant']}.npz")
            assert ck['found'].shape==(1020,10)
            assert ck['indegree'].sum()==ck['outdegree'].sum()
            assert abs(ck['found'].mean()-build['retention_at_10'])<1e-12
    checks.append('20 HNSW builds; edge conservation; raw query deltas; full rank checks; seven timing repeats')
    for name,res in steps[3]['results'].items():
        assert res['converged'] and res['n_observations']==20400 and res['n_clusters']==1020
        assert res['scale']==1
    checks.append('GEE convergence, common scale, sample and cluster counts')
    for i in range(1,14):assert (AUDIT/f'p0_audit_checklist/p0_{i:02d}_verified.md').exists()
    for p in (ROOT/'Phase_2_Q1_Journal/reports/stage_A').glob('module_a[2345]*.md'):
        s=p.read_text(encoding='utf-8')
        assert len(re.findall(r'^## [1-7]\.',s,re.M))==7,p
        assert not any(t in s for t in ['file:///','O(log N)','khớp hoàn hảo','Chứng minh định lý']),p
    checks.append('13 P0 evidence files and seven-section reports A.2–A.5')
    r2=steps[3]['results']['M2']['coefficients'];searle=steps[4]['results']['searle'];pic=steps[4]['results']['pic2word']
    lines=['# Kết quả hoàn thiện P0, P1 và P2b','',
        '> Phạm vi đợt này: sửa P0, tích hợp giao thức P1 và hoàn thiện A.1 P2b. Không đóng P2a/P2c/P3/P4.','',
        '## 1. Trạng thái nghiệm thu','',
        '| Hạng mục | Đã thực hiện | Giới hạn còn lại |','|---|---|---|',
        '| P0 | 13 evidence; sửa A.2–A.5/tổng kết; renderer từ JSON và hình A.4 đúng dải | Bản legacy được giữ trong archive; không gán cấu hình mới cho dữ liệu cũ |',
        '| P1 | Loader/schema/RC/LID/timing dùng chung; entrypoint Stage A nối pipeline chuẩn; chạy lại A.2/A.3, anchor A.4, RC/LID tám gallery | Chuỗi scale mở rộng không tái xác nhận: cần P3a kiểm định distractor. Metadata lịch sử thiếu vẫn ghi unknown |',
        '| P2b | 1020 query, neighbor/in-degree counts+CI, GEE M0–M2, 5 cặp build mỗi model, full exact-rank check và paired CI | Test ID tái dựng từ extraction order; chưa kiểm chứng độc lập embedding test. Một seed cho hồi quy; chưa làm stress |','',
        '## 2. Kết quả A.1 reference mới','',
        '| Model | Retention trước (%) | Sau (%) | Delta (điểm %) | CI 95% delta (điểm %) |','|---|---:|---:|---:|---|']
    for model,r in steps[4]['results'].items():
        c=r['paired_delta_ci'];lines.append(f"| {model} | {r['before']['retention_at_10']*100:.4f} | {r['after']['retention_at_10']*100:.4f} | {r['delta_retention']*100:.4f} | [{c['ci_lower']*100:.4f}, {c['ci_upper']*100:.4f}] |")
    lines+=['',f"Beta Pic2Word: M0={steps[3]['beta_model_path']['M0']:.6f}; M1={steps[3]['beta_model_path']['M1']:.6f}; M2={steps[3]['beta_model_path']['M2']:.6f}. p M2={r2['is_pic2word']['p_value']:.6g}.",
        '', 'Giữ riêng ý nghĩa thực nghiệm của cải thiện retention và kết luận nhân quả về hubness. Query-N10 không đổi theo phép biến đổi; graph được đo trực tiếp trước–sau. CI dùng paired query/seed bootstrap; không đọc giảm beta thành tỷ lệ tác động nhân quả.',
        '', '## 3. Kiểm tra đã chạy','']+['- '+c for c in checks]+[
        '', 'Kiểm tra số học độc lập trên mẫu nhỏ: `python Phase_2_Q1_Journal/R2_Audit/scripts/check_protocol.py` (graph theo vòng lặp, LID dense exact, centering identity, paired bootstrap và timing).',
        '', '## 4. Artifact và lệnh tái lập','',
        '- [Báo cáo A.1 đầy đủ](../reports/stage_A/module_a1_hubness_report.md).',
        '- [Checklist P0](./P0_AUDIT_CHECKLIST.md).',
        '- [P1 protocol](./p1_reference/PROTOCOL.md) và [danh mục kết quả](./p1_reference/REPORT.md).',
        '- [JSON A.1](./module_a1_revision/results/) và [dữ liệu từng query](./module_a1_revision/data/centering_per_query.parquet).',
        '- [Kết quả kiểm tra máy đọc](./verification.json).',
        '', '## 5. Việc chưa thuộc phạm vi đợt này','',
        'P2a signed-noise/swap curve, P2c N cố định/quét N, P3a distractor/matched quality, P3b H-MG và P4 Pareto còn mở. Chỉ hoàn thiện hồ sơ P0–P2 để gửi mentor sau khi bổ sung P2a/P2c. Không có thao tác gửi thông tin ra ngoài trong đợt này.']
    (AUDIT/'P0_P1_P2b_COMPLETION_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write_json(AUDIT/'verification.json',{'metadata':metadata('p0_p1_p2b_verification',inputs=[MODULE/'results/step4_centering.json',MODULE/'results/step3_nested_logit.json'],model=['searle','pic2word'],num_queries=1020,gallery_size=123403,index_config=cfg['hnsw']['reference']),'checks':checks,'status':'passed','limitations':['A4 scale extension remains legacy pending P3a','test query IDs reconstructed from source order','single-seed GEE; multiseed centering']})
    readme='''# R2 Audit — trạng thái sau P0/P1/P2b

| Mục | Trạng thái |
|---|---|
| P0.1–P0.13 | Đã sửa và đối chiếu; 13 evidence |
| P1 | Đã tích hợp config/metadata/RC/LID/timing và chạy lại phạm vi hợp lệ; scale mở rộng chờ P3a |
| P2b A.1 | Đã chạy reference 1020 query; M0–M2; in-degree; 5 cặp centering/model; paired CI |
| P2a A.2 | Chưa làm signed-noise/swap curves R2 |
| P2c A.5 | Chưa làm N cố định/quét N |
| P3/P4 | Chưa nghiệm thu |

Xem [báo cáo hoàn thiện](./P0_P1_P2b_COMPLETION_REPORT.md), [checklist P0](./P0_AUDIT_CHECKLIST.md), [P1 protocol](./p1_reference/PROTOCOL.md), [P1 results](./p1_reference/REPORT.md), [verification](./verification.json).

Các trạng thái trên xác nhận artifact và kiểm tra, không có nghĩa mọi giả thuyết khoa học đã được xác nhận. Lưu trữ trước sửa tại `archive/pre_p0_p1_p2b/`.
'''
    (AUDIT/'README.md').write_text(readme,encoding='utf-8')
    plan=ROOT/'Phase_2_Q1_Journal/R2_Current_Status_and_Completion_Plan.md';s=plan.read_text(encoding='utf-8');marker='## Cập nhật thực hiện P0/P1/P2b'
    if marker in s:s=s[:s.index(marker)].rstrip()
    s+='\n\n'+marker+'\n\nPhần đánh giá phía trên là snapshot trước triển khai. P0/P1/P2b nay đã có sản phẩm và kiểm tra theo [báo cáo hoàn thiện](./R2_Audit/P0_P1_P2b_COMPLETION_REPORT.md); P1 không tái xác nhận chuỗi scale mở rộng thiếu provenance. P2a/P2c/P3/P4 còn mở. Ước lượng cũ không phải khối lượng còn lại sau đợt này.\n'
    plan.write_text(s,encoding='utf-8')
    summary=ROOT/'Phase_2_Q1_Journal/reports/stage_A/stage_a_master_summary.md'
    s=summary.read_text(encoding='utf-8');marker='## Cập nhật đợt P0/P1/P2b'
    if marker in s:s=s[:s.index(marker)].rstrip()
    s+='\n\n'+marker+'\n\nĐã hoàn thiện P0/P1/P2b trong phạm vi nêu ở [báo cáo đợt](../../R2_Audit/P0_P1_P2b_COMPLETION_REPORT.md). A.1 dùng số liệu reference mới, centering trung bình năm cặp build; A.2/A.3 có phần P1 mới tách khỏi legacy; A.4 có anchor timing, A.5 có định nghĩa RC/LID thống nhất. P2a/P2c còn thiếu nên chưa hoàn tất hồ sơ P0–P2.\n'
    summary.write_text(s,encoding='utf-8')
    print('PASS. Completion report and current status published.')


if __name__=='__main__':main()
