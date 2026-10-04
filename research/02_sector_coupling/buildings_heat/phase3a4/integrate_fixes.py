"""One-time, fail-closed integration of approved fixes. No optimizer is invoked.

Runs inside WSL using the existing pypsa-earth environment. Requires clean frozen
worktrees. Refuses an existing destination rather than resetting user work.
"""
from pathlib import Path
import hashlib, json, subprocess, sys, time

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / 'evidence'
BASE = Path('/home/jin/research/SGP_ESE5004_Stage2')
POOL = BASE / 'phase2/model-source'
DEST = BASE / 'phase3a4/buildings_accounting_validation'
U = 'a3616a68ee44592af6527ca9024a90f1956646ae'
BRANCH = 'codex/buildings-accounting-validation'
FIXES = [
 ('E1','92e9118be20f0b3802f385adac2f56650d57299d','59dbd34880bcdb367fed54cdee39a2ace40182fd','30bafa420e5cd639e696cbdd56de0e7df36c0e47'),
 ('E2','31037d60d69fa762c9ed8ec9ce8289d95bd6a181','1f9405720a873918614df5aad361580cff7cedde','070db2918186829908a02a0b72a7b4426711c653'),
 ('E4','5d761eceeeb0d0519208d760224a41ff50ec1e30','78b23e7804ca05f2fd1f5ee5ec90f3fa6f8bbf7c','9342893fcf467eadbbc410f59c3dbe817d123aa9'),
]
receipt = dict(base=U, branch=BRANCH, worktree=str(DEST), solver_runs=0,
               steps=[], tests=[], protected_before=[], status='STARTED')

def cmd(args, cwd=None):
    p = subprocess.run(args,cwd=cwd,capture_output=True,text=True)
    if p.returncode:
        raise RuntimeError(f'{args}: {p.returncode}\n{p.stdout}\n{p.stderr}')
    return p.stdout.strip()

def git(*args, repo=DEST):
    return cmd(['git','-c','user.name=cyc292cycjin-oss','-c',
                'user.email=329621298+cyc292cycjin-oss@users.noreply.github.com',
                '-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol',
                '-C',str(repo),*args])

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save():
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/'INTEGRATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2))

def state(path):
    return dict(path=str(path),sha=git('rev-parse','HEAD',repo=path),
                status=git('status','--porcelain',repo=path))

def run_test(stage,fix,original=False):
    folder=DEST/'research/02_sector_coupling/buildings_engineering_tests'
    harness=folder/f'check_{fix}.py' if original else folder/f'phase3a3_{fix}/test_buildings_fixes.py'
    tag=f'{stage}_{fix}_'+('original' if original else 'strict')
    out=EVIDENCE/f'{tag}.json'
    args=[sys.executable,str(harness),'--repo',str(DEST),'--fix',fix,'--output',str(out)]
    start=time.time();p=subprocess.run(args,capture_output=True,text=True,timeout=120)
    (EVIDENCE/f'{tag}.log').write_text(p.stdout+p.stderr)
    rec=dict(stage=stage,fix=fix,original=original,command=args,exit_code=p.returncode,
             seconds=time.time()-start,output=out.name,harness_sha256=sha(harness),
             tested_commit=git('rev-parse','HEAD'))
    receipt['tests'].append(rec);save()
    if p.returncode: raise RuntimeError(f'Regression failed: {tag}; stop integration')
    print(tag+': '+p.stdout.strip(),flush=True)

