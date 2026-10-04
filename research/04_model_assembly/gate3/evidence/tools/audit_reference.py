"""Read-only Gate3 topology audit; graph reachability is a potential-path test."""
from pathlib import Path
import json,collections,math,argparse
import networkx as nx
parser=argparse.ArgumentParser();parser.add_argument('--evidence',type=Path);args=parser.parse_args()
W=Path(__file__).resolve().parent;E=args.evidence or W/'evidence'
raw=json.loads((E/'TUTORIAL_COMPONENTS.json').read_text());tables=raw['tables'];buses={r['Name']:r for r in tables['Bus']}
source='scripts/prepare_sector_network.py'
def finite(v):
    try:return math.isfinite(float(v))
    except (ValueError,TypeError):return False
def ports(r):return [(k,str(v)) for k,v in r.items() if k.startswith('bus') and k[3:].isdigit() and v not in ('',None)]
countries={name:r.get('country','') for name,r in buses.items()}
# Exact existing country metadata or exact location->electricity bus metadata.
for name,r in buses.items():
    if not countries[name] and r.get('location') in buses:
        countries[name]=buses[r['location']].get('country','')
neighbors=collections.defaultdict(set)
for r in tables['Link']:
    ps=[v for k,v in ports(r) if v in buses]
    cs={countries[v] for v in ps if countries[v]}
    for v in ps:neighbors[v]|=cs
electric=[];eg=nx.Graph();eg.add_nodes_from(buses)
for typ in ['Line','Link','Transformer']:
    for r in tables[typ]:
        a,b=r.get('bus0'),r.get('bus1')
        if a not in buses or b not in buses:continue
        if buses[a]['carrier'] not in ('AC','DC') or buses[b]['carrier'] not in ('AC','DC'):continue
        ca,cb=countries[a],countries[b]
        label='UNKNOWN' if not ca or not cb else 'DOMESTIC' if ca==cb else 'CROSS_BORDER'
        electric.append(dict(Name=r['Name'],ComponentType=typ,Carrier=r['carrier'],Bus0=a,Bus1=b,Country0=ca,Country1=cb,
                             Classification=label,FutureControllable=(label=='CROSS_BORDER'),Evidence='HISTORICAL_TUTORIAL_REFERENCE',Source=raw['source']))
        eg.add_edge(a,b)
audit=[]
for typ in ['Bus','Store','Link','Generator','Load']:
    for r in tables[typ]:
        ps=[r['Name']] if typ=='Bus' else ([r.get('bus')] if typ in ['Store','Generator','Load'] else [v for k,v in ports(r)])
        ps=[p for p in ps if p in buses];cs=sorted({countries[p] for p in ps if countries[p]})
        reached=sorted(set(cs)|set().union(*(neighbors[p] for p in ps if p!='co2 atmosphere')))
        co=cs[0] if len(cs)==1 else ''
        # Atmosphere role verified in add_co2, not name-only classification.
        atm=bool(ps) and all(p=='co2 atmosphere' and buses[p]['carrier']=='co2' for p in ps)
        shared=any(p!='co2 atmosphere' and not countries[p] and len(neighbors[p])>1 for p in ps)
        scope='REPORTING_ONLY' if atm else 'ASEAN_SHARED' if shared else 'NODE_LOCAL' if len(cs)==1 else 'UNKNOWN'
        role='AUDIT_ONLY_UNACCEPTED_REFERENCE'
        if typ=='Generator' and r.get('carrier') in ['gas','oil','coal','lignite'] and ps and buses[ps[0]]['carrier']==r['carrier']:
            scope='EXTERNAL_SUPPLY' if co else 'ASEAN_SHARED';role='COUNTRY_IMPORT_INTERFACE_REQUIRED'
        if scope in ('ASEAN_SHARED','UNKNOWN'):role='ISOLATE_OR_DEFER_WITH_BLOCKER'
        if atm:role='ALLOWED_ACCOUNTING_GLOBAL; DAC is ambient source, not point-source transport'
        expandable=bool(r.get('p_nom_extendable',r.get('e_nom_extendable',False)))
        cap={k:r[k] for k in ['p_nom','p_nom_min','p_nom_max','p_min_pu','p_max_pu','e_nom','e_initial','e_nom_min','e_nom_max','e_cyclic'] if k in r}
        carrier=r.get('carrier','');loc=source+' (component family; exact reference instance from NetCDF)';switch='sector/configuration family; see current source trace'
        if carrier in ('solid biomass','biomass','biogas'):loc=source+':1119 add_biomass';switch='sector.biomass_transport / solid_biomass_potential / biogas_potential'
        elif carrier in ('co2','co2 stored','co2 vent'):loc=source+':1409 add_co2';switch='sector.co2_network (false still shared physical pool)'
        elif carrier in ('gas','oil','coal','lignite') and typ in ['Bus','Generator','Store']:loc=source+':272 add_carrier_buses; :982 define_spatial';switch='sector.<fuel>.spatial_<fuel>'
        elif carrier in ('H2','H2 Electrolysis','SMR','SMR CC','H2 Fuel Cell','H2 Store Tank'):loc=source+':385 add_hydrogen';switch='sector.hydrogen.*'
        elif carrier=='Fischer-Tropsch':loc=source+':345 H2_liquid_fossil_conversions';switch='sector.fischer_tropsch'
        audit.append(dict(Name=r['Name'],ComponentType=typ,Carrier=carrier,Country=co,Node=';'.join(ps),Scope=scope,
            ConnectedCountries=';'.join(reached),Expandable=expandable,CapacityConstraint=json.dumps(cap,sort_keys=True),
            MarginalCost=r.get('marginal_cost'),CapitalCost=r.get('capital_cost'),SourceCodeLocation=loc,ConfigSwitch=switch,
            FirstFullSCRole=role,Evidence='HISTORICAL_TUTORIAL_NOT_CURRENT_RESEARCH_MODEL'))
