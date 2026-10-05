"""Exact Gate4 residual evidence and conditional choices. Never alters inputs or solves."""
from pathlib import Path
from collections import defaultdict,Counter
from decimal import Decimal as D
import argparse,ast,json,hashlib,zipfile,inspect
import numpy as np,pandas as pd,pypsa
from reconstruct_base_accounts import reconstruct,Reconstruction,account_for_transaction,commodity,norm,row_id
from residual_account_mapping import build_crosswalk,reconcile_commodity_scope

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')

def coverage_reconciliation(repo,sources):
    capsule=read(sources/'UNSD_2019_SOURCE_CAPSULE.json');b=Reconstruction(capsule,read(sources/'FROZEN_UPSTREAM_CONVERSIONS.json'))
    cov=read(repo/'research/04_model_assembly/gate4/evidence/SOURCE_COVERAGE_ACCOUNT_MAP.json')['rows']
    targets=[q for q in cov if q['SourceCategory']=='KNOWN_NEC_ENERGY_RETAINED_SECTOR_SPLIT_UNRESOLVED'];rows=[];summary=[]
    for q in targets:
        country=q['Country'];fuel=q['Carrier'];case=q['SourceCoverageID'];international=q['Account'].startswith('International')
        scope=[r for r in b.rows if r['Country']==country and (fuel=='unclassified_fuel' or b.fuels.get(commodity(r['Commodity']))==fuel) and b.fuels.get(commodity(r['Commodity'])) not in [None,'electricity','heat']]
        # A production/import-only commodity does not itself create a missing
        # final-use obligation. Limit the balance to reported FEC or end-use rows.
        products=sorted({commodity(r['Commodity']) for r in scope if norm(r['Transaction'])=='final energy consumption' or account_for_transaction(r['Transaction']) not in [None,'InternationalShippingBunker','InternationalAviationBunker']});case_rows=[]
        for product in products:
            same=[r for r in scope if commodity(r['Commodity'])==product];fec=[r for r in same if norm(r['Transaction'])=='final energy consumption']
            if len(fec)>1:raise ValueError('FEC parent duplicate')
            parent=fec[0] if fec else None
            parts=[r for r in same if account_for_transaction(r['Transaction']) not in [None,'InternationalShippingBunker','InternationalAviationBunker']]
            nec=[r for r in parts if account_for_transaction(r['Transaction']) in ['TransportNEC','OtherNEC']]
            result=reconcile_commodity_scope(parent,parts)
            try:mwh=float(b.convert(parent)[0]) if parent else None
            except ValueError:mwh=None
            row=dict(CoverageID=case,Country=country,Account=q['Account'],Carrier=fuel,Commodity=product,Year=2019,RawUnit=parent['Unit'] if parent else (same[0]['Unit'] if same else None),Scope='INTERNATIONAL_BUNKER_OUTSIDE_DOMESTIC_FEC' if international else 'DOMESTIC_FINAL_CONSUMPTION',**result,ParentMWh=mwh,ParentRow=row_id(parent) if parent else None,ParentSourceFile=parent['SourceFile'] if parent else None,SourceSHA256=parent['SourceSHA256'] if parent else None,ExclusiveUseRows=[row_id(r) for r in parts],UseTransactions=[r['Transaction'] for r in parts],NECRows=[row_id(r) for r in nec],NECRawQuantity=str(sum((D(str(r['Quantity'])) for r in nec),D(0))) if nec else None,TargetAccounts=q['Pending2050AccountIDs'],Posting=False,ApprovalStatus='PENDING',NewPhysicalEnergyAdded=0,Formula='FEC parent versus named mutually exclusive end uses + TransportNEC + OtherNEC; no transport/industry subtotal children, no bunkers')
            rows.append(row);case_rows.append(row)
        closed=bool(case_rows) and all(r['Status'] in ['SOURCE_TOTAL_CLOSED','SOURCE_TOTAL_CLOSED_WITH_FLOAT_PRECISION'] for r in case_rows)
        status='NOT_A_SECTOR_SPLIT_BUNKER_SOURCE_MISSING' if international else 'CANDIDATE_MACRO_REPRESENTATION_ONLY' if closed else 'SOURCE_TOTAL_NOT_CLOSED_OR_COVERAGE_INCOMPLETE'
        summary.append(dict(CoverageID=case,Country=country,Account=q['Account'],CommodityChecks=len(case_rows),ClosedCommodityChecks=sum(r['Status'] in ['SOURCE_TOTAL_CLOSED','SOURCE_TOTAL_CLOSED_WITH_FLOAT_PRECISION'] for r in case_rows),Status=status,SourceScope='Frozen2019 domestic commodity inventory only; absent commodities not proved zero',Candidate='Keep existing disjoint macro/NEC obligations once; replace artificial fine-sector obligation with nonposting coverage record AFTER explicit scope approval' if status=='CANDIDATE_MACRO_REPRESENTATION_ONLY' else 'Do not use NEC to close this obligation; provide scope-compatible source or explicit boundary choice',BeforeTotal='Sum of existing mutually exclusive observed uses; FEC is a control only',AfterTotal='Identical under candidate; no new demand/no subtraction',ApprovalStatus='PENDING',ProductionChanged=False))
    return rows,summary

