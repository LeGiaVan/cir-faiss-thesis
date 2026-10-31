"""D3: query-cluster bootstrap of exact-neighbor centrality."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,pickle,platform,subprocess,sys
import faiss,numpy as np,scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def normalize(values):
    a=np.ascontiguousarray(values,dtype=np.float32).copy()
    if not np.isfinite(a).all() or np.any(np.linalg.norm(a,axis=1)==0):raise ValueError('Invalid or zero vector')
    faiss.normalize_L2(a);return a

def bootstrap(a,b,seed):
    if a.shape!=b.shape or a.ndim!=1:raise ValueError('Invalid paired query data')
    rng=np.random.default_rng(seed);n=len(a);idx=rng.integers(0,n,size=(2000,n))
    aa=a[idx].mean(axis=1);bb=b[idx].mean(axis=1)
    return {'searle':np.percentile(aa,[2.5,97.5]).tolist(),'pic2word':np.percentile(bb,[2.5,97.5]).tolist(),'delta_pic2word_minus_searle':np.percentile(bb-aa,[2.5,97.5]).tolist()}

def result_summary(values,baseline,truth):
    query_means=values.mean(axis=1);freq=np.bincount(truth.ravel(),minlength=len(baseline));unique=freq>0
    return {'n_queries':len(truth),'neighbor_occurrences':int(truth.size),'unique_neighbor_images':int(unique.sum()),'gallery_baseline':float(baseline.mean()),'query_mean_az':float(query_means.mean()),'deviation_from_gallery':float(query_means.mean()-baseline.mean()),'occurrence_az_quantiles_10_50_90':np.quantile(values,[.1,.5,.9]).tolist(),'query_mean_az_quantiles_10_50_90':np.quantile(query_means,[.1,.5,.9]).tolist(),'unique_image_mean_az':float(baseline[unique].mean()),'unique_image_az_quantiles_10_50_90':np.quantile(baseline[unique],[.1,.5,.9]).tolist(),'max_query_occurrences_per_image':int(freq.max()),'images_repeated_across_queries':int((freq>1).sum()),'top_10_images_occurrence_share':float(np.sort(freq)[-10:].sum()/truth.size)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--project',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    root=args.project.resolve();out=args.out.resolve();snap=Path(__file__).resolve().parent
    if out!=root/'R4/Buoc_1/D3':raise ValueError('Unexpected output path')
    def git(*a):return subprocess.check_output(['git','-c',f'safe.directory={snap.as_posix()}','-C',str(snap),*a],text=True).strip()
    commit=git('rev-parse','HEAD')
    if git('status','--porcelain=v1','--untracked-files=all'):raise ValueError('Source snapshot not clean')
    faiss.omp_set_num_threads(8)
    c4path=root/'R3/C4/run_manifest.json'; d1path=root/'R4/Buoc_1/D1/manifest.json'; stagepath=root/'R3/stage0_manifest.json';comparepath=root/'R4/provenance/comparison.json'; qmanifestpath=root/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/query_manifest.json'
    c4=json.loads(c4path.read_text(encoding='utf-8'));d1=json.loads(d1path.read_text(encoding='utf-8'));stage=json.loads(stagepath.read_text(encoding='utf-8'));comparison=json.loads(comparepath.read_text(encoding='utf-8'));qm=json.loads(qmanifestpath.read_text(encoding='utf-8'))
    if sha(c4path)!=d1['c4_manifest_sha256'] or sha(stagepath)!=d1['stage0_manifest_sha256']:raise ValueError('Manifest mismatch')
    for s in ['val','test']:
        path=root/f'data/annotations/circo/{s}.json'
        if sha(path).upper()!=stage['frozen_inputs_sha256'][path.relative_to(root).as_posix()]:raise ValueError(f'Annotation changed: {s}')
    ann={s:json.loads((root/f'data/annotations/circo/{s}.json').read_text(encoding='utf-8')) for s in ['val','test']}
    ids=[f'{s}:{x["id"]}' for s in ['val','test'] for x in ann[s]]
    if len(ids)!=1020 or len(set(ids))!=1020 or qm['ids']!=ids or any(qm['models'][m]['query_ids']!=ids for m in ['searle','pic2word']):raise ValueError('Query pairing manifest mismatch')
    # Two official IDs have identical reference image and caption; sensitivity removes both.
    duplicates=[next(x for x in ann['test'] if str(x['id'])==k) for k in ['251','631']]
    if any(duplicates[0][k]!=duplicates[1][k] for k in ['reference_img_id','relative_caption']):raise ValueError('Duplicate query evidence changed')
    data=out/'data';data.mkdir(exist_ok=True);meta_inputs={}; arrays={}; allresults={}; pairrows=[{'query_row':i,'query_id':qid} for i,qid in enumerate(ids)]
    for model in ['searle','pic2word']:
        print('Verify gallery, query and exact results',model,flush=True)
        gpath=root/f'data/embeddings/{model}/circo_gallery.npy'; qpath=root/f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{model}.pkl'; valpath=root/f'data/queries/{model}/circo_queries.pkl'; truthpath=root/f'R3/C4/data/{model}_queries.npz'; azpath=root/'R4/Buoc_1/D1'/d1['gallery'][model]['path']
        if sha(gpath)!=d1['gallery'][model]['gallery_sha256'] or sha(gpath)!=c4['inputs_sha256'][gpath.relative_to(root).as_posix()] or sha(qpath)!=c4['inputs_sha256'][qpath.relative_to(root).as_posix()] or sha(azpath)!=d1['gallery'][model]['sha256']:raise ValueError('Input hash mismatch')
        comp=comparison['results'][model]
        if comp['test_matched_rows']!=800 or comp['test_failed_rows']!=0 or not comp['validation_target_order_verified'] or not comp['r2_manifest_consistent'] or comp['old_cache_sha256']!=sha(qpath):raise ValueError('Bước 0 pairing evidence mismatch')
        with np.load(azpath,allow_pickle=False) as z:az=z['a_z'].copy()
        if len(az)!=123403 or not np.isfinite(az).all() or abs(az.mean())>1e-10 or abs(az.std()-1)>1e-10:raise ValueError('Invalid a_z')
        with qpath.open('rb') as f:q=normalize(pickle.load(f)['query_features'])
        with valpath.open('rb') as f:val=pickle.load(f)
        normval=normalize(val['query_features'])
        canon=lambda x:sorted(str(int(z)) for z in x)
        if len(q)!=1020 or len(normval)!=220 or not np.allclose(q[:220],normval,atol=2e-6,rtol=0) or any(canon(a)!=canon(b['gt_img_ids']) for a,b in zip(val['target_ids'],ann['val'])):raise ValueError('Validation prefix/target mismatch')
        g=normalize(np.load(gpath)); index=faiss.IndexFlatIP(g.shape[1]);index.add(g);_,truth=index.search(q,100);truth=truth[:,:10]
        with np.load(truthpath,allow_pickle=False) as z:
            if str(z['signature'])!=c4['signature'] or not np.array_equal(z['truth'],truth):raise ValueError('C4 exact IDs do not match recomputation')
        if truth.shape!=(1020,10) or np.any(truth<0) or np.any(truth>=len(az)) or any(len(set(row))!=10 for row in truth):raise ValueError('Invalid exact neighbor IDs')
        values=az[truth];qm_az=values.mean(axis=1);freq=np.bincount(truth.ravel(),minlength=len(az))
        arrays[model]={'az':az,'truth':truth,'values':values,'query_means':qm_az,'freq':freq}
        for i,row in enumerate(pairrows):row[f'{model}_mean_az']=float(qm_az[i]);row[f'{model}_deviation_from_gallery']=float(qm_az[i]-az.mean())
        allresults[model]=result_summary(values,az,truth)
        meta_inputs[model]={'gallery_sha256':sha(gpath),'query_cache_sha256':sha(qpath),'validation_cache_sha256':sha(valpath),'centrality_sha256':sha(azpath),'c4_query_sha256':sha(truthpath),'c4_top10_exact_recomputed_and_equal':True,'validation_prefix_and_target_order_verified':True,'step0_matching_rows':comp['test_matched_rows'],'step0_ambiguous_rows':comp['ambiguous_new_feature_rows']}
        nonzero=np.flatnonzero(freq);target=data/f'{model}_neighbor_frequency.csv'
        with target.open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.writer(f);w.writerow(['gallery_row','query_occurrences','a_z']);w.writerows((int(i),int(freq[i]),float(az[i])) for i in nonzero)
        np.savez_compressed(data/f'{model}_exact_neighbors.npz',truth=truth,query_mean_az=qm_az)
        fig,ax=plt.subplots(figsize=(8,4.8));ax.hist(az,bins=65,density=True,alpha=.45,label='Toàn gallery');ax.hist(values.ravel(),bins=65,density=True,alpha=.45,label='Exact neighbor (occurrence)');ax.axvline(az.mean(),color='black',ls='--',lw=1,label='Mean gallery');ax.axvline(qm_az.mean(),color='tab:red',ls='--',lw=1,label='Mean neighbor theo query');ax.set_xlabel('Độ trung tâm chuẩn hóa a_z trong model');ax.set_ylabel('Mật độ');ax.set_title(model.upper()+' — gallery và exact neighbor');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/f'd3_{model}.png',dpi=160);plt.close(fig)
        del index,g,q
    s=arrays['searle'];pw=arrays['pic2word'];base_s=float(s['az'].mean());base_p=float(pw['az'].mean())
    before_s=s['query_means']-base_s;before_p=pw['query_means']-base_p
    ci=bootstrap(before_s,before_p,42);mask=np.array([qid not in ['test:251','test:631'] for qid in ids]);sensci=bootstrap(before_s[mask],before_p[mask],42)
    if int(mask.sum())!=1018:raise ValueError('Duplicate sensitivity mask invalid')
    delta=float(before_p.mean()-before_s.mean());sens_delta=float(before_p[mask].mean()-before_s[mask].mean())
    for model,vals in [('searle',before_s),('pic2word',before_p)]:
        allresults[model]['ci_95']=ci[model];allresults[model]['sensitivity_excluding_both']={'n_queries':1018,'deviation':float(vals[mask].mean()),'ci_95':sensci[model]}
        low,high=ci[model];allresults[model]['assessment']='phù hợp hướng âm' if vals.mean()<0 and high<0 else ('không ủng hộ hướng âm' if low>0 else 'chưa kết luận')
    compare={'estimand':'Pic2Word deviation minus SEARLE deviation; paired query bootstrap','delta':delta,'ci_95':ci['delta_pic2word_minus_searle'],'assessment':'phù hợp hướng âm' if delta<0 and ci['delta_pic2word_minus_searle'][1]<0 else ('không ủng hộ hướng âm' if ci['delta_pic2word_minus_searle'][0]>0 else 'chưa kết luận'),'sensitivity_excluding_both':{'n_queries':1018,'delta':sens_delta,'ci_95':sensci['delta_pic2word_minus_searle']}}
    metadata={'module':'R4_D3','timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'script_commit':commit,'source_snapshot_clean':True,'script_sha256':sha(Path(__file__)),'preregistration_sha256':sha(snap/'dang_ky_truoc.md'),'d1_manifest_sha256':sha(d1path),'c4_manifest_sha256':sha(c4path),'step0_comparison_sha256':sha(comparepath),'query_manifest_sha256':sha(qmanifestpath),'inputs':meta_inputs,'seeds_bootstrap':42,'bootstrap_replicates':2000,'bootstrap':'paired query clusters across models; percentile CI; 10 neighbors kept per query; gallery fixed','n_queries':1020,'sensitivity_excluded_ids':['test:251','test:631'],'cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'faiss':faiss.__version__,'faiss_threads':faiss.omp_get_max_threads(),'limitations':'Query IDs in historical cache reconstructed by row order; duplicate IDs share input; query bootstrap does not fully account for reused gallery images; R4 hypothesis after R3; CIs not simultaneous; normalized centrality is not a shared embedding space'}
    result={'metadata':metadata,'models':allresults,'comparison':compare}
    for name,obj in [('manifest.json',metadata),('results.json',result)]: (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (data/'per_query.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(pairrows[0]));w.writeheader();w.writerows(pairrows)
    report(out,result)
    print('D3 complete',flush=True)

def report(out,r):
    lines=['# D3 — Độ trung tâm của exact neighbor truy vấn CIR','','## 1. Câu hỏi và dự đoán','','Dự đoán exact neighbor CIR có `a_z` trung bình thấp hơn gallery trong từng model và Pic2Word lệch âm hơn SEARLE. Đây là phân tích R4 bổ sung sau khi biết kết quả R3; xem [đăng ký phân tích](./dang_ky_truoc.md).','','## 2. Thiết kế','','CIRCO: 123.403 ảnh gallery và 1.020 query/model. Với mỗi query lấy trung bình độ trung tâm chuẩn hóa trong model của 10 neighbor IP chính xác; so với trung bình toàn gallery. Bootstrap ghép cặp query giữa hai backbone 2.000 lần, cố định gallery và giữ đủ 10 neighbor/query; CI percentile 95%. Không xem các neighbor hoặc ảnh lặp là các query độc lập.','','## 3. Kết quả từng model','','| Model | Trung bình a_z neighbor theo query | Trung bình a_z gallery | Lệch | CI 95% | Số ảnh neighbor khác nhau |','|---|---:|---:|---:|---:|---:|']
    for model in ['searle','pic2word']:
        x=r['models'][model];lines.append(f"| {model} | {x['query_mean_az']:+.4f} | {x['gallery_baseline']:+.4f} | {x['deviation_from_gallery']:+.4f} | [{x['ci_95'][0]:+.4f}, {x['ci_95'][1]:+.4f}] | {x['unique_neighbor_images']} |")
    for model in ['searle','pic2word']:
        x=r['models'][model];s=x['sensitivity_excluding_both'];lines += ['',f"**{model}:** {x['assessment']}. Phân vị 10/50/90 của các neighbor occurrence: {', '.join(f'{v:+.3f}' for v in x['occurrence_az_quantiles_10_50_90'])}; của trung bình theo query: {', '.join(f'{v:+.3f}' for v in x['query_mean_az_quantiles_10_50_90'])}. Trung bình theo ảnh neighbor duy nhất: {x['unique_image_mean_az']:+.4f}; {x['images_repeated_across_queries']} ảnh xuất hiện nhiều hơn một lần, 10 ảnh xuất hiện nhiều nhất chiếm {x['top_10_images_occurrence_share']*100:.2f}% occurrence.",'',f"Độ nhạy bỏ cả `test:251` và `test:631`: lệch {s['deviation']:+.4f}, CI [{s['ci_95'][0]:+.4f}, {s['ci_95'][1]:+.4f}], {s['n_queries']} query.",'',f'![{model}](./d3_{model}.png)','']
    c=r['comparison'];s=c['sensitivity_excluding_both'];lines += ['## 4. So sánh trực tiếp hai backbone','',f"Δ = lệch Pic2Word − lệch SEARLE = **{c['delta']:+.4f}**, CI ghép cặp [{c['ci_95'][0]:+.4f}, {c['ci_95'][1]:+.4f}]: {c['assessment']}. Sau khi bỏ cả hai query trùng nội dung: Δ = {s['delta']:+.4f}, CI [{s['ci_95'][0]:+.4f}, {s['ci_95'][1]:+.4f}]. CI được tính trực tiếp cho chênh lệch, không suy ra từ việc so hai CI riêng.",'', '## 5. Hạn chế','','Chuẩn hóa riêng từng backbone chỉ cho vị trí tương đối theo phân phối gallery của model, không tạo cùng thang hình học. Các query có thể chia sẻ ảnh neighbor; bootstrap query không giải quyết đầy đủ phụ thuộc theo ảnh. Tập test có hai ID khác nhau nhưng cùng reference/caption; độ nhạy loại cả hai được báo riêng, kết quả chính giữ tập chính thức. Cache cũ không ghi source ID từng hàng; Bước 0 hỗ trợ tính nhất quán theo vị trí nhưng không chứng minh lịch sử ID tuyệt đối. CI theo từng phép không phải CI đồng thời.','','D3 dựa trên query CIR, chưa so với query ảnh; liên hệ này không chứng minh độ trung tâm gây ra gain centering hay là yếu tố duy nhất khác biệt giữa backbone. Thiết kế được đề xuất sau khi biết kết quả R3, không phải xác nhận độc lập.','','## 6. Tiếp theo','','Kết hợp D1–D3, sau đó thiết kế đối chứng query ảnh và kiểm tra chi phí/mật độ theo kế hoạch R4.','','[JSON kết quả](./results.json) · [manifest](./manifest.json) · [bảng từng query](./data/per_query.csv).']
    (out/'bao_cao_D3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
