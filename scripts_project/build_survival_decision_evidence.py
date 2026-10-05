"""Bounded, reproducible decision evidence; outputs candidates, never live inputs."""
from pathlib import Path
from decimal import Decimal as D
import json,csv,hashlib,argparse,collections
import pandas as pd
from unit_asset_survival import reconcile_units,lifetime_decision_table
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def derive(repo,source_evidence,mapping,plants,costs,output):
    root=repo/'research_inputs/assembly_v1/sources';g=repo/'research/04_model_assembly/gate4';raw=read(source_evidence)
    units=raw.get('unit_evidence',reconcile_units(raw['records']));parents=units['parent_reconciliation'];records=units['records']
    source='configs/powerplantmatching_config.yaml SHA256='+sha(repo/'configs/powerplantmatching_config.yaml')+'; fuel_to_lifetime:419-432'
    life=lifetime_decision_table(units,source)
    for r in life:
        if r['AffectedExistingCapacity']==0:r['DecisionRequired']='NO_OBSERVED_EXISTING_STOCK_AFFECTED; planned or unresolved status is separate from lifetime approval'
    p=pd.read_csv(plants);c=pd.read_csv(costs,index_col=0);cost=[]
    examples={'Biogas':'biogas','CCGT':'CCGT','Geothermal':'geothermal','Hard Coal':'coal','Hydro':'hydro','Lignite':'lignite','Nuclear':'nuclear','Oil':'oil','Solar':'solar-utility','Solid Biomass':'biomass','Waste':'waste CHP','Wind':'onwind'}
    for r in life:
        t=r['Technology'];rows=p[p.Fueltype==t];eff=pd.to_numeric(rows.Efficiency,errors='coerce').dropna();candidate=examples.get(t)
        vals=c.loc[candidate] if candidate in c.index else {}
        cost.append(dict(Technology=t,ObservedSourceCapacityMW=r['AffectedExistingCapacity'],OriginalEfficiencyAvailableRows=len(eff),OriginalEfficiencyRange=(str(eff.min())+'..'+str(eff.max())) if len(eff) else None,OriginalEfficiencySource=str(plants)+' SHA256='+sha(plants),NewCAPEXChargedToExisting=0,ExistingFixedOM='PENDING_SOURCE_QUALIFICATION; never blanket zero',ExistingVariableOM='PENDING_SOURCE_QUALIFICATION; charged per electric output',ExistingEfficiency='Source existing equipment only; no automatic2050 upgrade',NewBuild2050ContextTechnology=candidate,NewBuild2050FOM_EUR_MW_year=float(vals['investment']*vals['FOM']/100) if len(vals) else None,NewBuild2050AnnualCapitalPlusFOM=float(vals['fixed']) if len(vals) else None,NewBuild2050VOM=float(vals['VOM']) if len(vals) else None,ContextSource=str(costs)+' SHA256='+sha(costs),ContextMeaning='Illustrative frozen2050 NEW technology row only; not an accepted historical equipment cost mapping',Implementation='fixed capacity; capital_cost=0; independent audited annual FOM objective term; VOM on dispatch; input-basis conversion for thermal Links',ApprovalStatus='PENDING'))
    old=read(root/'UNSD_2019_SOURCE_CAPSULE.json')['records'];obs=read(root/'unsd_targeted/observations.json');conv=read(root/'FROZEN_UPSTREAM_CONVERSIONS.json')['constants']['fuels_conv_toTWh']
    names={'MO':('4652','Motor Gasoline'),'DL':('4670','Gas Oil/ Diesel Oil'),'AL':('5210','Biogasoline'),'BD':('5220','Biodiesel'),'ZG':('5212','Of which: biogasoline'),'ZD':('5222','Of which: biodiesel')}
    new={k:next(r for r in obs if r['Country']=='TH' and r['TRANSACTION']=='1221' and r['COMMODITY']==code) for k,(code,_) in names.items()}
    assert len({r['SourceSHA256'] for r in new.values()})==1
    th=[]
    for k,(code,name) in names.items():
        prior=[r for r in old if r['Country']=='TH' and r['Commodity'].lower()==name.lower() and r['Transaction']=='Consumption in road']
        if len(prior)>1:raise ValueError('Ambiguous prior Thailand source')
        z=new[k];before=prior[0] if prior else {}
        th.append(dict(Record=k,Commodity=name,Country='TH',Year=2019,Transaction='1221 Road',OldRawQuantity=before.get('Quantity'),NewRawQuantity=z['Quantity'],RawUnit='Metric tons, thousand',OldFootnote=before.get('Quantity Footnotes'),NewObservationStatus=z['OBS_STATUS'],OldSourceSHA256=before.get('SourceSHA256'),OldSourceRow=before.get('PhysicalLine'),NewSourceFile=z['SourceFile'],NewSourceSHA256=z['SourceSHA256'],QueryVersion=z['DSD']['structureID'],NewReportedConversionFactor=z['CONVERSION_FACTOR'],FrozenProjectFactorTWhPerKton=conv.get(name),Candidate2019MWh=None,Candidate2050MWh=None,Formula=None,Status='PENDING_LOCAL_VINTAGE_DECISION',Posting=False))
    growth=D('374.9')/D('145.2');subtotal={}
    for parent,bio,memo in [('MO','AL','ZG'),('DL','BD','ZD')]:
        fossil=D(new[parent]['Quantity'])-D(new[memo]['Quantity']);bioqty=D(new[bio]['Quantity'])
        assert fossil>=0 and D(new[memo]['Quantity'])<=bioqty
        for label,q,commodity in [(parent+'_fossil',fossil,names[parent][1]),(bio+'_total',bioqty,names[bio][1])]:
            base=q*D(str(conv[commodity]))*D(1000000);subtotal[label]=base
            th.append(dict(Record=label,Commodity=commodity,Country='TH',Year=2019,Transaction='1221 Road',OldRawQuantity=None,NewRawQuantity=str(q),RawUnit='Metric tons, thousand',OldFootnote=None,NewObservationStatus='A',OldSourceSHA256=None,OldSourceRow=None,NewSourceFile=new[parent]['SourceFile'],NewSourceSHA256=new[parent]['SourceSHA256'],QueryVersion=new[parent]['DSD']['structureID'],NewReportedConversionFactor=new[parent if label.endswith('fossil') else bio]['CONVERSION_FACTOR'],FrozenProjectFactorTWhPerKton=conv[commodity],Candidate2019MWh=str(base),Candidate2050MWh=str(base*growth),Formula=('('+parent+'-'+memo+')' if label.endswith('fossil') else bio)+' * frozen commodity factor *1e6; target *(374.9/145.2)',Status='CONDITIONAL_LOCAL_REPLACEMENT_NOT_ACCEPTED',Posting=False))
    reconstruction=read(root/'BASE_RECONSTRUCTION.json');selected=reconstruction['selected_rows'];th_old=[r for r in selected if r['Country']=='TH' and r['Account']=='RoadResidualFuel' and r['Commodity'].lower() in {v[1].lower() for v in names.values()}]
    thsum=dict(old_unreconciled_display_mwh=str(sum(D(r['MWh']) for r in th_old)),new_consistent_candidate_mwh=str(sum(subtotal.values())),candidate2050_mwh=str(sum(subtotal.values())*growth),delta_vs_unreconciled_display_mwh=str(sum(subtotal.values())-sum(D(r['MWh']) for r in th_old)),meaning='Affected MO/DL/AL/BD bundle only; old display was unresolved, not an accepted baseline. ZG/ZD are memo and never extra demand. Project frozen NCV factors retained; newAPI reported factors are recorded, not silently adopted.',posting=False)
    bio=[]
    for commodity in sorted({r['Commodity'] for r in selected if r['Carrier']=='biomass'}):
        rows=[r for r in selected if r['Commodity']==commodity];matches={'Biodiesel':['biodiesel crops'],'Biogases':['biogas','biogas manure'],'Charcoal':['solid biomass','biomass'],'Fuelwood':['solid biomass','biomass'],'Bagasse':['solid biomass','biomass'],'Animal waste':['biogas manure','biomass'],'Biogasoline':[]}[commodity]
        available=[dict(technology=k,fuel_field=float(c.at[k,'fuel']),co2_intensity_field=float(c.at[k,'CO2 intensity'])) for k in matches if k in c.index]
        bio.append(dict(Commodity=commodity,OriginalRawUnits=';'.join(sorted({r['RawUnit'] for r in rows})),ProjectEnergyBasis=';'.join(sorted({r['EnergyBasis'] for r in rows})),FrozenNCVFactorTWhPerKton=conv.get(commodity),NCVSource='FROZEN_UPSTREAM_CONVERSIONS.json SHA256='+sha(root/'FROZEN_UPSTREAM_CONVERSIONS.json'),AvailableCostContext=json.dumps(available),CostSource=str(costs)+' SHA256='+sha(costs),CostMeaning='Database technology fuel fields / crop-feedstock context are candidates, not verified delivered-price matches',PhysicalCO2Factor=None,PhysicalCO2Reason='Prepared net CO2=0 is not a verified combustion factor; no automatic lifecycle uptake credit',CarbonOrigin='Biogenic named commodity; physical composition/origin evidence pending, no assumed credit',Pooling='Exclusive commodity-specific fixed-obligation resource; no solid/liquid pooling',DecisionRequired='Compatible delivered fuel cost and physical CO2/origin basis, or explicit reviewed baseline method',ApprovalStatus='PENDING'))
    decisions=list(csv.DictReader((g/'REMAINING_ACCOUNT_DECISIONS.csv').open(encoding='utf-8-sig')));grouped=[]
    for label in ['RailNonElectric','TransportNEC','OtherNEC']:
        z=[r for r in decisions if ('Rail' in r['AccountGroup'] if label=='RailNonElectric' else 'transport' in r['SourceUse'].lower() if label=='TransportNEC' else 'other' in r['SourceUse'].lower()) and (label=='RailNonElectric' or 'Rail' not in r['AccountGroup'])]
        values=collections.defaultdict(D)
        for r in z:values[r['Country']]+=D(r['BaseValue'])
        grouped.append(dict(AccountGroup=label,AccountRows=len(z),Countries=';'.join(sorted(values)),CountryBaseMWh=json.dumps({k:str(v) for k,v in values.items()}),BaseValueMWh=str(sum(values.values())),SourceUse=';'.join(sorted({r['SourceUse'] for r in z})),ExistingDecisionCoverage='No approved2050 numerical rule for this source use; road method does not cover it',ProposedMethod='Candidate constant2019 only; not applied',FuelOverlap='PH rail oil/biodiesel overlap still unresolved' if label=='RailNonElectric' else 'Do not infer national blend allocation into NEC; preserve source-commodity identity; additional overlap evidence may be needed',ApprovalStatus='PENDING',SourceRows=';'.join(r['SourceRows'] for r in z)))
    assert sum(r['AccountRows'] for r in grouped)==20
    coverage=[r for r in csv.DictReader((g/'SOURCE_COVERAGE_REGISTER.csv').open(encoding='utf-8-sig')) if r['Status']=='UNRESOLVED'];assert len(coverage)==33
    for r in coverage:
        r['CurrentDisposition']='PENDING_NO_NEW_EXCLUSION';r['NewEvidenceThisRound']='None; same source family/transaction evidence retained; no repeated queries'
        r['DecisionScope']='Source-use disaggregation/coverage boundary; retained NEC is not a zero proof' if r['Category'].startswith('KNOWN_NEC') else 'Specific source family/transaction missing in cached scope; absence is not zero'
    mapping_data=read(mapping);mapping_counts=dict(collections.Counter(r['Status'] for r in mapping_data['rows']))
    summary=dict(recovered_229=sum(p['OriginalStatus']=='UNRESOLVED_COMMISSIONING' and p['CapacityReconciled'] and p['AllUnitYearsKnown'] for p in parents),recovered_capacity_mw=sum(p['ParentCapacity'] for p in parents if p['OriginalStatus']=='UNRESOLVED_COMMISSIONING' and p['CapacityReconciled'] and p['AllUnitYearsKnown']),confirmed_existing_missing_commissioning_mw=sum(r['OriginalCapacity'] or 0 for r in records if r['AssetClass']=='OBSERVED_EXISTING' and r['CommissioningYear'] is None),all_status_missing_year_mw=sum(p['MissingCommissioningSourceCapacity'] for p in parents),unmatched_or_capacity_discrepant_parent_mw=sum(p['ParentCapacity'] for p in parents if not p['CapacityReconciled']),lifetime_table_technologies=len(life),lifetime_technologies_with_observed_stock=sum(r['AffectedExistingCapacity']>0 for r in life),mapping_status_counts=mapping_counts,raw_ids_unique=True,candidate_lifetimes_entered_production=False,thailand=thsum,remaining_fuel_queries=list(csv.DictReader((g/'UNSD_MISSING_MEMO_REQUESTS.csv').open(encoding='utf-8-sig'))),source_coverage_counts=dict(collections.Counter(r['Category'] for r in coverage)))
    tables={'UNIT_LEVEL_SURVIVAL_RECONCILIATION.csv':records,'UNIT_PARENT_CAPACITY_RECONCILIATION.csv':parents,'ASSET_LIFETIME_DECISION_TABLE.csv':life,'EXISTING_ASSET_COST_TREATMENT.csv':cost,'THAILAND_LOCAL_VINTAGE_UPDATE_CANDIDATE.csv':th,'BIOFUEL_COMMODITY_PARAMETER_REVIEW.csv':bio,'REMAINING_ACCOUNT_GROUP_DECISIONS.csv':grouped,'REMAINING_SOURCE_COVERAGE_REVIEW.csv':coverage}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(dict(summary=summary,tables=tables,source_hashes={str(p):sha(p) for p in [source_evidence,mapping,plants,costs]}),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    for name in ['source-evidence','mapping','plants','costs','output']:p.add_argument('--'+name,type=Path,required=True)
    derive(**vars(p.parse_args()))
