"""Qualify input-only annual hydro groups and the explicitly accepted PHS proxy.

No solved capacities, dispatch, spill or state-of-charge series are accessed.
The original input resource envelope is fixed when surviving turbine MW change.
"""
from pathlib import Path
import argparse,json,hashlib,collections,math
import numpy as np,pandas as pd,pypsa

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,default=str)+'\n')

def prepare(repo,reference,costs,survival,contract,decisions,output,report):
 d=json.loads(decisions.read_text())
 if d.get('ApprovalStatus')!='HUMAN_ACCEPTED' or d.get('PHSMaxHours')!=6:raise ValueError('Hydro methods require explicit current human decision')
 n=pypsa.Network(reference);stock=json.loads(survival.read_text());base=json.loads(contract.read_text());c=pd.read_csv(costs,index_col=0);plants=pd.read_csv(stock['asset_source'])
 expected=pd.date_range('2013-01-01','2013-12-31 21:00',freq='3h')
 if not n.snapshots.equals(expected) or not (n.snapshot_weightings.to_numpy()==3).all():raise ValueError('Hydro source must cover 2013 full year at3h')
 if n.meta.get('snapshots',{}).get('start')!='2013-01-01':raise ValueError('Source weather year not traced')
 groups=collections.defaultdict(list);pending=[];rows=[]
 for u in stock['unit_evidence']['records']:
  if u['Technology']!='Hydro' or u['SurvivalStatus']!='SURVIVES_2050':continue
  sub=str(plants.iloc[int(u['ParentAssetID'].split(':')[1])].Technology);m=base['mapping'].get(str(u['OriginalMappedBus']),{})
  if m.get('ApprovalStatus')!='HUMAN_ACCEPTED' or m.get('Country')!=u['Country'] or m.get('OriginalPartition')!=m.get('NodePartition'):raise ValueError('Unqualified hydro mapping')
  groups[(m['Node'],sub,u['Country'],m['OriginalPartition'])].append(u)
 source=f'{reference} SHA256={sha(reference)}; INPUT ATTRIBUTES ONLY; original source code={n.meta.get("git_commit")}'
 for (node,sub,country,partition),members in sorted(groups.items()):
  carrier={'Reservoir':'hydro','Run-Of-River':'ror','Pumped Storage':'PHS'}.get(sub)
  typ='Generator' if carrier=='ror' else 'StorageUnit';table=n.df(typ);ref=table[table.carrier.eq(carrier)&table.bus.eq(node)]
  cap=sum(float(u['RetainedCapacity2050']) for u in members);ident=f'{sha(reference)}:{typ}:{node}:{carrier}'
  row=dict(ResourceIdentity=ident,Country=country,Node=node,OriginalPartition=partition,HydroSubtype=sub,SurvivingCapacityMW=cap,SourceUnitIDs=[u['AssetID'] for u in members],Source=source,SourceYear=2013,TargetYear=2050,SourceBasin='Original individual basin IDs unavailable; accepted existing100-node resource group, not an inferred cascade model',DecisionReference=d['DecisionReference'],Status='PENDING')
  reason=None
  if len(ref)!=1:reason='NO_UNIQUE_SAME_NODE_INPUT_RESOURCE_GROUP; no cross-node or cross-partition fallback'
  elif n.buses.at[node,'country']!=country or bool(ref.iloc[0].p_nom_extendable):reason='Reference input ownership or fixed-stock boundary differs'
  if reason:
   row['Reason']=reason;rows.append(row)
   for u in members:base['performance'][u['AssetID']]=dict(ApprovalStatus='PENDING',HydroSubtype=sub,PendingReason=reason);pending.append(dict(AssetID=u['AssetID'],CapacityMW=u['RetainedCapacity2050'],Reason=reason))
   continue
  name=ref.index[0];z=ref.iloc[0];sourcecap=float(z.p_nom)
  if sourcecap<=0 or not math.isfinite(sourcecap):raise ValueError('Unqualified reference INPUT capacity')
  eff=float(z.efficiency if typ=='Generator' else z.efficiency_dispatch)
  if not 0<eff<=1:raise ValueError('Hydro efficiency invalid')
  cr=c.loc[carrier]
  p=dict(ApprovalStatus='SOURCE_QUALIFIED_ENGINEERING_PROXY',AuthorizationReference=d['DecisionReference'],Source=source+'; '+str(costs)+' SHA256='+sha(costs),PerformanceBasis='SOURCE_TECHNOLOGY_ENGINEERING_PROXY',CostBasis='EXISTING_NO_NEW_CAPEX',ComponentType=typ,Carrier=carrier+' existing',Efficiency=eff,FixedOM_EUR_per_MW_e_year=float(cr.investment*cr.FOM/100),VariableOM_EUR_per_MWh_e=float(cr.VOM),ResourceGroup='EXISTING_ONLY_NO_NEW_CANDIDATE',ExistingOnlyEvidence='Frozen research new-build layer contains no hydro/ror/PHS candidate; no copied optimisation quantity',Profiles={},HydroSubtype=sub,HydroResourceIdentity=ident,SourceGroupCapacityMW=sourcecap,AdmittedGroupCapacityMW=cap,ParameterYear=2030)
  if p['FixedOM_EUR_per_MW_e_year']<=0:raise ValueError('Missing hydro FOM qualification')
  row.update(SourceComponent=name,SourceInputCapacityMW=sourcecap,OriginalAssetCoverage='Fixed '+carrier+' input aggregate at '+node+'; MW is coverage evidence only, not inherited stock; new surviving source IDs listed separately',CapacityDifferenceMW=cap-sourcecap,SourceProfileHash=None)
  if carrier=='ror':
   values=n.generators_t.p_max_pu[name]
   if not np.isfinite(values).all() or (values<0).any() or (values>1+1e-12).any():raise ValueError('Invalid normalised hydro availability')
   p['Profiles']['p_max_pu']=dict(ComponentType=typ,Component=name,Multiplier=sourcecap/cap,ClipUpper=1.,Aggregation='CAPACITY_WEIGHTED_NORMALISED',ResourceIdentity=ident,Source=source)
   original=values.to_numpy()*sourcecap;admitted=np.minimum(original,cap)
   row.update(Unit='dimensionless p_max_pu; derived fixed availability envelope MW',EnergyBoundary='Original input p_nom * original p_max_pu is a fixed power-availability envelope; clamp to surviving turbine MW; no inferred additional natural inflow',AllocationMethod='All members share the adjusted normalised group curve; capacity-weighted aggregation; group available MW never exceeds original envelope',OriginalAnnualEnvelopeMWh=float((values*sourcecap*n.snapshot_weightings.generators).sum()),AdmittedAnnualEnvelopeMWh=float(np.sum(admitted*n.snapshot_weightings.generators.to_numpy())),SourceProfileHash=hashlib.sha256(values.to_numpy().tobytes()).hexdigest())
  else:
   p.update(EfficiencyStore=float(z.efficiency_store),CyclicStateOfCharge=True,StaticOperatingInputs={'p_min_pu':-1. if carrier=='PHS' else 0.,'p_max_pu':1.},StorageInitialMWh=0.)
   if not 0<=p['EfficiencyStore']<=1:raise ValueError('Invalid storage input efficiency')
   if carrier=='PHS':
    # Prioritise a compatible raw energy record; never interpret missing/0 as real capacity.
    raw=plants.iloc[sorted({int(u['ParentAssetID'].split(':')[1]) for u in members})]
    duration=raw.Duration;energy=raw.StorageCapacity_MWh
    true_energy=bool(energy.notna().all() and (energy>0).all() and math.isclose(float(raw.Capacity.sum()),cap,rel_tol=1e-10))
    emax=float(energy.sum()) if true_energy else cap*d['PHSMaxHours']
    p.update(MaxHours=emax/cap,StorageEnergyBasis='SOURCE_RAW_ENERGY' if true_energy else 'ASSEMBLY_V1_PHS_6H_DURATION_PROXY',NaturalInflowMW=0.)
    if not math.isclose(p['EfficiencyStore']*eff,float(cr.efficiency),rel_tol=1e-12):raise ValueError('PHS roundtrip efficiency already split or conflicting')
    row.update(Unit='MW/MWh',EnergyBoundary='Closed annual cycle; e_initial input0; no natural inflow; losses applied once per charging/discharging direction',AllocationMethod='Sum admitted MW; real compatible MWh first, otherwise explicit6h proxy',MaxHours=p['MaxHours'],EnergyCapacityMWh=emax,DurationMethod=p['StorageEnergyBasis'],EfficiencyStore=p['EfficiencyStore'],EfficiencyDispatch=eff,RoundTripEfficiency=p['EfficiencyStore']*eff,SensitivityRequired=True)
   else:
    values=n.storage_units_t.inflow[name]
    if not np.isfinite(values).all() or (values<0).any():raise ValueError('Invalid absolute hydro inflow')
    # Reservoir energy is independently traced to its fixed input group. This
    # does NOT use the PHS6h decision or scale natural resource with new MW.
    sourcehours=float(z.max_hours);emax=sourcecap*sourcehours
    if sourcehours<=0 or not math.isfinite(emax):raise ValueError('Reservoir energy input unqualified')
    p.update(MaxHours=emax/cap,StorageEnergyBasis='FROZEN_RESERVOIR_GROUP_INPUT_E_MAX',SourceReservoirMaxHours=sourcehours)
    p['Profiles']['inflow']=dict(ComponentType=typ,Component=name,Multiplier=1.,Aggregation='SHARED_GROUP_ONCE',ResourceIdentity=ident,Source=source)
    row.update(Unit='MW inflow to internal storage; weighted integral MWh',EnergyBoundary='Reference group absolute inflow ONCE and reference group E_max unchanged; no scaling with admitted MW',AllocationMethod='One shared resource component at the same accepted node; no unit-level copied inflow',OriginalAnnualEnvelopeMWh=float((values*n.snapshot_weightings.stores).sum()),AdmittedAnnualEnvelopeMWh=float((values*n.snapshot_weightings.stores).sum()),SourceProfileHash=hashlib.sha256(values.to_numpy().tobytes()).hexdigest(),EnergyCapacityMWh=emax,MaxHours=p['MaxHours'],SourceReservoirMaxHours=sourcehours,ReservoirDurationSource='Reference INPUT max_hours; source metadata hydro_max_hours/default independently traced, not the current PHS duration approval',EfficiencyStore=p['EfficiencyStore'],EfficiencyDispatch=eff)
  row.update(Status='SOURCE_QUALIFIED_GROUP_PROXY',Limitation='Spatial source-to-node proxy, frozen source coverage and historic normalisation; not measured unit hydrology, not a complete cascade model')
  rows.append(row)
  for u in members:base['performance'][u['AssetID']]=p.copy()
 base['hydro_group_qualification']=dict(DecisionReference=d['DecisionReference'],source_reference_sha256=sha(reference),groups=rows,pending=pending)
 save(output,base);save(report,dict(groups=rows,pending=pending,inputs={str(x):sha(x) for x in [reference,costs,survival,contract,decisions]},source_hydro_metadata=n.meta.get('renewable',{}).get('hydro'),source_code=n.meta.get('git_commit'),solver_runs=0))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
 for arg in ['reference','costs','survival','contract','decisions','output','report']:p.add_argument('--'+arg,type=Path,required=True)
 prepare(**vars(p.parse_args()))
