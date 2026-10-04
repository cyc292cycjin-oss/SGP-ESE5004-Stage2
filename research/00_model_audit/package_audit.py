"""Package the requested audit and its evidence; excludes runtime links and intermediates."""
from pathlib import Path
import hashlib,json,zipfile
root=Path(__file__).resolve().parent
code=Path('C:/Users/20122/.codex/.chatgpt-projects/g-p-6ab8040523e881918c18587a52a2527d/audit_repo')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['Snakefile','config.default.yaml','configs/config.asean.yaml','configs/scenarios.asean.yaml','configs/tutorials/config.asean.yaml','configs/tutorials/config.sgp-lowmem.yaml','configs/tutorials/config.sgp-simplex.yaml','configs/bundle_config.yaml','configs/powerplantmatching_config.yaml','scripts/_helpers.py','scripts/final_asean_adjustment.py','scripts/prepare_sector_network.py','scripts/prepare_network.py','scripts/solve_network.py','scripts/append_cost_data.py','scripts/process_cost_data.py','scripts/build_demand_profiles.py','scripts/build_base_energy_totals.py','scripts/prepare_energy_totals.py','scripts/build_industry_demand.py','scripts/build_base_industry_totals.py','scripts/prepare_ports.py','scripts/prepare_airports.py','scripts/add_existing_baseyear.py','scripts/add_brownfield.py','doc-asean/docs/index.md']
(root/'SOURCE_CODE_MANIFEST.json').write_text(json.dumps({'commit':'ce327bfae2abe5526d4c1976173f0f8d08366ba5','root':str(code),'source_files':[{ 'path':p,'sha256':sha(code/p)} for p in paths]},indent=2)+'\n',encoding='utf-8',newline='\n')
skip={'node_modules','__pycache__','ledger_records.json','FILE_HASHES.json'}
files=sorted(p for p in root.glob('*') if p.is_file() and p.name not in skip)
files+=sorted(p for p in (root/'input_snapshot').rglob('*') if p.is_file())
manifest=[{'path':p.relative_to(root).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files]
(root/'FILE_HASHES.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
archive=root.parents[1]/'outputs/model_audit_20260930.zip'
archive.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files+[root/'FILE_HASHES.json']: z.write(p,'model_audit_20260930/'+p.relative_to(root).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for r in manifest:
        assert hashlib.sha256(z.read('model_audit_20260930/'+r['path'])).hexdigest()==r['sha256']
print(json.dumps({'archive':str(archive),'files':len(manifest)+1,'bytes':archive.stat().st_size,'sha256':sha(archive),'zip_integrity':'PASS'}))
