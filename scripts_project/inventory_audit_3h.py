"""Original 3h source-chain audit. No daily means, model construction or solve."""
from collections import defaultdict
from fractions import Fraction
import json,math
from pathlib import Path
import numpy as np
from inventory_audit import gamma,power_two
from fixed_accounts import validate_exported_accounting
from gate5_resources import sha

INPUT_SHA='238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'

def source_bound(series,weights,stocks,commodity_count):
    """A priori binary64 chain bound; NOT a solver tolerance or exact feasibility.

    Positive weighted sum: 2T-1 operations. Allocation/share/stock combination:
    conservative 4K-2. Independent weighted-prefix/state arithmetic: 2T-1.
    No daily aggregation operations occur. gamma is valid for n*u < 1.
    Bounds cover source rounding and validation arithmetic, never change data.
    """
    s=np.asarray(series);w=np.asarray(weights)
    if s.dtype!=np.float64 or w.dtype!=np.float64:raise TypeError('float64 required')
    if not len(s) or len(s)!=len(w) or np.any(~np.isfinite(s)) or np.any(~np.isfinite(w)) or np.any(s<0) or np.any(w<=0):raise ValueError('Invalid source series')
    if commodity_count!=len(stocks) or commodity_count<1 or not np.isfinite(stocks).all() or np.any(np.asarray(stocks)<0):raise ValueError('Invalid stocks')
    required=sum((Fraction(float(v))*Fraction(float(h)) for v,h in zip(s,w)),Fraction(0))
    stock=sum(map(lambda v:Fraction(float(v)),stocks),Fraction(0))
    ops=(2*len(s)-1)+(4*commodity_count-2)+(2*len(s)-1)
    magnitude=max(abs(float(required)),abs(float(stock)),math.fsum(float(v)*float(h) for v,h in zip(s,w)))
    be=gamma(ops)*magnitude;bp=be/float(w.min())
    if abs(float(required-stock))>be:raise ValueError('True source shortage/surplus exceeds prior rounding bound')
    return dict(operation_count_bound=ops,source_weighted_sum_operations=2*len(s)-1,
        share_stock_operations=4*commodity_count-2,prefix_state_operations=2*len(s)-1,daily_mean_operations=0,
        unit_roundoff=2.**-53,derived_3h_required_exact=str(required),initial_stocks_exact=str(stock),
        exact_annual_difference=str(required-stock),difference_mwh=float(required-stock),
        exact_binary64_annual_equality=required==stock,original_energy_error_bound_mwh=be,original_power_error_bound_mw=bp,
        scale=power_two(magnitude),bound_fixed_before_solver=True)

def prefix_check(initial,p,e,weights,energy_bound):
    p=np.asarray(p);e=np.asarray(e);w=np.asarray(weights)
    if not (p.dtype==e.dtype==w.dtype==np.float64):raise TypeError('float64 state required')
    if not len(p) or p.shape!=e.shape or p.shape!=w.shape or not np.isfinite(initial) or not np.isfinite(energy_bound) or energy_bound<0:raise ValueError('Invalid prefix inputs')
    if not np.isfinite(p).all() or not np.isfinite(e).all() or not np.isfinite(w).all() or np.any(w<=0):return dict(status='FAIL',reason='NONFINITE_OR_INVALID_WEIGHT')
    expected=initial-np.cumsum(p*w,dtype=np.float64)
    residual=float(np.max(np.abs(e-expected)))
    return dict(status='PASS' if residual<=energy_bound and e.min()>=-energy_bound and abs(e[-1])<=energy_bound and p.min()>=0 else 'FAIL',
                prefix_residual_mwh=residual,min_state_mwh=float(e.min()),terminal_mwh=float(e[-1]),bound_mwh=energy_bound)

