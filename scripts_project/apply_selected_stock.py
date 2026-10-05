"""Reproducible selected-stock build from frozen unit, cohort and resource inputs."""
from pathlib import Path
from collections import Counter
import argparse,copy,json,hashlib,math,ast
import pandas as pd,pypsa
from selected_closure import require_decision,reallocate_hydro,DECISION,retirement_upper_bound,qualify_cohort_identity
from asset_survival import select_asset

def read(p):return json.loads(Path(p).read_text())
def save(p,x):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def prepare(repo,reference,survival,contract,decisions,cohort_evidence,output_stock,output_contract,output_report):
    d=read(decisions);require_decision(d);stock=read(survival);base=read(contract);n=pypsa.Network(reference)
    c,hydro=reallocate_hydro(base,n,d);evidence=read(cohort_evidence);plants=pd.read_csv(stock['asset_source']);life=read(repo/'research_inputs/asset_survival/lifetime_decisions.json')['technologies']
    if evidence['source_powerplants_sha256']!=sha(stock['asset_source']):raise ValueError('Frozen plant identity changed')
    if evidence['gpd_zip_sha256']!=sha(evidence['gpd_zip']):raise ValueError('Frozen GPD identity changed')
    if evidence['gem_identity_sha256']!=sha(repo/evidence['gem_identity_file']):raise ValueError('GEM identity review changed')
    for entry in evidence['records']:
        for proof in entry.get('ResidualEvidence',[]):
            if sha(repo/proof['File'])!=proof['SHA256']:raise ValueError('Residual identity source hash changed')
    bounds=[];seen={u['AssetID'] for u in stock['unit_evidence']['records']}
    snapshots={'Global-Solar-Power-Tracker-February-2025.xlsx':2025,'Global-Wind-Power-Tracker-February-2025.xlsx':2025,'Geothermal-Power-Tracker-March-2025-Final.xlsx':2025,'Global-Oil-and-Gas-Plant-Tracker-GOGPT-August-2025.xlsx':2025}
    for i,u in enumerate(stock['unit_evidence']['records']):
        if u['SurvivalStatus']!='UNRESOLVED_COMMISSIONING':continue
        file=u['Source'];obs=snapshots.get(file)
        row=dict(AssetID=u['AssetID'],Country=u['Country'],Technology=u['Technology'],CapacityMW=u['OriginalCapacity'],CommissioningYear=None,OperatingByYear=obs,Lifetime=u['Lifetime'],Source=file,SourceVersion=u['SourceVersion'],SourceRow=u['SourceRow'],EvidenceMeaning='Published dated tracker snapshot, original unit status operating; not file download date' if obs else 'GBPT-V3 filename does not establish an observation year',Status='UNRESOLVED_COMMISSIONING',RetirementUpperBound=None)
        if obs:
            candidate=dict(u,OperatingObservation=dict(Year=obs,EvidenceKind='DATED_OPERATING_SOURCE_SNAPSHOT',Verified=True,Source=file+' SHA256='+u['SourceVersion']+' '+u['SourceRow']+' status=operating'))
            bound=retirement_upper_bound(candidate)
            if bound:stock['unit_evidence']['records'][i]=bound;row.update(Status=bound['SurvivalStatus'],RetirementUpperBound=bound['RetirementUpperBound'])
        bounds.append(row)
    review=[]
    for entry in evidence['records']:
        r=entry['raw'];parent=entry['ParentAssetID'];tech=entry['Technology'];pid=r['gppd_idnr'];source_id='GPD:'+pid
        if source_id in seen:raise ValueError('Duplicate source ID');
        seen.add(source_id);p=plants.iloc[int(parent.split(':')[1])];decl=life.get(tech,{})
        if pid not in ast.literal_eval(p.projectID).get('GPD',[]):raise ValueError('GPD parent ownership differs')
        year=r['commissioning_year'];u=dict(AssetID=source_id,RawUnitID=pid,ParentAssetID=parent,Country=entry['Country'],Technology=tech,OriginalCapacity=r['capacity_mw'],CommissioningYear=year,RetirementYear=None,CommissioningEvidenceVerified=False,RetirementEvidenceVerified=False,AssetClass='OBSERVED_EXISTING',Lifetime=decl.get('Lifetime'),LifetimeAccepted=decl.get('ApprovalStatus')=='HUMAN_ACCEPTED',LifetimeSource=decl.get('Source'),LifetimeDecisionReference=decl.get('DecisionReference'),OriginalMappedBus=str(p.bus),Source=evidence['gpd_zip'],SourceVersion=evidence['gpd_zip_sha256'],SourceRow='global_power_plant_database.csv::'+pid,CapacityReconciliation='MATCHED_PARENT',ParentCapacity=float(p.Capacity),ParentCapacityDifference=0.,AgeBasis='REPORTED_PLANT_COHORT_POSSIBLY_CAPACITY_WEIGHTED',CohortMethod='ASSEMBLY_V1_REPORTED_PLANT_COHORT_PROXY',CohortDecisionReference=DECISION+'#D',ReportedPlantYearSource=evidence['gpd_zip']+'::'+pid,ReportedPlantYear=year,IdentityReview=entry['IdentityStatus'],CostTreatment='No new CAPEX; accepted existing technology engineering O&M proxy',ResourceLimitTreatment='Qualification required separately')
        selected=select_asset(u);conditional=selected['RetainedCapacity2050'];reason=entry['IdentityStatus']
        # A cohort screening result cannot override source duplicate or technology/resource checks.
        if selected['SurvivalStatus']=='SURVIVES_2050':
            if reason!='DISJOINT_FROZEN_SOURCE_SELECTION':selected=qualify_cohort_identity(selected,reason)
            elif tech=='Hydro':c['performance'][source_id]=dict(ApprovalStatus='PENDING',PendingReason='GPD hydro cohort needs its own source group/resource assignment; approved seven pools cover GEM units only')
            elif entry.get('PerformanceCompatible') is not True:c['performance'][source_id]=dict(ApprovalStatus='PENDING',PendingReason='Original primary fuel does not prove accepted existing conversion technology')
        stock['unit_evidence']['records'].append(selected)
        review.append(dict(AssetID=source_id,ParentAssetID=parent,Country=entry['Country'],Technology=tech,PlantName=r['name'],CapacityMW=r['capacity_mw'],ReportedPlantYear=year,YearMeaning=u['AgeBasis'],Lifetime=u['Lifetime'],ConditionalSurvivingMW=conditional,FinalSelectionStatus=selected['SurvivalStatus'],ActualIntegratedMW=0.,IdentityStatus=reason,RelatedGEMIDs=entry.get('RelatedGEMIDs',[]),Evidence=entry['Evidence'],Source=r['source'],SourceURL=r['url'],DecisionReference=DECISION+'#D',SourceVersion=evidence['gpd_zip_sha256'],PendingReason=c['performance'].get(source_id,{}).get('PendingReason') if selected['SurvivalStatus']=='SURVIVES_2050' else reason))
        if year is None:bounds.append(dict(AssetID=source_id,Country=entry['Country'],Technology=tech,CapacityMW=r['capacity_mw'],CommissioningYear=None,OperatingByYear=None,Lifetime=decl.get('Lifetime'),Source=evidence['gpd_zip'],SourceVersion=evidence['gpd_zip_sha256'],SourceRow=pid,Status='OBSERVATION_YEAR_NOT_QUALIFIED',EvidenceMeaning='year_of_capacity_data absent; publication/download date is not an operating observation',RetirementUpperBound=None))
    recovered={r['ParentAssetID'] for r in evidence['records']}
    for p in stock['unit_evidence']['parent_reconciliation']:
        if p['ParentAssetID'] in recovered:
            rs=[r for r in review if r['ParentAssetID']==p['ParentAssetID']];total=sum(r['CapacityMW'] for r in rs)
            if not math.isclose(total,p['ParentCapacity'],rel_tol=1e-6,abs_tol=.01):raise ValueError('Recovered GPD parent capacity changed')
            p.update(SourceLinkRecovered=True,SourceLinkStatus='RECOVERED_GPD_PARENT_CAPACITY_RECONCILED',CapacityReconciled=True,SourceUnitCount=len(rs),KnownSourceUnitCapacity=total,UnmatchedPositiveParentCapacity=0.,SourceIDs=[r['AssetID'] for r in rs],SourceMeaning='GPD plant cohort records, not fabricated unit decomposition',SignedCapacityDifference=p['ParentCapacity']-total,OriginalSourceStatus=p['OriginalStatus'],KnownReportedPlantYearCapacity=sum(r['CapacityMW'] for r in rs if r['ReportedPlantYear'] is not None),MissingReportedPlantYearCapacity=sum(r['CapacityMW'] for r in rs if r['ReportedPlantYear'] is None),ConditionalSurvivorsMW=sum(r['ConditionalSurvivingMW'] or 0 for r in rs))
    stock['unit_evidence']['status_counts']=dict(Counter(u['SurvivalStatus'] for u in stock['unit_evidence']['records']))
    stock['selected_closure_decision']=DECISION;stock['selected_closure_inputs']={str(p):sha(p) for p in [survival,contract,decisions,cohort_evidence,reference]}
    save(output_stock,stock);save(output_contract,c)
    save(output_report,dict(hydro=hydro,gpd=review,retirement_bounds=bounds,inputs=stock['selected_closure_inputs'],solver_runs=0,fullsc_network_complete=False,decision=DECISION))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ['repo','reference','survival','contract','decisions','cohort-evidence','output-stock','output-contract','output-report']:p.add_argument('--'+k,type=Path,required=True)
    prepare(**vars(p.parse_args()))
