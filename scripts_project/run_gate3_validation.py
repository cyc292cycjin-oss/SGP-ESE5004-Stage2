"""Run bounded Gate3 tests and preserve per-test outcomes. Never solve."""
from pathlib import Path
import argparse,json,sys,unittest,importlib.util,io


def run(repo,output):
    path=Path(repo)/'tests/research/test_carrier_carbon.py'
    spec=importlib.util.spec_from_file_location('gate3_tests',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    records=[]
    class Result(unittest.TextTestResult):
        def addSuccess(self,test):
            super().addSuccess(test);records.append({'Test_ID':test.id(),'Status':'PASS','Evidence':'SYNTHETIC_STATIC_NO_SOLVER'})
        def addFailure(self,test,err):
            super().addFailure(test,err);records.append({'Test_ID':test.id(),'Status':'FAIL','Evidence':str(err[1])})
        def addError(self,test,err):
            super().addError(test,err);records.append({'Test_ID':test.id(),'Status':'ERROR','Evidence':str(err[1])})
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(module)
    result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/'gate3_tests.log').write_text(stream.getvalue());(output/'GATE3_TEST_RESULTS.json').write_text(json.dumps({'tests':result.testsRun,'pass':result.wasSuccessful(),'records':records,'solver_status':'NOT_RUN'},indent=2))
    if not result.wasSuccessful():raise RuntimeError(stream.getvalue())
    return result.testsRun


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print('Gate3 tests PASS:',run(a.repo,a.output))
