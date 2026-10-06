"""Exact rational certificate/witness for already extracted local blocks.

No solver, no modified demands/stocks. A proportional release is only a
feasibility witness for the closed local block, never an imposed dispatch.
"""
from pathlib import Path
from fractions import Fraction
from decimal import Decimal,getcontext
import json,sys
import numpy as np,pypsa
from assembly_components import install_research_constraint_hooks
from run_gate5_validation import dump,sha

def run(root,out):
    getcontext().prec=100
    original=json.loads((out/'LOCAL_FIXED_BLOCK_DIAGNOSIS.json').read_text())
    source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
    if sha(source)!=original['source_sha256']:raise ValueError('Input identity changed')
    n=pypsa.Network(source);n.optimize.create_model();install_research_constraint_hooks(n);m=n.model
    reports=[]
    for block in original['blocks']:
        if block['presolve_status']!='kInfeasible':continue
        number=block['group'];path=out/f'block_{number}.npz'
        if sha(path)!=block['local_binary_sha256']:raise ValueError('Local matrix changed')
        d=np.load(path);vl=d['variable_labels'];cl=d['constraint_labels'];terms=d['data'];inds=d['indices'];starts=d['indptr']
        final=block['final_buses'];stores=block['stores'];flows={};vals={}
        ids=n.loads.index[n.loads.bus.isin(final)]
        demand=n.get_switchable_as_dense('Load','p_set')[ids].sum(axis=1)
        stocks={s:Fraction(float(n.stores.at[s,'e_initial'])) for s in stores};total=sum(stocks.values())
        for s in stores:
            bus=n.stores.at[s,'bus'];link=n.links.index[n.links.bus0.eq(bus)][0]
            assert n.links.at[link,'efficiency']==1 and n.stores.at[s,'standing_loss']==0 and not n.stores.at[s,'e_cyclic']
            p=[Fraction(float(q))*stocks[s]/total for q in demand];e=stocks[s]
            for snap,flow in zip(n.snapshots,p):
                e-=Fraction(float(n.snapshot_weightings.at[snap,'stores']))*flow
                vals[int(m['Store-p'].labels.sel(snapshot=snap,Store=s))]=flow
                vals[int(m['Store-e'].labels.sel(snapshot=snap,Store=s))]=e
                vals[int(m['Link-p'].labels.sel(snapshot=snap,Link=link))]=flow
            vals[int(m['Link-p_nom'].labels.sel({'Link-ext':link}))]=max(p)
        if set(map(int,vl))!=set(vals):raise ValueError('Witness does not cover exact extracted columns')
        violations=[];zero=Fraction(0)
        for i,label in enumerate(cl):
            value=sum((Fraction(float(terms[j]))*vals[int(vl[inds[j]])] for j in range(starts[i],starts[i+1])),zero)
            lo,hi=d['row_lower'][i],d['row_upper'][i]
            if (np.isfinite(lo) and value<Fraction(float(lo))) or (np.isfinite(hi) and value>Fraction(float(hi))):
                violations.append({'row':int(label),'value':str(value),'lower':str(lo),'upper':str(hi)})
        for i,label in enumerate(vl):
            value=vals[int(label)];lo,hi=d['var_lower'][i],d['var_upper'][i]
            if (np.isfinite(lo) and value<Fraction(float(lo))) or (np.isfinite(hi) and value>Fraction(float(hi))):violations.append({'variable':int(label),'value':str(value),'lower':str(lo),'upper':str(hi)})
        # Verify the exact sum certificate's terminal nonnegativity in source rows.
        terminal=list(map(int,block['exact_binary64_algebra']['nonzero_lhs']));bounds=[]
        for i,label in enumerate(cl):
            js=list(range(starts[i],starts[i+1]))
            if len(js)==1 and int(vl[inds[js[0]]]) in terminal and terms[js[0]]==1 and d['row_lower'][i]==0:
                bounds.append(dict(variable=int(vl[inds[js[0]]]),row=int(label),lower=0))
        if {r['variable'] for r in bounds}!=set(terminal):raise ValueError('Terminal nonnegative source rows absent')
        record=dict(group=number,final_buses=final,local_binary_sha256=sha(path),presolve_status=block['presolve_status'],exact_binary64_algebra=block['exact_binary64_algebra'],terminal_nonnegative_bounds=bounds,
            witness_rows_checked=len(cl),witness_variable_bounds_checked=len(vl),exact_rational_witness_feasible=not violations,violations=violations,
            solver_runs=0,method='Fractions of exact input binary64; all local row/column bounds checked without tolerance. Witness only, not a production schedule.')
        if not violations:
            witness={str(k):str(v) for k,v in vals.items()};dump(out/f'block_{number}_rational_feasible_witness.json',witness)
            record['conclusion']='LOCAL_PRESOLVE_NUMERICAL_REJECTION_OF_EXACT_FEASIBLE_BLOCK'
        elif Decimal(block['exact_binary64_algebra']['rhs'])>0:
            record['conclusion']='EXACT_BINARY64_CONTRADICTION_AT_SUB_MICRO_MWH_SCALE'
        else:record['conclusion']='WITNESS_FAILED_NOT_A_GENERAL_INFEASIBILITY_PROOF'
        reports.append(record)
    dump(out/'EXACT_LOCAL_DIAGNOSIS_VERIFICATION.json',dict(status='COMPLETED',optimization_runs=0,blocks=reports));print(json.dumps(reports,indent=2))

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1];run(root,root/'results_project/validation/gate5_20261006_02/local_diagnosis')
