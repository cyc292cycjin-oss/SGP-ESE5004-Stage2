"""Materialise qualified existing units; no inference of dates, mapping or costs."""
import math,json,hashlib
from collections import defaultdict
import numpy as np
from asset_survival import select_asset,remaining_resource
from carrier_architecture import bus_name

def approved(x):
    return x.get('ApprovalStatus')=='HUMAN_ACCEPTED' and bool(x.get('Source')) and bool(x.get('DecisionReference'))

def finite(x,label,minimum=0):
    x=float(x)
    if not math.isfinite(x) or x<minimum:raise ValueError('Invalid '+label)
    return x

def integrate_survivors(n,evidence,contract,profile_network=None):
    units=evidence['records'];ids=[r['AssetID'] for r in units]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate unit ownership')
    if n.meta.get('existing_unit_components'):raise ValueError('Existing stock already integrated')
    plans=[];pending=[];groups=contract.get('resource_groups',{})
    for r in units:
        if r['SurvivalStatus']!='SURVIVES_2050':continue
        checked=select_asset(r)
        if checked['SurvivalStatus']!='SURVIVES_2050' or r.get('CapacityReconciliation')!='MATCHED_PARENT' or not math.isclose(float(r['RetainedCapacity2050']),checked['RetainedCapacity2050'],rel_tol=1e-12):raise ValueError('Unqualified unit promoted or retained capacity differs from original source')
        mapping=contract.get('mapping',{}).get(str(r['OriginalMappedBus']),{})
        p=contract.get('performance',{}).get(r['AssetID'],contract.get('performance',{}).get(r['Technology'],{}))
        if not approved(mapping) or not approved(p):pending.append(dict(AssetID=r['AssetID'],reason='Source-qualified mapping/performance/FOM/VOM pending'));continue
        node=mapping['Node']
        if node not in n.buses.index or mapping['Country']!=r['Country'] or n.buses.at[node,'country']!=r['Country']:raise ValueError('Mapping crosses country')
        if not mapping.get('OriginalPartition') or mapping['OriginalPartition']!=mapping.get('NodePartition'):raise ValueError('Mapping crosses original grid partition')
        eff=finite(p['Efficiency'],'existing efficiency',1e-9)
        if eff>1:raise ValueError('Invalid conversion efficiency')
        fom=finite(p['FixedOM_EUR_per_MW_e_year'],'existing fixed OM');vom=finite(p['VariableOM_EUR_per_MWh_e'],'existing variable OM')
        if fom==0 and p.get('ZeroFixedOMExplicitlyAccepted') is not True:raise ValueError('Unqualified zero existing OM')
        if p.get('CostBasis')!='EXISTING_NO_NEW_CAPEX' or p.get('PerformanceBasis')!='SOURCE_EXISTING_EQUIPMENT':raise ValueError('Existing investment/performance boundary violated')
        typ=p['ComponentType']
        if typ not in ['Generator','StorageUnit','Link']:raise ValueError('Unsupported existing component type')
        combustion={'CCGT','Hard Coal','Lignite','Oil','Solid Biomass','Biogas','Waste','Natural Gas'}
        if r['Technology'] in combustion and typ!='Link':raise ValueError('Existing combustion must retain explicit fuel and physical carbon ports')
        cap=finite(r['RetainedCapacity2050'],'surviving capacity')
        group=p.get('ResourceGroupByNode',{}).get(node,p.get('ResourceGroup'))
        if group=='EXISTING_ONLY_NO_NEW_CANDIDATE':
            if p.get('ExistingOnlyEvidence') is None:raise ValueError('Missing existing-only resource evidence')
        elif group not in groups or not approved(groups[group]):pending.append(dict(AssetID=r['AssetID'],reason='Resource limit semantics pending'));continue
        plans.append(dict(record=r,performance=p,node=node,type=typ,capacity=cap,efficiency=eff,fom=fom,vom=vom,group=group))
    # A resource group owns ONE potential envelope across all candidate copies.
    use=defaultdict(float)
    for q in plans:use[q['group']]+=q['capacity']
    envelopes={}
    for key,amount in use.items():
        if key=='EXISTING_ONLY_NO_NEW_CANDIDATE':continue
        g=groups[key];remaining=remaining_resource(finite(g['LimitMW'],'resource limit'),amount,g['Meaning'])
        candidates=g['NewBuildComponents'];seen=set()
        for c in candidates:
            typ=c['ComponentType'];name=c['Name'];df=n.df(typ)
            if (typ,name) in seen or name not in df.index or not df.at[name,'p_nom_extendable']:raise ValueError('Invalid/duplicate new build resource identity')
            seen.add((typ,name));finite(c['CapacityToMW'],'resource capacity conversion',1e-9)
            candidate_bus=df.at[name,'bus'] if typ in ['Generator','StorageUnit'] else df.at[name,'bus1']
            if any(q['node']!=candidate_bus for q in plans if q['group']==key):raise ValueError('Resource envelope crosses research node')
        envelopes[key]=dict(meaning=g['Meaning'],source_limit_mw=g['LimitMW'],existing_mw=amount,new_build_limit_mw=remaining,candidates=candidates,source=g['Source'])
    if len({(c['ComponentType'],c['Name']) for e in envelopes.values() for c in e['candidates']})!=sum(len(e['candidates']) for e in envelopes.values()):raise ValueError('Candidate assigned to multiple resource groups')
    # Aggregate only after screening: same node, technology, source-qualified
    # performance/profile contract and resource envelope. Never average ages to
    # decide survival. Different qualified performance classes stay distinct.
    aggregate=defaultdict(list)
    for q in plans:
        key=json.dumps([q['node'],q['record']['Technology'],q['performance'],q['group']],sort_keys=True)
        aggregate[key].append(q)
    combined=[]
    for key,members in aggregate.items():
        q=dict(members[0]);q['members']=[x['record'] for x in members];q['capacity']=sum(x['capacity'] for x in members)
        q['group_name']='existing_survivor::'+q['record']['AssetID'] if len(members)==1 else 'existing_survivor::'+q['node']+'::'+q['record']['Technology']+'::'+hashlib.sha256(key.encode()).hexdigest()[:12]
        combined.append(q)
    # Materialise only after all accepted plans and shared resource envelopes pass.
    identity={};carbon=[];fom_total=0.
    for q in combined:
        r=q['record'];p=q['performance'];node=q['node'];typ=q['type'];name=q['group_name'];carrier=p['Carrier'];members=q['members']
        if name in n.df(typ).index:raise ValueError('Duplicate existing component')
        if carrier not in n.carriers.index:n.add('Carrier',carrier,co2_emissions=0.)
        first=min(float(x['CommissioningYear']) for x in members);last=min(float(x['RetirementYear']) for x in members)
        common=dict(carrier=carrier,p_nom_extendable=False,build_year=first,lifetime=last-first,capital_cost=0.)
        if typ=='Link':
            fuel=p['FuelCarrier'];fuelbus=bus_name(node,fuel);atmo='ReportingCO2 atmosphere'
            if fuel not in {'gas','oil','coal','lignite'} and not approved(p.get('DedicatedFuelSupply',{})):raise ValueError('Existing conversion lacks an approved dedicated fuel boundary; fixed biomass obligations are unavailable to power')
            for b,ca,co in [(fuelbus,fuel,r['Country']),(atmo,'co2 atmosphere','')]:
                if ca not in n.carriers.index:n.add('Carrier',ca,co2_emissions=0.)
                if b not in n.buses.index:n.add('Bus',b,carrier=ca);n.buses.loc[b,'country']=co
            factor=finite(p['PhysicalCO2_t_per_MWh_fuel'],'existing physical CO2')
            n.add('Link',name,bus0=fuelbus,bus1=node,bus2=atmo,p_nom=q['capacity']/q['efficiency'],efficiency=q['efficiency'],efficiency2=factor,marginal_cost=q['vom']*q['efficiency'],p_min_pu=0.,**common)
            carbon.append(dict(component_type='Link',component=name,carrier=carrier,sector='Power',country=r['Country'],coefficient=factor,policy_weight=1.,accepted=True,source=p['Source'],physical_reporting=True,policy_assignment_status='SOURCE_EXISTING_POWER'))
        elif typ=='Generator':
            n.add(typ,name,bus=node,p_nom=q['capacity'],efficiency=q['efficiency'],marginal_cost=q['vom'],**common)
        else:
            n.add(typ,name,bus=node,p_nom=q['capacity'],efficiency_dispatch=q['efficiency'],efficiency_store=finite(p['EfficiencyStore'],'storage efficiency'),max_hours=finite(p['MaxHours'],'storage energy duration'),cyclic_state_of_charge=p['CyclicStateOfCharge'],marginal_cost=q['vom'],**common)
        for attr,v in p.get('StaticOperatingInputs',{}).items():
            if attr not in {'p_min_pu','p_max_pu','standing_loss'}:raise ValueError('Unapproved operating input field')
            n.df(typ).loc[name,attr]=finite(v,attr)
        for attr,source in p.get('Profiles',{}).items():
            if profile_network is None or not profile_network.snapshots.equals(n.snapshots):raise ValueError('Existing profile weather/time mismatch')
            if attr not in {'p_max_pu','p_min_pu','inflow'} or not source.get('Source'):raise ValueError('Unqualified existing time profile')
            frame=profile_network.pnl(source['ComponentType'])[attr]
            values=frame[source['Component']].to_numpy()*finite(source['Multiplier'],'profile multiplier')
            if not np.isfinite(values).all():raise ValueError('Invalid existing profile')
            n.import_series_from_dataframe(__import__('pandas').DataFrame({name:values},index=n.snapshots),typ,attr)
        df=n.df(typ)
        for k,v in dict(asset_role='existing_survivor',source_unit_id=r['RawUnitID'] if len(members)==1 else json.dumps([x['RawUnitID'] for x in members]),source_parent_id=json.dumps(sorted({x['ParentAssetID'] for x in members})),country=r['Country'],retained_electric_capacity_mw=q['capacity'],existing_fixed_om_eur_per_mw_year=q['fom'],existing_annual_fixed_om_eur=q['fom']*q['capacity'],source_asset_version=json.dumps(sorted({x['SourceVersion'] for x in members})),age_fields_meaning='Already screened2050 active group; first commissioning and earliest retirement envelope; no mean-age screening').items():df.loc[name,k]=v
        fom_total+=q['fom']*q['capacity']
        for u in members:identity[u['AssetID']]=dict(component_type=typ,component=name,capacity_mw=u['RetainedCapacity2050'],node=node,source=u['Source'],source_version=u['SourceVersion'],commissioning_year=u['CommissioningYear'],retirement_year=u['RetirementYear'])
    for e in envelopes.values():
        for c in e['candidates']:n.df(c['ComponentType']).loc[c['Name'],'p_nom_max']=min(float(n.df(c['ComponentType']).at[c['Name'],'p_nom_max']),e['new_build_limit_mw']/c['CapacityToMW'])
    n.meta.update(existing_unit_components=identity,existing_resource_groups=envelopes,existing_annual_fixed_om_eur=fom_total,existing_cost_boundary='New CAPEX=0; existing annual fixed OM added once by explicit objective hook; VOM charged to dispatch',existing_carbon_components=carbon)
    if identity:n.meta['required_constraint_hooks']=sorted(set(n.meta.get('required_constraint_hooks',[]))|{'research_existing_assets'})
    return dict(integrated_units=len(identity),integrated_components=len(combined),integrated_capacity_mw=sum(q['capacity'] for q in plans),annual_existing_fixed_om_eur=fom_total,pending_qualified_units=pending,resource_groups=envelopes,existing_units=identity)

def install_existing_asset_constraints(n):
    """Future hook after model/objective creation; never calls a solver."""
    if getattr(n,'_research_existing_assets_model',None) is n.model:raise ValueError('Existing cost/resource hook already installed')
    for key,g in n.meta.get('existing_resource_groups',{}).items():
        terms=[n.model[c['ComponentType']+'-p_nom'].sel({c['ComponentType']+'-ext':c['Name']})*c['CapacityToMW'] for c in g['candidates']]
        if terms:n.model.add_constraints(sum(terms)<=g['new_build_limit_mw'],name='ResearchExistingResource-'+key)
    # This frozen Linopy version rejects literal objective constants. A scalar
    # fixed at one carries the audited annual FOM without introducing capacity,
    # dispatch, a financing assumption or an optimisation choice.
    cost=float(n.meta.get('existing_annual_fixed_om_eur',0.))
    if cost:
        one=n.model.add_variables(lower=1.,upper=1.,name='Research-existing-FOM-constant')
        n.model.objective+=one*cost
    n._research_existing_assets_model=n.model