# Directed signed-port dependency graph. Atmosphere is an explicit environmental
# boundary. Electricity border edges are cut only for prohibited-carrier audits.
g=nx.DiGraph();g.add_nodes_from(buses)
for r in tables['Link']:
    p=dict(ports(r));bus0=p.get('bus0')
    if bus0 not in buses:continue
    ins=[bus0];outs=[]
    for k,v in p.items():
        if k=='bus0' or v not in buses:continue
        eff=r.get('efficiency' if k=='bus1' else 'efficiency'+k[3:],0)
        if not finite(eff):continue
        if float(eff)>0:outs.append(v)
        elif float(eff)<0:ins.append(v)
    reversible=finite(r.get('p_min_pu',0)) and float(r.get('p_min_pu',0))<0
    for a in ins:
        for b in outs:
            if 'co2 atmosphere' in (a,b):continue
            if buses[a]['carrier'] in ('AC','DC') and buses[b]['carrier'] in ('AC','DC') and countries[a]!=countries[b]:continue
            g.add_edge(a,b,component=r['Name'])
            if reversible:g.add_edge(b,a,component=r['Name'])
for r in tables['Line']+tables['Transformer']:
    a,b=r.get('bus0'),r.get('bus1')
    if a in buses and b in buses and countries[a] and countries[a]==countries[b]:
        g.add_edge(a,b,component=r['Name']);g.add_edge(b,a,component=r['Name'])
paths=[];shared=[name for name in buses if not countries[name] and len(neighbors[name])>1 and name!='co2 atmosphere']
for pool in shared:
    upstream={};downstream={}
    for node in nx.ancestors(g,pool):
        c=countries[node]
        if c and c not in upstream:upstream[c]=node
    for node in nx.descendants(g,pool):
        c=countries[node]
        if c and c not in downstream:downstream[c]=node
    # Finite common resource/source coupling needs no return Link from country A.
    # Register its access fan-out separately instead of pretending a directed
    # injection path from A was observed.
    for ca in sorted(neighbors[pool]):
        for cb in sorted(downstream):
            if ca==cb:continue
            if ca in upstream:
                route=nx.shortest_path(g,upstream[ca],pool)+nx.shortest_path(g,pool,downstream[cb])[1:];kind='DIRECTED_CONVERSION_PATH'
            else:
                route=[pool]+nx.shortest_path(g,pool,downstream[cb])[1:];kind='SHARED_RESOURCE_ACCESS_NOT_A_TO_B_INJECTION'
            components=[g[a][b]['component'] for a,b in zip(route,route[1:])]
            paths.append(dict(Carrier=buses[pool]['carrier'],OriginCountry=ca,DestinationCountry=cb,Path=' -> '.join(route),
                Components=';'.join(components),PhysicalNetworkPresent=False,AllowedByResearchDesign=False,
                ActionRequired='Country/node pool; preserve resource cap; require accepted allocation where finite',
                SharedPool=pool,PathType=kind,Evidence='STRUCTURAL_POTENTIAL_NOT_DISPATCH_FEASIBILITY'))
out={'audit':audit,'hidden':paths,'electricity':electric,'shared_pools':{x:sorted(neighbors[x]) for x in shared},
     'country_map':countries,'graph_edges':[(a,b,v['component']) for a,b,v in g.edges(data=True)],
     'notes':'Sign-aware directed multiport dependency over-approximation, not feasible dispatch. Shared-resource fan-out explicitly separate from directed transfer. Electric cross-border and ambient atmosphere routes excluded from prohibited-carrier audit.'}
(E/'REFERENCE_GRAPH_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False))
print(json.dumps({'audit_rows':len(audit),'hidden_rows':len(paths),'electricity':dict(collections.Counter(r['Classification'] for r in electric)),'shared_pools':out['shared_pools']},indent=2))
