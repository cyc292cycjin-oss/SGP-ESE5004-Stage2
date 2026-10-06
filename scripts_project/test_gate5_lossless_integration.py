"""Prepare real tiny LP without solving; mock the authorized execution boundary."""
import json,sys,tempfile,weakref
from pathlib import Path
from unittest.mock import patch
import numpy as np,pandas as pd,pypsa,highspy
from execute_gate5_lossless import prepare_detached,execute_prepared

class IdentityScaling:
    def columns(self,vl,lo,hi,c):self.d=np.ones(len(vl));self.parts=[];return lo,hi,c
    def rows(self,cl,a,lo,hi):self.parts.append(np.ones(len(cl)));return a,lo,hi
    def finish(self):self.r=np.concatenate(self.parts);return {'kind':'TEST_IDENTITY'}

def run(output):
    base=output.parent/'integration_fixtures';base.mkdir(exist_ok=True)
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO REAL SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        with tempfile.TemporaryDirectory(dir=base) as temp:
            out=Path(temp);n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=3,freq='h'))
            n.add('Bus','b');n.add('Generator','g',bus='b',p_nom=10.,marginal_cost=2.)
            n.add('Load','l',bus='b',p_set=[1.,2.,3.]);n.optimize.create_model()
            s=IdentityScaling();nr=weakref.ref(n);sr=weakref.ref(s);no=[n];so=[s];del n,s
            h,record,fidelity=prepare_detached(no,so,'synthetic-only','synthetic-only',out,[],{},lambda *x:None)
            assert no[0] is None and so[0] is None and nr() is None and sr() is None
            assert h.getNumCol()==3 and fidelity['status']=='PASS'
            h.clear();del h
            events=[]
            class FakeNative:
                def setOptionValue(self,k,v):events.append(('option',k,v));return highspy.HighsStatus.kOk
                def run(self):events.append(('mock_run',));return highspy.HighsStatus.kOk
            owner=[FakeNative()]
            def consume(native_owner,*args):
                assert ('before_run',) in events and ('mock_run',) in events
                events.append(('consume',));native_owner[0]=None
                return dict(status='FAILED_NATIVE_QUALIFICATION',qualification={},dynamic_checks='NOT_RUN')
            options={'threads':2,'time_limit':10800,'solver':'ipm','run_crossover':'on'}
            with patch('execute_gate5_lossless.consume_native',consume):
                result=execute_prepared(owner,record,fidelity,{},out,options,lambda *x:None,lambda *x:events.append(('before_run',)))
            assert owner[0] is None and events.count(('mock_run',))==1
            assert events.index(('before_run',))<events.index(('mock_run',))<events.index(('consume',))
            for key,value in options.items():assert ('option',key,value) in events
            try:execute_prepared([FakeNative()],record,fidelity,{},out,{**options,'run_crossover':'off'},lambda *x:None,lambda *x:None)
            except ValueError:pass
            else:raise AssertionError('Changed frozen options accepted')
    return dict(status='PASS',solver_runs=0,presolve_calls=0,mock_run_calls=1,
        checks=['actual_native_transfer_and_source_owner_destruction','D_workspace_mapping_destination',
                'before_run_receipt_precedes_mock_execution','one_execution_boundary_then_result_consumer','frozen_options_preserved','changed_crossover_rejected'])

if __name__=='__main__':
    output=Path(sys.argv[1]);output.write_text(json.dumps(run(output),indent=2)+'\n')
