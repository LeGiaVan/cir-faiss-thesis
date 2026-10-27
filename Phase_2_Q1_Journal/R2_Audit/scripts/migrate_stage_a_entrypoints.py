"""One-time migration: archive legacy code and route execution through P1 protocol."""
from pathlib import Path
import ast
import shutil

ROOT=Path(__file__).resolve().parents[3]


def replace_functions(text, replacements):
    lines=text.splitlines(keepends=True)
    nodes=[n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name in replacements]
    for n in sorted(nodes,key=lambda n:n.lineno,reverse=True):
        lines[n.lineno-1:n.end_lineno]=[replacements[n.name].rstrip()+'\n']
    return ''.join(lines)


def main():
    base=ROOT/'src/phase2/stage_a';archive=ROOT/'Phase_2_Q1_Journal/R2_Audit/archive/pre_p0_p1_p2b/scripts'
    archive.mkdir(parents=True,exist_ok=True)
    modules={'measure_hubness.py':'a1','measure_pq_perturbation.py':'a2','measure_ivf_routing.py':'a3','build_distractor_scale.py':'a4','evaluate_geometry_power.py':'a5'}
    renderers={'a1':'generate_hubness_markdown_report','a2':'generate_pq_markdown_report','a3':'generate_ivf_markdown_report','a4':'generate_scale_markdown_report','a5':'generate_geometry_markdown_report'}
    for filename,module in modules.items():
        p=base/filename
        if not (archive/filename).exists():shutil.copy2(p,archive/filename)
        text=p.read_text(encoding='utf-8')
        if 'P1_SHARED_ENTRYPOINT' in text:continue
        if module=='a1':
            main_body='''def main():
    import runpy
    runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts/run_reference_audit.py'), run_name='__main__')
'''
        else:
            main_body=f'''def main():
    import runpy
    runner = runpy.run_path(str(PROTOCOL_ROOT / 'Phase_2_Q1_Journal/R2_Audit/scripts/run_p1_reference.py'))
    runner['run_modules'](['{module}'])
'''
        replacements={'main':main_body}
        # Old report generators are retired; they must never overwrite current reports with old prose.
        for n in ast.parse(text).body:
            if isinstance(n,ast.FunctionDef) and n.name.startswith('generate_') and 'report' in n.name:
                replacements[n.name]=f'''def {n.name}(*args, **kwargs):
    raise RuntimeError('Legacy prose renderer retired. Run render_p0_reports.py for historical results or run_p1_reference.py --render-only for new reference results.')
'''
        if module=='a5':
            replacements['compute_relative_contrast']='''def compute_relative_contrast(gallery, num_samples=None):
    from phase2.protocol import geometry
    r = geometry(gallery)
    return r['relative_contrast'], r['rc_mean_distance'], r['rc_mean_nearest_distance']
'''
            replacements['compute_lid_levina_bickel']='''def compute_lid_levina_bickel(gallery, k=None, num_samples=None):
    from phase2.protocol import geometry
    r = geometry(gallery)
    return r['lid_mean'], r['lid_median']
'''
        text=replace_functions(text,replacements)
        injection='''
# P1_SHARED_ENTRYPOINT: all current runs use the same configuration and metadata.
from pathlib import Path
PROTOCOL_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROTOCOL_ROOT / 'src'))
from phase2.protocol import config as protocol_config
PROTOCOL = protocol_config()
'''
        text=text.replace('import faiss\n','import faiss\n'+injection,1)
        if module=='a2':
            text=text.replace('m_list=[8, 16], nlist=351, nprobe=32','m_list=None, nlist=None, nprobe=None')
            anchor='    N, d = gallery.shape\n'
            text=text.replace(anchor,"    m_list = m_list or PROTOCOL['ivfpq']['audit_m_list']\n    nlist = nlist or PROTOCOL['ivfpq']['nlist']\n    nprobe = nprobe or PROTOCOL['ivfpq']['default_nprobe']\n"+anchor,1)
            text=text.replace('nlist, m, 8, faiss.METRIC_INNER_PRODUCT','nlist, m, PROTOCOL["ivfpq"]["nbits"], faiss.METRIC_INNER_PRODUCT')
            text=text.replace('        index.nprobe = nprobe','        index.cp.seed = PROTOCOL["experiment_metadata"]["random_seed"]\n        index.pq.cp.seed = PROTOCOL["experiment_metadata"]["random_seed"]\n        index.nprobe = nprobe')
            text=text.replace('pred_rms_delta = mean_norm_e / sqrt_d','pred_rms_delta = rms_norm_e / sqrt_d')
            text=text.replace('95% CI','95th percentile (not CI)')
        if module=='a3':
            text=text.replace('nlist: int = 351','nlist: int = None').replace('nprobe_list = [1, 2, 4, 8, 16, 32, 64, 128]','nprobe_list = None')
            text=text.replace('    N, d = gallery.shape','    nlist = nlist or PROTOCOL["ivf"]["nlist"]\n    nprobe_list = nprobe_list or PROTOCOL["ivf"]["nprobe_list"]\n    N, d = gallery.shape',1)
            text=text.replace('verbose=False, spherical=True','verbose=False, spherical=True, seed=PROTOCOL["experiment_metadata"]["random_seed"]')
        if module=='a4':
            text=text.replace("label='FlatIP (Linear Cost O(N))'","label='FlatIP'").replace("label='HNSWFlat (Logarithmic Cost O(log N))'","label='HNSWFlat'")
            text=text.replace("'Scale Crossover: From Flat Exhaustive Search to 1 Million Vectors'","f'Scale benchmark: {min(scales):,}–{max(scales):,} vectors'")
            text=text.replace('"scale_crossover_1m.png"','"scale_crossover_measured.png"')
            # The legacy scale implementation is retained only in the archive, not as an active bypass.
            text=replace_functions(text,{'run_scale_benchmark':'''def run_scale_benchmark(*args, **kwargs):
    raise RuntimeError('Use P1 latency anchor; extended-gallery runs require P3a provenance validation.')
'''})
        p.write_text(text,encoding='utf-8')
    # Keep old A.1 filenames callable while eliminating hardcoded old experiment paths.
    scripts=ROOT/'Phase_2_Q1_Journal/R2_Audit/module_a1_revision/scripts'
    for filename in ['step1_build_neighbor_dataset.py','step4_centering_intervention.py']:
        p=scripts/filename
        if not (archive/filename).exists():shutil.copy2(p,archive/filename)
        p.write_text('''"""Shared-config P1/P2b entrypoint; legacy implementation archived."""
from run_reference_audit import main

if __name__ == '__main__':
    main()
''',encoding='utf-8')
    print('Migrated five Stage A entrypoints and retired old A.1 run paths; original code archived.')


if __name__=='__main__':main()