def audit(n,root):
    root=Path(root);validate_exported_accounting(n)
    base=root/'results_project/assembly_v1/final_allocation';manifest=json.loads((base/'allocation_manifest.json').read_text())
    registry=root/'research_inputs/assembly_v1/registry.json';reconstruction=root/'research_inputs/assembly_v1/sources/BASE_RECONSTRUCTION.json'
    if sha(base/manifest['arrays_file'])!=manifest['arrays_sha256'] or sha(registry)!=manifest['input_registry_sha256']:raise ValueError('Allocation source identity changed')
    records={r['InputID']:r for r in json.loads(registry.read_text())['records']};alloc={r['InputID']:r for r in manifest['records']}
    source=json.loads(reconstruction.read_text())['selected_rows'];demand=n.get_switchable_as_dense('Load','p_set');h=n.snapshot_weightings.stores.to_numpy()
    groups=defaultdict(list)
    for store,route in n.meta['biomass_obligation_routes'].items():groups[tuple(sorted(route['buses']))].append(store)
    report=[];integrals=[]
    with np.load(base/manifest['arrays_file']) as arrays:
        if not np.array_equal(arrays['weights'],h):raise ValueError('Original 3h allocation weights differ')
        for ident,ids in n.loads.groupby('source_account_id').groups.items():
            ar=alloc[ident];actual=float((demand[list(ids)].sum(axis=1)*h).sum());expected=float(ar['AnnualMWh'])
            if not math.isclose(actual,expected,rel_tol=5e-13,abs_tol=1e-7):raise ValueError('Account annual integral changed: '+ident)
            integrals.append(dict(account=ident,actual_mwh=actual,source_mwh=expected,status='PASS'))
        for number,(buses,stores) in enumerate(groups.items()):
            ids=n.loads.index[n.loads.bus.isin(buses)]
            if len(ids)!=1:raise ValueError('Fixed-resource group owner changed')
            load=ids[0];ident=n.loads.at[load,'source_account_id'];ar=alloc[ident];r=records[ident]
            node=load[len(ident)+1:];series=arrays[ar['ArrayKey']][:,ar['Nodes'].index(node)]
            if not np.array_equal(series,demand[load].to_numpy()):raise ValueError('3h source-to-node sequence differs')
            annual=float((series*arrays['weights']).sum())
            rows=[x for x in source if x['Country']==r['Country'] and x['Account']==r['Account'] and x['Carrier']=='biomass']
            total=sum(float(x['MWh']) for x in rows);byid={x['RowID']:x for x in rows};components=[];stocks=[]
            for store in stores:
                route=n.meta['biomass_obligation_routes'][store];row=byid[route['source_row']];stock=annual*float(row['MWh'])/total
                if not stock==n.stores.at[store,'e_initial']==n.stores.at[store,'e_nom']==route['annual_cap_mwh']:raise ValueError('Original stock source chain mismatch')
                stocks.append(stock);components.append(dict(store=store,source_row=row['RowID'],commodity=route['commodity'],initial_mwh=stock,source_mwh=float(row['MWh'])))
            bound=source_bound(series,h,stocks,len(stores))
            report.append(dict(group=number,source_account_id=ident,load=load,stores=stores,final_buses=list(buses),commodity_rows=components,
                source_annual_account_mwh=ar['AnnualMWh'],source_node_annual_mwh=annual,source_match='EXACT_ORIGINAL_2920_SEQUENCE',floating_quantity_changes=0,**bound))
    return dict(status='PASS',method='ORIGINAL_3H_SOURCE_CHAIN_POWER_OF_TWO_SCALING',source_input_sha256=INPUT_SHA,snapshots=2920,
        groups=report,group_count=len(report),store_count=sum(len(g['stores']) for g in report),account_integrals=integrals,
        max_energy_error_bound_mwh=max(g['original_energy_error_bound_mwh'] for g in report),
        source_hashes={str(p.relative_to(root)):sha(p) for p in [registry,reconstruction,base/'allocation_manifest.json',base/manifest['arrays_file']]},
        mathematical_scope='Original 3h problem; not equivalence to daily Gate5. Exact rational differences explicitly retained. Source-rounding acceptance is not proof of exact binary64 feasibility.',
        solver_tolerances_changed=False,solver_calls=0,model_builds=0,daily_mean_operations=0,
        bound_formula='gamma((2T-1)+(4K-2)+(2T-1))*max(abs(exact demand),abs(exact stocks),weighted sum); T=2920; power bound=energy bound/3h')
