"""Produce an independent checker-only candidate from the exact committed C02."""
from pathlib import Path
import ast, hashlib, json, difflib, subprocess, shutil
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_checker_20261012')
PARENT='2b3442826ddc2364f63e3bd44a4eab6aa94fc263'
REL='research/05_baseline_evolution/20261011/c02/code/c02_model.py'
def sha(b):return hashlib.sha256(b).hexdigest()
old=subprocess.check_output(['git','show',PARENT+':'+REL],cwd=R)
assert sha(old)=='676edc30c5860c4a6b52fe63a117d1a395e9230db0d58db3e6ff9bb5ba4934a1'
s=old.decode(); original=s
replacements=[
 ('from c02_common import read,write,sha','from c02_common import read,write,sha\nfrom c02_semantics import rhs_exact,bounds_exact'),
 ("    # These are the actual model row labels/values, later rechecked from exported chunks.",
  "    failure_path=out/'C02R_SEMANTIC_FAILURE.json'\n    # These are the actual model row labels/values, later rechecked from exported chunks."),
 ("        bits(rhs,np.r_[-q,np.zeros(364)]);bounds[int(row[0])]=(-q,-q,'initial:'+asset)",
  "        b=m.constraints['Store-energy_balance']\n        signs=b.sign.broadcast_like(b.rhs).sel(Store=asset).values\n        rhs_exact(rhs,np.r_[-q,np.zeros(364)],actual_signs=signs,expected_sign='=',asset_id=asset,family='Store-energy_balance',row_labels=row,report_path=failure_path)\n        bounds[int(row[0])]=(-q,-q,'initial:'+asset)"),
 ("            b=m.constraints[nm];dim=next(d for d in b.labels.dims if d!='snapshot');lab=b.labels.sel({dim:asset}).values;rr=b.rhs.sel({dim:asset}).values;bits(rr,np.full(365,val))",
  "            b=m.constraints[nm];dim=next(d for d in b.labels.dims if d!='snapshot');lab=b.labels.sel({dim:asset}).values;rr=b.rhs.sel({dim:asset}).values\n            signs=b.sign.broadcast_like(b.rhs).sel({dim:asset}).values\n            rhs_exact(rr,np.full(365,val),actual_signs=signs,expected_sign='>=' if nm=='Store-fix-e-lower' else '<=',asset_id=asset,family=nm,row_labels=lab,report_path=failure_path)"),
 ("        nm,b,dim=matched[0];lab=b.labels.sel({dim:bus}).values;rr=b.rhs.sel({dim:bus}).values;dd=n.loads_t.p_set[g['load']].to_numpy();bits(rr,dd)",
  "        nm,b,dim=matched[0];lab=b.labels.sel({dim:bus}).values;rr=b.rhs.sel({dim:bus}).values;dd=n.loads_t.p_set[g['load']].to_numpy()\n        signs=b.sign.broadcast_like(b.rhs).sel({dim:bus}).values\n        rhs_exact(rr,dd,actual_signs=signs,expected_sign='=',asset_id=bus,family=nm,row_labels=lab,report_path=failure_path)"),
 ("                x,y,why=bounds[int(l)];assert lower[j]==x and upper[j]==y,why;matchedbounds+=1",
  "                x,y,why=bounds[int(l)]\n                bounds_exact(np.array([lower[j]]),np.array([upper[j]]),np.array([x]),np.array([y]),asset_id=why.split(':',1)[1],family=name,row_labels=np.array([l]),report_path=failure_path)\n                matchedbounds+=1")]
for a,b in replacements:
    assert s.count(a)==1,a
    s=s.replace(a,b)
p=W/'candidate';p.mkdir(exist_ok=True)
(p/'c02_model.py').write_text(s)
shutil.copy2(W/'c02_semantics.py',p/'c02_semantics.py')
diff=''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='frozen_C02/c02_model.py',tofile='C02R_candidate/c02_model.py'))
(W/'C02R_MODEL_CHECKER.patch').write_text(diff)
oldt=ast.parse(original);newt=ast.parse(s)
oldf={n.name:ast.dump(n,include_attributes=False) for n in oldt.body if isinstance(n,ast.FunctionDef)}
newf={n.name:ast.dump(n,include_attributes=False) for n in newt.body if isinstance(n,ast.FunctionDef)}
changed=[n for n in oldf if oldf[n]!=newf[n]]
assert changed==['export_model']
remaining=[]
for n in ast.walk(newt):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='bits':
        remaining.append({'line':n.lineno,'call':ast.get_source_segment(s,n),
                          'disposition':'RETAINED_BIT_EXACT_INPUT_OBJECTIVE_COORDINATE_OR_FILE_READBACK'})
semantic=[{'line':n.lineno,'name':n.func.id,'call':ast.get_source_segment(s,n)} for n in ast.walk(newt)
          if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['rhs_exact','bounds_exact']]
assert len(semantic)==4
audit={'status':'LOCAL_CANDIDATE_ONLY_NOT_DEPLOYED','version':'C02R_EXACT_FINITE_ROW_CHECK_V1','parent_commit':PARENT,
 'parent_path':REL,'parent_sha256':sha(old),'candidate_sha256':sha(s.encode()),'helper_sha256':sha((p/'c02_semantics.py').read_bytes()),
 'changed_existing_functions':changed,'bits_function_AST_unchanged':oldf['bits']==newf['bits'],
 'other_existing_functions_AST_unchanged':[k for k in oldf if k!='export_model'],
 'semantic_call_sites':semantic,'remaining_bits_call_sites':sorted(remaining,key=lambda x:x['line']),
 'nonfinite_policy':'All RHS values finite binary64; only exact expected inactive-side bound sentinels are permitted. No active endpoint may become NaN/Inf.',
 'new_run_authorized':False,'cloud_connected':False,'new_network_or_LP_created':False,
 'candidate_worker_or_launcher_created':False,'old_runtime_and_payload_unchanged':True,
 'reuse_network_if_later_authorized':{'sha256':'b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2',
  'cloud_path':'/root/autodl-tmp/SGP/runs/c02_daily_build_20261012T025604Z_fcc0f784/artifacts/daily_365_unsolved.nc',
  'local_path':'D:/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012/cloud_evidence/daily_365_unsolved.nc'},
 'additional_known_blocker':{'kind':'OUTSIDE_APPROVED_SIGNED_ZERO_REPAIR_NOT_MODIFIED','parent_line':247,
   'expression':"assert len(names)==v4['constraint_blocks'][fam] and counts[fam]>0",
   'direct_evidence':'C02_CONSTRAINT_COVERAGE.json and C02_ZERO_ROW_BOUNDARY_CHECK.json: Line-ext-s_nom-upper, Link-ext-p_nom-upper, Store-ext-e_nom-upper each have zero active rows and +Inf expected maxima.',
   'implication':'If earlier checks pass, existing export coverage assertion will reject these known valid zero-row families. Requires a separately explicit, narrow disposition before a new full build; no constraint/model change is proposed or applied.'}}
assert audit['additional_known_blocker']['expression'] in original
audit['additional_known_blocker']['parent_line']=next(i for i,line in enumerate(original.splitlines(),1) if audit['additional_known_blocker']['expression'] in line)
(W/'C02R_PATCH_SCOPE_AND_IDENTITIES.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'changed_functions':changed,'semantic_call_sites':len(semantic),'retained_bits_calls':len(remaining),'candidate_SHA':audit['candidate_sha256']}))
