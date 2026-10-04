"""Create isolated engineering candidates from pinned U. No merge, no model runs.
Run in WSL with the existing PyPSA environment. Idempotent only for initial creation;
existing worktrees are verified, never reset. Tests are explicit synthetic fixtures.
"""
from pathlib import Path
import json, shutil, subprocess, sys
R=Path(__file__).resolve().parent
POOL=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/model-source')
HOME=POOL.parent.parent/'phase3a2'
U='a3616a68ee44592af6527ca9024a90f1956646ae'
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True).strip()
def replace(text,old,new):
    assert text.count(old)==1, (old[:80],text.count(old))
    return text.replace(old,new)
def change(fix,repo):
    p=repo/'scripts/prepare_sector_network.py';s=p.read_text()
    if fix=='E1':
        start=s.index('        if name == "urban central":\n',s.index('def add_heat('))
        end=s.index('        ## Add heat pumps',start)
        s=s[:start]+'''        if name == "urban central":
            # Preserve sector demand identities on the shared district heat bus.
            for sector in sectors:
                sector_load = (
                    heat_demand[[sector + " water", sector + " space"]]
                    .groupby(level=1, axis=1).sum()[h_nodes[name]]
                    .multiply(factor * (1 + options["district_heating"]["district_heating_loss"]))
                )
                n.madd(
                    "Load", h_nodes[name], suffix=f" {sector} {name} heat",
                    bus=h_nodes[name] + f" {name} heat", carrier=name + " heat",
                    p_set=sector_load,
                )
        else:
            n.madd(
                "Load", h_nodes[name], suffix=f" {name} heat",
                bus=h_nodes[name] + f" {name} heat", carrier=name + " heat",
                p_set=heat_load,
            )

'''+s[end:]
        start=s.index('    n.loads_t.p_set[heat_ind] = 1e6 * heat_shape_raw.mul(',s.index('def add_residential('))
        end=s.index('    heat_oil_demand =',start)
        s=s[:start]+'''    total_heat = (
        energy_totals["total residential space"]
        + energy_totals["total residential water"]
    )
    remaining_heat = total_heat - energy_totals[
        ["residential heat biomass", "residential heat oil", "residential heat gas"]
    ].sum(axis=1)
    if ((remaining_heat < -1e-9) | (total_heat < 0)).any():
        raise ValueError("Residential remaining heat must be between zero and total heat")
    fraction = remaining_heat.div(total_heat.where(total_heat > 0)).fillna(0.)
    # Keep existing nodal allocation and district losses; never rescale services.
    scale = pd.Series(heat_ind.str[:2], index=heat_ind).map(fraction)
    if scale.isna().any():
        raise ValueError("Missing residential country heat totals")
    n.loads_t.p_set[heat_ind] = n.loads_t.p_set[heat_ind].mul(scale, axis=1)

'''+s[end:]
        start=s.index('    for country in countries:\n',s.index('def add_residential('))
        end=s.index('    # Revise residential electricity demand',start)
        s=s[:start]+s[end:];p.write_text(s)
    elif fix=='E2':
        q=repo/'scripts/prepare_heat_data.py';t=q.read_text()
        helper='''def normalize_heat_profile(shape, annual, label):
    """Reject unmappable positive annual demand instead of silently dropping it.

    Inputs use the existing hourly convention: annual TWh -> hourly MW.
    No synthetic replacement shape is generated for zero-HDD locations.
    """
    annual = annual.reindex(shape.columns)
    if not np.isfinite(annual).all() or (annual < 0).any():
        raise ValueError(f"{label}: invalid annual demand")
    positive = annual > 0
    selected = shape.loc[:, positive]
    invalid = (~np.isfinite(selected)).any() | (selected < 0).any() | (selected.sum() <= 0)
    if invalid.any():
        raise ValueError(f"{label}: positive demand without valid profile at {list(invalid.index[invalid])}")
    output = pd.DataFrame(0., index=shape.index, columns=shape.columns)
    output.loc[:, positive] = selected.div(selected.sum()).mul(annual[positive]) * 1e6
    return output


'''
        t=replace(t,'def prepare_heat_data(',helper+'def prepare_heat_data(')
        start=t.index('        heat_demand[f"{sector} {use}"] = (')
        end=t.index('    heat_demand = pd.concat',start)
        t=t[:start]+'''        heat_demand[f"{sector} {use}"] = normalize_heat_profile(
            heat_demand_shape, nodal_energy_totals[f"total {sector} {use}"],
            f"total {sector} {use}",
        )
        electric_heat_supply[f"{sector} {use}"] = normalize_heat_profile(
            heat_demand_shape, nodal_energy_totals[f"electricity {sector} {use}"],
            f"electricity {sector} {use}",
        )

'''+t[end:]
        q.write_text(t)
        s=replace(s,'''    heat_demand = read_csv_nafix(
        heat_demand_fn, index_col=0, header=[0, 1], parse_dates=True
    ).fillna(0)''','''    heat_demand = read_csv_nafix(
        heat_demand_fn, index_col=0, header=[0, 1], parse_dates=True
    )
    if not np.isfinite(heat_demand).all().all() or (heat_demand < 0).any().any():
        raise ValueError("Invalid heat demand profile; positive annual demand must not be silently dropped")''')
        p.write_text(s)
    elif fix=='E4':
        q=repo/'scripts/final_asean_adjustment.py'
        q.write_text(replace(q.read_text(),'    "service electricity",','    "services electricity",'))
    # Preserve original Git blob line endings so the candidate diff stays minimal.
    for name in git(repo,'diff','--name-only','--','scripts').splitlines():
        path=repo/name
        original=subprocess.check_output(['git','-C',str(repo),'show',f'{U}:{name}'])
        content=path.read_text().encode()
        if b'\r\n' in original:content=content.replace(b'\n',b'\r\n')
        path.write_bytes(content)

