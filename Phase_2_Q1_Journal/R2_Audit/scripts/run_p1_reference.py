"""P1 reruns under shared config, isolated from legacy JSON and P2a/P2c designs."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
import argparse
import json
import pickle
import time
import numpy as np
import faiss
from phase2.protocol import setup,metadata,write_json,normalized,geometry,timed_search,hnsw,search,sha256

OUT=ROOT/'Phase_2_Q1_Journal/R2_Audit/p1_reference'
REPORTS=ROOT/'Phase_2_Q1_Journal/reports/stage_A'


def circo(model):
    gp=ROOT/f'data/embeddings/{model}/circo_gallery.npy';qp=ROOT/f'data/queries/{model}/circo_queries.pkl'
    data=pickle.load(qp.open('rb'))
    return normalized(np.load(gp)),normalized(data['query_features']),data,[gp,qp]


def save(name, results, paths, **kwargs):
    write_json(OUT/'results'/f'{name}.json',{'metadata':metadata(name,inputs=paths,numerical_code_signature=code_signature(),**kwargs),'results':results})


def code_signature():
    paths=[Path(__file__),ROOT/'src/phase2/protocol.py',ROOT/'src/phase2/stage_a/measure_pq_perturbation.py',ROOT/'src/phase2/stage_a/measure_ivf_routing.py']
    return {p.relative_to(ROOT).as_posix():sha256(p) for p in paths}


def reusable(name):
    p=OUT/'results'/f'{name}.json'
    if not p.exists():return False
    m=json.loads(p.read_text(encoding='utf-8'))['metadata']
    valid=(m.get('config_sha256')==sha256(ROOT/'configs/reference.yaml') and m.get('numerical_code_signature')==code_signature()
           and all(sha256(ROOT/i['path'])==i['sha256'] for i in m['inputs']))
    if valid:print('Reuse verified P1 checkpoint:',name,flush=True)
    return valid


def run_modules(modules):
    cfg=setup();OUT.mkdir(parents=True,exist_ok=True)
    if 'a2' in modules:
        from phase2.stage_a.measure_pq_perturbation import run_pq_perturbation_analysis
        for model in ['searle','pic2word']:
            if reusable('a2_'+model):continue
            print('P1 A2',model,flush=True)
            g,q,_,paths=circo(model);c=cfg['ivfpq']
            result=run_pq_perturbation_analysis(model,g,q,m_list=c['audit_m_list'],nlist=c['nlist'],nprobe=c['default_nprobe'])
            save('a2_'+model,result,paths,model=model,gallery_size=len(g),num_queries=len(q),index_config=c,
                 query_profile='val_labeled',scope='P1 absolute-noise rerun; not signed-noise P2a')
    if 'a3' in modules:
        from phase2.stage_a.measure_ivf_routing import analyze_ivf_routing
        for model in ['searle','pic2word']:
            if reusable('a3_'+model):continue
            print('P1 A3',model,flush=True)
            g,q,bundle,paths=circo(model);np_path=ROOT/f'data/embeddings/{model}/circo_names.npy'
            names=np.load(np_path);mapping={str(n):i for i,n in enumerate(names)};c=cfg['ivf']
            result=analyze_ivf_routing(g,q,bundle['target_ids'],mapping,nlist=c['nlist'],nprobe_list=c['nprobe_list'])
            save('a3_'+model,result,paths+[np_path],model=model,gallery_size=len(g),num_queries=len(q),index_config=c,query_profile='val_labeled')
    if 'a4' in modules:
        # P1 latency anchor uses only the original gallery; distractor validation is P3a.
        for model in ['searle','pic2word']:
            if reusable('a4_anchor_'+model):continue
            print('P1 A4 latency anchor',model,flush=True)
            g,q,_,paths=circo(model);flat=faiss.IndexFlatIP(g.shape[1]);flat.add(g)
            _,truth,tflat=timed_search(flat,q,10);idx=hnsw(g,cfg['experiment_metadata']['random_seed'])
            _,actual,thnsw=timed_search(idx,q,10)
            retention=float(np.mean([len(set(a)&set(t))/10 for a,t in zip(actual,truth)]))
            c=cfg['ivf'];quant=faiss.IndexFlatIP(g.shape[1]);ivf=faiss.IndexIVFFlat(quant,g.shape[1],c['nlist'],faiss.METRIC_INNER_PRODUCT)
            ivf.cp.seed=cfg['experiment_metadata']['random_seed'];ivf.train(g);ivf.add(g);ivf.nprobe=c['default_nprobe']
            _,actual,tivf=timed_search(ivf,q,10)
            ir=float(np.mean([len(set(a)&set(t))/10 for a,t in zip(actual,truth)]))
            save('a4_anchor_'+model,{'N':len(g),'FlatIP':tflat,'HNSWFlat':{**thnsw,'retention':retention,'speedup':tflat['ms_per_query']/thnsw['ms_per_query']},'IVFFlat':{**tivf,'retention':ir,'speedup':tflat['ms_per_query']/tivf['ms_per_query']}},paths,model=model,gallery_size=len(g),num_queries=len(q),index_config={'hnsw':cfg['hnsw']['reference'],'ivf':c},query_profile='val_labeled',scope='P1 timing anchor; not a new scale/distractor or matched-retention claim')
    if 'a5' in modules:
        legacy=ROOT/'data/results/phase2_stageA/json/module_a5_geometry_power.json'
        for row in json.loads(legacy.read_text(encoding='utf-8'))['records']:
            model,ds=row['model'],row['dataset'];prefix='fashioniq_dress' if ds=='fashioniq' else ds
            if reusable(f'a5_geometry_{model}_{ds}'):continue
            gp=ROOT/f'data/embeddings/{model}/{prefix}_gallery.npy'
            print('P1 geometry',model,ds,flush=True)
            g=normalized(np.load(gp));r=geometry(g)
            # No old retention is relabeled as a new result. Fixed-N analysis remains P2c.
            save(f'a5_geometry_{model}_{ds}',r,[gp],model=model,dataset=ds,gallery_size=len(g),num_queries=r['lid_sample_size'],index_config={'type':'FlatIP','purpose':'exact geometry'},profile='geometry_standardized',scope='P1 definitions rerun; no P2c fixed-N/retention regression')
    render()


def render():
    rows=[]
    for p in sorted((OUT/'results').glob('*.json')):
        d=json.loads(p.read_text(encoding='utf-8'));m=d['metadata'];r=d['results']
        rows.append(f"| [{p.stem}](./results/{p.name}) | {m['model']} | {m['dataset']} | {m['gallery_size']} | {m['num_queries']} | {m['hardware']['threads']} |")
    (OUT/'REPORT.md').write_text('# P1 — kết quả chạy lại theo cấu hình chung\n\nKhông trộn với JSON legacy; mỗi file chứa hash đầu vào, snapshot cấu hình, code hash, hardware và phiên bản thư viện.\n\n| Run | Model | Dataset | Gallery | Query/sample | FAISS threads |\n|---|---|---|---|---|---|\n'+'\n'.join(rows)+'\n\nA.2 ở đây chỉ chạy lại phép đo trị tuyệt đối đã có, chưa thay thế P2a. A.5 tính lại định nghĩa RC/LID trên gallery gốc, chưa thay thế P2c N cố định. A.4 chỉ là anchor latency trên gallery gốc; chuỗi mở rộng/distractor cần P3a.\n',encoding='utf-8')
    for number,filename in [('a2','module_a2_pq_perturbation_report.md'),('a3','module_a3_ivf_routing_report.md'),('a4','module_a4_scale_report.md'),('a5','module_a5_geometry_power_report.md')]:
        p=REPORTS/filename;s=p.read_text(encoding='utf-8');marker='\n### Cập nhật P1 — profile chuẩn hóa\n'
        s=s.split(marker)[0]
        lines=[]
        for f in sorted((OUT/'results').glob(number+'*.json')):
            d=json.loads(f.read_text(encoding='utf-8'));r=d['results'];model=d['metadata']['model']
            link=f'../../R2_Audit/p1_reference/results/{f.name}'
            if number=='a2':
                for code,v in r.items():lines.append(f"- {model}, m={code}: RMS random={v['stats_random']['rms']:.6f}, top-10={v['stats_top10']['rms']:.6f}; retention={v['retention_at_10']:.2f}%. [JSON]({link}).")
            elif number=='a3':
                for code,v in r['by_nprobe'].items():lines.append(f"- {model}, nlist={r['nlist']}, nprobe={code}: retention={v['retention_at_10']:.2f}%, coverage={v['retained_candidate_ratio']:.2f}%. [JSON]({link}).")
            elif number=='a4':
                lines.append(f"- {model}, N={r['N']}: FlatIP median={r['FlatIP']['ms_per_query']:.4f} ms/query; HNSW median={r['HNSWFlat']['ms_per_query']:.4f}, retention={r['HNSWFlat']['retention']:.2%}; IVF median={r['IVFFlat']['ms_per_query']:.4f}, retention={r['IVFFlat']['retention']:.2%}. [JSON]({link}).")
            else:lines.append(f"- {model}/{d['metadata']['dataset']}: RC={r['relative_contrast']:.6f}, LID={r['lid_mean']:.6f}; loại {r['lid_excluded_neighborhoods']} neighborhood không hợp lệ. [JSON]({link}).")
        if lines:
            notes={'a2':'Cấu hình nlist/nprobe/m lấy từ JSON mới; không so chênh lệch với legacy như một hiệu ứng chỉ do m.',
                   'a3':'Reference nlist khác legacy; không dùng ngưỡng nprobe của profile này cho profile khác.',
                   'a4':'1 warm-up, 7 lần đo, batch query=1, cùng số luồng; JSON lưu từng lần đo. Chênh lệch với legacy/ICRCV chưa thể quy về một nguyên nhân vì metadata lịch sử thiếu. Không tái xác nhận chuỗi 250K/500K chưa kiểm định distractor.',
                   'a5':'RC là mean cosine distance cặp non-self / mean nearest non-self cosine distance; LID dùng Euclidean chord và MLE k=20. LID legacy dùng 1−cosine (bình phương khoảng cách Euclidean chia hai), có thể làm thay đổi thang ước lượng. Sai khác còn do chọn mẫu và xử lý zero-distance; chưa khẳng định khớp ICRCV khi chưa có cấu hình gốc.'}
            p.write_text(s+marker+'\n'+notes[number]+'\n\n'+'\n'.join(lines)+'\n',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--modules',nargs='+',choices=['a2','a3','a4','a5'],default=['a2','a3','a4','a5']);parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    if args.render_only:render()
    else:run_modules(args.modules)
