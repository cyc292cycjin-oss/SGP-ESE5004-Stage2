"""Explicit Gate4 choices; source-fixed resource allocations and cost semantics.

No solver, no new resource. Source identities are retained through allocations.
"""
import copy,json,hashlib,math
from pathlib import Path
from collections import defaultdict
import numpy as np

DECISION='GATE4-20261006-CANONICAL-SELECTED-CLOSURE'
POOLS={'ID:ID_Sulawesi0:Reservoir','ID:ID_Sumatra3:Run-Of-River','LA:LA2:Reservoir','MM:MM2:Reservoir','MM:MM2:Run-Of-River','PH:PH_Mindanao6:Run-Of-River','VN:VN2:Run-Of-River'}

def require_decision(d):
    if d.get('ApprovalStatus')!='HUMAN_ACCEPTED' or d.get('DecisionReference')!=DECISION:raise ValueError('Selected closure needs explicit human decision')
    if set(d.get('HydroPools',[]))!=POOLS:raise ValueError('Hydro approval scope differs')

def apply_cost_choices(n,source,d):
    require_decision(d)
    expected=.01+.002*(np.random.RandomState(174).random_sample(len(source.links))-.5)
    noise=dict(zip(source.links.index,expected));rows=[]
    ids=n.links.index[n.links.carrier.isin(['DC','B2B'])]
    if len(ids)!=13:raise ValueError('Frozen transmission scope changed')
    for name in ids:
        old=float(n.links.at[name,'marginal_cost'])
        if old!=noise[name]:raise ValueError('Connection marginal cost is not traced inherited noise')
        n.links.at[name,'marginal_cost']=0.
        n.links.loc[name,'variable_cost_method']='ASSEMBLY_V1_REMOVE_INHERITED_TRANSMISSION_NOISE'
        rows.append(dict(Component=name,Before=old,After=0.,Method=n.links.at[name,'variable_cost_method'],DecisionReference=DECISION,CapitalCostAfterRebuild=float(n.links.at[name,'capital_cost']),CapitalNoiseTreatment='Already rebuilt from frozen2050 unit costs; no second subtraction'))
    count=0
    for name,z in n.generators.iterrows():
        if z.get('asset_role')!='new_build_candidate' or z.carrier not in ['solar','onwind','offwind-ac','offwind-dc']:continue
        value=.01 if z.carrier=='solar' else .015
        if z.marginal_cost!=value:raise ValueError('Frozen renewable configuration differs')
        n.generators.loc[name,'variable_cost_method']='ASSEMBLY_V1_EXPLICIT_CONFIG_VARIABLE_COST';count+=1
    if count!=340:raise ValueError('Frozen explicit configuration scope changed')
    n.meta['selected_cost_decision']=dict(DecisionReference=DECISION,transmission=rows,renewable_components=count,renewable_units='EUR2020/MWh',classification='EXPLICIT_MODEL_ASSUMPTION_NOT_MEASURED_VOM',solver_runs=0)
    return rows

def resource_profile(spec,n):
    """Rebuild each accepted envelope from original INPUT series, before sharing."""
    total=np.zeros(len(n.snapshots))
    for t in spec['ResourceTerms']:
        v=n.pnl(t['ComponentType'])[t['Attribute']][t['Component']].to_numpy()*float(t['SourceMultiplier'])
        if t.get('AcceptedClipMW') is not None:v=np.minimum(v,float(t['AcceptedClipMW']))
        if not np.isfinite(v).all() or (v<0).any():raise ValueError('Invalid accepted envelope')
        if hashlib.sha256(v.tobytes()).hexdigest()!=t['AcceptedEnvelopeSHA256']:raise ValueError('Accepted envelope changed')
        total+=v*float(t['AllocationShare'])
    return total/float(spec.get('NormalisationMW',1.))

