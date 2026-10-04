"""Record completed tests in the independent integration branch; no model edits."""
from pathlib import Path
import hashlib,json,shutil,subprocess
R=Path(__file__).resolve().parent
rec=json.loads((R/'evidence/INTEGRATION_RECEIPT.json').read_text())
repo=Path(rec['worktree'])
def git(*args):
    return subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c',
      'user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-c',
      'core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','-C',str(repo),*args],text=True).strip()
assert rec['status']=='PASS' and not git('status','--porcelain')
assert git('rev-parse','HEAD')==rec['integrated_commit']
dest=repo/'research/02_sector_coupling/buildings_engineering_tests/phase3a4_combined'
dest.mkdir()
for name in ['INTEGRATION_RECEIPT.json','COMBINED_TESTS.json','ACCOUNTING_CONTRACT_TESTS.json','INTEGRATED_E3_DIAGNOSTIC.json']:
    shutil.copyfile(R/'evidence'/name,dest/name)
(dest/'README.md').write_text('''# E1/E2/E4 combined validation

Engineering integration only, from frozen U a3616a68ee44592af6527ca9024a90f1956646ae.
All approved source and validation patches are recorded with `cherry-pick -x`.
The three following documentation corrections record actual PyPSA 0.30.3.
Original cases: E1=5, E2=7, E4=1. Final strict checks: 777+197+88=1062 PASS.
All staged active-fix regression suites passed. No solver was invoked.
The source bytes equal the previously tested Phase3A3 combined overlay.
P/U/R/T and 19 retained model input files are unchanged.

The 18 synthetic accounting-contract checks demonstrate proposed identities and
reject duplicate/lost demand. They do not close actual ASEAN E3 accounting.
The integrated E3 diagnostic still reproduces total-target + omitted Services.
E3 patch is NOT implemented; data acceptance remains pending.

Runtime: Python3.11.13 / PyPSA0.30.3 / NumPy1.26.4 / pandas2.3.1.
The existing PROJ database warning persists; these tests do not call GIS transforms.
`INTEGRATION_RECEIPT.json` records the tested parent commit; this documentation
commit does not change model source. Final HEAD is recorded by the research audit.
''')
git('add','--',str(dest.relative_to(repo)))
git('diff','--cached','--check')
git('commit','-m','audit: record combined buildings fix validation without changing model inputs')
assert not git('status','--porcelain')
for f,h in rec['source_hashes'].items():assert hashlib.sha256((repo/f).read_bytes()).hexdigest()==h
out=dict(branch=rec['branch'],base=rec['base'],tested_source_commit=rec['integrated_commit'],
         combined_commit=git('rev-parse','HEAD'),working_tree_clean=True,model_source_unchanged_by_record=True)
(R/'evidence/FINAL_INTEGRATION_IDENTITY.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
