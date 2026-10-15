"""Actual-network preservation against the prior delivered input assets; no solver."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,pandas as pd,pypsa
from build_diagnostic_network import read,save,sha,verify_guards,check_physical_reachability,normalise_optional_strings
from check_assembly_inputs import load_registry
from build_research_network import build as full_build

def validate(repo,prior,output):
    root=repo/'results_project/assembly_v1';assets=root/'assets';manifest=read(root/'DIAGNOSTIC_NETWORK_MANIFEST.json');n=pypsa.Network(root/'research_2050_diagnostic_partial_unsolved.nc');verify_guards(n)
    if sha(root/'research_2050_diagnostic_partial_unsolved.nc')!=manifest['network_sha256']:raise ValueError('Diagnostic bytes changed')
    old=pypsa.Network(prior/'production_assets/electric_base_2050_unsolved.nc');base=pypsa.Network(assets/'electric_base_2050_unsolved.nc')
    normalise_optional_strings(old);normalise_optional_strings(base)
    if old.meta['existing_unit_components']!=base.meta['existing_unit_components'] or base.meta['existing_unit_components']!=n.meta['existing_unit_components']:raise ValueError('Existing stock identity/capacity changed')
    for comp in old.iterate_components():
        pd.testing.assert_frame_equal(comp.df.sort_index(),base.df(comp.name).sort_index().reindex(columns=comp.df.columns),check_dtype=False,check_names=False,rtol=1e-12,atol=1e-12)
        for attr,frame in comp.pnl.items():
            if len(frame.columns):pd.testing.assert_frame_equal(frame,base.pnl(comp.name)[attr].reindex(columns=frame.columns),check_dtype=False,check_names=False,check_freq=False,rtol=1e-12,atol=1e-12)
    for f in ['model_cost_layer.json','external_pending_fixed_accounts.json']:
        if sha(assets/f)!=sha(prior/'production_assets'/f):raise ValueError('Unchanged fixed or price layer drifted')
    oldalloc=read(prior/'actual_allocation/allocation_manifest.json');newalloc=read(root/'allocation/allocation_manifest.json');oldrows={r['InputID']:r for r in oldalloc['records']};newrows={r['InputID']:r for r in newalloc['records']}
    if not set(oldrows)<=set(newrows):raise ValueError('Previously qualified demand removed')
    changed=[];same=[]
    with np.load(prior/'actual_allocation'/oldalloc['arrays_file'],allow_pickle=False) as a,np.load(root/'allocation'/newalloc['arrays_file'],allow_pickle=False) as b:
        for k,r in oldrows.items():
            z=newrows[k]
            if r['ArraySHA256']==z['ArraySHA256']:
                np.testing.assert_array_equal(a[r['ArrayKey']],b[z['ArrayKey']]);same.append(k)
            else:changed.append(dict(InputID=k,BeforeAnnualMWh=r['AnnualMWh'],AfterAnnualMWh=z['AnnualMWh'],DeltaMWh=z['AnnualMWh']-r['AnnualMWh']))
    if any(not (x['InputID'].startswith('MM:2050:') and ':OtherNEC:oil' in x['InputID']) for x in changed):raise ValueError('Unapproved changed demand allocation')
    added=[newrows[k] for k in sorted(set(newrows)-set(oldrows))]
    if any(not(x['InputID'].startswith('TL:2050:') and ':OtherNEC:oil' in x['InputID']) for x in added):raise ValueError('Unapproved new physical account')
    # Run the ORIGINAL complete entry: it must still refuse and leave no full net.
    complete=root/'research_fullsc_2050_unsolved.nc'
    if complete.exists():raise ValueError('Unexpected full network exists')
    code=full_build(repo,root/'allocation',assets/'asset_bundle.json',complete,output/'FULL_ENTRY_REFUSAL.json')
    if code!=2 or complete.exists():raise ValueError('Partial data escaped complete gate')
    from assembly_components import install_research_constraint_hooks
    try:install_research_constraint_hooks(n)
    except ValueError as exc:
        if 'Diagnostic partial' not in str(exc):raise
    else:raise ValueError('Diagnostic allowed optimization hook')
    m=dict(existing_units=len(n.meta['existing_unit_components']),existing_mw=sum(r['capacity_mw'] for r in n.meta['existing_unit_components'].values()),new_existing_mw=0.,unchanged_allocation_count=len(same),changed_allocations=changed,added_allocations=added,all_old_accounts_preserved=True,price_layer_byte_identical=True,fixed_ledger_byte_identical=True,full_entry_refused=True,full_network_exists=False,diagnostic_optimization_hook_refused=True,physical_reachability=check_physical_reachability(n),solver_runs=0)
    save(output/'ACTUAL_PRESERVATION.json',m);print(json.dumps(m,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['repo','prior','output']:p.add_argument('--'+name,type=Path,required=True)
    validate(**vars(p.parse_args()))