def validate_allocated_resources(contract,n,admitted_unit_ids=None):
    ledger=contract.get('resource_reallocation',[]);seen=set();totals=defaultdict(float);emax=defaultdict(float)
    if not ledger:return True
    for r in ledger:
        key=(r['ResourceIdentity'],r['RecipientNode'])
        if key in seen:raise ValueError('Duplicate allocated resource recipient')
        seen.add(key);totals[r['ResourceIdentity']]+=r['AllocationShare'];emax[r['ResourceIdentity']]+=r['AllocatedEmaxMWh']
        if admitted_unit_ids is not None and not set(r['RecipientUnits'])<=set(admitted_unit_ids):raise ValueError('Accepted resource beneficiary failed integration')
    for ident in totals:
        rs=[r for r in ledger if r['ResourceIdentity']==ident]
        if not math.isclose(totals[ident],1.,rel_tol=1e-12,abs_tol=1e-12):raise ValueError('Resource shares must sum to one')
        if not math.isclose(emax[ident],rs[0]['OriginalEmaxMWh'],rel_tol=1e-12,abs_tol=1e-8):raise ValueError('Resource Emax budget changed')
    # Contract terms must match the ledger, rather than trusting unique derived IDs.
    for u,p in contract['performance'].items():
        for spec in p.get('Profiles',{}).values():
            if 'ResourceTerms' not in spec:continue
            expected=[r for r in ledger if u in r['RecipientUnits']]
            got={(t['ResourceIdentity'],t['AllocationShare']) for t in spec['ResourceTerms']}
            if got!={(r['ResourceIdentity'],r['AllocationShare']) for r in expected}:raise ValueError('Profile allocation not backed by resource ledger')
            resource_profile(spec,n)
    return True

def reallocate_hydro(contract,n,d):
    require_decision(d);c=copy.deepcopy(contract);groups=c['hydro_group_qualification']['groups'];ledger=[]
    def pool(g):return g['Country']+':'+g['Node'].rsplit(' ',1)[0]+':'+g['HydroSubtype']
    for pid in sorted(POOLS):
        recipients=[g for g in groups if pool(g)==pid]
        original=[g for g in recipients if g['Status']=='SOURCE_QUALIFIED_GROUP_PROXY']
        pending=[g for g in recipients if g['Status']=='PENDING']
        if not original or not pending:raise ValueError('Approved pool is not a mix of accepted resource and pending turbines')
        cap=sum(g['SurvivingCapacityMW'] for g in recipients)
        if len({g['Node'] for g in recipients})!=len(recipients):raise ValueError('Duplicate recipient node')
        prototype=c['performance'][original[0]['SourceUnitIDs'][0]]
        for g in original:
            p=c['performance'][g['SourceUnitIDs'][0]]
            for k in ['ComponentType','Efficiency','FixedOM_EUR_per_MW_e_year','VariableOM_EUR_per_MWh_e','HydroSubtype']:
                if p[k]!=prototype[k]:raise ValueError('Incompatible resource-group performance classes')
        terms=[];emax=0.
        for g in original:
            is_ror=g['HydroSubtype']=='Run-Of-River';attr='p_max_pu' if is_ror else 'inflow';typ='Generator' if is_ror else 'StorageUnit'
            v=n.pnl(typ)[attr][g['SourceComponent']].to_numpy()*(g['SourceInputCapacityMW'] if is_ror else 1.)
            if is_ror:v=np.minimum(v,g['SurvivingCapacityMW'])
            energy=float(v@n.snapshot_weightings['generators' if is_ror else 'stores'].to_numpy());E=0. if is_ror else g['EnergyCapacityMWh'];emax+=E
            terms.append(dict(ResourceIdentity=g['ResourceIdentity'],ComponentType=typ,Component=g['SourceComponent'],Attribute=attr,SourceMultiplier=g['SourceInputCapacityMW'] if is_ror else 1.,AcceptedClipMW=g['SurvivingCapacityMW'] if is_ror else None,AcceptedEnvelopeSHA256=hashlib.sha256(v.tobytes()).hexdigest(),OriginalAnnualMWh=energy,OriginalEmaxMWh=E))
        for g in recipients:
            share=g['SurvivingCapacityMW']/cap;is_ror=g['HydroSubtype']=='Run-Of-River';p=copy.deepcopy(prototype)
            ident=pid+'::allocated::'+g['Node'];ts=[dict(t,AllocationShare=share) for t in terms]
            spec=dict(ComponentType='Generator' if is_ror else 'StorageUnit',Component=ident,ResourceIdentity=ident,ResourceTerms=ts,NormalisationMW=g['SurvivingCapacityMW'] if is_ror else 1.,Aggregation='CAPACITY_WEIGHTED_NORMALISED' if is_ror else 'SHARED_GROUP_ONCE',Source=DECISION+'#C; exact original ResourceIdentity terms retained')
            p.update(Profiles={'p_max_pu' if is_ror else 'inflow':spec},HydroResourceIdentity=ident,AdmittedGroupCapacityMW=g['SurvivingCapacityMW'],SourceGroupCapacityMW=sum(x['SourceInputCapacityMW'] for x in original),AuthorizationReference=DECISION+'#C',SpatialMethod='ASSEMBLY_V1_ACCEPTED_RESOURCE_SPATIAL_PROXY')
            if not is_ror:p.update(MaxHours=emax/cap,StorageEnergyBasis='ACCEPTED_RESOURCE_EMAX_CONSERVED_SPATIAL_PROXY')
            v=resource_profile(spec,n)
            if is_ror and (v>1+1e-12).any():raise ValueError('ROR envelope requires additional unapproved clipping')
            was_pending=g['Status']=='PENDING'
            g.update(Status='SOURCE_QUALIFIED_SPATIAL_PROXY',OriginalStatus=g['Status'],ResourceIdentity=ident,SourceResources=[t['ResourceIdentity'] for t in terms],AdmittedAnnualEnvelopeMWh=float((v*(g['SurvivingCapacityMW'] if is_ror else 1.))@n.snapshot_weightings['generators' if is_ror else 'stores'].to_numpy()),EnergyCapacityMWh=emax*share if not is_ror else 0.,DecisionReference=DECISION+'#C',SensitivityRequired=True,HydrologicalEquivalenceEstablished=False)
            for u in g['SourceUnitIDs']:c['performance'][u]=copy.deepcopy(p)
            for t in terms:ledger.append(dict(PoolID=pid,ResourceIdentity=t['ResourceIdentity'],SourceComponent=t['Component'],RecipientNode=g['Node'],RecipientUnits=g['SourceUnitIDs'],RecipientCapacityMW=g['SurvivingCapacityMW'],NewlyAdmitted=was_pending,AllocationShare=share,OriginalAnnualMWh=t['OriginalAnnualMWh'],AllocatedAnnualMWh=t['OriginalAnnualMWh']*share,OriginalEmaxMWh=t['OriginalEmaxMWh'],AllocatedEmaxMWh=t['OriginalEmaxMWh']*share,AcceptedEnvelopeSHA256=t['AcceptedEnvelopeSHA256'],Method='ASSEMBLY_V1_ACCEPTED_RESOURCE_SPATIAL_PROXY',DecisionReference=DECISION+'#C',BasinEquivalence=False))
    covered={u for r in ledger for u in r['RecipientUnits']};c['resource_reallocation']=ledger
    c['hydro_group_qualification']['pending']=[r for r in c['hydro_group_qualification']['pending'] if r['AssetID'] not in covered]
    c['hydro_group_qualification']['resource_reallocation']=ledger
    validate_allocated_resources(c,n)
    return c,ledger

