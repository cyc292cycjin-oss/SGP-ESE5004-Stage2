"""SYNTHETIC_TEST_ONLY: numerical handoff regressions, never research results."""
import json
from decimal import Decimal
from pathlib import Path
import sys
import tempfile
import numpy as np
import pandas as pd
import linopy
import pypsa
from precision_handoff import transfer,audited_direct_backend,exact,research_scalar_assignment


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    receipt=dict(artifact_role='SYNTHETIC_TEST_ONLY',synthetic_solver_runs=0,real_gate5_runs=0,tests=[])
    def save(): (out/'PRECISION_REGRESSION_RESULTS.json').write_text(json.dumps(receipt,indent=2)+'\n')
    def passed(name,**detail): receipt['tests'].append(dict(test=name,status='PASS',**detail)); save()
    def solve(m,label,direct=True):
        def count_run(*args): receipt['synthetic_solver_runs']+=1;save()
        if direct:
            with audited_direct_backend(out/(label+'_transfer.json'),before_run=count_run):
                return m.solve(solver_name='highs',io_api='direct',log_fn=out/(label+'.log'),threads=2)
        count_run()
        return m.solve(solver_name='highs',io_api='lp',problem_fn=out/(label+'.lp'),keep_files=True,log_fn=out/(label+'.log'),threads=2)
    q=43981693.3088273
    # Choose a representable fixed stock with a positive 12-digit serialized gap.
    candidates=[q+i*0.00001 for i in range(100)]
    q=next(v for v in candidates if Decimal(format(v/365,'.12g'))*365-Decimal(format(v,'.12g'))>Decimal('0.000001'))
    def inventory(shortage=0):
        m=linopy.Model();f=m.add_variables(lower=0,coords=[pd.Index(range(365),name='day')],name='flow')
        end=m.add_variables(lower=0,name='stock_end')
        m.add_constraints(f==q/365,name='fixed-demand')
        m.add_constraints(end+f.sum()==q-shortage,name='fixed-stock')
        m.add_objective(f.sum());return m
    m=inventory(); status=solve(m,'rounded_lp',False)
    assert status[1]=='infeasible',status
    passed('A_12_digit_text_contradiction',stock=q,per_day=q/365,exact_serialized_gap=str(Decimal(format(q/365,'.12g'))*365-Decimal(format(q,'.12g'))),termination=status[1])
    m=inventory();h,mapping,r=transfer(m,slice_size=53)
    # Independent frozen canonical matrix cross-check (small synthetic model only).
    M=m.matrices; lp=h.getLp()
    ri=pd.Index(mapping.matrices.clabels).get_indexer(M.clabels)
    ci=pd.Index(mapping.matrices.vlabels).get_indexer(M.vlabels)
    from scipy.sparse import csr_matrix
    st,starts,inds,vals=h.getRowsEntries(len(ri),ri.astype(np.int32))
    actual=csr_matrix((vals,inds,np.r_[starts,len(vals)]),shape=(len(ri),len(ci)))[:,ci]
    delta=actual-M.A
    assert delta.nnz==0 or np.max(abs(delta.data))==0
    exact(M.lb,np.asarray(lp.col_lower_)[ci],'independent canonical lower')
    exact(M.ub,np.asarray(lp.col_upper_)[ci],'independent canonical upper')
    exact(M.c,np.asarray(lp.col_cost_)[ci],'independent canonical objective')
    assert r['max_absolute_transfer_difference']==0
    passed('B_original_float64_and_frozen_canonical_matrix_preserved',rows=r['constraints'],nnz=r['nnz'])
    status=solve(m,'faithful_feasible'); assert status==('ok','optimal'),status
    assert abs(float(m['stock_end'].solution))<1e-6
    passed('C_feasible_inventory_solved',termination=status[1])
    m=inventory(1);status=solve(m,'real_shortage');assert status[1]=='infeasible',status
    passed('D_real_shortage_remains_infeasible',termination=status[1])
    # Masks, duplicate terms, >= and <= rows, objective sense and label reorder.
    m=linopy.Model(); x=m.add_variables(lower=-2,upper=4,coords=[pd.Index([2,1,0],name='node')],name='x')
    m.add_constraints(x+x<=6,name='duplicates');m.add_constraints(x>=-1,name='lower');m.add_objective(-x.sum(),sense='max')
    h,labels,r=transfer(m,slice_size=2)
    assert r['objective_sense']=='max'; assert r['all_rows_verified']
    passed('B_duplicate_coalescing_and_direction_bounds',rows=r['constraints'])
    n=pypsa.Network();n.set_snapshots(pd.date_range('2013-01-01',periods=3,freq='D'))
    n.add('Bus','synthetic');n.add('Generator','supply',bus='synthetic',p_nom=10,marginal_cost=2)
    n.add('Load','fixed',bus='synthetic',p_set=[1.23456789012345,2,3])
    n.meta={'artifact_role':'SYNTHETIC_TEST_ONLY','scientific_results_allowed':False}
    n.optimize.create_model(); original=n.model
    n.model.add_constraints(n.model['Generator-p'].sum()<=7,name='Research-synthetic-hook')
    one=n.model.add_variables(lower=1,upper=1,name='Research-synthetic-FOM');n.model.objective+=one*17
    def count_network(*args): receipt['synthetic_solver_runs']+=1;save()
    with audited_direct_backend(out/'network_transfer.json',before_run=count_network), research_scalar_assignment():
        status=n.optimize.solve_model(solver_name='highs',io_api='direct',solver_options={'threads':2},log_fn=out/'network.log')
    assert status==('ok','optimal') and n.model is original
    assert 'Research-synthetic-hook' in n.model.constraints
    assert abs(float(one.solution)-1)==0
    exact(n.generators_t.p['supply'].values,n.loads_t.p_set['fixed'].values,'primal labels mapped to original network')
    passed('E_same_model_and_research_hook_retained')
    path=out/'synthetic_solved.nc';n.export_to_netcdf(path);loaded=pypsa.Network(path)
    pd.testing.assert_frame_equal(n.generators_t.p,loaded.generators_t.p,check_freq=False)
    assert loaded.meta==n.meta
    assert np.isclose(n.objective,2*n.loads_t.p_set.sum().sum()+17,rtol=1e-14)
    passed('F_primal_labels_objective_and_netcdf_roundtrip',objective=n.objective)
    receipt['status']='PASS';save();print(json.dumps(receipt,indent=2))

if __name__=='__main__':run(Path(sys.argv[1]))
