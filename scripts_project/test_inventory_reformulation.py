"""LOCAL_DIAGNOSTIC_ONLY: bounded A/B/C comparisons and physical negative cases."""
import json,sys,math
from pathlib import Path
import numpy as np,pandas as pd,pypsa,highspy
from scipy.sparse import csr_matrix,eye
from assembly_components import install_research_constraint_hooks
from inventory_audit import audit,evaluate_block,sha
from precision_handoff import ok,exact

def extract(n,m,g):
    final,stores=g['final_buses'],g['stores'];buses=list(final)+n.stores.loc[stores,'bus'].tolist()
    links=n.links.index[n.links.bus0.isin(buses)|n.links.bus1.isin(buses)].tolist();frames=[];names={}
    for name,c in m.constraints.items():
        if name=='Bus-nodal_balance':selected=c.sel(Bus=buses)
        elif name.startswith(('Store-','Link-')):
            prefix='Store' if name.startswith('Store-') else 'Link';dims=[d for d in c.coord_dims if d.startswith(prefix)]
            if not dims:continue
            dim=dims[0];ids=[s for s in (stores if prefix=='Store' else links) if s in c.coords[dim].values]
            if not ids:continue
            selected=c.sel({dim:ids})
        elif name in {'ResearchStoreDirection-'+s for s in stores}:selected=c
        else:continue
        f=selected.flat
        if len(f):names.update({int(k):name for k in f.labels.unique()});frames.append(f[['labels','vars','coeffs','rhs','sign']])
    f=pd.concat(frames,ignore_index=True);r=f.drop_duplicates('labels');cl=r.labels.to_numpy(dtype=np.int64);vl=np.sort(f.vars.unique())
    a=csr_matrix((f.coeffs.to_numpy(),(pd.Index(cl).get_indexer(f.labels),pd.Index(vl).get_indexer(f.vars))),shape=(len(cl),len(vl)));a.sum_duplicates();a.sort_indices();a.eliminate_zeros()
    vf=m.variables.flat.set_index('labels').loc[vl];rhs=r.rhs.to_numpy();sign=r.sign.to_numpy()
    return dict(data=a.data,indices=a.indices,indptr=a.indptr,shape=np.array(a.shape),row_lower=np.where(sign!='<=',rhs,-np.inf),row_upper=np.where(sign!='>=',rhs,np.inf),var_lower=vf.lower.to_numpy(),var_upper=vf.upper.to_numpy(),variable_labels=vl,constraint_labels=cl),[names[int(k)] for k in cl]

def cumulative(d,names):
    """Invertible prefix sum of each Store's energy equations; local comparison."""
    a=csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']));energy=[i for i,n in enumerate(names) if n=='Store-energy_balance']
    current={};nextrow={};roots=[]
    for i in energy:
        js=range(a.indptr[i],a.indptr[i+1]);negative=[a.indices[j] for j in js if a.data[j]==-1];positive=[a.indices[j] for j in js if a.data[j]==1]
        assert len(negative)==1
        current[i]=negative[0]
        if positive: assert len(positive)==1;nextrow[positive[0]]=i
        else:roots.append(i)
    transform=eye(a.shape[0],format='lil');visited=set()
    for first in roots:
        row=first;prefix=[]
        while True:
            prefix.append(row);visited.add(row);transform.rows[row]=prefix.copy();transform.data[row]=[1.]*len(prefix)
            if current[row] not in nextrow:break
            row=nextrow[current[row]]
    assert visited==set(energy)
    t=transform.tocsr();b=(t@a).tocsr();b.eliminate_zeros();b.sort_indices()
    lo=d['row_lower'].copy();up=d['row_upper'].copy()
    for i in energy:
        ids=t.indices[t.indptr[i]:t.indptr[i+1]]
        assert np.array_equal(d['row_lower'][ids],d['row_upper'][ids])
        lo[i]=up[i]=math.fsum(d['row_lower'][ids])
    # Prefix sums are inverted by adjacent differencing; verify original rows.
    for first in roots:
        row=first;previous=None
        while True:
            original=b[row] if previous is None else b[row]-b[previous]
            delta=(original-a[row]).data
            assert np.all(delta==0)
            assert (lo[row] if previous is None else lo[row]-lo[previous])==d['row_lower'][row]
            if current[row] not in nextrow:break
            previous,row=row,nextrow[current[row]]
    return b,lo,up

