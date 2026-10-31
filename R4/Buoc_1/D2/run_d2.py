"""D2: Spearman correlations for gallery N10, with provenance checks."""
from pathlib import Path
import argparse,csv,datetime,hashlib,json,os,platform,subprocess,sys
import numpy as np,faiss,scipy
from scipy.stats import skew,spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def weighted_spearman(ix,nx,iy,ny,w):
    fx=np.bincount(ix,weights=w,minlength=nx);fy=np.bincount(iy,weights=w,minlength=ny)
    rx=np.cumsum(fx)-(fx-1)/2;ry=np.cumsum(fy)-(fy-1)/2;center=(w.sum()+1)/2
    vx=np.dot(fx,(rx-center)**2);vy=np.dot(fy,(ry-center)**2)
    if vx<=0 or vy<=0:return np.nan
    cross=np.bincount(iy,weights=w*(rx[ix]-center),minlength=ny)
    return float(np.dot(cross,ry-center)/np.sqrt(vx*vy))

def selftest():
    rng=np.random.default_rng(7)
    for _ in range(10):
        x=rng.integers(0,8,30);y=rng.integers(0,7,30);sample=rng.integers(0,30,30)
        _,ix=np.unique(x,return_inverse=True);_,iy=np.unique(y,return_inverse=True)
        got=weighted_spearman(ix,int(ix.max()+1),iy,int(iy.max()+1),np.bincount(sample,minlength=30))
        if not np.isclose(got,spearmanr(x[sample],y[sample]).statistic,atol=1e-12,rtol=0):raise AssertionError('Bootstrap rank check failed')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    root=args.project.resolve();out=args.out.resolve();snap=Path(__file__).resolve().parent
    if out!=root/'R4/Buoc_1/D2':raise ValueError('Unexpected output path')
    def git(*a):return subprocess.check_output(['git','-c',f'safe.directory={snap.as_posix()}','-C',str(snap),*a],text=True).strip()
    commit=git('rev-parse','HEAD')
    if git('status','--porcelain=v1','--untracked-files=all'):raise ValueError('Dirty snapshot')
    selftest();d1path=root/'R4/Buoc_1/D1/manifest.json';c4path=root/'R3/C4/run_manifest.json';stagepath=root/'R3/stage0_manifest.json'
    d1=json.loads(d1path.read_text(encoding='utf-8'));c4=json.loads(c4path.read_text(encoding='utf-8'));stage=json.loads(stagepath.read_text(encoding='utf-8'))
    c4code=root/'R3/C4/acquire_c4.py'
    if sha(c4code)!=c4['script_sha256']:raise ValueError('C4 acquisition source hash mismatch')
    if sha(c4path)!=d1['c4_manifest_sha256'] or sha(stagepath)!=d1['stage0_manifest_sha256']:raise ValueError('D1 provenance mismatch')
    outdata=out/'data';outdata.mkdir(exist_ok=True); inputs={};results={}; allrows=[]
    for model in ['searle','pic2word']:
        print('Checking source and sample',model,flush=True)
        gpath=root/f'data/embeddings/{model}/circo_gallery.npy'; ghash=sha(gpath)
        if ghash!=d1['gallery'][model]['gallery_sha256'] or ghash!=c4['inputs_sha256'][f'data/embeddings/{model}/circo_gallery.npy']:raise ValueError('Gallery mismatch')
        vpath=root/'R4/Buoc_1/D1'/d1['gallery'][model]['path']
        if sha(vpath)!=d1['gallery'][model]['sha256']:raise ValueError('D1 centrality hash mismatch')
        with np.load(vpath,allow_pickle=False) as z:a=z['a'].copy(); cn=z['centered_norm'].copy();mu=z['mu'].copy()
        n=123403;m=np.linalg.norm(mu)
        if len(a)!=n or len(cn)!=n or not np.isfinite(a).all() or not np.isfinite(cn).all() or m<=0:raise ValueError('Invalid centrality data')
        identity=float(np.max(np.abs(cn**2-(1-2*m*a+m*m))))
        if identity>2e-6:raise ValueError('Centered norm identity check failed')
        g=np.ascontiguousarray(np.load(gpath),dtype=np.float32).copy();faiss.omp_set_num_threads(8);faiss.normalize_L2(g);gc=np.ascontiguousarray(g-g.mean(axis=0),dtype=np.float32)
        smp=np.random.default_rng(42).choice(n,128,replace=False);stats={};counts={};references=[]
        for variant,X in [('before',g),('after',gc)]:
            base=root/'R3/C4/data';npz=base/f'{model}_{variant}_n10.npz';progress=base/f'{model}_{variant}_progress.npz';statfile=base/f'{model}_{variant}_n10_stats.json'
            with np.load(npz,allow_pickle=False) as z,np.load(progress,allow_pickle=False) as pr:
                if str(z['signature'])!=c4['signature'] or str(pr['signature'])!=c4['signature'] or int(pr['next_row'])!=n or not np.array_equal(z['counts'],pr['counts']):raise ValueError('N10 provenance/progress mismatch')
                y=z['counts'].copy()
            st=json.loads(statfile.read_text(encoding='utf-8'))
            if y.shape!=(n,) or not np.issubdtype(y.dtype,np.integer) or np.any(y<0) or int(y.sum())!=10*n or st['sum']!=10*n or st['k']!=10 or st['self_removed_by_id'] is not True:raise ValueError('Invalid N10')
            now_skew=float(skew(y));zero=int((y==0).sum())
            if abs(now_skew-st['skewness'])>1e-10 or zero!=st['zero_count'] or int(y.max())!=st['max'] or not np.isclose(zero/n,st['zero_ratio'],atol=1e-14,rtol=0):raise ValueError('N10 summary inconsistent')
            index=faiss.IndexFlatIP(X.shape[1]);index.add(X);_,near=index.search(np.ascontiguousarray(X[smp]),11);sample_counts=np.zeros(n,dtype=np.int64)
            for self_id,row in zip(smp,near):
                if (row<0).any() or (row>=n).any():raise ValueError('Invalid exact gallery neighbor ID')
                keep=row[row!=self_id][:10]
                if len(keep)!=10 or (keep==self_id).any():raise ValueError('Self-removal check failed')
                np.add.at(sample_counts,keep,1)
            if np.any(sample_counts>y):raise ValueError('Sample contributions exceed stored N10')
            del index
            stats[variant]={'sum':int(y.sum()),'zero_count':zero,'zero_ratio':zero/n,'skewness':now_skew,'max':int(y.max()),'quantiles':np.quantile(y,[0,.25,.5,.75,.9,.95,.99,1]).tolist()};counts[variant]=y
            references.append({'variant':variant,'n10_sha256':sha(npz),'progress_sha256':sha(progress),'stats_sha256':sha(statfile),'sample_queries':len(smp),'sample_rng':42,'sample_counts_within_total':True})
        inputs[model]={'gallery_sha256':ghash,'centrality_sha256':sha(vpath),'norm_identity_error':identity,'n10':references,'historical_n10_hash':'C4 manifest did not separately pin N10 payload; current checksum and recorded signature/progress/stats were checked'}
        specs=[('a_vs_n10_original',a,counts['before']),('norm_vs_n10_centered',cn,counts['after'])]
        fig,axs=plt.subplots(1,2,figsize=(11,4));model_results={}
        for j,(name,x,y) in enumerate(specs):
            print(model,name,'bootstrap start',flush=True);rho=float(spearmanr(x,y).statistic)
            _,ix=np.unique(x,return_inverse=True);_,iy=np.unique(y,return_inverse=True);nx=int(ix.max()+1);ny=int(iy.max()+1)
            rng=np.random.default_rng(42);boot=np.empty(2000)
            for b in range(2000):
                w=np.bincount(rng.integers(0,n,n),minlength=n);boot[b]=weighted_spearman(ix,nx,iy,ny,w)
                if (b+1)%500==0:print(model,name,b+1,'/ 2000',flush=True)
            if not np.isfinite(boot).all():raise ValueError('Invalid bootstrap')
            lo,hi=np.percentile(boot,[2.5,97.5]);status='phù hợp hướng dương' if rho>0 and lo>0 else ('không ủng hộ hướng dương' if hi<0 else 'chưa kết luận')
            freq=np.bincount(iy);row={'model':model,'comparison':name,'rho':rho,'ci_lower':float(lo),'ci_upper':float(hi),'n':n,'x_unique_values':nx,'n10_unique_values':ny,'n10_rows_in_ties':int(freq[freq>1].sum()),'status':status};allrows.append(row);model_results[name]=row
            np.savez_compressed(outdata/f'{model}_{name}_bootstrap.npz',rho=boot)
            edges=np.unique(np.quantile(x,np.linspace(0,1,21)));bins=np.searchsorted(edges[1:-1],x,side='right');xx=[];yy=[]
            for b in range(len(edges)-1):
                mask=bins==b
                if mask.any():xx.append(float(x[mask].mean()));yy.append(float(y[mask].mean()))
            axs[j].plot(xx,yy,marker='o',markersize=3);axs[j].set_xlabel('Độ trung tâm a' if j==0 else 'Norm centered');axs[j].set_ylabel('N10 gallery trung bình');axs[j].grid(alpha=.25);axs[j].set_title('Original' if j==0 else 'Centered')
        fig.suptitle(model.upper()+' — 20 nhóm phân vị; biểu đồ chỉ minh họa');fig.tight_layout();fig.savefig(out/f'd2_{model}.png',dpi=160);plt.close(fig)
        results[model]={'correlations':model_results,'n10_stats':stats}
        del g,gc
    metadata={'module':'R4_D2','timestamp_utc':datetime.datetime.now(datetime.UTC).isoformat(),'source_snapshot_commit':commit,'source_snapshot_clean':True,'script_sha256':sha(Path(__file__)),'preregistration_sha256':sha(snap/'dang_ky_truoc.md'),'d1_manifest_sha256':sha(d1path),'c4_manifest_sha256':sha(c4path),'c4_acquisition_script_sha256':sha(c4code),'inputs':inputs,'bootstrap_replicates':2000,'rng_seed':42,'bootstrap':'gallery rows, exact Spearman midrank with ties; CI percentile 95% conditional on observed gallery','cpu':os.environ.get('PROCESSOR_IDENTIFIER',platform.processor()),'faiss_threads':faiss.omp_get_max_threads(),'python':sys.version,'faiss':faiss.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'limitations':'R4 hypothesis formulated after R3; no historical independently pinned N10 payload hash; N10s dependent on same gallery; bootstrap images not independent; CIs not simultaneous'}
    result={'metadata':metadata,'models':results};(out/'manifest.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');(out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (out/'spearman.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    report(out,result)
    print('D2 complete',flush=True)

def report(out,r):
    lines=['# D2 — Độ trung tâm, norm centered và N10 gallery','','## 1. Câu hỏi và dự đoán','','Dự đoán `ρ(a, N10_gallery_original)>0` và `ρ(||x−μ||, N10_gallery_centered)>0` cho từng backbone. Đây là phân tích R4 được đề xuất sau khi đã xem R3, không phải xác nhận độc lập. Xem [đăng ký](./dang_ky_truoc.md).','','## 2. Thiết kế','','CIRCO có 123.403 ảnh/model. N10 gallery đếm số ảnh khác chọn một ảnh vào top-10 exact IP; centered trừ mean khỏi cả query gallery và index, không chuẩn hóa lại, loại self theo ID. Tính Spearman midrank trên toàn gallery; CI percentile 95% từ 2.000 lần bootstrap ảnh, RNG 42. CI chỉ mô tả có điều kiện vì N10 phụ thuộc cùng gallery.','','## 3. Kết quả','','| Model | Tương quan | Spearman ρ | CI 95% mô tả | Đánh giá hướng dương |','|---|---|---:|---:|---|']
    for model in ['searle','pic2word']:
        for name in ['a_vs_n10_original','norm_vs_n10_centered']:
            x=r['models'][model]['correlations'][name];lines.append(f"| {model} | {name} | {x['rho']:+.4f} | [{x['ci_lower']:+.4f}, {x['ci_upper']:+.4f}] | {x['status']} |")
    lines += ['', '### Phân phối N10 gallery','', '| Model | Biến thể | Skewness | N10 = 0 | Tỷ lệ N10 = 0 | Max |','|---|---|---:|---:|---:|---:|']
    for model in ['searle','pic2word']:
        for variant in ['before','after']:
            x=r['models'][model]['n10_stats'][variant];lines.append(f"| {model} | {variant} | {x['skewness']:.4f} | {x['zero_count']} | {x['zero_ratio']*100:.2f}% | {x['max']} |")
        lines += ['',f'![{model}](./d2_{model}.png)','']
    lines += ['## 4. Diễn giải','','Mỗi dấu/CI được đánh giá riêng theo quy tắc đã ghi trước; tương quan không chứng minh độ trung tâm hoặc norm gây ra hubness. Tỷ lệ N10 bằng 0, skewness và chất lượng retrieval đo các khía cạnh khác nhau. N10 gallery khác bậc vào HNSW đo ở D1.','','## 5. Giới hạn và provenance','','Các ảnh không độc lập vì N10 tính từ cùng gallery; CI bootstrap chỉ mô tả có điều kiện và không đồng thời cho bốn phép. C4 không lưu toàn bộ danh sách neighbor theo hàng và không ghi hash riêng của payload N10 ở thời điểm tạo: D2 đối chiếu signature, progress, thống kê và 128 ảnh mẫu, nhưng không xác minh độc lập mọi lần loại self. Hash payload tại thời điểm D2 và snapshot code sạch được lưu trong manifest. Không diễn giải đây là xác nhận độc lập của giả thuyết đã được hình thành sau R3.','','## 6. Tiếp theo','','Đối chiếu với D1 và chạy D3 trước khi đánh giá tổng thể giả thuyết độ trung tâm.','','[JSON](./results.json) · [manifest](./manifest.json) · [bảng tương quan](./spearman.csv).']
    (out/'bao_cao_D2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__=='__main__':main()
