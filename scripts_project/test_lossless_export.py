"""Sequential export and source-lifetime test, entirely without optimization."""
import json,tempfile,weakref,gc,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np,pandas as pd,pypsa,highspy
from finish_gate5_lossless import export_sequential,frame_signature

if __name__=='__main__':
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        with tempfile.TemporaryDirectory() as temp:
            n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=3,freq='h'))
            n.add('Bus','b');n.add('Generator','g',bus='b',p_nom=10.,marginal_cost=2.)
            n.generators_t.p=pd.DataFrame([1.,2.,3.],index=n.snapshots,columns=n.generators.index)
            n.meta={'test_only':True};ref=weakref.ref(n);owner=[n];del n
            def check_after_release(reread,identity):
                gc.collect();assert ref() is None
                assert np.array_equal(reread.generators_t.p['g'],[1.,2.,3.])
                return [{'Status':'PASS'}]
            with patch('finish_gate5_lossless.physical_checks',check_after_release):
                result=export_sequential(owner,Path(temp)/'result.nc',{})
            assert owner[0] is None and result['status']=='PASS'
    Path(sys.argv[1]).write_text(json.dumps(dict(status='PASS',solver_runs=0,presolve_calls=0,
        checks=['sequential_network_weakref_dead_before_readback_validation','actual_netcdf_frame_signature_roundtrip'],
        limitation='Physical model checks mocked for this tiny engineering fixture, not a Gate5 validation result'),indent=2)+'\n')
