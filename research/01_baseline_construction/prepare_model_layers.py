"""Create isolated checkouts from existing Git history; original model stays untouched."""
from pathlib import Path
import subprocess,json,datetime,urllib.request,os
HERE=Path(__file__).resolve().parent
BASE=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2')
ORIGINAL=BASE.parent/'pypsa-asean'
UPSTREAM='https://github.com/pypsa-meets-earth/pypsa-asean.git'
PAPER='5bacad702ccfed17ad19ab510fa710651e966f2c'
def call(argv,cwd=None):
    return subprocess.check_output(argv,cwd=cwd,text=True,stderr=subprocess.STDOUT).strip()
def main():
    BASE.mkdir(parents=True,exist_ok=True)
    pool=BASE/'model-source'
    if not pool.exists():
        print(call(['git','clone','--quiet','--no-hardlinks','--no-checkout',str(ORIGINAL),str(pool)]),flush=True)
        call(['git','-C',str(pool),'remote','rename','origin','local-history'])
        call(['git','-C',str(pool),'remote','add','upstream',UPSTREAM])
        call(['git','-C',str(pool),'remote','add','origin','https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2.git'])
    remote=call(['git','ls-remote',UPSTREAM,'refs/heads/main'])
    sha=remote.split()[0]
    call(['git','-C',str(pool),'fetch','--quiet','upstream','main',PAPER])
    branches=[('paper_reference','codex/paper-reference-5bacad70',PAPER),('upstream_sc_baseline','codex/upstream-sc-baseline-'+sha[:12],sha),('research_model','codex/research-sc-main',sha),('fix_industrial_gdp','codex/fix-industrial-gdp',sha),('fix_carbon_config','codex/fix-carbon-config',sha),('fix_topology','codex/fix-topology-765-766',sha)]
    out=[]
    for folder,branch,commit in branches:
        path=BASE/folder
        if not path.exists():call(['git','-C',str(pool),'worktree','add','--quiet','-b',branch,str(path),commit])
        out.append({'directory':str(path),'branch':call(['git','-C',str(path),'branch','--show-current']),'sha':call(['git','-C',str(path),'rev-parse','HEAD']),'status':call(['git','-C',str(path),'status','--porcelain'])})
    r={'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'official_url':UPSTREAM,'official_branch':'main','official_sha':sha,'paper_sha':PAPER,'checkouts':out,'original_status':call(['git','-C',str(ORIGINAL),'status','--porcelain']),'remote_publication':'not pushed'}
    (HERE/'LAYER_IDENTITIES.json').write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2),flush=True)
if __name__=='__main__':main()
