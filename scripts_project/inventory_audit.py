"""Source-identity audit and a-priori roundoff budgets. No source changes."""
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
import hashlib,json,math
import numpy as np
from fixed_accounts import validate_exported_accounting

FROZEN='7a07a0ec728b7cc4b9b27a4a2461b67c960790750fd45eed6a3705624c8e06cd'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def power_two(q):
    mantissa,exp=math.frexp(q)
    return math.ldexp(1.,exp-1 if mantissa==.5 else exp)
def gamma(n):
    u=2.**-53
    return n*u/(1-n*u)

def audit(n,root):
    validate_exported_accounting(n)
    base=root/'results_project/assembly_v1/final_allocation'
    manifest=json.loads((base/'allocation_manifest.json').read_text()); arrays=np.load(base/manifest['arrays_file'])
    if sha(base/manifest['arrays_file'])!=manifest['arrays_sha256']:raise ValueError('Allocation bytes changed')
    registry=root/'research_inputs/assembly_v1/registry.json'
    if sha(registry)!=manifest['input_registry_sha256']:raise ValueError('Registry binding changed')
    reconstruction=root/'research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json'
    source=json.loads(reconstruction.read_text())['selected_rows']
    records={r['InputID']:r for r in json.loads(registry.read_text())['records']}
    allocations={r['InputID']:r for r in manifest['records']}
    grouped=defaultdict(list)
    for s,r in n.meta['biomass_obligation_routes'].items():grouped[tuple(sorted(r['buses']))].append(s)
    demand=n.get_switchable_as_dense('Load','p_set'); report=[]
    for group,(final,stores) in enumerate(grouped.items()):
        loadids=n.loads.index[n.loads.bus.isin(final)]
        if len(loadids)!=1:raise ValueError('Audited frozen identity expects one node/account load')
        key=loadids[0];ident=n.loads.at[key,'source_account_id'];ar=allocations[ident];r=records[ident]
        node=key[len(ident)+1:];j=ar['Nodes'].index(node);series=arrays[ar['ArrayKey']][:,j]
        annual=float((series*arrays['weights']).sum())
        raw=[z for z in source if z['Country']==r['Country'] and z['Account']==r['Account'] and z['Carrier']=='biomass']
        total=sum(float(z['MWh']) for z in raw);raw_by_id={z['RowID']:z for z in raw}
        recomputed=[]
        for s in stores:
            route=n.meta['biomass_obligation_routes'][s];z=raw_by_id[route['source_row']]
            value=annual*float(z['MWh'])/total
            if value!=n.stores.at[s,'e_initial'] or value!=n.stores.at[s,'e_nom'] or value!=route['annual_cap_mwh']:raise ValueError('Stock source-operation chain mismatch: '+s)
            recomputed.append(dict(store=s,commodity=route['commodity'],source_row=z['RowID'],base_commodity_mwh=float(z['MWh']),initial_mwh=value))
        daily=series.reshape(365,8).mean(axis=1)
        if not np.array_equal(daily,demand[key].values):raise ValueError('Daily mean is not the source-derived load: '+key)
        req=sum((Fraction(float(q))*Fraction(float(w)) for q,w in zip(demand[key],n.snapshot_weightings.stores)),Fraction(0))
        stock=sum((Fraction(float(n.stores.at[s,'e_initial'])) for s in stores),Fraction(0))
        # Sequential-sum upper bound (pairwise implementations can be tighter):
        # native time weighting+sum: 2*N-1; raw-composition sum, multiply/divide
        # and stock sum: 4*K-2; daily mean: 8; daily weighting+sum: 2*T-1.
        ops=(2*len(series)-1)+(4*len(stores)-2)+8+(2*len(n.snapshots)-1)
        magnitude=max(float(stock),float(req),abs(annual))
        budget=gamma(ops)*magnitude
        if abs(float(req-stock))>budget:raise ValueError('Annual mismatch exceeds pre-solve source rounding bound')
        scale=power_two(magnitude)
        report.append(dict(group=group,source_account_id=ident,load=key,final_buses=list(final),stores=stores,source_annual_account_mwh=ar['AnnualMWh'],source_node_annual_mwh=annual,
            commodity_rows=recomputed,source_composition_total_mwh=total,derived_daily_required_exact=str(req),initial_stocks_exact=str(stock),exact_annual_difference=str(req-stock),
            difference_mwh=float(req-stock),relative_difference=float((req-stock)/stock),operation_count_bound=ops,unit_roundoff=2.**-53,original_energy_error_bound_mwh=budget,
            original_power_error_bound_mw=budget/float(n.snapshot_weightings.stores.min()),scale=scale,scale_exponent=int(math.log2(scale)),
            floating_quantity_changes=0,source_match='EXACT_RECOMPUTATION',bound_fixed_before_solver=True))
    result=dict(method='POWER_OF_TWO_FIXED_INVENTORY_SCALING',source_input_sha256=FROZEN,groups=report,group_count=len(report),store_count=sum(len(g['stores']) for g in report),
        positive_differences=sum(g['difference_mwh']>0 for g in report),negative_differences=sum(g['difference_mwh']<0 for g in report),max_relative_difference=max(abs(g['relative_difference']) for g in report),
        max_energy_error_bound_mwh=max(g['original_energy_error_bound_mwh'] for g in report),source_hashes={'registry':sha(registry),'allocation_manifest':sha(base/'allocation_manifest.json'),'allocation_arrays':sha(base/manifest['arrays_file']),'base_reconstruction':sha(reconstruction)},
        distinction='No RHS or scientific quantity is adjusted. Reversible scaling preserves exact infeasibility. Acceptance within a-priori source-operation rounding bounds is finite-precision treatment, not proof of exact feasibility of the original binary64 model.',
        bound_formula='gamma_n=n*u/(1-n*u), u=2^-53; n=(2*2920-1)+(4*K-2)+8+(2*365-1). B_E=gamma_n*max(node annual, sum stocks, weighted daily total), B_P=B_E/min(hours). Same conservative bound also covers 365-step state arithmetic. Not derived from solver outcomes or solver tolerance.')
    return result

def evaluate_block(d,x,budget_mwh,budget_mw,row_names):
    """Independent original-unit checks; no relative solver tolerance shortcut."""
    from scipy.sparse import csr_matrix
    a=csr_matrix((d['data'],d['indices'],d['indptr']),shape=tuple(d['shape']))
    # fsum avoids cancellation hidden by ordinary sparse accumulation.
    value=np.array([math.fsum(float(a.data[j])*float(x[a.indices[j]]) for j in range(a.indptr[i],a.indptr[i+1])) for i in range(a.shape[0])])
    lo,hi=d['row_lower'],d['row_upper'];violation=np.maximum(np.maximum(lo-value,value-hi),0.)
    budget=np.array([budget_mwh if name.startswith('Store-') and ('-e-' in name or 'energy_balance' in name) else budget_mw for name in row_names])
    vviol=np.maximum(np.maximum(d['var_lower']-x,x-d['var_upper']),0.)
    # Variable bounds here are free/default nominal lower bounds. Use stricter MW budget.
    return dict(accepted=bool(np.isfinite(x).all() and np.all(violation<=budget) and np.all(vviol<=budget_mw)),max_original_row_violation=float(violation.max()),max_variable_bound_violation=float(vviol.max()),worst_row=int(d['constraint_labels'][int(violation.argmax())]),energy_budget_mwh=budget_mwh,power_budget_mw=budget_mw)
