from pathlib import Path
import json,hashlib,zipfile,ast
W=Path(__file__).resolve().parent;R=W/'release'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
old=W.parent/'c02_daily_build_20261012/cloud_evidence/original_run_receipts/artifacts'
records={name:sha(old/name) for name in ['SCHEME_A_DAILY_EXACT_GROUPS.json','C02_NETWORK_LP_DIFF_REGISTER.json','NETWORK_READBACK.json']}
(R/'REUSE_BUILD_RECEIPTS.json').write_text(json.dumps(records,indent=2)+'\n')
files={}
for p in sorted(R.rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts and p.name!='C03_RELEASE_MANIFEST.json':
        if p.suffix=='.py':ast.parse(p.read_text())
        files[str(p.relative_to(R))]={'bytes':p.stat().st_size,'sha256':sha(p)}
m={'version':'C02R_C03_DAILY_122_COMBINED_V1','parent_git_commit':'291fcd057e14a73eb093a986348846a74f8e40eb','files':files,'code_scope':'checker/storage/labels/lifecycle only; no scientific formula changes','daily_network_sha256':'b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2','authorization_sha256':'db5f437777b731e996e304c3077ad77830e14c5dc0694f815d265050fbe36b4d'}
(R/'C03_RELEASE_MANIFEST.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
z=W/'C02R_C03_122_RELEASE.zip'
with zipfile.ZipFile(z,'x',zipfile.ZIP_DEFLATED) as f:
    for rel in sorted([*files,'C03_RELEASE_MANIFEST.json']):f.write(R/rel,rel)
with zipfile.ZipFile(z) as f:assert f.testzip() is None
receipt={'zip_path':str(z),'zip_bytes':z.stat().st_size,'zip_sha256':sha(z),'manifest_sha256':sha(R/'C03_RELEASE_MANIFEST.json'),'members':len(files)+1,'payload_bytes':sum(x['bytes'] for x in files.values()),'CRC':'PASS'}
(W/'RELEASE_DELIVERY.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
