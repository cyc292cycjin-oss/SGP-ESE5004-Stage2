"""Test recording success/failure/stale outputs without solving a model."""
from pathlib import Path
import json, subprocess, sys, tempfile
from run_manifest import run

root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='manifest-test-') as temp:
    t=Path(temp);repo=t/'repo';repo.mkdir()
    subprocess.run(['git','init','-q',str(repo)],check=True)
    for k,v in [('user.name','Manifest test'),('user.email','test@example.invalid')]:subprocess.run(['git','-C',str(repo),'config',k,v],check=True)
    (repo/'tracked').write_text('test fixture')
    subprocess.run(['git','-C',str(repo),'add','tracked'],check=True)
    subprocess.run(['git','-C',str(repo),'commit','-qm','test: manifest fixture'],check=True)
    sha=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    config=t/'config';config.write_text('synthetic');environment=t/'env';environment.write_text(sys.version)
    out=t/'out';metrics=t/'metrics.json'
    spec=dict(run_id='unit',model_layer='UNIT_TEST',repository=str(repo),expected_git_commit=sha,upstream_commit=sha,run_directory=str(t/'success'),config_files=[str(config)],input_files=[str(repo/'tracked')],environment_file=str(environment),output_files=[str(out)],metrics_file=str(metrics),solver='NONE',solver_version='NONE',snapshots={},planning_year=None,scenario='UNIT_TEST')
    code='from pathlib import Path;import json,sys;Path(sys.argv[1]).write_text("fixture");Path(sys.argv[2]).write_text(json.dumps(dict(objective=0,solver_status="optimal",constraint_residual=0)))'
    rc,m=run(spec,[sys.executable,'-c',code,str(out),str(metrics)]);assert rc==0 and m['status']=='COMPLETED'
    results={'records_success':True,'hashes_output':bool(m['output_hash'])}
    rc,m=run(dict(spec,run_directory=str(t/'stale')),[sys.executable,'-c','pass']);assert rc==1 and 'stale' in m['error'];results['rejects_stale_outputs']=True
    rc,m=run(dict(spec,run_directory=str(t/'failure'),output_files=[str(t/'missing')],metrics_file=str(t/'missing-metrics')),[sys.executable,'-c','raise SystemExit(7)']);assert rc==1 and m['returncode']==7 and m['end_time'];results['records_command_failure']=True
    (repo/'tracked').write_text('dirty')
    rc,m=run(dict(spec,run_directory=str(t/'dirty')),[sys.executable,'-c','pass']);assert rc==1 and 'dirty' in m['error'];results['rejects_dirty_checkout']=True
    (root/'RUN_MANIFEST_TESTS.json').write_text(json.dumps(results,indent=2));print(results)
