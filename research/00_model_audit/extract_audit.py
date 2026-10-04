"""Read frozen source/input/output metadata; never import workflow or solve.
Run with existing WSL Python, passing source repo and output directory.
"""
import sys
sys.dont_write_bytecode = True
import json, hashlib, subprocess, math
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import pypsa

root, out = map(Path, sys.argv[1:3])
out.mkdir(parents=True, exist_ok=True)
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()
def git(*a): return subprocess.check_output(['git','-C',str(root),*a],text=True).strip()
report={'read_at':datetime.now(timezone.utc).isoformat(),'root':str(root),'head':git('rev-parse','HEAD'),'status_before':git('status','--short'),'networks':[], 'inputs':[]}
for p in sorted((root/'results/baseline-aims-3H-tutorial/postnetworks').glob('*.nc')):
    n=pypsa.Network(p)
    rec={'file':str(p.relative_to(root)),'sha256':sha(p),'meta':{k:n.meta.get(k) for k in ['co2','sector','final_adjustment','scenario','demand_data','costs']},'weights':n.snapshot_weightings.sum().to_dict(),'constraints':n.global_constraints.reset_index().to_dict('records'),'components':{}}
    for comp,df in [('buses',n.buses),('loads',n.loads),('generators',n.generators),('links',n.links),('stores',n.stores),('storage_units',n.storage_units),('lines',n.lines)]:
        rows=[]
        for carrier,g in df.groupby('carrier',dropna=False):
            row={'carrier':carrier,'count':len(g)}
            for col in ['p_nom_extendable','e_nom_extendable','s_nom_extendable']:
                if col in g: row[col]=int(g[col].sum())
            for col in ['capital_cost','marginal_cost','p_nom_max','e_nom_max']:
                if col in g: row[col+'_range']=[float(g[col].min()),float(g[col].max())]
            if comp=='loads':
                vals=n.get_switchable_as_dense('Load','p_set').loc[:,g.index]
                row['weighted_demand_MWh']=float((vals.sum(axis=1)*n.snapshot_weightings.generators).sum())
                row['nonzero_loads']=int((vals.abs().sum()>0).sum())
            rows.append(row)
        rec['components'][comp]=rows
    rec['co2_stores']=n.stores[n.stores.carrier.str.contains('co2',case=False)].reset_index().to_dict('records')
    rec['emission_carriers']=n.carriers[n.carriers.co2_emissions!=0].reset_index().to_dict('records')
    rec['dangling_link_ports']={c:n.links.index[(n.links[c]!='') & ~n.links[c].isin(n.buses.index)].tolist() for c in n.links.columns if c.startswith('bus')}
    report['networks'].append(rec)
patterns=['resources/baseline-aims-3H-tutorial/*cost*.csv','resources/baseline-aims-3H-tutorial/energy_totals*.csv','data/AEO8-input/*.csv','data/demand/*.csv','data/demand/unsd/paths/*.xlsx','data/ports/*','data/worldbank_pop_forecast.csv','config.yaml','results/baseline-aims-3H-tutorial/configs/*.yaml']
for pattern in patterns:
    for p in sorted(root.glob(pattern)):
        if p.is_file():
            rec={'file':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)}
            if p.suffix=='.csv':
                try:
                    d=pd.read_csv(p); rec.update(rows=len(d),columns=list(d.columns),sample=d.head(2).to_dict('records'))
                except Exception as e: rec['error']=str(e)
            report['inputs'].append(rec)
            # Small exact copies, original bytes retained; no upstream write.
            if p.suffix in ['.csv','.yaml','.json','.xlsx'] and p.stat().st_size<5000000:
                dest=out/'input_snapshot'/p.relative_to(root); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(p.read_bytes())
report['resource_top']= [str(p.relative_to(root)) for p in (root/'resources').glob('*')]
report['status_after']=git('status','--short')
def portable(v):
    if isinstance(v,float) and not math.isfinite(v):return 'NaN' if math.isnan(v) else ('Infinity' if v>0 else '-Infinity')
    if isinstance(v,dict):return {k:portable(x) for k,x in v.items()}
    if isinstance(v,list):return [portable(x) for x in v]
    return v
(out/'AUDIT_RUNTIME_EVIDENCE.json').write_text(json.dumps(portable(report),ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
print(json.dumps({'head':report['head'],'network_count':len(report['networks']),'input_count':len(report['inputs']),'status_before':report['status_before'],'status_after':report['status_after']}))
