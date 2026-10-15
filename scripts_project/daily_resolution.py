"""Exact 2920x3h -> 365x24h reduction of an unsolved research network (S1-8 input).

Same arithmetic as the accepted C02 daily build (c02_model.average): every time-varying
input series is replaced by the exact rational mean of its eight 3-hour values per day,
so annual integrals are conserved to the last bit; weights become 24 h. Static tables and
metadata are copied unchanged. No solver.
"""
from fractions import Fraction as F
import copy
import numpy as np
import pandas as pd

HOURS=3;PER_DAY=8;DAYS=365

def average(a):
    a=np.asarray(a,dtype='<f8')
    if a.shape!=(DAYS*PER_DAY,) or not np.isfinite(a).all():raise ValueError('Daily aggregation expects 2920 finite values')
    if np.all(a.view('<u8')==a.view('<u8')[0]):return np.full(DAYS,a[0],dtype='<f8')
    return np.array([float(sum(map(lambda x:F(float(x)),v),F(0))/PER_DAY) for v in a.reshape(DAYS,PER_DAY)],dtype='<f8')

def to_daily(n):
    expected=pd.date_range('2013-01-01',periods=DAYS*PER_DAY,freq='3h',name='snapshot')
    if not n.snapshots.equals(expected):raise ValueError('Research 2920x3h snapshot boundary required')
    for col in ('objective','generators','stores'):
        if not np.array_equal(n.snapshot_weightings[col].to_numpy(),np.full(DAYS*PER_DAY,3.)):raise ValueError('Physical 3 h weights required')
    days=pd.DatetimeIndex(expected[::PER_DAY].values,name='snapshot')
    frames={};ledger=[]
    for c in n.iterate_components():
        for attr,frame in c.pnl.items():
            if not len(frame.columns):continue
            if 'Output' in str(c.attrs.at[attr,'status']):raise ValueError('Solved output cannot be aggregated: '+c.name+'.'+attr)
            result=np.empty((DAYS,len(frame.columns)),dtype='<f8')
            for i,name in enumerate(frame.columns):result[:,i]=average(frame[name].to_numpy())
            before=frame.to_numpy(dtype='<f8').sum(axis=0)*HOURS;after=result.sum(axis=0)*24.
            if not np.allclose(before,after,rtol=1e-12,atol=1e-6):raise ValueError('Annual integral changed: '+c.name+'.'+attr)
            frames[c.name,attr]=pd.DataFrame(result,index=days,columns=frame.columns)
            ledger.append(dict(component=c.name,attribute=attr,assets=int(len(frame.columns)),annual_integral_before=float(before.sum()),annual_integral_after=float(after.sum()),method='exact rational mean of 8 x 3h values per day'))
    out=n.copy();out.meta=copy.deepcopy(n.meta)
    out.set_snapshots(days)
    out.snapshot_weightings.loc[:,['objective','generators','stores']]=24.
    for (c,a),frame in frames.items():out.pnl(c)[a]=frame
    for c in n.iterate_components():pd.testing.assert_frame_equal(c.df,out.df(c.name),check_exact=True)
    out.meta.update(temporal_resolution='365x24h',temporal_reduction='S1 exact daily mean of frozen 2920x3h inputs (C02 arithmetic)',parent_resolution='2920x3h')
    return out,ledger
