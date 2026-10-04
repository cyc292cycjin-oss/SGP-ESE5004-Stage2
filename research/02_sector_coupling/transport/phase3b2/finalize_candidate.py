"""Commit one isolated engineering fix and preserve its exact patch/identity."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
V=Path('/home/jin/research/SGP_ESE5004_Stage2/phase3b2/shipping_allocation_validation')
BASE='a3616a68ee44592af6527ca9024a90f1956646ae'
def git(*args, raw=False):
    b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(V),*args])
    return b if raw else b.decode().strip()
assert git('rev-parse','HEAD')==BASE
assert json.loads((R/'evidence/SHIPPING_TEST_AFTER.json').read_text())['passed']
paths=['scripts/prepare_sector_network.py','scripts/_shipping_allocation.py','tests/transport/test_shipping_allocation.py']
git('add','-f','--',*paths)
assert sorted(git('diff','--cached','--name-only').splitlines())==sorted(paths)
git('diff','--cached','--check')
git('commit','-m','fix: conserve shipping country demand before node aggregation')
assert not git('status','--porcelain')
patch=git('diff','--binary',BASE,'HEAD',raw=True)
(R/'candidate/SHIPPING_ALLOCATION.patch').write_bytes(patch)
record=dict(base=BASE,commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),path=str(V),clean=True,merged_into_research_model=False,patch_sha256=hashlib.sha256(patch).hexdigest(),changed_files=paths,scope='Engineering fix candidate; no config, source quantities, carbon or solver changes')
(R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
