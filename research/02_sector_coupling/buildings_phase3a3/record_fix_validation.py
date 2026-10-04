"""Append independent validation commits to the existing E1/E2/E4 branches.

No scientific data/config changes, no source changes, no merge, no push.
"""
from pathlib import Path
import hashlib, json, subprocess
R=Path(__file__).resolve().parent
BASE=Path('/home/jin/research/SGP_ESE5004_Stage2')
U='a3616a68ee44592af6527ca9024a90f1956646ae'
SOURCE={'E1':'92e9118be20f0b3802f385adac2f56650d57299d','E2':'31037d60d69fa762c9ed8ec9ce8289d95bd6a181','E4':'5d761eceeeb0d0519208d760224a41ff50ec1e30'}
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
records=[]
for fix,source in SOURCE.items():
    repo=BASE/'phase3a2'/('fix_'+fix.lower())
    assert git(repo,'rev-parse','HEAD')==source
    assert not git(repo,'status','--porcelain')
    before=json.loads((R/f'evidence/{fix}_before.json').read_text())
    after=json.loads((R/f'evidence/{fix}_after.json').read_text())
    assert not before['all_pass'] and after['all_pass']
    dest=repo/f'research/02_sector_coupling/buildings_engineering_tests/phase3a3_{fix}'
    dest.mkdir(parents=True,exist_ok=False)
    (dest/'test_buildings_fixes.py').write_bytes((R/'test_buildings_fixes.py').read_bytes())
    for stage in ['before','after']:
        (dest/(stage+'.json')).write_bytes((R/f'evidence/{fix}_{stage}.json').read_bytes())
    (dest/'README.md').write_text(f'''# {fix}: Phase 3A-3 national conservation validation

Source fix: `{source}`; frozen baseline: `{U}`.
The source fix already exists as a separate commit. This follow-up adds stricter,
11-country-label/22-node synthetic regressions. It changes no source or input.

Run with the recorded PyPSA {after['pypsa']} environment:
`python {dest.relative_to(repo)}/test_buildings_fixes.py --repo . --fix {fix} --output /tmp/{fix}_audit.json`

The matching test on frozen U must fail; this branch must pass. Numeric energy
tolerance: abs(error) <= 1e-6 MWh + 1e-12 * abs(expected MWh).
Test countries are labels, not measured demand. No optimizer. Not merged into R.
E3 and real-data electricity accounting remain outside this patch.
''')
    git(repo,'add',str(dest.relative_to(repo)))
    git(repo,'-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com',
      'commit','-m',f'audit: verify {fix} with national buildings conservation regressions')
    head=git(repo,'rev-parse','HEAD')
    assert not git(repo,'diff',source,head,'--','scripts','data','config.yaml','configs')
    patches=R/'patches';patches.mkdir(exist_ok=True)
    for name,rev in [(f'{fix}.patch',source),(f'{fix}_validation.patch',head)]:
        (patches/name).write_bytes(subprocess.check_output(['git','-C',str(repo),'format-patch','-1',rev,'--stdout']))
    records.append(dict(fix=fix,branch=git(repo,'branch','--show-current'),source_commit=source,
      validation_commit=head,base=U,worktree=str(repo),clean=not bool(git(repo,'status','--porcelain')),
      source_unchanged_by_validation=True,merged_into_research_model=False,status='PENDING_HUMAN_MERGE_REVIEW'))
(R/'evidence/FIX_COMMITS.json').write_text(json.dumps(records,indent=2))
print(json.dumps(records,indent=2))
