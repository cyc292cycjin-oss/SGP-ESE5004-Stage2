"""Semantic NetCDF round trip of a (solved) network (V5 gate A4).

PyPSA omits time-series columns that equal the attribute default on export; such columns are
restored from the declared default before comparing (same rule as the D-stage
daily_physics.netcdf_roundtrip). Derived tables (SubNetwork) are not compared.
"""
from pathlib import Path
import numpy as np
import pandas as pd

# Topology/impedance bookkeeping that PyPSA recomputes at optimise time and does not treat as data.
DERIVED_TOPOLOGY_COLUMNS={'sub_network','x_pu','r_pu','g_pu','b_pu','x_pu_eff','r_pu_eff'}

def netcdf_readback(n,path):
    import pypsa
    path=Path(path);n.export_to_netcdf(str(path));back=pypsa.Network(str(path))
    if n.meta!=back.meta or not n.snapshots.equals(back.snapshots):raise ValueError('NetCDF snapshot/metadata mismatch')
    pd.testing.assert_frame_equal(n.snapshot_weightings,back.snapshot_weightings.reindex(columns=n.snapshot_weightings.columns),check_dtype=False,check_freq=False)
    restored=[];tables=0
    for c in n.iterate_components():
        if c.name=='SubNetwork':continue
        other=back.df(c.name)
        if set(c.df.index)!=set(other.index):raise ValueError('Component identity changed '+c.name)
        a=c.df.sort_index();b=other.reindex(index=c.df.index,columns=c.df.columns).sort_index()
        for col in a.columns:
            if col in DERIVED_TOPOLOGY_COLUMNS:continue  # recomputed by determine_network_topology/calculate_dependent_values, not a result
            x,y=a[col],b[col]
            if pd.api.types.is_numeric_dtype(x):
                if not np.array_equal(x.to_numpy(dtype=float),y.to_numpy(dtype=float),equal_nan=True):raise ValueError('NetCDF static mismatch '+c.name+'.'+col)
            elif not x.fillna('').astype(str).equals(y.fillna('').astype(str)):raise ValueError('NetCDF static mismatch '+c.name+'.'+col)
        for attr,frame in c.pnl.items():
            if not len(frame.columns):continue
            got=back.pnl(c.name)[attr];missing=frame.columns.difference(got.columns)
            if len(missing):
                default=c.attrs.at[attr,'default'] if attr in c.attrs.index else 0.
                try:default=float(default)
                except (TypeError,ValueError):raise ValueError('NetCDF omitted non-numeric columns '+c.name+':'+attr)
                original=frame[missing].to_numpy(dtype=float)
                if not np.isfinite(default) or not np.all(original==default):raise ValueError('NetCDF nondefault values missing '+c.name+':'+attr)
                got=got.reindex(index=frame.index,columns=frame.columns,fill_value=default);restored.append(dict(component=c.name,attribute=attr,columns=int(len(missing)),declared_default=default))
            got=got.reindex(index=frame.index,columns=frame.columns)
            if not np.array_equal(frame.to_numpy(dtype=float),got.to_numpy(dtype=float),equal_nan=True):raise ValueError('NetCDF dynamic mismatch '+c.name+':'+attr)
            tables+=1
    return back,dict(status='EXACT_SEMANTIC_ROUNDTRIP',dynamic_tables=tables,pypsa_omitted_declared_default_columns_restored=restored)
