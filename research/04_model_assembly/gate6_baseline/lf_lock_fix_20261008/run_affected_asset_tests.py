"""Unmodified existing asset regressions; isolated receipts, no native solve.

Select the existing classes that exercise the two LF-only source paths.
Unrelated historic demand/source-count, policy and transmission tests are not
part of this supplementary selection. The complete Gate6 suite runs separately.
"""
import contextlib,datetime,hashlib,importlib,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import highspy
from pypsa.optimization.optimize import OptimizationAccessor

SELECTION=[
 'test_surviving_asset_integration.UnitTests',
 'test_surviving_asset_integration.IntegrationTests',
 'test_gate4_assets.SourceAndAssetTests',
 'test_gate4_activation.HydroAggregationTests',
 'test_gate4_selected_closure.CohortBoundTests',
 'test_gate4_exact_closure.FixedInclusionTests',
 'test_hydro_policy_separation.HydroTests',
 'test_limited_ocgt_and_blend_bounds.LimitedLifetime',
 'test_source_scope.SourceScopeTests.test_unapproved_lifetime_fixture_remains_pending',
]

def run(root,out):
 root=Path(root).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
 tmp=out/'tmp';tmp.mkdir();tempfile.tempdir=str(tmp);os.environ['TMPDIR']=str(tmp)
 sys.path[:0]=[str(root/'tests/research'),str(root/'scripts_project')]
 # A legacy roundtrip test writes an evidence receipt under assembly_v1_tests.
 # Redirect only that output subtree to this new directory; assertions/read
 # dependencies and existing production/historical files are untouched.
 legacy=root/'results_project/assembly_v1_tests';isolated=out/'legacy_receipts'
 original_open=Path.open;original_mkdir=Path.mkdir
 def mapped(path):
  try:return isolated/Path(path).absolute().relative_to(legacy)
  except ValueError:return path
 def output_open(path,*args,**kwargs):return original_open(mapped(path),*args,**kwargs)
 def output_mkdir(path,*args,**kwargs):return original_mkdir(mapped(path),*args,**kwargs)
 with (out/'AFFECTED_ASSET_TESTS.log').open('x') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log),patch.object(Path,'open',output_open),patch.object(Path,'mkdir',output_mkdir),patch.object(highspy.Highs,'run',side_effect=AssertionError('NO NATIVE RUN')) as native_run,patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO NATIVE PRESOLVE')) as native_pre,patch.object(OptimizationAccessor,'create_model',side_effect=AssertionError('NO PYPSA MATRIX BUILD')) as build:
  suite=unittest.TestLoader().loadTestsFromNames(SELECTION)
  result=unittest.TextTestRunner(stream=log,verbosity=2,failfast=True).run(suite)
  calls=dict(solver_calls=native_run.call_count,presolve_calls=native_pre.call_count,pypsa_matrix_build_calls=build.call_count)
  passed=result.wasSuccessful() and not result.skipped and all(v==0 for v in calls.values())
  sources={}
  for name in sorted({s.split('.')[0] for s in SELECTION}):
   rel='tests/research/'+name+'.py';data=(root/rel).read_bytes();blob=subprocess.check_output(['git','show','HEAD:'+rel],cwd=root)
   assert data.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n')
   sources[rel]=dict(actual_sha256=hashlib.sha256(data).hexdigest(),git_blob_sha256=hashlib.sha256(blob).hexdigest(),unchanged_from_git_except_possible_worktree_line_endings=True)
  receipt=dict(status='PASS' if passed else 'FAIL',selection=SELECTION,tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),**calls,full_gate6_matrix_built=False,original_test_assertions_unchanged=True,historical_output_writes_redirected=str(isolated),sources=sources,observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 with (out/'AFFECTED_ASSET_TESTS.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
 print(json.dumps(receipt,indent=2));return 0 if passed else 1

if __name__=='__main__':raise SystemExit(run(*sys.argv[1:]))
