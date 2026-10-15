"""Bounded exact-input submatrix presolve diagnostics; no optimization runs."""
import json,sys,hashlib
from pathlib import Path
from collections import defaultdict
from decimal import Decimal,getcontext
import numpy as np,pandas as pd,pypsa,highspy
from scipy.sparse import csr_matrix
from assembly_components import install_research_constraint_hooks
from precision_handoff import ok,exact
from run_gate5_validation import dump,sha

def run(root,out):
    getcontext().prec=100
    out.mkdir(parents=True,exist_ok=False)
    source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
    assert sha(source)=='7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'
    n=pypsa.Network(source);n.optimize.create_model();install_research_constraint_hooks(n);m=n.model
    groups=defaultdict(list)
    for name,r in n.meta['biomass_obligation_routes'].items():groups[tuple(sorted(r['buses']))].append(name)
    source_vars=m.variables.flat.set_index('labels')
    results=[]; failures=0
    for number,(final,stores) in enumerate(groups.items()):
        buses=list(final)+n.stores.loc[stores,'bus'].tolist()
        links=n.links.index[n.links.bus0.isin(buses)|n.links.bus1.isin(buses)].tolist()
        frames=[];row_sources={}
        for name,c in m.constraints.items():
            if name=='Bus-nodal_balance':selected=c.sel(Bus=buses)
            elif name.startswith('Store-'):
                dims=[d for d in c.coord_dims if d.startswith('Store')]
                if not dims:continue
                dim=dims[0];ids=[s for s in stores if s in c.coords[dim].values]
                if not ids:continue
                selected=c.sel({dim:ids})
            elif name.startswith('Link-'):
                dims=[d for d in c.coord_dims if d.startswith('Link')]
                if not dims:continue
                dim=dims[0];ids=[s for s in links if s in c.coords[dim].values]
                if not ids:continue
                selected=c.sel({dim:ids})
            elif name in {'ResearchStoreDirection-'+s for s in stores}:selected=c
            else:continue
            f=selected.flat
            if not f.empty:
                row_sources.update({int(k):name for k in f.labels.unique()});frames.append(f[['labels','vars','coeffs','rhs','sign']])
        f=pd.concat(frames,ignore_index=True);rr=f.drop_duplicates('labels');cl=rr.labels.to_numpy(dtype=np.int64)
        vl=np.sort(f.vars.unique());rows=pd.Index(cl).get_indexer(f.labels);cols=pd.Index(vl).get_indexer(f.vars)
        a=csr_matrix((f.coeffs.to_numpy(),(rows,cols)),shape=(len(cl),len(vl)));a.sum_duplicates();a.sort_indices();a.eliminate_zeros()
        v=source_vars.loc[vl];lb=v.lower.to_numpy();ub=v.upper.to_numpy();rhs=rr.rhs.to_numpy();sign=rr.sign.to_numpy()
        rl=np.where(sign!='<=',rhs,-np.inf);ru=np.where(sign!='>=',rhs,np.inf)
        h=highspy.Highs();ok(h.setOptionValue('output_flag',False));ok(h.setOptionValue('threads',2))
        ok(h.addVars(len(vl),lb,ub));ok(h.addRows(len(cl),rl,ru,a.nnz,a.indptr.astype(np.int32),a.indices.astype(np.int32),a.data))
        ids=np.arange(len(cl),dtype=np.int32);st,_,rlo,rup,_=h.getRows(len(ids),ids);ok(st);exact(rl,rlo,'local lower');exact(ru,rup,'local upper')
        st,starts,inds,vals=h.getRowsEntries(len(ids),ids);ok(st)
        rec=csr_matrix((vals,inds,np.r_[starts,len(vals)]),shape=a.shape);rec.sort_indices()
        exact(a.indptr,rec.indptr,'local offsets');exact(a.indices,rec.indices,'local indices');exact(a.data,rec.data,'local data')
        h.presolve();status=h.getModelPresolveStatus().name
        report=dict(group=number,final_buses=list(final),stores=stores,rows=len(cl),columns=len(vl),nnz=a.nnz,presolve_status=status,actual_optimize_runs=0,scope='Exact original model row/column subset; sufficient local rejection only, not a whole-model IIS')
        if status=='kInfeasible':
            failures+=1
            # Store exact binary input, label map and selected original constraints.
            np.savez_compressed(out/f'block_{number}.npz',data=a.data,indices=a.indices,indptr=a.indptr,shape=a.shape,row_lower=rl,row_upper=ru,var_lower=lb,var_upper=ub,variable_labels=vl,constraint_labels=cl)
            dump(out/f'block_{number}_rows.json',row_sources)
            # Same closed-block algebra as the original certificate, independently
            # accumulated on source binary64 inputs. No new demand or boundary.
            lhs=defaultdict(Decimal);total=Decimal(0);count=0
            for i,label in enumerate(cl):
                name=row_sources[int(label)]
                factor=Decimal(24) if name=='Bus-nodal_balance' else Decimal(1) if name=='Store-energy_balance' else None
                if factor is None:continue
                assert sign[i]=='='
                count+=1;total+=factor*Decimal.from_float(float(rhs[i]))
                for j in range(a.indptr[i],a.indptr[i+1]):lhs[int(vl[a.indices[j]])]+=factor*Decimal.from_float(float(a.data[j]))
            report['exact_binary64_algebra']={'equations':count,'rhs':str(total),'nonzero_lhs':{str(k):str(v) for k,v in lhs.items() if v}}
            report['local_binary_sha256']=sha(out/f'block_{number}.npz')
        results.append(report)
        if number%25==0:print(f'LOCAL {number+1}/{len(groups)}; rejected={failures}',flush=True)
    dump(out/'LOCAL_FIXED_BLOCK_DIAGNOSIS.json',dict(source_sha256=sha(source),optimization_runs=0,local_presolve_calls=len(results),infeasible_local_blocks=failures,blocks=results))
    print('COMPLETE',len(results),failures,flush=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];run(root,root/'results_project/validation/gate5_20261006_02/local_diagnosis')
