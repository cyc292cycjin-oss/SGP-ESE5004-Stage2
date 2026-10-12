"""No-rebuild raw vector to scientific component tables. Not an acceptance bypass."""
from pathlib import Path
import hashlib,json,pickle,sys,math
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'gurobi_barrier_preparation_20261009'))
from adapter import sha256,open_problem
from author_objective import reconcile_objectives

def scatter_active(labels,active_labels,values,missing=0.):
    labels=np.asarray(labels);ok=labels>=0;flat=labels[ok]
    positions=np.searchsorted(active_labels,flat)
    if np.any(positions>=len(active_labels)) or not np.array_equal(active_labels[positions],flat):raise ValueError('active label mismatch')
    out=np.full(labels.shape,missing,dtype=np.float64);out[ok]=values[positions]
    if not np.isfinite(out).all():raise ValueError('nonfinite mapped result')
    return out

def original_labels(block,start,n):
    size=int(np.prod(block['shape']));labels=np.arange(start,start+size,dtype=np.int64).reshape(block['shape'])
    if block['name']=='StorageUnit-spill':labels=np.where(n.get_switchable_as_dense('StorageUnit','inflow').to_numpy()>0,labels,-1)
    a=np.ascontiguousarray(labels);h=hashlib.sha256();h.update(str(a.dtype).encode());h.update(str(a.shape).encode());h.update(memoryview(a).cast('B'))
    if h.hexdigest()!=block['labels_sha256']:raise ValueError('block label hash')
    for dim in block['dims']:
        idx=pd.DatetimeIndex(n.snapshots.values,name='snapshot') if dim=='snapshot' else (n.get_extendable_i(dim[:-4]).rename(dim) if dim.endswith('-ext') else n.df(dim).index.rename(dim))
        if hashlib.sha256(pickle.dumps(idx,protocol=5)).hexdigest()!=block['coordinate_sha256'][dim]:raise ValueError('coordinate hash')
    return labels

def restore_tables(n,mapping,active_labels,original_x):
    """n must be a freshly loaded byte-verified frozen network, never n.model."""
    scalars={};start=0
    for block in mapping['variables']:
        labels=original_labels(block,start,n);start+=int(np.prod(block['shape']))
        v=scatter_active(labels,active_labels,original_x);name=block['name']
        if not block['dims']:scalars[name]=float(v);continue
        c,attr=name.split('-',1);df=n.df(c)
        if 'snapshot' not in block['dims']:
            n.df(c).loc[n.get_extendable_i(c),attr+'_opt']=v;continue
        frame=pd.DataFrame(v,index=n.snapshots,columns=df.index)
        if name=='Line-s':n.pnl(c)['p0']=frame;n.pnl(c)['p1']=-frame
        elif name=='Link-p':
            n.links_t['p0']=frame
            for port in [x for x in df if x.startswith('bus') and x[3:].isdigit() and x!='bus0']:
                suffix=port[3:];eff='efficiency'+('' if suffix=='1' else suffix)
                result=-frame*n.get_switchable_as_dense('Link',eff)
                result.loc[:,df[port]=='']=0.
                n.links_t['p'+suffix]=result
        else:n.pnl(c)[attr]=frame
    for c,nom in [('Generator','p_nom'),('Link','p_nom'),('Line','s_nom'),('StorageUnit','p_nom'),('Store','e_nom')]:
        df=n.df(c);ids=df.index[~df[nom+'_extendable']];df.loc[ids,nom+'_opt']=df.loc[ids,nom]
    n.storage_units_t['p']=n.storage_units_t.p_dispatch-n.storage_units_t.p_store
    n.loads_t['p']=n.get_switchable_as_dense('Load','p_set').copy()
    return scalars

def load_objective_overlay(base_folder,derivation_path):
    """Reuse old adapter: only cost and offset differ, every structural array referenced."""
    base_folder=Path(base_folder);record=json.loads(Path(derivation_path).read_text())
    if sha256(base_folder/'MATH_PROBLEM.json')!=record['original_math_manifest_sha256']:raise ValueError('base manifest')
    meta,a=open_problem(base_folder,verify=True)
    c=Path(record['adapted_objective']['path'])
    if sha256(c)!=record['adapted_objective']['sha256']:raise ValueError('adapted cost')
    changed=np.load(c,mmap_mode='r',allow_pickle=False)
    if changed.dtype!=np.float64 or changed.shape!=a['cost'].shape:raise ValueError('adapted cost schema')
    a=dict(a,cost=changed);meta=dict(meta,offset=record['adapted_objective']['offset'])
    return meta,a,record

def mathematical_gap_decision(metrics):
    """Proposed 1 ppm numerical certificate, separate from physical gates and approval."""
    scale=max(1.,abs(metrics['primal_objective']),abs(metrics['dual_objective_numeric']))
    keys=['relative_gap','stationarity_normalized_max','complementarity_l1','stationarity_weighted_l1']
    valid=all(math.isfinite(metrics[k]) and metrics[k]>=0 for k in keys) and all(math.isfinite(metrics[k]) for k in ['primal_objective','dual_objective_numeric'])
    good=valid and metrics['relative_gap']<=1e-6 and metrics['stationarity_normalized_max']<=1e-6 and metrics['complementarity_l1']/scale<=1e-6 and metrics['stationarity_weighted_l1']/scale<=1e-6
    return {'numeric_draft_pass':bool(good),'full_acceptance':False,'dual_sign_physical_semantic_export_gates':'REQUIRED_SEPARATELY','original_objective_optimality':'NOT_PROVEN'}
