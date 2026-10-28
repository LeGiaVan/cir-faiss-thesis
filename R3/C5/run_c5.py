"""C5: validate paired query provenance and analyze retention gain by s1."""
from pathlib import Path
import sys, json, pickle, hashlib, datetime, platform, os
import numpy as np
import pandas as pd
import faiss
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent; ROOT=P.parents[1];sys.path.insert(0,str(ROOT/'src'))
from phase2.protocol import setup,normalized,search,sha256
DATA=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data'
SEEDS=[42,43,44,45,46]; NBOOT=2000

def lfhash(p):return hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()
def jsonwrite(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def main():
    setup(); stage=json.loads((ROOT/'R3/stage0_manifest.json').read_text(encoding='utf-8')); c4=json.loads((ROOT/'R3/C4/run_manifest.json').read_text(encoding='utf-8'))
    lock=stage['frozen_inputs_sha256']; paths=['Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/centering_per_query.parquet','Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/query_manifest.json','configs/reference.yaml','src/phase2/protocol.py','Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py','data/annotations/circo/val.json','data/annotations/circo/test.json']
    paths += [f'data/embeddings/{m}/circo_gallery.npy' for m in ['searle','pic2word']]+[f'data/queries/{m}/circo_queries.pkl' for m in ['searle','pic2word']]+[f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{m}.pkl' for m in ['searle','pic2word']]
    hashes={p:sha256(ROOT/p).upper() for p in paths}
    for p in paths:
        if hashes[p]!=lock[p] and not (p.endswith(('.py','.yaml','.json')) and lfhash(ROOT/p)==lock[p]):raise ValueError(f'Stage 0 input hash mismatch: {p}')
    manifest=json.loads((DATA/'query_manifest.json').read_text(encoding='utf-8')); ids=manifest['ids']
    anns={s:json.loads((ROOT/f'data/annotations/circo/{s}.json').read_text(encoding='utf-8')) for s in ['val','test']}
    expected_ids=[f'{split}:{r["id"]}' for split in ['val','test'] for r in anns[split]]
    if ids!=expected_ids or len(ids)!=1020 or len(set(ids))!=1020:raise ValueError('Query manifest does not match annotation order')
    df=pd.read_parquet(DATA/'centering_per_query.parquet')
    if len(df)!=20400 or df.duplicated(['model','seed','query_id','variant']).any() or not df.retention.between(0,1).all():raise ValueError('Invalid retention rows')
    allowed={(m,s,v) for m in ['searle','pic2word'] for s in SEEDS for v in ['before','after']}
    if set(zip(df.model,df.seed,df.variant))!=allowed:raise ValueError('Unexpected seed/model/variant combinations')
    meta={'module':'R3_C5','timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'input_sha256':hashes,'script_sha256':sha256(Path(__file__)),'c4_manifest_sha256':sha256(ROOT/'R3/C4/run_manifest.json'),'git_commit_stage0':stage['repository']['head_commit'],'git_dirty':True,'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'faiss':faiss.__version__,'numpy':np.__version__,'pandas':pd.__version__,'seeds':SEEDS,'bootstrap_replicates':NBOOT,'bootstrap_seed':42,'reference_index':{'M':32,'efConstruction':200,'efSearch':128},'test_query_identity':'row/ID alignment reconstructed from annotations; source ID per feature row not independently verified','bootstrap_primary':'query within fixed quintile after averaging five seeds','bootstrap_sensitivity':'crossed paired seed and query within fixed quintile'}
    output=P/'data';output.mkdir(exist_ok=True); results={'metadata':meta,'models':{}}; rows=[]; audit={}
    for model in ['searle','pic2word']:
        print('Validating',model,flush=True)
        if manifest['models'][model]['query_ids']!=ids:raise ValueError('Model query manifest mismatch')
        gp=ROOT/f'data/embeddings/{model}/circo_gallery.npy'; qp=DATA/f'circo_1020_queries_{model}.pkl'; vp=ROOT/f'data/queries/{model}/circo_queries.pkl'
        with qp.open('rb') as f:q=normalized(pickle.load(f)['query_features'])
        with vp.open('rb') as f:v=pickle.load(f)
        val=normalized(v['query_features'])
        if len(q)!=1020 or len(val)!=220 or not np.allclose(q[:220],val,atol=2e-6):raise ValueError('Validation feature prefix mismatch')
        canon=lambda values:sorted(str(int(x)) for x in values)
        if any(canon(a)!=canon(b['gt_img_ids']) for a,b in zip(v['target_ids'],anns['val'])):raise ValueError('Validation annotation mismatch')
        g=normalized(np.load(gp)); mu=g.mean(0); gc=np.ascontiguousarray(g-mu,dtype=np.float32)
        index=faiss.IndexFlatIP(g.shape[1]);index.add(g);scores,truth=search(index,q,100)
        centered=faiss.IndexFlatIP(g.shape[1]);centered.add(gc);_,truth_c=search(centered,q,10)
        if not np.array_equal(truth[:,:10],truth_c):raise ValueError('Exact top10 differs before/after centering')
        c4path=ROOT/f'R3/C4/data/{model}_queries.npz'
        with np.load(c4path) as z:
            if str(z['signature'])!=c4['signature'] or not np.array_equal(z['truth'],truth[:,:10]) or not np.allclose(z['s1'],scores[:,0],atol=1e-6,rtol=0) or not np.allclose(z['s100'],scores[:,99],atol=1e-6,rtol=0):raise ValueError('C4 exact data mismatch')
        numerical=lfhash(ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py').lower()+lfhash(ROOT/'src/phase2/protocol.py').lower()
        expected=sha256(gp)+sha256(qp)+lock['configs/reference.yaml'].lower()+numerical
        before=np.empty((5,1020));after=np.empty((5,1020)); source_hashes={}
        for i,seed in enumerate(SEEDS):
            for variant,arr in [('before',before),('after',after)]:
                ck=DATA/f'reference_{model}_{seed}_{variant}.npz'
                with np.load(ck) as z:
                    if str(z['signature'])!=expected:raise ValueError('R2 checkpoint signature mismatch')
                    vals=z['found'].mean(axis=1)
                subset=df[(df.model==model)&(df.seed==seed)&(df.variant==variant)].set_index('query_id')
                if len(subset)!=1020 or set(subset.index)!=set(ids):raise ValueError('Query row coverage mismatch')
                actual=subset.loc[ids,'retention'].to_numpy()
                if not np.allclose(actual,vals,rtol=0,atol=1e-12):raise ValueError('Query retention does not match source checkpoint')
                arr[i]=actual;source_hashes[ck.name]=sha256(ck)
        exact_gain=after-before; avg=exact_gain.mean(axis=0)
        # qcut retains tied values within a group and fails instead of silently splitting ties.
        labels,edges=pd.qcut(scores[:,0],5,labels=False,retbins=True,duplicates='raise')
        labels=np.asarray(labels,dtype=int); edges=np.asarray(edges,dtype=float)
        if len(np.unique(labels))!=5 or any(not np.any(labels==i) for i in range(5)):raise ValueError('Cannot form five s1 groups')
        rg=np.random.default_rng(42); boots=np.empty((NBOOT,5)); cross=np.empty((NBOOT,5)); group_stats=[]
        groups=[np.flatnonzero(labels==i) for i in range(5)]
        for b in range(NBOOT):
            si=rg.integers(0,5,5)
            for j,idx in enumerate(groups):
                qi=rg.choice(idx,len(idx),replace=True)
                boots[b,j]=avg[qi].mean();cross[b,j]=exact_gain[si][:,qi].mean()
        for j,idx in enumerate(groups):
            primary=np.percentile(boots[:,j],[2.5,97.5]);sens=np.percentile(cross[:,j],[2.5,97.5])
            group_stats.append({'bin':j+1,'count':len(idx),'s1_min':float(scores[idx,0].min()),'s1_max':float(scores[idx,0].max()),'s1_mean':float(scores[idx,0].mean()),'s100_mean':float(scores[idx,99].mean()),'ret_before':float(before[:,idx].mean()),'ret_after':float(after[:,idx].mean()),'gain':float(avg[idx].mean()),'ci_query':primary.tolist(),'ci_crossed':sens.tolist(),'per_seed_gain':exact_gain[:,idx].mean(axis=1).tolist()})
        contrast=boots[:,0]-boots[:,4]; cross_contrast=cross[:,0]-cross[:,4]; diff=group_stats[0]['gain']-group_stats[4]['gain']; ici=np.percentile(contrast,[2.5,97.5]); cci=np.percentile(cross_contrast,[2.5,97.5])
        monotonic=all(group_stats[i]['gain']>=group_stats[i+1]['gain'] for i in range(4)); supported=bool(monotonic and diff>0 and ici[0]>0)
        results['models'][model]={'s1_edges':edges.tolist(),'groups':group_stats,'contrast_low_minus_high':{'estimate':diff,'ci_query':ici.tolist(),'ci_crossed':cci.tolist()},'monotonic_point_estimates':monotonic,'preregistered_working_rule_supported':supported,'rank_invariance':True}
        audit[model]={'query_count':1020,'val_prefix_verified':True,'val_target_order_verified':True,'exact_top10_invariance':True,'c4_exact_verified_by_recomputation':True,'retention_checkpoint_row_matches':True,'r2_checkpoints_sha256':source_hashes,'c4_query_sha256':sha256(c4path),'s1_boundary_tie_counts':[int(np.sum(scores[:,0]==x)) for x in edges[1:-1]],'test_identity_limitation':meta['test_query_identity']}
        for j,qid in enumerate(ids):
            row={'model':model,'query_row':j,'query_id':qid,'s1':float(scores[j,0]),'s100':float(scores[j,99]),'s1_bin':int(labels[j]+1),'ret_before':float(before[:,j].mean()),'ret_after':float(after[:,j].mean()),'gain':float(avg[j])}
            for i,seed in enumerate(SEEDS):row[f'gain_seed_{seed}']=float(exact_gain[i,j])
            rows.append(row)
        fig,ax=plt.subplots(figsize=(8,5)); xs=np.arange(1,6); means=np.array([z['gain'] for z in group_stats])*100; low=np.array([z['ci_query'][0] for z in group_stats])*100;high=np.array([z['ci_query'][1] for z in group_stats])*100
        ax.errorbar(xs,means,yerr=[means-low,high-means],fmt='o-',capsize=5,color='#17679a',label='Gain trung bình và CI 95% query')
        for j,z in enumerate(group_stats):
            ax.scatter(np.full(5,xs[j])+np.linspace(-.12,.12,5),np.array(z['per_seed_gain'])*100,color='grey',alpha=.5,s=18)
        ax.axhline(0,color='black',lw=.8);ax.set_xticks(xs,[f"{z['bin']}\nn={z['count']}" for z in group_stats]);ax.set_xlabel('Nhóm s1 trong từng model: thấp → cao');ax.set_ylabel('Gain retention@10 (điểm %)');ax.set_title(model.upper()+' — centering cùng efSearch=128');ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(P/f'c5_{model}.png',dpi=160);plt.close(fig)
        print('Validated and analyzed',model,flush=True)
    jsonwrite(P/'run_manifest.json',meta);jsonwrite(P/'mapping_audit.json',audit);jsonwrite(P/'results.json',results)
    frame=pd.DataFrame(rows);frame.to_parquet(output/'query_gains.parquet',index=False)
    frame.to_csv(output/'query_gains.csv',index=False,encoding='utf-8-sig')
    report(results)

def report(result):
    meta=result['metadata']; lines=['# C5 — Query nào được lợi từ centering?','','## 1. Câu hỏi nghiên cứu','','Trong từng backbone, query có `s1` thấp có gain retention@10 lớn hơn khi centering gallery không? Gain là retention centered trừ original, trung bình 5 seed.','', '## 2. Dự đoán trước khi chạy','','Dự đoán đăng ký trước: gain cao hơn ở `s1` thấp, giảm đơn điệu từ nhóm thấp đến cao. Quy tắc làm việc: trung bình 5 nhóm không tăng và CI 95% của chênh lệch nhóm thấp nhất − cao nhất hoàn toàn dương. Xem [kế hoạch](./ke_hoach_C5.md) và [đăng ký trước](../stage0_preregistration.md).','', '## 3. Thiết kế','','CIRCO, 1.020 query/model, 5 seed, HNSW IP `M=32`, `efConstruction=200`, `efSearch=128`. Từ exact IP trên gallery gốc, chia query thành quintile `s1` riêng từng backbone; điểm `s1` thấp là độ tương đồng top-1 thấp trong backbone đó. Bootstrap 2.000 lần lấy mẫu query trong nhóm cố định, sau khi trung bình 5 seed; CI độ nhạy bootstrap chéo query và seed. CI theo nhóm không phải CI đồng thời.','', 'Dữ liệu parquet ghép đúng từng query/seed với checkpoint R2, và exact C4 được tính lại để đối chiếu. Validation prefix và thứ tự target đã kiểm tra; 800 test feature rows chưa có ID nguồn xác minh độc lập. Đây là so sánh cùng efSearch, chưa khớp ndis hoặc mật độ.','', '## 4. Kết quả','']
    for model in ['searle','pic2word']:
        m=result['models'][model];lines += [f'### {model.upper()}','',f'![Gain theo nhóm s1](./c5_{model}.png)','','| Nhóm s1 | Khoảng s1 thực tế | Query | Original | Centered | Gain (điểm %) | CI query 95% | CI query + seed 95% |','|---:|---:|---:|---:|---:|---:|---:|---:|']
        for g in m['groups']:
            lo,hi=g['ci_query'];a,b=g['ci_crossed']; lines.append(f"| {g['bin']} | {g['s1_min']:.5f}–{g['s1_max']:.5f} | {g['count']} | {g['ret_before']*100:.2f}% | {g['ret_after']*100:.2f}% | {g['gain']*100:+.2f} | [{lo*100:+.2f}, {hi*100:+.2f}] | [{a*100:+.2f}, {b*100:+.2f}] |")
        c=m['contrast_low_minus_high']; lines += ['',f"Chênh lệch gain nhóm thấp nhất − cao nhất: **{c['estimate']*100:+.2f} điểm %**, CI query **[{c['ci_query'][0]*100:+.2f}, {c['ci_query'][1]*100:+.2f}]**, CI độ nhạy query + seed **[{c['ci_crossed'][0]*100:+.2f}, {c['ci_crossed'][1]*100:+.2f}]**. Trung bình theo 5 nhóm không tăng: **{'có' if m['monotonic_point_estimates'] else 'không'}**; quy tắc làm việc đã định trước được hỗ trợ: **{'có' if m['preregistered_working_rule_supported'] else 'không'}**.",'']
    lines += ['## 5. Đánh giá dự đoán','']
    for model in ['searle','pic2word']:
        m=result['models'][model]; c=m['contrast_low_minus_high']; gs=m['groups']
        if m['preregistered_working_rule_supported']:
            verdict='ỦNG HỘ theo quy tắc làm việc đã đăng ký: ước lượng giảm đơn điệu và CI chênh lệch hai nhóm đầu cuối hoàn toàn dương.'
        elif c['ci_query'][0]>0 and c['estimate']>0:
            verdict=(f"ỦNG HỘ MỘT PHẦN: nhóm thấp nhất có gain cao hơn nhóm cao nhất với CI query dương, nhưng chưa đạt quy tắc đơn điệu của cả năm nhóm. Ví dụ gain nhóm 2 là {gs[1]['gain']*100:+.2f} điểm % và nhóm 3 là {gs[2]['gain']*100:+.2f} điểm %; không khẳng định hai nhóm giữa khác nhau có ý nghĩa thống kê.")
        else:
            verdict='CHƯA KẾT LUẬN: chưa có bằng chứng theo quy tắc đã đăng ký; CI chênh lệch hai nhóm đầu cuối chưa hỗ trợ mức tăng dương.'
        lines += [f'**{model.upper()} — {verdict}**','']
    lines += ['CI của một nhóm không kiểm định sự khác biệt giữa hai nhóm. Kết quả không thỏa quy tắc mô tả không đồng nghĩa bác bỏ mọi quan hệ có thể tồn tại.','', '## 6. Hạn chế','','Cùng efSearch không bảo đảm cùng ndis hay số cạnh. C1 khảo sát cùng ndis ở mức tổng thể; C2 chưa đạt khớp số cạnh. CI chính cố định 5 đồ thị và ngưỡng nhóm; CI độ nhạy chỉ dùng 5 seed. Query có thể phụ thuộc do chia sẻ ảnh; bootstrap query chưa giải quyết đầy đủ phụ thuộc theo ảnh. CI từng điểm không điều chỉnh đồng thời nhiều so sánh. 800 test query ID được tái dựng từ thứ tự extraction, chưa xác minh độc lập theo từng feature row. Điểm s1 giữa hai backbone không nhất thiết cùng thang đo.','', '## 7. Bước tiếp theo','','Xem C5 cùng C1/C2/C4, sau đó kiểm tra H-MG theo kế hoạch R3; không coi tương quan giữa s1 và gain là bằng chứng nhân quả.','', '[JSON kết quả](./results.json) · [manifest](./run_manifest.json) · [kiểm tra ghép query](./mapping_audit.json) · [dữ liệu từng query](./data/query_gains.parquet).']
    (P/'bao_cao_C5.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
