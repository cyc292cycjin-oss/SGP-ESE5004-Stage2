"""Run requested before/after function regressions; never call a solver."""
from pathlib import Path
import json, subprocess, sys, time
R=Path(__file__).resolve().parent
BASE=Path('/home/jin/research/SGP_ESE5004_Stage2')
records=[]
for fix in ['E1','E2','E4']:
    for stage,repo in [('before',BASE/'phase2/upstream_sc_baseline'),('after',BASE/'phase3a2'/('fix_'+fix.lower()))]:
        out=R/'evidence'/f'{fix}_{stage}.json'
        cmd=[sys.executable,str(R/'test_buildings_fixes.py'),'--repo',str(repo),'--fix',fix,'--output',str(out)]
        started=time.time();run=subprocess.run(cmd,text=True,capture_output=True,timeout=120)
        (R/'evidence'/f'{fix}_{stage}.log').write_text(run.stdout+run.stderr)
        record=dict(fix=fix,stage=stage,command=cmd,exit_code=run.returncode,seconds=time.time()-started,
          output=str(out),source_commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip())
        records.append(record);print(json.dumps(record),flush=True)
        if not out.exists():raise RuntimeError('Harness failed before producing results; inspect log, do not count as a scientific failure')
(R/'evidence/RUN_RECEIPT.json').write_text(json.dumps(records,indent=2))
