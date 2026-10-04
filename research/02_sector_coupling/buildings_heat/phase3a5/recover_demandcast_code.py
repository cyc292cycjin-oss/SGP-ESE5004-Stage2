"""Recover only the documented DemandCast version's boundary-relevant files."""
from pathlib import Path
import hashlib,json,urllib.request
R=Path(__file__).resolve().parent;raw=R/'data/raw/buildings'
reg=json.loads((raw/'SOURCE_REGISTRY.json').read_text(encoding='utf8'))
files=['ETL/download_annual_electricity_data.py','models/xgboost/inference.py','models/README.md','README.md']
tree=json.loads((raw/'demandcast-v090-tree.json').read_text())
by_path={r['path']:r for r in tree['tree']}
for name in files:
    url='https://raw.githubusercontent.com/open-energy-transition/demandcast/v0.9.0/'+name
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Research-provenance-audit/1.0'}),timeout=30) as f:b=f.read()
    blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert blob==by_path[name]['sha']
    dest=R/'evidence/demandcast_v090'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(b)
    reg.append(dict(source_id='DEMANDCAST_CODE_'+name,url=url,file=str(dest.relative_to(R)).replace('\\','/'),
      sha256=hashlib.sha256(b).hexdigest(),git_blob=blob,git_tree=tree['sha'],version='v0.9.0 paper-cited version; not proven export SHA of2026 dataset',
      year='2025',license='Repository license applies; source audit',purpose='Annual electricity/profile boundary trace',access='RETRIEVED',status='UNVERIFIED'))
(raw/'SOURCE_REGISTRY.json').write_text(json.dumps(reg,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(dict(files=len(files),all_git_blobs_match=True)))
