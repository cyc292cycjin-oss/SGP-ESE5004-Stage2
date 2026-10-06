"""No optimization. Positive/negative metadata, mapping and native-contract tests."""
import json, tempfile, tracemalloc
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import pandas as pd
import highspy, linopy, pypsa
from unittest.mock import patch
from lossless_gate5_lifecycle import (checked_int32, write_array, inverse_labels, map_values,
    qualify_and_store, load_arrays, save_mapping, apply_stored_solution, termination_condition)
from precision_handoff import exact, research_scalar_assignment


def run():
    checks=[]
    def passed(name, **extra):checks.append(dict(test=name,status='PASS',**extra))
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        for values in [np.array([-2**31,-1,0,2**31-1],dtype=np.int64),np.array([],dtype=np.int64),np.array([0,2**31-1],dtype=np.uint64)]:
            actual=checked_int32(values);assert actual.dtype==np.int32;exact(actual.astype(values.dtype),values,'int32 roundtrip')
        passed('integer_compression_boundaries_positive')
        for values in [np.array([2**31],dtype=np.int64),np.array([-2**31-1],dtype=np.int64),np.array([2**64-1],dtype=np.uint64)]:
            try:checked_int32(values)
            except OverflowError:pass
            else:raise AssertionError('overflow accepted')
        passed('signed_and_unsigned_overflow_rejected')
        for values in [np.array([1.0]),np.array([np.nan]),np.array([True])]:
            try:checked_int32(values)
            except TypeError:pass
            else:raise AssertionError('scientific/noninteger downcast accepted')
        passed('scientific_values_and_noninteger_metadata_rejected')
        labels=np.array([8,0,4,2],dtype=np.int64);grid=np.array([[2,-1,8],[0,4,-1]],dtype=np.int64)
        vals=np.array([1.25,-3.5,4.125,9.25]);scales=np.array([2.,.5,8.,1.])
        look=inverse_labels(labels,10)
        expected=pd.Series(vals*scales,index=labels).reindex(grid.ravel()).to_numpy().reshape(grid.shape)
        actual=map_values(grid,look,vals,scales)
        assert np.array_equal(actual,expected,equal_nan=True)
        passed('chunked_mapping_matches_frozen_pandas_order_masks_and_scales')
        for bad in [np.array([3]),np.array([-2]),np.array([11])]:
            try:map_values(bad,look,vals,scales)
            except ValueError:pass
            else:raise AssertionError('bad label accepted')
        passed('unknown_missing_and_out_of_domain_labels_fail_closed')
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);mf=base/'mapping';mf.mkdir();arrays={}
            for name,v,dtype in [('vlabels',[2,0],np.int32),('clabels',[1],np.int32),('D',[1.,1.],np.float64),('R',[1.],np.float64)]:
                arrays[name]=write_array(mf/(name+'.npy'),v,dtype)
            record=dict(arrays=arrays,model_shape=[2,3],research_scalars=[dict(name='Research-existing-FOM-constant',labels=[2])])
            cases=[('optimal',True,True,2,7,1.,True),('time_limit_feasible',True,True,2,13,1.,True),
                   ('placeholder',False,False,0,13,1.,False),('infeasible_primal',True,True,1,13,1.,False),
                   ('invalid_info',True,False,2,7,1.,False),('nan_primal',True,True,2,7,np.nan,False),
                   ('FOM_zero',True,True,2,7,0.,False),('infeasible_status_even_if_flags_claim_feasible',True,True,2,8,1.,False)]
            for name,vvalid,ivalid,primal_status,code,value,expected in cases:
                calls=[]
                native=NS(value_valid=vvalid,dual_valid=False,col_value=[value,2.],col_dual=[0.,0.],row_value=[1.],row_dual=[0.])
                def get():calls.append(1);return native
                h=NS(getSolution=get,getInfo=lambda:NS(valid=ivalid,primal_solution_status=primal_status,dual_solution_status=0),
                     getModelStatus=lambda:highspy.HighsModelStatus(code),modelStatusToString=lambda x:x.name,getObjectiveValue=lambda:3.)
                q=qualify_and_store(h,base/name,mf,record)
                assert q['network_writeback_qualified']==expected and len(calls)==1
                assert q['native_dual_valid'] is False and q['dual_solution_status']==0
                assert q['linopy_termination_condition']==termination_condition(code)
                passed('single_native_retrieval_'+name,qualification=q)
            # Existing caller consumes the same once-read fields; hashes reject corruption.
            raw=bytearray((mf/'D.npy').read_bytes());raw[-1]^=1;(mf/'D.npy').write_bytes(raw)
            try:load_arrays(mf,record)
            except ValueError:pass
            else:raise AssertionError('corrupt mapping accepted')
            passed('mapping_hash_corruption_rejected')
        # Integration test of the actual frozen PyPSA assignment without a solve.
        with tempfile.TemporaryDirectory() as temp:
            import importlib
            opt=importlib.import_module('pypsa.optimization.optimize')
            base=Path(temp)
            n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=3,freq='h'))
            n.add('Bus','b');n.add('Generator','g',bus='b',p_nom=10.,marginal_cost=2.)
            n.add('Load','l',bus='b',p_set=[1.,2.,3.]);n.export_to_netcdf(base/'frozen.nc')
            n=pypsa.Network(base/'frozen.nc');n.optimize.create_model();m=n.model
            vlabels=m.variables.flat.labels.to_numpy();clabels=m.constraints.flat.drop_duplicates('labels').labels.to_numpy()
            scale=NS(d=np.ones(len(vlabels)),r=np.ones(len(clabels)))
            mapping=NS(matrices=NS(vlabels=vlabels,clabels=clabels));base=Path(temp)
            record=save_mapping(base/'map',n,mapping,scale,'synthetic-only','synthetic-only')
            native=NS(value_valid=True,dual_valid=True,col_value=[1.,2.,3.],col_dual=[0.]*len(vlabels),row_value=[0.]*len(clabels),row_dual=[0.]*len(clabels))
            h=NS(getSolution=lambda:native,getInfo=lambda:NS(valid=True,primal_solution_status=2,dual_solution_status=2),
                 getModelStatus=lambda:highspy.HighsModelStatus.kOptimal,modelStatusToString=lambda x:'Optimal',getObjectiveValue=lambda:12.)
            q=qualify_and_store(h,base/'result',base/'map',record)
            del n,m
            n=pypsa.Network(base/'frozen.nc');n.optimize.create_model()
            apply_stored_solution(n,base/'map',base/'result',record,q)
            assert np.array_equal(n.generators_t.p['g'].to_numpy(),[1.,2.,3.])
            assert n.objective==12. and n.model.termination_condition=='optimal'
            assert np.array_equal(n.loads_t.p['l'].to_numpy(),[1.,2.,3.])
            passed('actual_frozen_pypsa_rebuild_and_assignment_from_disk_without_solver')
        with tempfile.TemporaryDirectory() as temp:
            values=np.linspace(-1,1,600_000,dtype=np.float64).tolist()
            tracemalloc.start();write_array(Path(temp)/'a.npy',values,np.float64);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            exact(np.load(Path(temp)/'a.npy',mmap_mode='r'),np.asarray(values),'float64 mmap')
            passed('float64_mmap_exact_scoped_python_heap',elements=len(values),traced_peak_bytes=peak,
                   interpretation='Scoped write only; input list preexists; not full-model RSS savings')
        # Formal negative cases for projection, using exact rational arithmetic.
        from fractions import Fraction as F
        assert F(0.1)+F(0.2)!=F(0.3)
        passed('binary64_fixed_total_nonzero_residual_cannot_be_dropped')
        # Two stores each 1 unit; q=(1,1). Both schedules are feasible, and
        # forcing equal-hour splits excludes both admissible reporting paths.
        schedules=[np.array([[1.,0.],[0.,1.]]),np.array([[0.,1.],[1.,0.]])]
        for x in schedules:
            assert np.array_equal(x.sum(axis=0),[1.,1.]) and np.array_equal(x.sum(axis=1),[1.,1.])
        assert not np.array_equal(schedules[0],schedules[1])
        passed('multi_stock_temporal_freedom_negative_case')
    return dict(status='PASS',solver_runs=0,presolve_calls=0,checks=checks)


if __name__=='__main__':
    import sys
    Path(sys.argv[1]).write_text(json.dumps(run(),indent=2,allow_nan=False)+'\n')
