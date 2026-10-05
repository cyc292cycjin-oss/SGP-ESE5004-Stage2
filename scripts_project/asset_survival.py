"""Explicit2050 age/status selection; missing evidence is never zero or infinity."""
import math
METHOD='ASSEMBLY_V1_2050_SINGLE_YEAR_SURVIVING_ASSETS'
def select_asset(r,year=2050):
    out=dict(r,DecisionBasis=METHOD,RetainedCapacity2050=None)
    capacity=float(r['OriginalCapacity'])
    if not math.isfinite(capacity) or capacity<0:raise ValueError('Invalid source capacity')
    role=r.get('AssetClass','UNKNOWN')
    if role in ['MODEL_OPTIMISED_ADDITION','NEW_BUILD_CANDIDATE','COMMITTED_OR_PLANNED']:
        return dict(out,SurvivalStatus='NOT_INHERITED_'+role)
    if role!='OBSERVED_EXISTING':return dict(out,SurvivalStatus='UNRESOLVED_EXISTING_STATUS')
    commissioning=r.get('CommissioningYear');retirement=r.get('RetirementYear')
    if commissioning is None or r.get('CommissioningEvidenceVerified') is not True:return dict(out,SurvivalStatus='UNRESOLVED_COMMISSIONING')
    if retirement is not None and r.get('RetirementEvidenceVerified') is True:basis='VERIFIED_RETIREMENT_RECORD'
    elif r.get('Lifetime') is not None and r.get('LifetimeAccepted') is True:
        retirement=float(commissioning)+float(r['Lifetime']);basis='DERIVED_FROM_ACCEPTED_LIFETIME'
    else:return dict(out,SurvivalStatus='UNRESOLVED_RETIREMENT_OR_LIFETIME')
    if not math.isfinite(float(commissioning)) or not math.isfinite(float(retirement)) or retirement<=commissioning:raise ValueError('Invalid lifetime boundary')
    survives=commissioning<=year<retirement
    return dict(out,RetirementYear=retirement,RetirementDerivation=basis,SurvivalStatus='SURVIVES_2050' if survives else 'NOT_ACTIVE_2050',RetainedCapacity2050=capacity if survives else 0.)

def remaining_resource(total,survivors,meaning):
    if meaning=='TOTAL_CAPACITY':
        if survivors>total+1e-8:raise ValueError('Existing exceeds resource total')
        return max(0.,total-survivors)
    if meaning=='ADDITIONAL_POTENTIAL':return total
    raise ValueError('Resource-limit semantics unresolved')
