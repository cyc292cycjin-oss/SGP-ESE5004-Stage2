"""Screen source units before any node/technology aggregation.

Conditional lifetime calculations are separately labelled and never accepted
production stock. Parent capacity discrepancies remain explicit, not normalised.
"""
import math
from collections import Counter,defaultdict
from asset_survival import select_asset

def numeric(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def reconcile_units(parents,lifetimes=None):
    lifetimes=lifetimes or {};seen={};units=[];summary=[]
    for p in parents:
        for s in p['SourceSubassets']:
            if s['ID'] in seen:raise ValueError('Duplicate raw unit ID '+s['ID'])
            seen[s['ID']]=p['AssetID']
    for p in parents:
        subs=p['SourceSubassets'];caps=[s['Capacity'] for s in subs if numeric(s['Capacity']) and s['Capacity']>=0]
        known=sum(caps);difference=float(p['OriginalCapacity'])-known
        capacity_complete=bool(subs) and len(caps)==len(subs) and len(subs)==len(p['SourceIDs'])
        balanced=capacity_complete and math.isclose(known,p['OriginalCapacity'],rel_tol=1e-6,abs_tol=.01)
        rec=[]
        for s in sorted(subs,key=lambda x:x['ID']):
            cap=s['Capacity'] if numeric(s['Capacity']) and s['Capacity']>=0 else None
            start=s['StartYear'] if numeric(s['StartYear']) else None
            retired=s['RetiredYear'] if numeric(s['RetiredYear']) else None
            status=str(s['Status']).lower()
            role='OBSERVED_EXISTING' if status=='operating' else 'COMMITTED_OR_PLANNED' if status in {'announced','pre-construction','construction','shelved','cancelled','proposed'} else 'UNKNOWN'
            decision=lifetimes.get(p['Technology'],{})
            accepted=decision.get('ApprovalStatus')=='HUMAN_ACCEPTED' and bool(decision.get('DecisionReference')) and bool(decision.get('Source'))
            life=decision.get('Lifetime') if accepted else p.get('Lifetime')
            u=dict(AssetID='GEM:'+s['ID'],RawUnitID=s['ID'],ParentAssetID=p['AssetID'],Country=p['Country'],Technology=p['Technology'],OriginalCapacity=cap,CommissioningYear=start,RetirementYear=retired,CommissioningEvidenceVerified=start is not None,RetirementEvidenceVerified=retired is not None,AssetClass=role,Lifetime=life,LifetimeAccepted=accepted,LifetimeSource=decision.get('Source') if accepted else p['LifetimeSource'],LifetimeDecisionReference=decision.get('DecisionReference') if accepted else None,OriginalMappedBus=p['OriginalMappedBus'],Source=s['Source'],SourceVersion=s['SourceSHA256'],SourceRow=f"{s['Sheet']}:{s['ExcelRow']}",CapacityReconciliation='MATCHED_PARENT' if balanced else 'PARENT_CAPACITY_DISCREPANCY_OR_MISSING',ParentCapacity=p['OriginalCapacity'],ParentCapacityDifference=difference,CostTreatment=p['CostTreatment'],ResourceLimitTreatment=p['ResourceLimitTreatment'])
            if cap is not None:
                chosen=select_asset(u)
                if not balanced and chosen['SurvivalStatus']=='SURVIVES_2050':chosen.update(SurvivalStatus='UNRESOLVED_PARENT_CAPACITY_RECONCILIATION',RetainedCapacity2050=None)
                candidate=select_asset(dict(u,LifetimeAccepted=numeric(life) and life>0))
                chosen.update(ConditionalSurvivalStatus=candidate['SurvivalStatus'],ConditionalRetainedMW=candidate['RetainedCapacity2050'],ConditionalCalculation='NOT_ACCEPTED_PRODUCTION_CAPACITY',ConditionalCapacityQualified=balanced)
            else:chosen=dict(u,SurvivalStatus='UNRESOLVED_UNIT_CAPACITY',RetainedCapacity2050=None,ConditionalRetainedMW=None,ConditionalSurvivalStatus='UNRESOLVED_UNIT_CAPACITY',ConditionalCalculation='NOT_ACCEPTED_PRODUCTION_CAPACITY',ConditionalCapacityQualified=False)
            units.append(chosen);rec.append(chosen)
        # Keep unlinked/missing source amounts separately: never fabricate a unit.
        missing_year=sum(r['OriginalCapacity'] for r in rec if r['OriginalCapacity'] is not None and r['CommissioningYear'] is None)
        known_year=sum(r['OriginalCapacity'] for r in rec if r['OriginalCapacity'] is not None and r['CommissioningYear'] is not None)
        summary.append(dict(ParentAssetID=p['AssetID'],Country=p['Country'],Technology=p['Technology'],ParentCapacity=p['OriginalCapacity'],SourceUnitCount=len(rec),KnownSourceUnitCapacity=known,KnownCommissioningCapacity=known_year,MissingCommissioningSourceCapacity=missing_year,UnmatchedPositiveParentCapacity=max(0.,difference),SignedCapacityDifference=difference,CapacityReconciled=balanced,OriginalStatus=p['SurvivalStatus'],AllUnitYearsKnown=bool(rec) and all(r['CommissioningYear'] is not None for r in rec),AcceptedRetainedMW=sum(r['RetainedCapacity2050'] or 0 for r in rec),ConditionalSurvivorsMW=sum(r['ConditionalRetainedMW'] or 0 for r in rec) if balanced else None,SourceIDs=p['SourceIDs']))
    return dict(schema='unit-first-survival-v1',target_year=2050,weather_year=2013,records=units,parent_reconciliation=summary,raw_unit_ids_unique=True,production_lifetimes_accepted=any(r.get('LifetimeAccepted') for r in units),status_counts=dict(Counter(r['SurvivalStatus'] for r in units)),note='Raw-unit selection precedes aggregation. Conditional results must not be promoted by renaming a status. Capacity discrepancies are never normalised.')

def lifetime_decision_table(evidence,source):
    groups=defaultdict(list)
    for p in evidence['parent_reconciliation']:groups[p['Technology']].append(p)
    rows=[]
    for tech,parents in sorted(groups.items()):
        units=[r for r in evidence['records'] if r['Technology']==tech]
        eligible=[r for r in units if r['AssetClass']=='OBSERVED_EXISTING' and r['ConditionalCapacityQualified']]
        candidate=sorted({r['Lifetime'] for r in units if numeric(r.get('Lifetime'))})
        unknown=sum(p['ParentCapacity'] for p in parents if not p['CapacityReconciled'])+sum(r['OriginalCapacity'] or 0 for r in units if r['ConditionalCapacityQualified'] and (r['AssetClass']=='UNKNOWN' or r['AssetClass']=='OBSERVED_EXISTING' and r['CommissioningYear'] is None))
        rows.append(dict(Technology=tech,CandidateLifetime=candidate[0] if len(candidate)==1 else None,SourceFileAndVersion=source,SourceMeaning='Frozen fuel_to_lifetime generic imputation assumption; not actual retirement notice and not automatically accepted historic-equipment lifetime',AffectedExistingCapacity=sum(r['OriginalCapacity'] or 0 for r in eligible),SurvivorsUnderCandidate=sum(r['ConditionalRetainedMW'] or 0 for r in eligible),UnresolvedCapacity=unknown,KnownNonExistingCapacity=sum(r['OriginalCapacity'] or 0 for r in units if r['ConditionalCapacityQualified'] and r['AssetClass']=='COMMITTED_OR_PLANNED'),DecisionRequired='Accept source-backed historical lifetime assumption or compatible alternative for observed stock; no approval inferred for planned/unknown identities',ApprovalStatus='PENDING',CapacityBasis='MW; parent-compatible observed-existing raw units; unresolved excludes known non-existing projects; candidate survivors are not accepted stock'))
    return rows
