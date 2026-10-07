"""Sequential export and source-lifetime test, entirely without optimization."""
import json,tempfile,weakref,gc,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np,pandas as pd,pypsa,highspy,xarray as xr
from finish_gate5_lossless import export_sequential,frame_signature,export_complete_timeseries


def edge_network():
    n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=3,freq='h'))
    n.add('Bus','b')
    for name in ['z-active','a-zero','\u96f6\u503c']:
        n.add('Generator',name,bus='b',p_nom=10.,marginal_cost=2.)
    n.generators_t.p=pd.DataFrame([[np.nextafter(1.,2.),-0.,0.],[2.,-0.,0.],[3.,-0.,0.]],index=n.snapshots,columns=n.generators.index)
    n.generators_t.q=pd.DataFrame(-0.,index=n.snapshots,columns=n.generators.index)
    n.generators_t.mu_upper=pd.DataFrame(np.nan,index=n.snapshots,columns=n.generators.index)
    n.meta={'test_only':True}
    return n

if __name__=='__main__':
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')),patch.object(highspy.Highs,'getSolution',side_effect=AssertionError('NO NATIVE RETRIEVAL')):
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
            n=edge_network();expected=n.generators_t.p.copy();old=Path(temp)/'legacy.nc'
            n.export_to_netcdf(old);legacy=pypsa.Network(old)
            assert expected.equals(legacy.generators_t.p.reindex(columns=expected.columns))
            assert frame_signature(expected)!=frame_signature(legacy.generators_t.p)
            assert np.signbit(expected.to_numpy()).sum()>np.signbit(legacy.generators_t.p.to_numpy()).sum()
            del legacy
            signatures={attr:frame_signature(n.generators_t[attr]) for attr in ['p','q','mu_upper']}
            owner=[n];ref=weakref.ref(n);del n
            def exact_edge_check(reread,identity):
                gc.collect();assert ref() is None
                for attr,signature in signatures.items():assert frame_signature(reread.generators_t[attr])==signature
                return [{'Status':'PASS'}]
            out=Path(temp)/'complete.nc'
            with patch('finish_gate5_lossless.physical_checks',exact_edge_check):
                assert export_sequential(owner,out,{})['status']=='PASS'
            with xr.open_dataset(out) as ds:
                for attr in ['p','q','mu_upper']:
                    assert ds['generators_t_'+attr].dtype==np.dtype('float64')
                    assert ds['generators_t_'+attr].shape==(3,3)
                assert list(ds.generators_t_p_i.values)==list(expected.columns)
            def corrupt_one_ulp(network,output):
                export_complete_timeseries(network,output)
                with xr.open_dataset(output) as stored:data=stored.load()
                data['generators_t_p'].values[0,0]=np.nextafter(data['generators_t_p'].values[0,0],np.inf)
                data.to_netcdf(output);data.close()
            with patch('finish_gate5_lossless.export_complete_timeseries',corrupt_one_ulp):
                try:export_sequential([edge_network()],Path(temp)/'corrupted.nc',{})
                except ValueError as error:assert str(error)=='Export time series changed: Generator.p'
                else:raise AssertionError('A one-ULP export change passed')
    Path(sys.argv[1]).write_text(json.dumps(dict(status='PASS',solver_runs=0,presolve_calls=0,
        checks=['sequential_network_weakref_dead_before_readback_validation','actual_netcdf_frame_signature_roundtrip',
                'legacy_default_column_elision_reproduces_order_and_signed_zero_loss',
                'unsorted_unicode_default_zero_signed_zero_all_nan_frames_exact_roundtrip',
                'stored_scientific_time_series_remain_float64','one_ulp_export_corruption_still_rejected'],
        limitation='Physical model checks mocked for this tiny engineering fixture, not a Gate5 validation result'),indent=2)+'\n')
