"""TEST_ONLY: unchanged 60 asset tests plus 12 directly affected diagnostic guards."""
import importlib.util,json,os,sys
from pathlib import Path
from unittest.mock import patch
import highspy

root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve()
driver=root/'research/04_model_assembly/gate6_baseline/lf_lock_fix_20261008/run_affected_asset_tests.py'
spec=importlib.util.spec_from_file_location('unchanged_asset_regression_driver',driver)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.SELECTION=module.SELECTION+['test_diagnostic_network.DiagnosticTests']
with patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NO NATIVE GETSOLUTION')) as native:
 code=module.run(root,out)
 assert native.call_count==0
receipt=dict(status='PASS' if code==0 else 'FAIL',getSolution_calls=native.call_count,existing_driver_unchanged=True,additional_selection='test_diagnostic_network.DiagnosticTests',fixture='TEST_ONLY')
with (out/'NATIVE_READ_TRAP.json').open('x') as f:json.dump(receipt,f,indent=2)
raise SystemExit(code)