def retirement_upper_bound(r,year=2050):
    """No invented commissioning year: only a verified operating observation."""
    o=r.get('OperatingObservation',{})
    if r.get('AssetClass')!='OBSERVED_EXISTING' or r.get('CommissioningYear') is not None:return None
    if not r.get('LifetimeAccepted') or o.get('EvidenceKind')!='DATED_OPERATING_SOURCE_SNAPSHOT' or not o.get('Source') or o.get('Verified') is not True:return None
    y=o.get('Year');life=r.get('Lifetime')
    if y is None or life is None or not math.isfinite(float(y)+float(life)):return None
    if y+life<=year:return dict(r,SurvivalStatus='RETIREMENT_PROVEN_BY_COMMISSIONING_UPPER_BOUND',RetainedCapacity2050=0.,RetirementYear=None,CommissioningUpperBound=y,RetirementUpperBound=y+life,DecisionBasis=DECISION+'#9; accepted lifetime applied to dated operating observation; no imputed age')
    return None

def qualify_cohort_identity(selected,identity_status):
    """Duplicate source entries add no capacity; their physical stock is elsewhere."""
    out=copy.deepcopy(selected)
    if out['SurvivalStatus']!='SURVIVES_2050':return out
    if identity_status=='DUPLICATE_EXISTING_GEM_SITE':
        out.update(SurvivalStatus='NOT_INHERITED_DUPLICATE_SOURCE',RetainedCapacity2050=0.,InventoryDisposition='ALREADY_REPRESENTED_BY_GEM_NOT_PHYSICALLY_RETIRED')
    elif identity_status!='DISJOINT_FROZEN_SOURCE_SELECTION':
        out.update(SurvivalStatus='UNRESOLVED_PHYSICAL_IDENTITY',RetainedCapacity2050=None)
    return out