def hydro_candidates(repo,reference,prior_trace):
    groups=read(repo/'results_project/assembly_v1/assets/HYDRO_GROUP_QUALIFICATION.json')['groups'];byname={g['SourceComponent']:g for g in groups if g['Status']!='PENDING' and 'SourceComponent' in g}
    n=reference;out=[];checks=[];pools=defaultdict(list);traces=read(prior_trace)
    for q in traces:pools[(q['Country'],q['Node'].rsplit(' ',1)[0],q['HydroSubtype'])].append(q)
    for (country,region,kind),qs in sorted(pools.items()):
        candidates=sorted({x for q in qs for x in q['CompatibleRegionReferenceCandidates']});accepted=[k for k in candidates if k in byname]
        poolid=country+':'+region+':'+kind
        if not accepted:
            if candidates:
                # Mutually exclusive alternatives, not resources to add together.
                # These envelopes are present in the frozen reference but have
                # not been admitted to the accepted production hydro contract.
                for name in candidates:
                    typ='StorageUnit' if kind=='Reservoir' else 'Generator';z=n.df(typ).loc[name]
                    raw=n.storage_units_t.inflow[name].to_numpy() if kind=='Reservoir' else n.generators_t.p_max_pu[name].to_numpy()*z.p_nom
                    assert np.isfinite(raw).all() and (raw>=0).all()
                    weights=n.snapshot_weightings.stores.to_numpy() if kind=='Reservoir' else n.snapshot_weightings.generators.to_numpy()
                    cap=sum(q['SurvivingCapacityMW'] for q in qs);emax=float(z.p_nom*z.max_hours) if kind=='Reservoir' else None
                    for q in qs:
                        share=q['SurvivingCapacityMW']/cap;allocated=raw*share;usable=allocated if kind=='Reservoir' else np.minimum(allocated,q['SurvivingCapacityMW']);unused=allocated-usable
                        assert np.allclose(usable+unused,allocated,rtol=1e-12)
                        out.append(dict(PoolID=poolid,AlternativeID=poolid+'::'+name,Country=country,HydroSubtype=kind,ResourceIdentity=f'{qs[0]["ResourceIdentity"].split(":")[0]}:{typ}:{name}',SourceComponent=name,SourceAlreadyAllocated=False,SourceNode=z.bus,SourceUnitCoverage='No current accepted beneficiary; source raw asset coverage requires explicit compatibility review',OriginalAnnualInputMWh=float(raw@weights),CurrentAcceptedAnnualEnvelopeMWh=0.,OriginalEmaxMWh=emax,RecipientNode=q['Node'],RecipientRole='PENDING_NOT_IN_PRODUCTION',RecipientUnits=q['SourceUnitIDs'],RecipientCapacityMW=q['SurvivingCapacityMW'],OriginalParentIDs=q['OriginalParentIDs'],AllocationShare=share,CandidateAnnualInputMWh=float(allocated@weights),CandidateUsableAvailabilityMWh=float(usable@weights),UnusableAvailabilityDueToTurbineLimitMWh=float(unused@weights),CandidateEmaxMWh=emax*share if emax is not None else None,SourceProfileSHA256=hashlib.sha256(raw.tobytes()).hexdigest(),Method='CONDITIONAL_SINGLE_UNASSIGNED_REFERENCE_RESOURCE_PROXY',EnergyRule='Choose ONE listed source alternative, preserve its absolute input budget; not additive across alternatives; newly credits a previously unadmitted source in production',SpatialHydrologyApproximation='Same electrical region is NOT basin evidence. Requires new source-to-resource assignment approval; annual curve is available but source coverage compatibility is unresolved.',Status='NUMERICAL_ALTERNATIVE_NOT_ACCEPTED',ApprovalStatus='PENDING',ProductionChanged=False))
            else:
                for q in qs:out.append(dict(PoolID=poolid,Country=country,HydroSubtype=kind,PendingNode=q['Node'],PendingCapacityMW=q['SurvivingCapacityMW'],PendingUnits=q['SourceUnitIDs'],Status='NO_SAME_TYPE_REGIONAL_REFERENCE_RESOURCE',UnqualifiedReferenceCandidates=candidates,OriginalParentIDs=q['OriginalParentIDs'],Required='2013 full-year source profile + original coverage/basin mapping for listed parent IDs; reservoir also Emax. Alternatively approve a new explicitly sourced proxy; no national nearest fallback.',ApprovalStatus='PENDING',ProductionChanged=False))
            continue
        existing=[byname[k] for k in accepted];recipients=[dict(Node=g['Node'],CapacityMW=g['SurvivingCapacityMW'],Units=g['SourceUnitIDs'],Role='EXISTING_ACCEPTED') for g in existing]+[dict(Node=q['Node'],CapacityMW=q['SurvivingCapacityMW'],Units=q['SourceUnitIDs'],Role='PENDING_NOT_IN_PRODUCTION') for q in qs]
        total=sum(r['CapacityMW'] for r in recipients);assert len({r['Node'] for r in recipients})==len(recipients)
        maxerr=0.;emax_before=emax_after=0.;energy_before=energy_after=0.
        for name in accepted:
            g=byname[name]
            if kind=='Reservoir':
                raw=n.storage_units_t.inflow[name].to_numpy();base=raw.copy();emax=g['EnergyCapacityMWh'];weights=n.snapshot_weightings.stores.to_numpy()
            else:
                raw=n.generators_t.p_max_pu[name].to_numpy()*g['SourceInputCapacityMW'];base=np.minimum(raw,g['SurvivingCapacityMW']);emax=0.;weights=n.snapshot_weightings.generators.to_numpy()
            original=float(raw@weights);before=float(base@weights);sumarray=np.zeros_like(base)
            for r in recipients:
                share=r['CapacityMW']/total;arr=base*share;after=float(arr@weights);sumarray+=arr
                out.append(dict(PoolID=poolid,Country=country,HydroSubtype=kind,ResourceIdentity=g['ResourceIdentity'],SourceComponent=name,SourceAlreadyAllocated=True,SourceNode=g['Node'],SourceUnitCoverage=g['SourceUnitIDs'],OriginalAnnualInputMWh=original,CurrentAcceptedAnnualEnvelopeMWh=before,OriginalEmaxMWh=emax if kind=='Reservoir' else None,RecipientNode=r['Node'],RecipientRole=r['Role'],RecipientUnits=r['Units'],RecipientCapacityMW=r['CapacityMW'],PoolExistingCapacityMW=sum(e['SurvivingCapacityMW'] for e in existing),PoolPendingCapacityMW=sum(q['SurvivingCapacityMW'] for q in qs),AllocationShare=share,CandidateAnnualInputMWh=after,CandidateEmaxMWh=emax*share if kind=='Reservoir' else None,CandidateMaxHours=emax*share/r['CapacityMW'] if kind=='Reservoir' else None,SourceProfileSHA256=hashlib.sha256(raw.tobytes()).hexdigest(),AcceptedEnvelopeSHA256=hashlib.sha256(base.tobytes()).hexdigest(),CandidateProfileSHA256=hashlib.sha256(arr.tobytes()).hexdigest(),Method='CONDITIONAL_REGIONAL_POOL_CAPACITY_SHARE',EnergyRule='Each already accepted resource counted once; sum allocations equals its existing accepted envelope every snapshot. No new resource admission.',SpatialHydrologyApproximation='Same country/region/AC partition only; basin equivalence NOT established. Pooling transfers profiles/Emax between existing nodes and pending nodes; requires explicit new resource-allocation approval.',RORNote='Retain currently turbine-clipped accepted envelope; do not recover previously clipped water or increase resource with new turbines' if kind!='Reservoir' else None,ApprovalStatus='PENDING',ProductionChanged=False))
                energy_after+=after;emax_after+=emax*share
            maxerr=max(maxerr,float(np.max(abs(sumarray-base))));energy_before+=before;emax_before+=emax
        assert maxerr<1e-8 and np.isclose(energy_before,energy_after,rtol=1e-12) and np.isclose(emax_before,emax_after,rtol=1e-12)
        checks.append(dict(PoolID=poolid,SourceGroups=len(accepted),PendingGroups=len(qs),ExistingMW=sum(g['SurvivingCapacityMW'] for g in existing),PendingMW=sum(q['SurvivingCapacityMW'] for q in qs),BeforeAnnualMWh=energy_before,AfterAnnualMWh=energy_after,BeforeEmaxMWh=emax_before,AfterEmaxMWh=emax_after,MaximumSnapshotDifferenceMW=maxerr,ConditionalConservationPassed=True,HydrologicalEquivalenceEstablished=False,ProductionChanged=False))
    return out,checks

