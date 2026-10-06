"""Sequential no-solve suite. All artifacts and temporary payloads stay on D."""
import argparse, hashlib, json, os, runpy, subprocess, sys, tempfile
from pathlib import Path

TESTS=['test_precision_handoff_no_solve.py','test_lossless_gate5_lifecycle.py','test_lossless_export.py',
       'test_gate5_lossless_integration.py','test_solver_result_qualification.py','test_gate5_resources.py','test_chunk_build.py']

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--one',choices=TESTS)
    args=ap.parse_args();out=args.output.resolve()
    assert out.is_relative_to(Path('/mnt/d/ResearchWorkspaces/ASEAN')), 'D workspace required'
    out.mkdir(parents=True,exist_ok=True)
    temp=out/'tmp';temp.mkdir(exist_ok=True);tempfile.tempdir=str(temp)
    os.environ.update(TMPDIR=str(temp),PYTHONDONTWRITEBYTECODE='1')
    here=Path(__file__).resolve().parent
    if args.one:
        import highspy
        from unittest.mock import patch
        sys.path.insert(0,str(here));sys.argv=[str(here/args.one),str(out/(Path(args.one).stem+'.json'))]
        with patch.object(highspy.Highs,'run',side_effect=AssertionError('REAL SOLVE FORBIDDEN')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('PRESOLVE FORBIDDEN')):
            runpy.run_path(str(here/args.one),run_name='__main__')
        return
    rows=[]
    for test in TESTS:
        with (out/(Path(test).stem+'.log')).open('w') as log:
            p=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--output',str(out),'--one',test],stdout=log,stderr=subprocess.STDOUT)
        assert p.returncode==0, f'{test} FAILED: see D log'
        result=out/(Path(test).stem+'.json');r=json.loads(result.read_text())
        assert r['status']=='PASS'
        assert all(r.get(k,0)==0 for k in ['solver_runs','real_gate5_runs','synthetic_solves','presolve_calls'])
        count=len(r.get('checks',[])) or 1
        rows.append(dict(test=test,status='PASS',checks=count,source_sha256=sha(here/test),evidence_sha256=sha(result)))
        print(test,'PASS',count,flush=True)
    core=['precision_handoff.py','fixed_inventory_scaling.py','gate5_resources.py','gate5_memory_preflight.py','run_gate5_stable_inventory.py',
          'lossless_gate5_lifecycle.py','execute_gate5_lossless.py','finish_gate5_lossless.py']
    receipt=dict(status='PASS',scope='NO_SOLVE_ENGINEERING_FREEZE',real_gate5_solver_runs=0,synthetic_solver_runs=0,presolve_calls=0,
                 checks=sum(r['checks'] for r in rows),suites=rows,code_sha256={name:sha(here/name) for name in core},
                 suite_sha256=sha(Path(__file__)),tests_complete=True)
    (out/'LOSSLESS_FREEZE_TESTS.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':main()
