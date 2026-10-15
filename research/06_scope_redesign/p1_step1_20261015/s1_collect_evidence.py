"""Assemble S1_EVIDENCE.json from the receipts written by the S1 scripts (read-only; run from this folder).

    python s1_collect_evidence.py
"""
from pathlib import Path
import hashlib,json,subprocess,time

HERE=Path(__file__).resolve().parent
REPO=Path(r'\\wsl.localhost\Ubuntu\home\jin\research\SGP_ESE5004_Stage2\phase2\research_model')
S1=REPO/'results_project'/'s1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def opt(p):return read(p) if Path(p).exists() else None
def wsl(cmd):
    r=subprocess.run(['wsl.exe','-e','bash','-c',cmd],capture_output=True,text=True);return r.stdout.replace('\x00','').strip()

def main():
    ev=dict(schema='s1-evidence-v1',generated_epoch=time.time(),branch=wsl('cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model && git rev-parse --abbrev-ref HEAD'),head=wsl('cd /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model && git rev-parse HEAD'),
            skeleton_status='INTERIM_S1_SKELETON',solver_runs_on_research_networks=0,smoke_test_label='SMOKE_TEST_ONLY')
    ev['stock_review']=opt(S1/'S1_STOCK_REVIEW.json')
    ev['memory_estimate']=opt(S1/'S1_BUILD_MEMORY_ESTIMATE.json');ev['memory_measured']=opt(S1/'S1_BUILD_MEMORY_MEASURED.json')
    ev['builds']={}
    for s in ['integrated','disconnected']:
        r=opt(S1/s/f'{s}_BUILD_RECEIPT.json')
        if r:
            ev['builds'][s]=dict(status=r['status'],network=r['network'],daily_network={k:v for k,v in r.get('daily_network',{}).items() if k!='aggregation'},inputs=r['inputs'],research_config_sha256=r['research_config_sha256'],
                                 cross_border={k:{kk:vv for kk,vv in v.items() if kk not in ('edges','pipelines','removed')} for k,v in r['cross_border'].items()},transmission_limit=r['transmission_limit'],demand=r['demand'],
                                 upstream={k:v for k,v in r['upstream'].items() if k not in ('pipeline_endpoint_remaps',)},candidates=r['candidates'],static_validation={k:v for k,v in r['static_validation'].items() if k!='guard_replacements'},
                                 inventory=r['inventory'],rename_map_count=r['rename_map_count'],atmosphere_moves=r['atmosphere_moves'],u4_zeroed_carriers=r['u4_zeroed_carriers'],cost_scaling=r['cost_scaling'],code_sha=r['code_sha'],build_seconds=r['build_seconds'])
    ev['cost_layer_hash_check']=opt(S1/'S1_COST_LAYER_HASH_CHECK.json');ev['determinism_check']=opt(S1/'S1_DETERMINISM_CHECK.json')
    ev['smoke']={}
    for s in ['integrated','disconnected']:
        d=S1/'smoke'/s
        if (d/'SOLVE_RECEIPT.json').exists():
            r=read(d/'SOLVE_RECEIPT.json');ev['smoke'][s]=dict(receipt={k:v for k,v in r.items() if k not in ('solver_parameters',)},gates=opt(d/'V5_GATES.json'),emissions=opt(d/'EMISSIONS_BY_COUNTRY.json'),infeasibility=opt(d/'INFEASIBILITY_DIAGNOSIS.json'),
                                                                 files={p.name:sha(p) for p in d.glob('*.csv')})
    ev['smoke']['B5_B6']=opt(S1/'smoke'/'S1_SMOKE_B5_B6.json')
    ev['corridors']=dict(file='research_inputs/corridors/cross_border_corridors.csv',sha256=sha(REPO/'research_inputs/corridors/cross_border_corridors.csv'))
    ev['lifetime_decisions_s1']=dict(file='research_inputs/asset_survival/lifetime_decisions_s1.json',sha256=sha(REPO/'research_inputs/asset_survival/lifetime_decisions_s1.json'))
    ev['configs']={f:sha(REPO/'configs/research'/f) for f in ['baseline.yaml','integrated.yaml','disconnected.yaml']}
    ev['tests']=opt(HERE/'S1_TEST_RUN.json')
    ev['release']=opt(HERE/'S1_RELEASE_DELIVERY.json')
    ev['local_license_review']=opt(HERE/'S1_LOCAL_LICENSE_REVIEW.json')
    ev['r12a']=opt(HERE/'R12A_WIND_ZERO_DIAGNOSIS.json')
    out=HERE/'S1_EVIDENCE.json';out.write_text(json.dumps(ev,indent=2,ensure_ascii=False,default=str)+'\n',encoding='utf-8')
    print('written',out,sha(out))

if __name__=='__main__':main()
