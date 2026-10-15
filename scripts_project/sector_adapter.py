"""Adapter around upstream scripts/prepare_sector_network.py used as a component library (S1-1, R0).

The upstream module is imported unchanged. Every module global it expects is injected by
`inject()`; the source of each injected value is recorded in the returned ledger and in
`INJECTED_GLOBALS`. The functions in `NOT_CALLED` are never invoked by the research layer.

Naming decision (S1-1): the research layer adopts the upstream bus naming
`"<node> <carrier>"` (e.g. `TH2 0 gas`, `TH2 0 H2`); the Phase4 research naming
`"<node> :: <carrier>"` is renamed on load (see carrier_architecture.rename_legacy_bus).
"""
from pathlib import Path
from types import SimpleNamespace
import copy,json,logging,sys
import numpy as np
import pandas as pd

NOT_CALLED=('convert_conventional_generators_to_links','average_every_nhours','add_co2_budget','add_heat','add_residential','add_services')
# Upstream add_hydrogen builds its full `tech_params` dictionary eagerly, so every row named
# there must exist in `costs` even when the technology is not selected. Rows that the frozen
# cost table lacks are added as NaN placeholders; no placeholder value ever reaches a component
# (asserted in add_hydrogen()).
TECH_PARAM_ROWS=('electrolysis','Alkaline electrolyzer large size','Alkaline electrolyzer medium size','Alkaline electrolyzer small size','PEM electrolyzer small size','SOEC',
                 'H2 production solid biomass steam reforming','H2 production biomass gasification','H2 production biomass gasification CC','SMR','SMR CC',
                 'H2 production natural gas steam reforming','H2 production natural gas steam reforming CC','H2 production coal gasification','H2 production coal gasification CC',
                 'H2 production heavy oil partial oxidation','solid biomass','gas','coal','oil')
INJECTED_GLOBALS={
    'snakemake':'SimpleNamespace built here: params.sector_options = merged upstream config sector block with research.hydrogen overrides; params.countries = 11 ASEAN ISO2; params.h2_underground=False; input.pipelines = empty CSV (no gas network -> greenfield H2 routing); wildcards.planning_horizons="2050"',
    'options':'same dict as snakemake.params.sector_options (upstream reads both names)',
    'spatial':'upstream define_spatial(nodes, options) with nodes = research spatial nodes (96 AC buses + DC buses without B2B converter)',
    'countries':'sorted carrier_architecture.COUNTRIES',
    'pop_layout':'DataFrame indexed by the spatial nodes, no columns: only its index is used by define_spatial; population-based functions are in NOT_CALLED',
    'investment_year':'2050 (research target year)',
    'demand_sc':'configs/research/baseline.yaml research_assembly.demand_scenario',
    'costs':'passed explicitly to each upstream function: EUR2020 price-layer table of costs_2050_sec.csv (price_basis.load_table)',
    'logger':'upstream module logger left as is',
}

def load_upstream(repo):
    repo=Path(repo)
    if str(repo/'scripts') not in sys.path:sys.path.insert(0,str(repo/'scripts'))
    import prepare_sector_network as psn
    for name in NOT_CALLED:
        if not hasattr(psn,name):raise ValueError('Upstream function listed in NOT_CALLED is missing: '+name)
    return psn

def spatial_nodes(n):
    """Research spatial nodes: AC buses plus DC buses that have no back-to-back converter."""
    ac=list(n.buses.index[n.buses.carrier=='AC']);dc=list(n.buses.index[n.buses.carrier=='DC'])
    b2b=n.links[n.links.carrier=='B2B'];coupled=set(b2b.bus0)|set(b2b.bus1)
    return ac+[b for b in dc if b not in coupled]

def dc_to_ac(n):
    """Converter-coupled DC bus -> co-located AC bus (B2B links, length 0)."""
    out={}
    for _,z in n.links[n.links.carrier=='B2B'].iterrows():
        dc,ac=(z.bus0,z.bus1) if n.buses.at[z.bus0,'carrier']=='DC' else (z.bus1,z.bus0)
        if n.buses.at[dc,'carrier']!='DC' or n.buses.at[ac,'carrier']!='AC':raise ValueError('B2B converter does not couple DC to AC: '+str(z.name))
        out[dc]=ac
    return out

def build_options(sector_cfg,research_hydrogen):
    """Upstream sector options with the research S1 hydrogen decisions applied (documented in baseline.yaml)."""
    options=copy.deepcopy(sector_cfg);h=options.setdefault('hydrogen',{})
    h.update(network=True,network_routes='greenfield',gas_network_repurposing=False,hydrogen_colors=False,
             h2_turbine=bool(research_hydrogen['h2_turbine']),production_technologies=list(research_hydrogen['production_technologies']),
             network_limit=research_hydrogen.get('network_limit_GWkm'))
    h.setdefault('underground_storage',{});h['underground_storage']=dict(h['underground_storage'],enabled=bool(research_hydrogen['underground_storage']))
    if research_hydrogen['network']!='greenfield_along_grid':raise ValueError('Only greenfield H2 routing is implemented in S1')
    options['co2_network']=True  # spatial per node (define_spatial); add_co2 itself is not called in S1
    options.setdefault('ammonia',{})['enable']=False
    for k in ('gas','oil','coal','lignite'):options.setdefault(k,{})['spatial_'+k]=True
    options['biomass_transport']=True
    return options

