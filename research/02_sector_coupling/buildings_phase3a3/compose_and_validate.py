"""Build an isolated E1+E2+E4 source overlay and run the same tests. No R merge.

The overlay lives under work/, not in any model worktree. Patches are applied
mechanically to U files using Git's patch engine. No experiment/network solve.
"""
from pathlib import Path
import hashlib, json, os, subprocess, sys
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
B=Path('/home/jin/research/SGP_ESE5004_Stage2')
POOL=B/'phase2/model-source';U='a3616a68ee44592af6527ca9024a90f1956646ae'
OUT=ROOT/'work/phase3a3_combined_source'
OUT.mkdir(parents=True,exist_ok=False)
files=['scripts/_helpers.py','scripts/prepare_sector_network.py','scripts/prepare_heat_data.py','scripts/final_asean_adjustment.py']
for f in files:
    p=OUT/f;p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(subprocess.check_output(['git','-C',str(POOL),'show',U+':'+f]))
record=dict(base=U,overlay=str(OUT),patches=[])
for fix in ['E1','E2','E4']:
    repo=B/'phase3a2'/('fix_'+fix.lower())
    sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    patch=subprocess.check_output(['git','-C',str(repo),'diff','--binary',U,sha,'--','scripts'])
    run=subprocess.run(['git','apply','-'],cwd=OUT,input=patch,capture_output=True,
      env={**os.environ,'GIT_CEILING_DIRECTORIES':str(OUT.parent)})
    if run.returncode:raise RuntimeError(run.stderr.decode())
    record['patches'].append(dict(fix=fix,commit=sha,source_patch_sha256=hashlib.sha256(patch).hexdigest()))
record['source_hashes']={f:hashlib.sha256((OUT/f).read_bytes()).hexdigest() for f in files}
cmd=[sys.executable,str(R/'test_buildings_fixes.py'),'--repo',str(OUT),'--fix','combined','--output',str(R/'evidence/COMBINED_TESTS.json')]
run=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
(R/'evidence/COMBINED_TESTS.log').write_text(run.stdout+run.stderr)
record.update(command=cmd,returncode=run.returncode,model_merged=False,solver_runs=0)
(R/'evidence/COMBINED_SOURCE_RECEIPT.json').write_text(json.dumps(record,indent=2))
print(run.stdout);sys.exit(run.returncode)