def run(root,out):
    out.mkdir(parents=True,exist_ok=False);source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
    n=pypsa.Network(source);previous=root/'results_project/validation/inventory_local_20261006_01'
    identity=json.loads((previous/'FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())
    assert sha(source)==identity['source_input_sha256']
    (out/'FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').write_text(json.dumps(identity,indent=2)+'\n')
    n.optimize.create_model();install_research_constraint_hooks(n);m=n.model
    groups=identity['groups'];pick=sorted(set([120,320,min(groups,key=lambda g:g['source_node_annual_mwh'])['group'],max(groups,key=lambda g:g['source_node_annual_mwh'])['group'],0]))
    result={'role':'LOCAL_DIAGNOSTIC_AND_SYNTHETIC_TEST_ONLY','real_gate5_runs':0,'local_solver_runs':0,'synthetic_solver_runs':0,'tests':[],'presolve_option':'choose (unchanged)','primal_feasibility_tolerance':1e-7,'source_identity':{k:v for k,v in identity.items() if k!='groups'}}
    def save(): (out/'LOCAL_NUMERICAL_REGRESSION_RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    def solve(d,names,g,method,label,synthetic=False):
        a=csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']));lo=d['row_lower'].copy();up=d['row_upper'].copy();lb=d['var_lower'].copy();ub=d['var_upper'].copy();scale=g['scale']
        if method in ['A','A_CROSSOVER']:
            lo/=scale;up/=scale;lb/=scale;ub/=scale
            exact(lo*scale,d['row_lower'],'A inverse RHS');exact(up*scale,d['row_upper'],'A inverse RHS');exact(lb*scale,d['var_lower'],'A inverse bounds');exact(ub*scale,d['var_upper'],'A inverse bounds')
        elif method=='B':a,lo,up=cumulative(d,names)
        h=highspy.Highs();ok(h.setOptionValue('output_flag',False));ok(h.setOptionValue('threads',2));ok(h.setOptionValue('solver','ipm'));ok(h.setOptionValue('run_crossover','on' if method=='A_CROSSOVER' else 'off'));ok(h.setOptionValue('log_file',str(out/(label+'.log'))));ok(h.setOptionValue('log_to_console',False))
        if method=='C':ok(h.setOptionValue('user_bound_scale',-g['scale_exponent']))
        ok(h.addVars(a.shape[1],lb,ub));ok(h.addRows(a.shape[0],lo,up,a.nnz,a.indptr.astype(np.int32),a.indices.astype(np.int32),a.data))
        ids=np.arange(a.shape[0],dtype=np.int32);st,_,rlo,rup,_=h.getRows(len(ids),ids);ok(st);exact(rlo,lo/scale if method=='C' else lo,'received transformed lower');exact(rup,up/scale if method=='C' else up,'received transformed upper')
        st,starts,ix,v=h.getRowsEntries(len(ids),ids);ok(st);exact(starts,a.indptr[:-1],'received offsets');exact(ix,a.indices,'received indices');exact(v,a.data,'received transformed matrix')
        result['synthetic_solver_runs' if synthetic else 'local_solver_runs']+=1;save()
        ok(h.setOptionValue('output_flag',True));h.run();status=h.getModelStatus().name
        record=dict(test=label,group=g['group'],method=method,solver_status=status,transformed_nnz=int(a.nnz),scale=scale,source_quantity_changes=0)
        if status=='kOptimal':
            x=np.asarray(h.getSolution().col_value)*(scale if method in ['A','A_CROSSOVER','C'] else 1.)
            record['original_unit_validation']=evaluate_block(d,x,g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'],names)
            if method=='C':
                lp=h.getLp();record['api_lp_restored_original_bounds']=bool(np.array_equal(lp.row_lower_,d['row_lower']) and np.array_equal(lp.row_upper_,d['row_upper']))
            np.save(out/(label+'_original_primal.npy'),x)
        else:record['original_unit_validation']={'accepted':False,'reason':'no primal'}
        result['tests'].append(record);save();return record
    blocks={}
    for group in pick:
        g=groups[group];d,names=extract(n,m,g);blocks[group]=(d,names)
        np.savez_compressed(out/f'block_{group}.npz',**d);(out/f'block_{group}_row_names.json').write_text(json.dumps(names)+'\n')
        methods=['A_CROSSOVER']
        if group==120:methods+=['C']
        if group==320:methods+=['B','C']
        if group==79:
            prior=json.loads((previous/'CROSSOVER_JUSTIFICATION_PROBE.json').read_text());prior.update(group=79,method='A_CROSSOVER',reused_from_previous_probe=True);result['tests'].append(prior);methods=[]
        for method in methods:
            r=solve(d,names,g,method,f'block_{group}_{method}');print(r,flush=True)
    # A witness of block 320 is mapped exactly by power-of-two scaling; it is not
    # prescribed as a commodity production schedule.
    from fractions import Fraction
    witness=json.loads((root/'research/04_model_assembly/final_validation/precision_handoff_evidence/block_320_rational_feasible_witness.json').read_text())
    assert all(Fraction(v)/Fraction(groups[320]['scale'])*Fraction(groups[320]['scale'])==Fraction(v) for v in witness.values())
    result['rational_witness_invertible_mapping']='PASS'
    d,names=blocks[120];g=groups[120]
    init=[i for i,name in enumerate(names) if name=='Store-energy_balance' and d['row_lower'][i]!=0]
    assert len(init)==1
    for label,short in [('real_1_mwh_shortage',1.),('outside_roundoff_shortage',max(100*g['original_energy_error_bound_mwh'],1e-3))]:
        bad={k:v.copy() for k,v in d.items()};i=init[0];bad['row_lower'][i]+=short;bad['row_upper'][i]+=short
        r=solve(bad,names,g,'A_CROSSOVER',label,synthetic=True)
        if r['original_unit_validation']['accepted']:raise AssertionError('Scaled acceptance hid real shortage')
    x=np.load(out/'block_320_A_CROSSOVER_original_primal.npy');d,names=blocks[320];g=groups[320]
    # Violate one terminal stock directly, and inject unbalanced free supply.
    base=json.loads((root/'research/04_model_assembly/final_validation/precision_handoff_evidence/EXACT_LOCAL_DIAGNOSIS_VERIFICATION.json').read_text())['blocks'][1]
    for label,mutator in [('negative_inventory',lambda z:z.__setitem__(list(d['variable_labels']).index(base['terminal_nonnegative_bounds'][0]['variable']),-1.)),('extra_supply',lambda z:z.__setitem__(0,z[0]+1.))]:
        bad=x.copy();mutator(bad);checked=evaluate_block(d,bad,g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'],names)
        # Nominal capacity may have no upper limit: choose an actual nonzero flow
        # column for the extra-supply test rather than a free nominal parameter.
        if label=='extra_supply':
            bad=x.copy();a=csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']));i=next(i for i,v in enumerate(names) if v=='Bus-nodal_balance');col=a.indices[a.indptr[i]];bad[col]+=1.;checked=evaluate_block(d,bad,g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'],names)
        assert not checked['accepted'];result['tests'].append(dict(test=label,status='PASS_REJECTED',original_unit_validation=checked))
    # Wrong efficiency: perturb an actual source-bus equation coefficient.
    bad={k:v.copy() for k,v in d.items()}
    choices=[j for i,v in enumerate(names) if v=='Bus-nodal_balance' for j in range(d['indptr'][i],d['indptr'][i+1])]
    j=max(choices,key=lambda j:abs(x[d['indices'][j]]));bad['data'][j]*=.9
    checked=evaluate_block(bad,x,g['original_energy_error_bound_mwh'],g['original_power_error_bound_mw'],names);assert not checked['accepted']
    result['tests'].append(dict(test='wrong_efficiency',status='PASS_REJECTED',original_unit_validation=checked))
    positive=[r for r in result['tests'] if r.get('method')=='A_CROSSOVER' and r['test'].startswith('block_')]
    result['selected_method']='A_CROSSOVER';result['status']='PASS' if all(r['original_unit_validation']['accepted'] for r in positive) else 'FAILED_LOCAL_ORIGINAL_UNIT_CHECKS'
    save();print('FINAL',result['status'],result['local_solver_runs'],result['synthetic_solver_runs'],flush=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];run(root,root/'results_project/validation/inventory_local_20261006_02')
