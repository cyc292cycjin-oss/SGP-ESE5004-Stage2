"""Full-year temporal reduction with input-only, component-wise conservation."""
from copy import deepcopy
import hashlib
import numpy as np
import pandas as pd

FROZEN_SHA='238262c9d52e9d087d116799cbba0e3b5140aade7f64e6b8ebc02a448cd1419d'

def daily_validation_network(n):
    if n.meta.get('artifact_role')!='FULL_SC_RESEARCH_BASELINE_UNSOLVED' or not n.meta.get('fullsc_network_complete'):
        raise ValueError('Only complete frozen Gate4 input may enter Gate5')
    expected=pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h',name='snapshot')
    if not n.snapshots.equals(expected) or not np.all(n.snapshot_weightings.to_numpy()==3):
        raise ValueError('Frozen 2013 / 3h / 8760h time boundary required')
    if n.meta.get('policy_enabled') is not False:raise ValueError('Gate5 policy must remain OFF')
    accounts=set(n.loads.source_account_id)
    if len(accounts)!=171:raise ValueError('Accepted account set changed')
    frames={};checks=[]
    allowed={('Load','p_set'),('Generator','p_max_pu'),('StorageUnit','inflow')}
    for c in n.iterate_components():
        for attr,frame in c.pnl.items():
            if not len(frame.columns):continue
            if (c.name,attr) not in allowed:raise ValueError('Time varying field needs explicit aggregation semantics: '+c.name+'.'+attr)
            reduced=frame.resample('24h').mean()
            before=frame.sum()*3;after=reduced.sum()*24
            difference=after-before
            if not np.allclose(after,before,rtol=5e-13,atol=1e-7):raise ValueError('Annual input integral changed')
            for name in frame:
                checks.append(dict(Component=c.name,Attribute=attr,Name=name,BeforeIntegral=float(before[name]),AfterIntegral=float(after[name]),Difference=float(difference[name]),Unit='MWh' if attr in ['p_set','inflow'] else 'availability-hours',Status='PASS'))
            frames[c.name,attr]=reduced
    # Work on an independent object; all static tables and metadata are copied.
    out=n.copy();out.meta=deepcopy(n.meta)
    out.set_snapshots(pd.date_range('2013-01-01','2013-12-31',freq='24h',name='snapshot'))
    out.snapshot_weightings.loc[:,:]=24.
    for (c,a),frame in frames.items():out.pnl(c)[a]=frame
    for c in n.iterate_components():
        pd.testing.assert_frame_equal(c.df,out.df(c.name))
    out.meta.update(artifact_role='GATE5_REDUCED_VALIDATION_INPUT',validation_only=True,solver_allowed=True,scientific_results_allowed=False,gate5_allowed=True,gate6_allowed=False,formal_phase5_allowed=False,parent_gate4_sha256=FROZEN_SHA,temporal_reduction='2013 full-year 3h to24h weighted mean; 365x24h; no sampled days',constraint_hook_state='REGISTERED_NOT_YET_INSTALLED')
    return out,checks