def main():
    resume='--resume-verified-crlf' in sys.argv
    if DEST.exists() and not resume: raise RuntimeError('Destination exists; inspect before any retry')
    if resume:
        previous=json.loads((EVIDENCE/'INTEGRATION_RECEIPT.json').read_text())
        assert previous['status']=='STOP' and 'trailing whitespace' in previous['error']
        assert git('rev-parse','HEAD')=='18d7df24d4eeb36800b58a11db3447b0396d55d4'
        assert not git('status','--porcelain')
        f='scripts/prepare_sector_network.py'
        a=subprocess.check_output(['git','-C',str(DEST),'show','HEAD:'+f])
        b=subprocess.check_output(['git','-C',str(POOL),'show',FIXES[0][1]+':'+f])
        assert a==b and a.count(b'\r\n')==a.count(b'\n')
        (EVIDENCE/'INITIAL_CRLF_PREFLIGHT_STOP.json').write_text(json.dumps(previous,indent=2))
        receipt['mechanical_preflight_resolution']=dict(source_blob_exact=True,
            CRLF_lines=a.count(b'\r\n'),source_modified=False,
            diff_check='git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check')
    for path,expected in [('phase2/paper_reference','5bacad702ccfed17ad19ab510fa710651e966f2c'),
                          ('phase2/upstream_sc_baseline',U),('phase2/research_model',U),
                          ('pypsa-asean','ce327bfae2abe5526d4c1976173f0f8d08366ba5')]:
        s=state(BASE/path);assert s['sha']==expected and not s['status'],s
        receipt['protected_before'].append(s)
    inputs=json.loads((HERE.parent/'evidence/LOCAL_INPUT_HASHES.json').read_text())
    receipt['input_hash_checks']=[]
    for row in inputs:
        actual=sha(Path(row['path']));assert actual==row['sha256'],row['path']
        receipt['input_hash_checks'].append(dict(path=row['path'],sha256=actual))
    save()
    if not resume: git('worktree','add','-b',BRANCH,str(DEST),U,repo=POOL)
    active=[]
    for fix,source,validation,doc in FIXES:
        for kind,original in [('source',source),('validation',validation),('environment_doc_correction',doc)]:
            assert not git('status','--porcelain')
            paths=git('diff-tree','--no-commit-id','--name-only','-r',original).splitlines()
            if kind=='environment_doc_correction':
                assert paths==[f'research/02_sector_coupling/buildings_engineering_tests/phase3a3_{fix}/README.md'],paths
            before=git('rev-parse','HEAD')
            if resume and fix=='E1' and kind=='source':
                before=U
                output='Recovered already-applied clean cherry-pick after byte-identical CRLF preflight inspection'
            else:
                output=git('cherry-pick','-x',original)
            resulting=git('rev-parse','HEAD')
            # Stable patch identity, including original validation assets.
            a=subprocess.check_output(['git','-C',str(POOL),'show','--pretty=format:',original])
            b=subprocess.check_output(['git','-C',str(DEST),'show','--pretty=format:',resulting])
            def pid(raw):
                return subprocess.check_output(['git','patch-id','--stable'],input=raw).decode().split()[0]
            assert pid(a)==pid(b),(fix,kind,'patch mismatch')
            git('diff','--check',before,resulting)
            assert not git('status','--porcelain')
            receipt['steps'].append(dict(fix=fix,kind=kind,original=original,before=before,
                integrated=resulting,patch_id=pid(a),paths=paths,conflicts=False,clean=True,
                cherry_pick_output=output))
            save()
        active.append(fix)
        for active_fix in active:
            run_test('after_'+fix,active_fix,original=True)
            run_test('after_'+fix,active_fix)
        assert not git('status','--porcelain')
    harness=DEST/'research/02_sector_coupling/buildings_engineering_tests/phase3a3_E1/test_buildings_fixes.py'
    out=EVIDENCE/'COMBINED_TESTS.json'
    args=[sys.executable,str(harness),'--repo',str(DEST),'--fix','combined','--output',str(out)]
    p=subprocess.run(args,capture_output=True,text=True,timeout=120)
    (EVIDENCE/'COMBINED_TESTS.log').write_text(p.stdout+p.stderr)
    assert p.returncode==0,p.stderr
    receipt['combined_test']=dict(command=args,exit_code=p.returncode,output=out.name)
    prior=json.loads((HERE.parent.parent/'buildings_phase3a3/evidence/COMBINED_SOURCE_RECEIPT.json').read_text())
    receipt['source_hashes']={f:sha(DEST/f) for f in prior['source_hashes']}
    assert receipt['source_hashes']==prior['source_hashes'],'Prior composed-source byte identity differs'
    receipt['prior_composed_source_exact_match']=True
    receipt['protected_after']=[state(Path(s['path'])) for s in receipt['protected_before']]
    assert receipt['protected_before']==receipt['protected_after']
    for row in receipt['input_hash_checks']:assert sha(Path(row['path']))==row['sha256']
    changed=git('diff','--name-only',U).splitlines()
    assert all(f in prior['source_hashes'] or f.startswith('research/') for f in changed),changed
    git('diff','--check',U)
    receipt['changed_paths']=changed
    receipt['integrated_commit']=git('rev-parse','HEAD')
    receipt['status']='PASS'
    receipt['working_tree_clean']=not bool(git('status','--porcelain'))
    (EVIDENCE/'INTEGRATED_SOURCE.diff').write_bytes(subprocess.check_output(['git','-C',str(DEST),'diff',U,'--','scripts']))
    save();print(json.dumps({k:receipt[k] for k in ['branch','integrated_commit','status','working_tree_clean']}),flush=True)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        receipt['status']='STOP';receipt['error']=repr(exc);save();raise
