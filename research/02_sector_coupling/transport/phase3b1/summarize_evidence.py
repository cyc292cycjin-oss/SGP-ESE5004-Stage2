"""Summarize saved evidence without rerunning a source workflow or model."""
from pathlib import Path
import json,math,hashlib
R=Path(__file__).resolve().parent
def plain(x):
    if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
    if isinstance(x,list):return [plain(v) for v in x]
    if isinstance(x,float) and not math.isfinite(x):return 'NaN' if math.isnan(x) else str(x)
    return x
p=R/'evidence/NETWORK_TRANSPORT_EVIDENCE.json'
data=plain(json.loads(p.read_text()))
for case in data:
    for row in case['transport_loads']:
        if 'emissions' in row['carrier'] and 'weighted_MWh' in row:
            row['weighted_tCO2']=row.pop('weighted_MWh')
            row['min_tCO2_per_h']=row.pop('min_MW');row['max_tCO2_per_h']=row.pop('max_MW')
p.write_text(json.dumps(data,indent=2,allow_nan=False))
rows=[]
for case in data:
    ld=[r for r in case['transport_loads'] if 'weighted_MWh' in r]
    rows.append(dict(role=case['role'],file=Path(case['path']).name,loads={c:dict(count=len(vals:=[r for r in ld if r['carrier']==c]),nonfinite_count=sum(not isinstance(r['weighted_MWh'],(float,int)) for r in vals),finite_subtotal_MWh=sum(r['weighted_MWh'] for r in vals if isinstance(r['weighted_MWh'],(float,int))),subtotal_is_total=all(isinstance(r['weighted_MWh'],(float,int)) for r in vals)) for c in sorted({r['carrier'] for r in ld})},links={c:n for c,n in case['component_counts']['links'].items() if any(t in c for t in ['BEV','V2G','H2 liquefaction'])},ev_stores={c:n for c,n in case['component_counts']['stores'].items() if any(t in c.lower() for t in ['ev battery','li ion','battery storage'])}))
(R/'evidence/NETWORK_SUMMARY.json').write_text(json.dumps(rows,indent=2))
sources=json.loads((R/'evidence/SOURCE_MANIFEST.json').read_text())
source_map={(s['layer'],s['path']):s for s in sources}
diffs=[]
for (layer,path),src in source_map.items():
    if layer=='U' and ('P',path) in source_map:diffs.append(dict(path=path,same_bytes=src['sha256']==source_map['P',path]['sha256']))
(R/'evidence/P_U_FILE_COMPARISON.json').write_text(json.dumps(diffs,indent=2))
print(json.dumps(rows,indent=2))
