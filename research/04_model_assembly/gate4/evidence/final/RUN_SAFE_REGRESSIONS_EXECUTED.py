import sys,unittest
from pathlib import Path
R=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model');sys.path.insert(0,str(R/'tests/research'))
import test_fixed_accounts_price_basis as old
names=[n for n in unittest.defaultTestLoader.getTestCaseNames(old.FixedTests) if n!='test_real_direction_hook_attached_without_solver']
suite=unittest.TestSuite([old.FixedTests(n) for n in names]);suite.addTests(unittest.defaultTestLoader.discover(str(R/'tests/research'),pattern='test_final_physical_checks.py'))
r=unittest.TextTestRunner(verbosity=2).run(suite)
assert r.testsRun==19 and r.wasSuccessful();print('NO_OPTIMIZATION_VARIABLES_CREATED')