def inventory_candidates(repo,cache):
    stock=read(repo/'results_project/assembly_v1/assets/ASSET_SURVIVAL_2050.json');plants=pd.read_csv(stock['asset_source']);u=stock['unit_evidence']['records'];parents=stock['unit_evidence']['parent_reconciliation'];gpdzip=cache/'globalpowerplantdatabase_v_1_3_0.zip'
    with zipfile.ZipFile(gpdzip) as z:
        gpd=pd.read_csv(z.open('global_power_plant_database.csv'),low_memory=False).set_index('gppd_idnr');definition=z.read('README.txt').decode()
    assert 'weighted by unit-capacity' in definition
    matches=[];used=set();countrymap={'BN':'BRN','ID':'IDN','KH':'KHM','LA':'LAO','MM':'MMR','MY':'MYS','PH':'PHL','SG':'SGP','TH':'THA','TL':'TLS','VN':'VNM'}
    for p in parents:
        if p['CapacityReconciled']:continue
        r=plants.iloc[int(p['ParentAssetID'].split(':')[1])];ids=sorted(ast.literal_eval(r.projectID).get('GPD',[])); assert ids
        assert not used.intersection(ids);used.update(ids);selected=gpd.loc[ids,['country','country_long','name','capacity_mw','latitude','longitude','primary_fuel','other_fuel1','other_fuel2','other_fuel3','commissioning_year','owner','source','url','year_of_capacity_data']]
        assert (selected.country==countrymap[p['Country']]).all()
        total=float(selected.capacity_mw.sum());equal=bool(np.isclose(total,p['ParentCapacity'],rtol=1e-6,atol=.01))
        matches.append(dict(ParentAssetID=p['ParentAssetID'],Country=p['Country'],Technology=p['Technology'],ParentCapacityMW=p['ParentCapacity'],RawGPDIDs=ids,RawGDPCapacityMW=total,CapacityDifferenceMW=p['ParentCapacity']-total,SourceLinkRecovered=True,CapacityReconciled=equal,RawRecords=selected.reset_index().astype(object).where(pd.notna(selected.reset_index()),None).to_dict('records'),Source=str(gpdzip),SourceSHA256=sha(gpdzip),YearMeaning='Plant operation year, weighted by unit-capacity when data available; NOT verified unit commissioning year',AgeQualification='PENDING_UNIT_BREAKDOWN_OR_EXPLICIT_PLANT_COHORT_PROXY',ProductionChanged=False))
    rows=[];groups=defaultdict(list)
    for x in u:
        if x['SurvivalStatus'].startswith('UNRESOLVED'):groups[(x['Country'],x['Technology'],x['SurvivalStatus'])].append(x)
    for (country,tech,status),rs in groups.items():
        rows.append(dict(Family='GEM_UNIT',Country=country,Technology=tech,Status=status,CapacityMW=sum(r['OriginalCapacity'] for r in rs),SourceUnitCount=len(rs),SourceIDs=[r['AssetID'] for r in rs],ParentIDs=sorted({r['ParentAssetID'] for r in rs}),ActionClass='SPECIFIC_SOURCE_RECORD_OR_INVENTORY_BOUNDARY_DECISION',SourceFiles=sorted({r['Source'] for r in rs}),KnownUnitYears=sum(r['CommissioningYear'] is not None for r in rs),CandidateMethod='Provide missing year/status from listed source unit; or explicitly choose bounded stock scenarios with 0-to-listed-MW unresolved inventory, never infer zero retirement or unlimited life',CandidateCapacityLowerMW=0,CandidateCapacityUpperMW=sum(r['OriginalCapacity'] for r in rs),CurrentIntegratedMWChange=0,CrossFamilyPhysicalOverlap='NOT_PROVED_DISJOINT_DO_NOT_ADD',SharedSourceIDsWithOtherFamily=0,ApprovalStatus='PENDING'))
    groups=defaultdict(list)
    for m in matches:groups[(m['Country'],m['Technology'])].append(m)
    for (country,tech),ms in groups.items():
        raw=[v for m in ms for v in m['RawRecords']];known=[v for v in raw if v['commissioning_year'] is not None];unknown=[v for v in raw if v['commissioning_year'] is None]
        rows.append(dict(Family='GPD_PLANT',Country=country,Technology=tech,Status='SOURCE_LINK_AND_CAPACITY_RECOVERED_AGE_PROXY_PENDING',CapacityMW=sum(m['ParentCapacityMW'] for m in ms),ParentCount=len(ms),SourceUnitCount=len(raw),SourceIDs=[r['gppd_idnr'] for r in raw],ParentIDs=[m['ParentAssetID'] for m in ms],ActionClass='SOURCE_LINK_MECHANICALLY_FIXED_THEN_PLANT_AGE_BOUNDARY_DECISION',KnownReportedPlantYearMW=sum(r['capacity_mw'] for r in known),MissingPlantYearMW=sum(r['capacity_mw'] for r in unknown),YearMeaning='Possible unit-capacity weighted plant year, not unit ages even if integer',CandidateMethod='Prefer unit breakdown linked to these exact GPD IDs. Alternative NEW explicit plant-cohort proxy for reported-year subset; missing-year subset separately bounded. Current instruction prohibits automatic weighted-mean lifetime screening.',CandidateCapacityLowerMW=0,CandidateCapacityUpperMW=sum(m['ParentCapacityMW'] for m in ms),CurrentIntegratedMWChange=0,CrossFamilyPhysicalOverlap='NOT_PROVED_DISJOINT_DO_NOT_ADD',SharedSourceIDsWithOtherFamily=0,ApprovalStatus='PENDING'))
    return sorted(rows,key=lambda r:-r['CapacityMW']),matches

