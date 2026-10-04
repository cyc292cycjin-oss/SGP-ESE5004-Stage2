"""Commit the reviewed target guard separately; preserve both candidate stages."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parent
old=json.loads((R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text())
V=Path(old['path']);BASE=old['base']
def git(*args,raw=False):
    b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(V),*args])
    return b if raw else b.decode().strip()
assert git('rev-parse','HEAD')==old['commit']
assert git('branch','--show-current')=='codex/transport-shipping-target-guard'
assert json.loads((R/'evidence/SHIPPING_TARGET_GUARD_AFTER.json').read_text())['passed']
git('add','-f','--','scripts/prepare_sector_network.py','tests/transport/test_shipping_allocation.py')
git('-c','core.whitespace=cr-at-eol','diff','--cached','--check')
git('commit','-m','fix: reject mismatched shipping load targets')
assert not git('status','--porcelain')
patch=git('diff','--binary',BASE,'HEAD',raw=True)
(R/'candidate/SHIPPING_ALLOCATION.patch').write_bytes(patch)
(R/'candidate/test_shipping_allocation_initial.py').write_bytes(git('show',old['commit']+':tests/transport/test_shipping_allocation.py',raw=True))
(R/'evidence/SHIPPING_ALLOCATION_STAGE1_IDENTITY.json').write_text(json.dumps(old,indent=2))
record=dict(base=BASE,commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),path=str(V),clean=True,merged_into_research_model=False,patch_sha256=hashlib.sha256(patch).hexdigest(),changed_files=old['changed_files'],candidate_commits=[dict(commit=old['commit'],branch=old['branch'],purpose='Numeric allocation before aggregation; 15 tests'),dict(commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),purpose='Actual Load target guard; 17 tests; restores frozen upstream line endings')],base_to_tip_numstat=git('diff','--numstat',BASE,'HEAD'),scope='Two isolated engineering commits, each on its own branch; no source quantities/config/carbon/solver changes')
(R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
