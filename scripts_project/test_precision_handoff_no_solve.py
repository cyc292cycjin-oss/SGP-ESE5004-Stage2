"""Binary64 handoff regressions only: no optimization, LP solve, or presolve."""
import json, sys
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
import highspy, linopy, numpy as np, pandas as pd
from scipy.sparse import csr_matrix
from precision_handoff import transfer, exact


def canonical_check(m, size):
    h, mapping, receipt = transfer(m, slice_size=size)
    try:
        M=m.matrices; lp=h.getLp()
        ri=pd.Index(mapping.matrices.clabels).get_indexer(M.clabels)
        ci=pd.Index(mapping.matrices.vlabels).get_indexer(M.vlabels)
        assert (ri>=0).all() and (ci>=0).all()
        _, starts, inds, vals=h.getRowsEntries(len(ri),ri.astype(np.int32))
        actual=csr_matrix((vals,inds,np.r_[starts,len(vals)]),shape=(len(ri),len(ci)))[:,ci]
        delta=actual-M.A
        assert delta.nnz==0 or np.max(abs(delta.data))==0
        for key, native in [('lb',lp.col_lower_),('ub',lp.col_upper_),('c',lp.col_cost_)]:
            exact(getattr(M,key),np.asarray(native,dtype=np.float64)[ci],key)
        assert receipt['max_absolute_transfer_difference']==0 and receipt['all_rows_verified']
        assert not receipt['solver_run_started']
        return receipt
    finally:
        h.clear()


def run():
    checks=[]
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('REAL SOLVE FORBIDDEN')), patch.object(highspy.Highs,'presolve',side_effect=AssertionError('PRESOLVE FORBIDDEN')):
        q=43981693.3088273
        q=next(v for v in [q+i*0.00001 for i in range(100)] if Decimal(format(v/365,'.12g'))*365-Decimal(format(v,'.12g'))>Decimal('0.000001'))
        gap=Decimal(format(q/365,'.12g'))*365-Decimal(format(q,'.12g'))
        checks.append(dict(test='12_digit_serialization_contradiction_arithmetic_only',status='PASS',gap=str(gap)))
        m=linopy.Model()
        flow=m.add_variables(lower=0,coords=[pd.Index(range(365),name='day')],name='flow')
        end=m.add_variables(lower=0,name='stock_end')
        m.add_constraints(flow==q/365,name='fixed-demand')
        m.add_constraints(end+flow.sum()==q,name='fixed-stock');m.add_objective(flow.sum())
        receipt=canonical_check(m,53)
        checks.append(dict(test='independent_canonical_sparse_matrix_bounds_costs_and_all_rows_exact',status='PASS',variables=receipt['variables'],constraints=receipt['constraints']))
        m=linopy.Model()
        x=m.add_variables(lower=-2,upper=4,coords=[pd.Index([2,1,0],name='node')],name='x')
        m.add_constraints(x+x<=6,name='duplicates');m.add_constraints(x>=-1,name='lower')
        m.add_objective(-x.sum(),sense='max')
        receipt=canonical_check(m,2);assert receipt['objective_sense']=='max'
        checks.append(dict(test='duplicates_direction_bounds_max_sense_and_reordered_labels',status='PASS'))
    return dict(status='PASS',scope='SMALL_NATIVE_TRANSFER_WITHOUT_SOLVING',solver_runs=0,presolve_calls=0,checks=checks,
                excluded='Solve-dependent tests in test_precision_handoff.py and test_inventory_mapping.py are not invoked; no new feasibility/optimality claim.')


if __name__=='__main__':
    Path(sys.argv[1]).write_text(json.dumps(run(),indent=2)+'\n')