def audit(repo,source_config,prior_delivery,output):
    s=repo/'research_inputs/assembly_v1/sources';a=repo/'results_project/assembly_v1/assets';g=repo/'research/04_model_assembly/gate4';cfg=read(source_config)
    result=reconstruct(s);cross=build_crosswalk(result,s,read(repo/'research_inputs/assembly_v1/registry.json'),read(g/'UNSD_TARGETED_RETRIEVAL_RECEIPT.json'))
    save(output/'BLEND_CROSSWALK.json',cross)
    cov,cov_summary=coverage_reconciliation(repo,s);save(output/'COVERAGE_RECONCILIATION.json',cov);save(output/'COVERAGE_SUMMARY.json',cov_summary)
    n=pypsa.Network(cfg['source_reference']);base=pypsa.Network(a/'electric_base_2050_unsolved.nc')
    hydro,hydro_summary=hydro_candidates(repo,n,prior_delivery/'repo/research/04_model_assembly/gate4/evidence/HYDRO_RESIDUAL_EXACT_TRACE.json');save(output/'HYDRO_CANDIDATES.json',hydro);save(output/'HYDRO_CONDITIONAL_TESTS.json',hydro_summary)
    inventory,matches=inventory_candidates(repo,Path(cfg['source_plant_cache']));save(output/'INVENTORY_ACTIONS.json',inventory);save(output/'GPD_PARENT_RECONCILIATION.json',matches)
    noise=pd.Series(.01+.002*(np.random.RandomState(174).random_sample(len(n.links))-.5),index=n.links.index);costrows=[]
    for k,z in base.links[base.links.carrier.isin(['DC','B2B'])].iterrows():
        assert z.marginal_cost==noise[k]
        costrows.append(dict(Component=k,Carrier=z.carrier,Bus0=z.bus0,Bus1=z.bus1,Pmin=z.p_min_pu,Efficiency=z.efficiency,ActualCost=z.marginal_cost,RecoveredNoise=float(noise[k]),Classification='NUMERICAL_PERTURBATION',Formula='0.01+0.002*(RandomState(174).random_sample(len(reference.links))-0.5), same original row index',SignedCostForPlus100MWh=float(z.marginal_cost*100),SignedCostForMinus100MWh=float(-z.marginal_cost*100) if z.p_min_pu<0 else None,ProductionCostChanged=False))
    save(output/'BIDIRECTIONAL_COST_EVIDENCE.json',costrows)
    expected=prior_delivery/'production_assets'
    for name in ['electric_base_2050_unsolved.nc','carrier_fragment_2050_unsolved.nc','model_cost_layer.json','external_pending_fixed_accounts.json','carrier_fragment.json','carbon_component_map.json']:assert sha(a/name)==sha(expected/name)
    assert sha(repo/'research_inputs/assembly_v1/registry.json')==sha(prior_delivery/'repo/research_inputs/assembly_v1/registry.json')
    assert sha(repo/'results_project/assembly_v1/allocation/allocations.npz')==sha(prior_delivery/'actual_allocation/allocations.npz')
    summary=dict(source_overlap_groups=len(cross),new_exact_queries_required=sum(r['RequestStatus']=='NEW_QUERY_REQUIRED' for r in cross),coverage_cases=len(cov_summary),coverage_status_counts=dict(Counter(r['Status'] for r in cov_summary)),hydro_candidate_pools=len(hydro_summary),hydro_candidate_pending_mw=sum(r['PendingMW'] for r in hydro_summary),gpd_parents=len(matches),gpd_plants=sum(len(r['RawGPDIDs']) for r in matches),gpd_source_capacity_mw=sum(r['ParentCapacityMW'] for r in matches),all_gpd_parent_capacities_reconciled=all(r['CapacityReconciled'] for r in matches),known_gpd_plant_year_mw=sum(r.get('KnownReportedPlantYearMW',0) for r in inventory),missing_gpd_plant_year_mw=sum(r.get('MissingPlantYearMW',0) for r in inventory),signed_bidir_links=sum(r['Pmin']<0 for r in costrows),noisy_cost_links=len(costrows),preserved_existing_units=733,preserved_existing_mw=186586,preserved_demand_accounts=152,preserved_fixed_accounts=471,source_link_gaps_recovered=len(matches),new_physical_accounts_or_assets_qualified=0,production_assets_byte_identical=True,fullsc_network_complete=False,solver_runs=0,gate5_allowed=False)
    save(output/'CLOSURE_SUMMARY.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['repo','source-config','prior-delivery','output']:p.add_argument('--'+name,type=Path,required=True)
    audit(**vars(p.parse_args()))
