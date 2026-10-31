"""D1: per-seed Spearman with exact tie-aware gallery bootstrap."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,platform,subprocess,sys,time
import numpy as np
import faiss
from scipy.stats import rankdata,spearmanr
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SEEDS=[42,43,44,45,46]; VARIANTS=['original','centered','delta']

def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def weighted_spearman(ix,nx,iy,ny,weights):
    """Spearman of expanded bootstrap sample, including midranks for ties."""
    fx=np.bincount(ix,weights=weights,minlength=nx);fy=np.bincount(iy,weights=weights,minlength=ny)
    rx=np.cumsum(fx)-(fx-1)/2;ry=np.cumsum(fy)-(fy-1)/2
    center=(weights.sum()+1)/2;vx=np.dot(fx,(rx-center)**2);vy=np.dot(fy,(ry-center)**2)
    if vx<=0 or vy<=0:return np.nan
    grouped=np.bincount(iy,weights=weights*(rx[ix]-center),minlength=ny)
    return float(np.dot(grouped,ry-center)/np.sqrt(vx*vy))

def selftest():
    rng=np.random.default_rng(7)
    for _ in range(10):
        x=rng.integers(0,8,30);y=rng.integers(0,7,30);sample=rng.integers(0,30,30)
        _,ix=np.unique(x,return_inverse=True);_,iy=np.unique(y,return_inverse=True);w=np.bincount(sample,minlength=len(x))
        exact=spearmanr(x[sample],y[sample]).statistic; got=weighted_spearman(ix,ix.max()+1,iy,iy.max()+1,w)
        if not np.isclose(got,exact,atol=1e-12,rtol=0):raise AssertionError('Weighted bootstrap does not match SciPy Spearman')

def run():
    p=argparse.ArgumentParser();p.add_argument('--project',required=True,type=Path);p.add_argument('--out',required=True,type=Path);args=p.parse_args()
    root=args.project.resolve();out=args.out.resolve();snap=Path(__file__).resolve().parent
    if out!=root/'R4/Buoc_1/D1':raise ValueError('Unexpected output path')
    def git(*a):return subprocess.check_output(['git','-c',f'safe.directory={snap.as_posix()}','-C',str(snap),*a],text=True).strip()
    commit=git('rev-parse','HEAD');status=git('status','--porcelain=v1','--untracked-files=all')
    if status:raise ValueError(f'Source snapshot dirty: {status}')
    selftest();data=out/'data';data.mkdir(exist_ok=True)
    stage=json.loads((root/'R3/stage0_manifest.json').read_text(encoding='utf-8')); c4=json.loads((root/'R3/C4/run_manifest.json').read_text(encoding='utf-8'))
    stage_hash=sha(root/'R3/stage0_manifest.json'); c4_hash=sha(root/'R3/C4/run_manifest.json')
    refs={}; rows=[];summary={}; vectors={}
    for model in ['searle','pic2word']:
        print('Validating and computing centrality',model,flush=True)
        gallery=root/f'data/embeddings/{model}/circo_gallery.npy';qh=root/f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/circo_1020_queries_{model}.pkl'
        gallery_hash=sha(gallery);query_hash=sha(qh)
        if gallery_hash!=c4['inputs_sha256'][f'data/embeddings/{model}/circo_gallery.npy'] or gallery_hash.upper()!=stage['frozen_inputs_sha256'][f'data/embeddings/{model}/circo_gallery.npy']:raise ValueError('Gallery hash mismatch')
        if query_hash!=c4['inputs_sha256'][qh.relative_to(root).as_posix()]:raise ValueError('Query source hash mismatch')
        g=np.ascontiguousarray(np.load(gallery),dtype=np.float32).copy()
        if g.shape!=(123403,512 if model=='searle' else 768) or not np.isfinite(g).all():raise ValueError('Bad gallery shape/values')
        faiss.normalize_L2(g)
        norm=np.linalg.norm(g,axis=1); norm_error=float(np.max(np.abs(norm-1)))
        mu=np.mean(g,axis=0,dtype=np.float64);m=float(np.linalg.norm(mu))
        if m<=0 or norm_error>1e-6:raise ValueError('Gallery normalization check failed')
        u=mu/m;a=g@u;az=(a-a.mean())/a.std();mean_error=abs(float(a.mean())-m)
        if a.std()<=0 or mean_error>1e-8:raise ValueError('Centrality identity failed')
        norms_sq=np.empty(len(g),dtype=np.float64)
        for st in range(0,len(g),1024):
            x=g[st:st+1024].astype(np.float64);norms_sq[st:st+len(x)]=np.einsum('ij,ij->i',x-mu,x-mu)
        identity_error=float(np.max(np.abs(norms_sq-(1-2*m*a+m*m))))
        if identity_error>2e-6:raise ValueError('Centered norm identity failed')
        centered_norm=np.sqrt(np.maximum(norms_sq,0))
        dest=data/f'{model}_centrality.npz';np.savez_compressed(dest,a=a,a_z=az,centered_norm=centered_norm,mu=mu)
        vectors[model]={'path':dest.relative_to(out).as_posix(),'sha256':sha(dest),'gallery_sha256':gallery_hash,'mean_norm':m,'a_mean':float(a.mean()),'a_std':float(a.std()),'a_quantiles':np.quantile(a,[0,.05,.25,.5,.75,.95,1]).tolist(),'norm_max_error':norm_error,'mean_identity_error':mean_error,'squared_norm_identity_error':identity_error}
        arrays=[]; raw={};checkpoint_info=[]
        for seed in SEEDS:
            pair=[]
            for variant in ['before','after']:
                cp=root/f'R3/C4/data/{model}_{seed}_{variant}.npz';orig=root/f'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/data/reference_{model}_{seed}_{variant}.npz'
                with np.load(cp,allow_pickle=False) as z,np.load(orig,allow_pickle=False) as source:
                    if str(z['signature'])!=c4['signature'] or str(z['source_sha256'])!=sha(orig):raise ValueError(f'Checkpoint provenance mismatch: {cp}')
                    expected=gallery_hash+query_hash+stage['frozen_inputs_sha256']['configs/reference.yaml'].lower()+c4['r2_script_lf_sha256']+c4['r2_protocol_lf_sha256']
                    if str(source['signature'])!=expected:raise ValueError(f'R2 signature mismatch: {orig}')
                    indeg=z['indegree'].copy();outdeg=z['outdegree'].copy()
                    if not np.array_equal(indeg,source['indegree']) or not np.array_equal(outdeg,source['outdegree']):raise ValueError('C4 degrees differ from source')
                if indeg.shape!=(len(g),) or outdeg.shape!=(len(g),) or np.any(indeg<0) or np.any(outdeg<0) or int(indeg.sum())!=int(outdeg.sum()):raise ValueError('Invalid graph degrees')
                pair.append(indeg.astype(np.int64));checkpoint_info.append({'seed':seed,'variant':variant,'c4_path':cp.relative_to(root).as_posix(),'c4_sha256':sha(cp),'source_path':orig.relative_to(root).as_posix(),'source_sha256':sha(orig),'edges':int(indeg.sum())})
            raw[seed]={'original':pair[0],'centered':pair[1],'delta':pair[1]-pair[0]}; arrays.extend([raw[seed][v] for v in VARIANTS])
        # Precompute tie groups. A weighted midrank on bootstrap multiplicities is exactly
        # the usual Spearman coefficient on the explicitly resampled rows.
        _,ix=np.unique(a,return_inverse=True);nx=int(ix.max()+1);maps=[]
        for y in arrays:
            _,iy=np.unique(y,return_inverse=True);maps.append((iy,int(iy.max()+1)))
        obs=np.array([spearmanr(a,y).statistic for y in arrays]);bt=np.empty((2000,len(arrays)));rng=np.random.default_rng(42)
        for b in range(2000):
            weights=np.bincount(rng.integers(0,len(a),len(a)),minlength=len(a))
            for j,(iy,ny) in enumerate(maps):bt[b,j]=weighted_spearman(ix,nx,iy,ny,weights)
            if (b+1)%100==0:print(model,'bootstrap',b+1,'/ 2000',flush=True)
        if not np.isfinite(bt).all():raise ValueError('Bootstrap produced nonfinite values')
        cilo,cihi=np.percentile(bt,[2.5,97.5],axis=0)
        for i,seed in enumerate(SEEDS):
            for j,variant in enumerate(VARIANTS):
                k=3*i+j;y=raw[seed][variant];_,counts=np.unique(y,return_counts=True)
                rows.append({'model':model,'seed':seed,'variant':variant,'rho':float(obs[k]),'ci_lower':float(cilo[k]),'ci_upper':float(cihi[k]),'n':len(a),'degree_unique_values':len(counts),'degree_rows_in_ties':int(counts[counts>1].sum()),'a_unique_values':nx,'degree_quantiles':np.quantile(y,[0,.05,.25,.5,.75,.95,1]).tolist()})
        expected_sign={'original':1,'centered':-1,'delta':-1};model_summary={}
        for j,variant in enumerate(VARIANTS):
            rr=[x for x in rows if x['model']==model and x['variant']==variant];sign=expected_sign[variant]
            aligned=[x for x in rr if sign*x['rho']>0 and (x['ci_lower']>0 if sign==1 else x['ci_upper']<0)]
            opposite=[x for x in rr if sign*x['rho']<0 and (x['ci_upper']<0 if sign==1 else x['ci_lower']>0)]
            label='ủng hộ trên 5 seed' if len(aligned)==5 else ('không ủng hộ hướng dự đoán' if len(opposite)==5 else ('ủng hộ một phần' if aligned else 'chưa kết luận'))
            model_summary[variant]={'rho_mean':float(np.mean([x['rho'] for x in rr])),'rho_median':float(np.median([x['rho'] for x in rr])),'rho_min':float(min(x['rho'] for x in rr)),'rho_max':float(max(x['rho'] for x in rr)),'seeds_expected_sign_ci':len(aligned),'seeds_opposite_sign_ci':len(opposite),'status':label}
        summary[model]=model_summary;refs[model]=checkpoint_info
        np.savez_compressed(data/f'{model}_bootstrap.npz',rho=bt,observed=obs,seeds=SEEDS,variants=VARIANTS)
        # One marker per quantile bin, per-seed degree means; independent from CI computation.
        fig,axs=plt.subplots(1,3,figsize=(14,4),sharex=True); bounds=np.unique(np.quantile(a,np.linspace(0,1,21))); bin_ids=np.searchsorted(bounds[1:-1],a,side='right')
        for j,variant in enumerate(VARIANTS):
            for seed in SEEDS:
                yy=raw[seed][variant];xx=[];yyb=[]
                for b in range(len(bounds)-1):
                    mask=bin_ids==b
                    if mask.any():xx.append(float(a[mask].mean()));yyb.append(float(yy[mask].mean()))
                axs[j].plot(xx,yyb,alpha=.45,lw=1)
            axs[j].set_title(variant);axs[j].set_xlabel('Độ trung tâm a');axs[j].set_ylabel('In-degree trung bình' if variant!='delta' else 'Δ in-degree trung bình');axs[j].grid(alpha=.2)
        fig.suptitle(model.upper()+' — 20 nhóm a; mỗi đường là 1 seed');fig.tight_layout();fig.savefig(out/f'd1_{model}.png',dpi=160);plt.close(fig)
        del g,raw,arrays,maps,bt
    manifest={'module':'R4_D1','timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'script_commit':commit,'source_snapshot_clean':True,'script_sha256':sha(Path(__file__)),'preregistration_sha256':sha(snap/'dang_ky_truoc.md'),'stage0_manifest_sha256':stage_hash,'c4_manifest_sha256':c4_hash,'checkpoints':refs,'gallery':vectors,'n':123403,'seeds':SEEDS,'bootstrap_replicates':2000,'bootstrap_rng_seed':42,'bootstrap':'gallery rows paired across variants and seeds; exact Spearman midrank for ties; percentile 95%, conditional on fixed graph/gallery','cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'faiss':faiss.__version__,'limitations':'R4 hypothesis uses R3 results; graph nodes dependent; 5 seeds; no p-values or simultaneous CI; R3 data and environment external to source commit'}
    result={'metadata':manifest,'results':summary,'seed_results':rows}
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (out/'spearman_by_seed.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['model','seed','variant','rho','ci_lower','ci_upper','n','degree_unique_values','degree_rows_in_ties','a_unique_values','degree_quantiles']);w.writeheader();w.writerows(rows)
    report(out,result)
    print('D1 complete',flush=True)

def report(out,r):
    lines=['# D1 — Độ trung tâm và bậc vào HNSW','','## 1. Câu hỏi và dự đoán','','Tương quan giữa độ trung tâm gallery `a` và bậc vào HNSW thay đổi như thế nào sau centering? Dự đoán theo feedback: original dương, centered âm và chênh lệch bậc vào centered − original âm. [Đăng ký phân tích](./dang_ky_truoc.md) được ghi sau khi đã biết R3, trước khi tính D1.','','## 2. Thiết kế','','CIRCO: 123.403 ảnh/model, hai backbone, HNSW IP M=32, 5 seed. Tính Spearman midrank trên toàn gallery; in-degree có hướng tầng 0. Với từng seed, 2.000 bootstrap ảnh ghép cặp, CI percentile 95% có điều kiện trên đồ thị/gallery. Kiểm tra code Spearman bootstrap với SciPy trên mẫu mô phỏng có ties.','','## 3. Kết quả','','| Model | Seed | Đại lượng | Spearman ρ | CI 95% mô tả |','|---|---:|---|---:|---:|']
    for row in r['seed_results']:
        lines.append(f"| {row['model']} | {row['seed']} | {row['variant']} | {row['rho']:+.4f} | [{row['ci_lower']:+.4f}, {row['ci_upper']:+.4f}] |")
    lines += ['', 'CI theo từng hệ số không phải CI đồng thời. Chi tiết ties và phân vị trong [bảng dữ liệu](./spearman_by_seed.csv).','', '## 4. Đánh giá từng hướng','']
    for model in ['searle','pic2word']:
        lines += [f'### {model.upper()}','']
        for variant in VARIANTS:
            x=r['results'][model][variant]
            lines.append(f"- **{variant}:** {x['status']}; ρ trung bình {x['rho_mean']:+.4f}, khoảng giữa các seed [{x['rho_min']:+.4f}, {x['rho_max']:+.4f}], {x['seeds_expected_sign_ci']}/5 seed có CI theo dấu dự đoán.")
        lines += ['',f'![{model}](./d1_{model}.png)','']
    lines += ['## 5. Hạn chế và cách diễn giải','','Tương quan quan sát không chứng minh độ trung tâm gây ra bậc vào hay giải thích lợi ích centering. Bootstrap ảnh coi các nút là đơn vị lấy mẫu nhưng các nút phụ thuộc trong cùng đồ thị; CI chỉ mô tả có điều kiện. Chỉ có năm seed, các CI không đồng thời và phân tích R4 được xây dựng sau khi xem R3. Không có ngưỡng được đăng ký trước để gọi tương quan là mạnh. D1 không dùng query test và không giải quyết cổng ID cho D3.','','Checkpoint R2 và source C4 đã đối chiếu hash/chữ ký và dữ liệu bậc vào/ra. Snapshot commit khóa mã D1 và preregistration, không chứa dữ liệu/weights hoặc toàn bộ môi trường; manifest ghi hash và phiên bản.','','## 6. Bước tiếp theo','','Đối chiếu D1 với D2 và D3 trước khi đánh giá giả thuyết độ trung tâm; không suy ra cơ chế nhân quả chỉ từ ba tương quan.','','[JSON](./results.json) · [manifest](./manifest.json) · [bảng theo seed](./spearman_by_seed.csv).']
    (out/'bao_cao_D1.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':run()
