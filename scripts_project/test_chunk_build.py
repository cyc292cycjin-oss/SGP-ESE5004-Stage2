"""Prove small eager/chunked full-transfer identity, no run or presolve."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import pypsa, highspy, dask
from unittest.mock import patch
from precision_handoff import transfer
from lossless_gate5_lifecycle import explicit_empty_dask_chunks,bounded_build_allocator

def build(chunk):
    n=pypsa.Network();n.set_snapshots(pd.date_range('2050-01-01',periods=65,freq='h'))
    n.add('Bus','b',carrier='AC');n.add('Carrier','AC');n.add('Generator','g',bus='b',p_nom=10.,marginal_cost=2.)
    n.add('Load','l',bus='b',p_set=np.linspace(1.,3.,65))
    n.add('Store','s',bus='b',e_nom=10.,e_initial=3.,standing_loss=0.)
    with bounded_build_allocator(), explicit_empty_dask_chunks(),dask.config.set(scheduler='synchronous'):
        n.optimize.create_model(chunk=chunk)
        h,m,r=transfer(n.model)
    h.clear()
    return r

if __name__=='__main__':
    import sys
    with patch.object(highspy.Highs,'run',side_effect=AssertionError('NO SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('NO PRESOLVE')):
        a,b=build(None),build(64)
        assert a==b
    Path(sys.argv[1]).write_text(json.dumps(dict(status='PASS',solver_runs=0,presolve_calls=0,
        test='65_snapshot_eager_vs_chunk64_complete_float64_transfer_receipts_identical',receipt=a),indent=2)+'\n')
