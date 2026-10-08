"""Same bounded suite on local/cloud; hard traps, durable logs, no full build."""
import json,os,runpy,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import highspy
from gate5_resources import sha
from gate6_result import write

REGRESSION=['test_precision_handoff_no_solve.py','test_lossless_gate5_lifecycle.py','test_lossless_export.py',
 'test_gate5_lossless_integration.py','test_solver_result_qualification.py','test_gate5_resources.py','test_chunk_build.py','test_gate5_metadata_closeout.py','test_gate5_cloud_resources.py']

def run(root,out):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=False)
    tmp=out/'tmp';tmp.mkdir();tempfile.tempdir=str(tmp);os.environ.update(TMPDIR=str(tmp),PYTHONDONTWRITEBYTECODE='1')
    rows=[];folder=root/'scripts_project'
    from run_gate6_baseline import dispatch,CONFIG,read
    # Production input FILE validation only; default entry hard-blocks create_model.
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO REAL RUN')) as nr,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')) as np:
        preflight=dispatch(root,out/'input_preflight')
        from test_gate6_baseline_3h import run as new_tests
        case=out/'new_runner';case.mkdir();test=new_tests(root,case);write(case/'GATE6_ENTRY_TESTS.json',test)
        assert nr.call_count==np.call_count==0
    rows.append(dict(test='test_gate6_baseline_3h.py',status=test['status'],checks=len(test['checks']),receipt_sha256=sha(case/'GATE6_ENTRY_TESTS.json')))
    for name in REGRESSION:
        destination=out/(Path(name).stem+'.json')
        with (out/(Path(name).stem+'.log')).open('w') as log:
            process=subprocess.run([sys.executable,str(Path(__file__)),str(folder/name),str(destination)],cwd=root,stdout=log,stderr=subprocess.STDOUT)
        if process.returncode:raise ValueError('No-solver regression failed: '+name+'; see '+str(out))
        r=read(destination);assert r['status']=='PASS'
        rows.append(dict(test=name,status='PASS',checks=len(r.get('checks',[])) or 1,receipt_sha256=sha(destination)))
        print(name,'PASS',flush=True)
    cfg=read(root/CONFIG);lock=read(root/cfg['lock'])
    sourcefiles=[r['path'] for r in lock['files'] if r['role']=='GIT_CODE_OR_CONFIG']+['scripts_project/'+x for x in REGRESSION]
    receipt=dict(status='PASS',scope='GATE6_ORIGINAL_3H_ENGINEERING_NO_SOLVE',solver_calls=0,presolve_calls=0,full_gate6_optimization_model_built=False,
        input_identity=preflight,input_lock_sha256=sha(root/cfg['lock']),tested_code_sha256={p:sha(root/p) for p in sorted(set(sourcefiles))},suites=rows,
        synthetic_fixtures_are_scientific_results=False,code_sha_at_test=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        code_binding='Exact source hashes; enclosing receipt commit may be a later descendant. No Gate5 receipts repinned.')
    write(out/'GATE6_3H_NO_SOLVER_TESTS.json',receipt);return receipt

if __name__=='__main__':
    path=Path(sys.argv[1]);output=Path(sys.argv[2]);tempfile.tempdir=os.environ['TMPDIR'];sys.argv=[str(path),str(output)]
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO REAL RUN')) as run_native,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')) as pre:
        runpy.run_path(str(path),run_name='__main__')
        assert run_native.call_count==pre.call_count==0