records=json.loads((R/'evidence/CANDIDATE_COMMITS.json').read_text()) if (R/'evidence/CANDIDATE_COMMITS.json').exists() else []
for fix,title in [('E1','preserve residential and services heat demand identities'),('E2','reject positive heat demand without a valid profile'),('E4','retain services electricity when filtering carriers')]:
    repo=HOME/('fix_'+fix.lower());branch='codex/buildings-'+fix.lower()
    if any(x['fix']==fix for x in records):
        assert not git(repo,'status','--porcelain'), 'existing candidate must remain clean'
        continue
    HOME.mkdir(exist_ok=True)
    existed=repo.exists()
    if not existed:subprocess.run(['git','-C',str(POOL),'worktree','add','-b',branch,str(repo),U],check=True,stdout=subprocess.DEVNULL)
    assert git(repo,'rev-parse','HEAD')==U
    dest=repo/'research/02_sector_coupling/buildings_engineering_tests';dest.mkdir(parents=True,exist_ok=True)
    shutil.copy2(R/'check_candidate_fixes.py',dest/'check_candidate_fixes.py')
    ev=R/'evidence';ev.mkdir(exist_ok=True)
    def test(stage):
        output=ev/f'{fix}_{stage}.json'
        source=POOL.parent/'upstream_sc_baseline' if stage=='before' else repo
        r=subprocess.run([sys.executable,str(dest/'check_candidate_fixes.py'),'--repo',str(source),'--fix',fix,'--output',str(output)],capture_output=True,text=True)
        (ev/f'{fix}_{stage}.log').write_text(r.stdout+r.stderr)
        assert output.exists(), 'test harness crashed; not a scientific failing test'
        return r.returncode
    assert test('before')==1,fix+' must demonstrate failing baseline test'
    if not git(repo,'diff','--name-only','--','scripts'):change(fix,repo)
    assert test('after')==0,fix+' candidate must pass'
    for stage in ['before','after']:shutil.copy2(ev/f'{fix}_{stage}.json',dest/f'{fix}_{stage}.json')
    (dest/'README.md').write_text(f'# {fix} engineering candidate\n\nBase: `{U}`. Synthetic fixtures only; no solver and no accepted demand data.\n\nRun: `python research/02_sector_coupling/buildings_engineering_tests/check_candidate_fixes.py --repo . --fix {fix} --output /tmp/{fix}.json`\n\nThe before result fails, the after result passes. Pending human review; not merged into Research Model.\n')
    git(repo,'add','scripts','research/02_sector_coupling/buildings_engineering_tests')
    # Upstream has '* text=auto' but historical blobs contain CRLF. Preserve these
    # exact bytes in the index; otherwise Git rewrites the entire source file.
    for name in git(repo,'diff','--cached','--name-only','--','scripts').splitlines():
        blob=git(repo,'hash-object','-w','--no-filters',str(repo/name))
        git(repo,'update-index','--cacheinfo','100644',blob,name)
    git(repo,'-c','user.name=cyc292cycjin-oss','-c','user.email=329621298+cyc292cycjin-oss@users.noreply.github.com','commit','-m','fix: '+title)
    sha=git(repo,'rev-parse','HEAD')
    patches=R/'patches';patches.mkdir(exist_ok=True)
    (patches/f'{fix}.patch').write_bytes(subprocess.check_output(['git','-C',str(repo),'format-patch','-1','--stdout']))
    records.append(dict(fix=fix,branch=branch,commit=sha,base=U,worktree=str(repo),status='PENDING_HUMAN_REVIEW',merged=False,clean=not bool(git(repo,'status','--porcelain'))))
    (R/'evidence/CANDIDATE_COMMITS.json').write_text(json.dumps(records,indent=2))
    print(records[-1],flush=True)
