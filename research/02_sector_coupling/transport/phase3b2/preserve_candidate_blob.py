"""Preserve frozen CRLF source bytes in Git; no Python semantics are changed."""
from pathlib import Path
import ast,hashlib,json,subprocess
R=Path(__file__).resolve().parent
record=json.loads((R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').read_text())
V=Path(record['path'])
def git(*args,raw=False):
    b=subprocess.check_output(['git','-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','-C',str(V),*args])
    return b if raw else b.decode().strip()
if record.get('ast_unchanged_from_tested_guard') and git('rev-parse','HEAD')==record['commit']:
    print('Byte-fidelity receipt already complete; no changes.')
    raise SystemExit(0)
assert git('rev-parse','HEAD')=='cf4b0f816086470dce40ec950e20c045044eec0c'
before=git('show','HEAD:scripts/prepare_sector_network.py',raw=True)
work=(V/'scripts/prepare_sector_network.py').read_bytes()
assert ast.dump(ast.parse(before))==ast.dump(ast.parse(work))
git('switch','-c','codex/transport-shipping-reviewable-patch')
attr=V/'.gitattributes'
attr.write_bytes(attr.read_bytes().rstrip(b'\r\n')+b'\n# Preserve the frozen upstream CRLF blob for a minimal shipping review diff.\n/scripts/prepare_sector_network.py -text\n')
git('add','--','.gitattributes')
# Git may retain the prior cached clean conversion after attributes change.
# Re-stage under the new explicit -text rule and verify bytes before commit.
git('add','--renormalize','--','scripts/prepare_sector_network.py')
assert git('show',':scripts/prepare_sector_network.py',raw=True)==work
git('-c','core.whitespace=cr-at-eol','diff','--cached','--check')
git('commit','-m','fix: preserve frozen source bytes in shipping review patch')
assert not git('status','--porcelain')
assert git('show','HEAD:scripts/prepare_sector_network.py',raw=True)==work
patch=git('diff','--binary',record['base'],'HEAD',raw=True)
(R/'candidate/SHIPPING_ALLOCATION.patch').write_bytes(patch)
record['candidate_commits'].append(dict(commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),purpose='Git byte-fidelity only; source AST unchanged; avoids whole-file line-ending diff'))
record.update(commit=git('rev-parse','HEAD'),branch=git('branch','--show-current'),patch_sha256=hashlib.sha256(patch).hexdigest(),changed_files=['.gitattributes']+record['changed_files'],base_to_tip_numstat=git('diff','--numstat',record['base'],'HEAD'),scope='Two isolated functional candidates plus byte-fidelity commit, each on separate branch; no source quantities/config/carbon/solver changes',functional_candidate_count=2,byte_fidelity_commits=1,ast_unchanged_from_tested_guard=True)
(R/'evidence/SHIPPING_CANDIDATE_IDENTITY.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record,indent=2))
