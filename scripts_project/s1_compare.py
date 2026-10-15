"""Cross-scenario V5 gates (B5, B6) and the cost-layer hash identity check (B12) for S1.

    python scripts_project/s1_compare.py gates --integrated <solve dir> --disconnected <solve dir> --output <json>
    python scripts_project/s1_compare.py hash --with-layer <nc> --without-layer <nc> --output <json>
"""
from pathlib import Path
import argparse,hashlib,json,sys
HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str)+'\n')

def gates(repo,integrated,disconnected,output):
    import pypsa,logging
    logging.disable(logging.CRITICAL)
    from phase4_static import config
    from v5.v5_gates import gate_b5_single_switch,gate_b6_cost,load_contract
    ri=json.loads((Path(integrated)/'SOLVE_RECEIPT.json').read_text());rd=json.loads((Path(disconnected)/'SOLVE_RECEIPT.json').read_text())
    if ri['label']!=rd['label']:raise ValueError('Scenario runs carry different labels')
    # An infeasible or failed scenario has no solved network: B5 then uses the unsolved input
    # (capacity structure only, flows not evaluable) and B6 is NOT_EVALUABLE. Nothing is relaxed.
    def load(r):
        if r.get('solved_network'):return pypsa.Network(r['solved_network']),'SOLVED'
        n=pypsa.Network(r['input_network']['path'])
        for typ,nom in [('Line','s_nom'),('Link','p_nom')]:n.df(typ)[nom+'_opt']=n.df(typ)[nom]
        return n,'UNSOLVED_'+str(r.get('termination_condition',r.get('decision','FAILED'))).upper()
    ni,si=load(ri);nd,sd=load(rd)
    b5=gate_b5_single_switch(config(repo,'integrated'),config(repo,'disconnected'),n_dis_solved=nd,n_int_solved=ni);b5['disconnected_state']=sd;b5['integrated_state']=si
    if sd!='SOLVED':b5['flow_check']='NOT_EVALUABLE_NO_SOLUTION (capacity structure checked on the unsolved network)'
    if si=='SOLVED' and sd=='SOLVED':b6=gate_b6_cost(ri['objective'],rd['objective'])
    else:b6=dict(gate='B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED',passed=None,status='NOT_EVALUABLE',integrated_state=si,disconnected_state=sd,integrated_objective=ri.get('objective'),disconnected_objective=rd.get('objective'),note='a scenario without an optimal solution has no comparable total cost; no constraint was relaxed to obtain one')
    contract=load_contract()
    out=dict(label=ri['label'],contract=contract['contract_id'],result_label=contract['result_label'],B5=b5,B6=b6,inputs=dict(integrated=ri.get('solved_network') or ri['input_network']['path'],disconnected=rd.get('solved_network') or rd['input_network']['path']),passed=bool(b5['passed'] and b6.get('passed')))
    save(output,out);print(json.dumps(dict(B5=b5['passed'],B6=b6.get('passed'),states=[si,sd])));return out

def canonical_hash(path):
    """Content hash independent of NetCDF variable order: every component table sorted by index and
    column, every time series, snapshot weightings and the metadata with sorted keys."""
    import pypsa,logging,pandas as pd
    logging.disable(logging.CRITICAL)
    n=pypsa.Network(str(path));h=hashlib.sha256()
    h.update(json.dumps(n.meta,sort_keys=True,default=str).encode())
    h.update(pd.util.hash_pandas_object(n.snapshot_weightings.sort_index().sort_index(axis=1),index=True).to_numpy().tobytes())
    for name in sorted(c.name for c in n.iterate_components()):
        df=n.df(name).sort_index().sort_index(axis=1).astype(str)
        h.update(name.encode());h.update(pd.util.hash_pandas_object(df,index=True).to_numpy().tobytes())
        for attr in sorted(n.pnl(name)):
            fr=n.pnl(name)[attr]
            if len(fr.columns):h.update(attr.encode());h.update(fr.sort_index(axis=1).to_numpy(dtype='<f8').tobytes())
    return h.hexdigest()

def hash_check(with_layer,without_layer,output):
    a,b=sha(with_layer),sha(without_layer);ca,cb=canonical_hash(with_layer),canonical_hash(without_layer)
    out=dict(gate='B12_COST_LAYER_HASH_IDENTITY',with_layer=dict(file=str(with_layer),sha256=a,canonical_sha256=ca),without_layer=dict(file=str(without_layer),sha256=b,canonical_sha256=cb),
             file_identical=a==b,content_identical=ca==cb,passed=(a==b and ca==cb),
             rule='all research.cost_scaling factors 1.0 -> NetCDF byte-identical to a build without the layer (builds run with PYTHONHASHSEED=0 because PyPSA writes components in set-iteration order); content hash is order-independent')
    save(output,out);print(json.dumps(dict(file_identical=a==b,content_identical=ca==cb)));return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['gates','hash']);p.add_argument('--repo',type=Path,default=HERE.parent);p.add_argument('--integrated',type=Path);p.add_argument('--disconnected',type=Path);p.add_argument('--with-layer',type=Path);p.add_argument('--without-layer',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='gates':gates(a.repo,a.integrated,a.disconnected,a.output)
    else:hash_check(a.with_layer,a.without_layer,a.output)
