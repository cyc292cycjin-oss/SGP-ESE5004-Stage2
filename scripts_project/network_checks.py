"""Solver-free network helpers kept from the retired build_diagnostic_network.py (S1-2)."""
import numpy as np
import pandas as pd

def assert_input_only(n):
    if len(n.loads) or n.meta.get('demand_owners'):raise ValueError('Electric base contains bound demand')
    if n.meta.get('source_is_solved') is not False or n.meta.get('input_only_extraction') is not True:raise ValueError('Base input provenance missing')
    for c in n.iterate_components():
        if not c.df.index.is_unique:raise ValueError('Nonunique '+c.name)
        if any(len(frame.columns) for attr,frame in c.pnl.items() if 'Output' in str(c.attrs.at[attr,'status'])):raise ValueError('Solved output leaked')

def compare_roundtrip(before,after):
    if before.meta!=after.meta:
        keys=sorted(k for k in set(before.meta)|set(after.meta) if before.meta.get(k)!=after.meta.get(k))
        raise ValueError('Metadata changed in NetCDF roundtrip: '+','.join(keys[:12]))
    if not before.snapshots.equals(after.snapshots):raise ValueError('Snapshots lost')
    pd.testing.assert_frame_equal(before.snapshot_weightings,after.snapshot_weightings.reindex(columns=before.snapshot_weightings.columns),check_dtype=False,check_freq=False)
    for c in before.iterate_components():
        if c.name=='SubNetwork':continue  # derived topology table (determine_network_topology), not an input; not persisted by PyPSA NetCDF
        other=after.df(c.name)
        if set(c.df.index)!=set(other.index):raise ValueError('Component identity changed '+c.name)
        # PyPSA may reconstruct default columns and reorder them on import.
        pd.testing.assert_frame_equal(c.df.sort_index(),other.reindex(index=c.df.index,columns=c.df.columns).sort_index(),check_dtype=False,check_names=False,check_freq=False,rtol=1e-12,atol=1e-12)
        for attr,frame in c.pnl.items():
            if len(frame.columns):pd.testing.assert_frame_equal(frame,after.pnl(c.name)[attr].reindex(columns=frame.columns),check_dtype=False,check_names=False,check_freq=False,rtol=1e-12,atol=1e-12)

def normalise_optional_strings(n):
    """Use PyPSA NetCDF's empty-string representation for absent string tags."""
    changed={}
    for c in n.iterate_components():
        for col in c.df:
            s=c.df[col]
            if s.dtype==object and s.isna().any() and all(isinstance(x,str) for x in s.dropna()):
                changed[c.name+'.'+col]=int(s.isna().sum());c.df[col]=s.fillna('')
    return changed

def check_physical_reachability(n):
    """Structural input-to-load reachability, not dispatch/capacity feasibility."""
    import networkx as nx
    g=nx.DiGraph();g.add_nodes_from(n.buses.index);sources=set()
    for name,z in n.generators.iterrows():
        if (z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0) and z.p_max_pu>0:sources.add(z.bus)
    for _,z in n.stores.iterrows():
        if z.e_initial>0:sources.add(z.bus)
    for name,z in n.storage_units.iterrows():
        if name in n.storage_units_t.inflow and (n.storage_units_t.inflow[name]>0).any() or z.inflow>0:sources.add(z.bus)
    for _,z in n.links.iterrows():
        if not (z.p_nom>0 or z.p_nom_extendable and z.p_nom_max>0):continue
        ports={int(c[3:]):z[c] for c in n.links if c.startswith('bus') and c[3:].isdigit() and z[c]}
        inputs=[ports[0]]+[b for i,b in ports.items() if i and z['efficiency' if i==1 else 'efficiency'+str(i)]<0]
        outputs=[b for i,b in ports.items() if i and z['efficiency' if i==1 else 'efficiency'+str(i)]>0]
        for b in inputs:
            for target in outputs:g.add_edge(b,target)
        if z.p_min_pu<0 and len(ports)==2:g.add_edge(ports[1],ports[0])
    for table in [n.lines,n.transformers]:
        for _,z in table.iterrows():
            if z.s_nom>0 or z.s_nom_extendable and z.s_nom_max>0:g.add_edge(z.bus0,z.bus1);g.add_edge(z.bus1,z.bus0)
    reached=set(sources)
    for b in sources:reached.update(nx.descendants(g,b))
    missing=[name for name,z in n.loads.iterrows() if z.bus not in reached]
    if missing:raise ValueError('No structural supply path for Load '+','.join(missing[:8]))
    return dict(source_buses=len(sources),reached_buses=len(reached),loads=len(n.loads),unreached_loads=0)