def inject(psn,n,options,nodes,countries,pipelines_csv,demand_scenario):
    nodes=pd.Index(nodes,name='Bus')
    pipelines_csv=Path(pipelines_csv);pipelines_csv.parent.mkdir(parents=True,exist_ok=True)
    if not pipelines_csv.exists():pipelines_csv.write_text('bus0,bus1,length,capacity\n')
    snakemake=SimpleNamespace(params=SimpleNamespace(sector_options=options,countries=sorted(countries),h2_underground=False,demand_scenario=demand_scenario),
                              input=SimpleNamespace(pipelines=str(pipelines_csv),h2_cavern=None),wildcards=SimpleNamespace(planning_horizons='2050'),config={})
    psn.snakemake=snakemake;psn.options=options;psn.countries=sorted(countries)
    psn.pop_layout=pd.DataFrame(index=nodes);psn.investment_year=2050;psn.demand_sc=demand_scenario
    psn.spatial=psn.define_spatial(nodes,options)
    return dict(injected={k:v for k,v in INJECTED_GLOBALS.items()},not_called=list(NOT_CALLED),spatial_nodes=int(len(nodes)),
                hydrogen_options={k:options['hydrogen'].get(k) for k in ['network','network_routes','gas_network_repurposing','hydrogen_colors','h2_turbine','production_technologies','network_limit','underground_storage']},
                pipelines_csv=pipelines_csv.name)  # name only: the output directory must not leak into network metadata (byte-identical builds)

def prepare_costs(costs):
    """Add NaN placeholder rows for names the upstream dict literal references but the frozen table lacks."""
    c=costs.copy();added=[]
    for t in TECH_PARAM_ROWS:
        if t not in c.index:c.loc[t]=np.nan;added.append(t)
    return c,added

def _snapshot(n):return {c.name:set(c.df.index) for c in n.iterate_components()}

def add_hydrogen(psn,n,costs,nodes,mapping):
    """Call upstream add_hydrogen once; then (a) tag H2 buses with their country, (b) remap pipeline
    endpoints at converter-coupled DC buses to the co-located AC bus (upstream assumes DC links join
    AC buses; the PyPSA-ASEAN 100-node network has 3 converter buses), (c) register any Load the
    upstream function created, (d) prove that no placeholder cost reached a component."""
    c,placeholders=prepare_costs(costs);before=_snapshot(n)
    psn.add_hydrogen(n,c)
    after=_snapshot(n);added={k:sorted(after[k]-before.get(k,set())) for k in after if after[k]-before.get(k,set())}
    removed={k:sorted(before[k]-after.get(k,set())) for k in before if before[k]-after.get(k,set())}
    for b in added.get('Bus',[]):
        node=b[:-3] if b.endswith(' H2') else None
        if node is None or node not in n.buses.index:raise ValueError('Unexpected upstream bus: '+b)
        n.buses.loc[b,'country']=n.buses.at[node,'country'];n.buses.loc[b,'location']=node
    remaps=[];renamed=[]
    pipes=n.links.index[n.links.carrier=='H2 pipeline']
    for name in list(pipes):
        z=n.links.loc[name];changed=False;ends=[]
        for col in ['bus0','bus1']:
            node=z[col][:-3]
            if node in mapping:
                target=mapping[node]+' H2'
                if target not in n.buses.index:raise ValueError('Mapped AC node has no H2 bus: '+target)
                n.links.at[name,col]=target;changed=True;remaps.append(dict(pipeline=name,port=col,before=z[col],after=target))
            ends.append(n.links.at[name,col])
        if ends[0]==ends[1]:
            n.remove('Link',name);remaps.append(dict(pipeline=name,port='both',before=str(list(z[['bus0','bus1']])),after='REMOVED_SELF_LOOP'));continue
        if changed:
            new='H2 pipeline '+ends[0][:-3]+' -> '+ends[1][:-3]+' via HVDC'
            n.links.rename(index={name:new},inplace=True);renamed.append(dict(before=name,after=new))
    for name,z in n.links[n.links.carrier=='H2 pipeline'].iterrows():
        if not (z.bus0.endswith(' H2') and z.bus1.endswith(' H2')) or z.bus0 not in n.buses.index or z.bus1 not in n.buses.index:raise ValueError('Dangling H2 pipeline port: '+name)
    for typ in ['Generator','Link','Store','StorageUnit']:
        df=n.df(typ)
        for name in added.get(typ,[]):
            if name not in df.index:continue
            if not np.isfinite(float(df.at[name,'capital_cost'])):raise ValueError('Placeholder cost reached component '+name)
    loads=added.get('Load',[])
    if loads:
        from assembly_components import register_upstream_loads
        register_upstream_loads(n,loads,'add_hydrogen','HydrogenUpstream')
    ledger=dict(function='prepare_sector_network.add_hydrogen',added={k:len(v) for k,v in added.items()},removed_by_upstream={k:v for k,v in removed.items()},
                carriers_added=sorted({str(n.df(t).at[x,'carrier']) for t in ['Generator','Link','Store'] for x in added.get(t,[]) if x in n.df(t).index}),
                placeholder_cost_rows=placeholders,pipeline_endpoint_remaps=remaps,pipeline_renames=renamed,upstream_loads_registered=list(loads),
                europe_specific_parameters_disabled=dict(network_limit_GWkm='not applied (upstream solve-time constraint H2_network_limit lives in solve_network.py, which the research layer does not use)',gas_network_repurposing_0_8='not applied (gas_network_repurposing=False, empty pipelines file -> greenfield only)',hydrogen_colors='False (no grid/green/grey/blue/pink H2 buses)',underground_storage='disabled (no ASEAN cavern data; DATA_PENDING)'))
    return ledger
