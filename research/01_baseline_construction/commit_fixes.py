"""Commit only reviewed source fixes/tests and export portable Git patches."""
from engineering_review import *
patches=HERE/'patches';patches.mkdir(exist_ok=True)
records=[]
for folder,paths,message in [
 ('fix_industrial_gdp',['scripts/build_shapes.py','scripts/build_industry_demand.py','tests/test_industrial_conservation.py','tests/test_gdp_cache.py'],'fix: restore ASEAN GDP coverage and conserve national industrial demand'),
 ('fix_carbon_config',['configs/config.asean.yaml','tests/test_asean_carbon_budget.py'],'fix: restore paper carbon trajectory through the current budget key')]:
    repo=BASE/folder
    subprocess.run(['git','-C',str(repo),'diff','--check'],check=True)
    subprocess.run(['git','-C',str(repo),'add','--',*paths],check=True)
    subprocess.run(['git','-C',str(repo),'commit','-m',message],check=True)
    sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    patch=subprocess.check_output(['git','-C',str(repo),'format-patch','-1','--stdout'])
    target=patches/(folder+'.patch');target.write_bytes(patch)
    records.append({'branch':subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip(),'sha':sha,'message':message,'patch':str(target.relative_to(HERE)),'patch_sha256':hashlib.sha256(patch).hexdigest(),'status':subprocess.check_output(['git','-C',str(repo),'status','--porcelain'],text=True)})
(HERE/'FIX_COMMITS.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
