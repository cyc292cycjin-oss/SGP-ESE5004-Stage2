"""Gate2 demand contracts. No upstream demand builders, network mutation or solver.

Amounts are final-energy MWh, never useful service inferred from fuel consumption.
Missing evidence is an error at materialisation; observation tables may retain it.
"""
from copy import deepcopy
import math

COUNTRIES = ('BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN')
STATUSES = {'HUMAN_ACCEPTED','FROZEN_UPSTREAM','APPROVED_ENGINEERING','EMBEDDED',
            'PENDING','MISSING','REFERENCE_ONLY','VALIDATION_ONLY','BLOCKER'}
TYPES = {'DIRECT_ELECTRICITY','DIRECT_FUEL','EXPLICIT_SERVICE',
         'ENDOGENOUS_CONVERSION_INPUT','BUNKER_FUEL','UNCLASSIFIED','EMBEDDED'}
FIELDS = ('Country Year Sector Subsector Carrier DemandType RawValue RawUnit '
          'ConvertedMWh ParentAccount ChildAccount Representation Source SourceYear '
          'SourceSHA256 Transformation SpatialRule TemporalRule IncludedInAstar '
          'TransferredFromAstar FixedOrEndogenous Status HumanAcceptance Notes '
          'RowID OwnerAccount Posting Required NumericAccepted ZeroEvidence '
          'LogicalDestination ExistingEnergyLoad EmissionsPresent SourceLocator Group '
          'ParentBefore TransferredChild ParentAfter IndependentReference').split()


def energy(value):
    if value is None or value == '' or isinstance(value, bool):
        raise ValueError('Missing annual energy is not zero')
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError('Annual energy must be finite and nonnegative')
    return value


def same(expected, actual):
    if not math.isclose(energy(expected), energy(actual), rel_tol=1e-10, abs_tol=1e-6):
        raise ValueError('Conservation failed')


def convert(value, unit):
    factors = {'Kilowatt-hours, million':1000.,'MWh/year':1.,'TWh/year':1e6,'Terajoules':1e6/3600}
    if unit not in factors:
        raise ValueError('Unit or calorific basis requires explicit source approval: '+unit)
    return energy(value) * factors[unit]


def parent_transfer(parent_before, children, independent_reference, *, accepted):
    """Atomic subtract-once transaction. children is [(unique account, MWh)].

    The independent reference is read separately from the frozen parent source,
    never reconstructed from the child list. Zero children means no transfer,
    not an observation that heating or historical EV equals zero.
    """
    if not accepted:
        raise ValueError('Parent and subset membership need human acceptance')
    before=energy(parent_before); same(independent_reference,before)
    ids=[k for k,v in children]
    if len(ids)!=len(set(ids)) or any(not k for k in ids):
        raise ValueError('Duplicate or empty transferred child identity')
    moved=math.fsum(energy(v) for k,v in children)
    if moved>before:
        raise ValueError('Transfer exceeds independent parent')
    after=before-moved
    same(before,after+moved)
    return dict(ParentBefore=before,TransferredChild=moved,ParentAfter=after,
                IndependentReference=energy(independent_reference),Children=dict(children))


def road_energy(parent_final, electric_share, residual_carrier_shares, *,
                basis, accepted, share_kind='final_energy'):
    """External ENERGY share, not vehicle share or share times kWh/km.

    No efficiency claim: EV and residual fuel MWh sum on final-energy basis.
    Residual carrier composition is supplied explicitly, not silently all oil.
    """
    if not accepted or basis!='final_energy_MWh' or share_kind!='final_energy':
        raise ValueError('Accepted final-energy total/share/fuel basis required')
    total=energy(parent_final); share=energy(electric_share)
    if share>1: raise ValueError('EV share outside [0,1]')
    if set(residual_carrier_shares)-{'oil','gas','biomass','coal'}:
        raise ValueError('Unknown residual fuel carrier')
    weights={k:energy(v) for k,v in residual_carrier_shares.items()}
    if total*(1-share)>0 or weights: same(1,math.fsum(weights.values()))
    fuel={k:total*(1-share)*v for k,v in weights.items()}
    electric=total*share
    same(total,electric+math.fsum(fuel.values()))
    return dict(ParentFinalEnergy=total,EVFinalEnergy=electric,ResidualFuel=fuel,
                Basis=basis,UsefulTractionEquivalence='NOT_ASSERTED')


def electric_evolution(base, base_year, target_year, *, factor=None,
                       accepted=False, excludes_future_conversion=False):
    base=energy(base)
    if target_year<base_year: raise ValueError('Invalid projection year')
    if target_year==base_year: return base
    if not accepted or factor is None or not excludes_future_conversion:
        raise ValueError('FUTURE_DIRECT_ELECTRICITY_PENDING')
    return base*energy(factor)


def allocate(annual, country, nodes, shapes, physical_weights, *, expected_hours):
    """nodes: node -> {country,weight}; shapes: snapshot -> nonnegative shape.

    Independent annual and represented-hours controls are mandatory. No silent
    normalization of invalid node weights; temporal shapes are weighted once.
    """
    annual=energy(annual)
    if country not in COUNTRIES or not nodes or not shapes:
        raise ValueError('Missing country/node/time identity')
    if set(shapes)!=set(physical_weights): raise ValueError('Snapshot identity mismatch')
    if any(v['country']!=country for v in nodes.values()):
        raise ValueError('Cross-country allocation')
    nw={k:energy(v['weight']) for k,v in nodes.items()}; same(1,math.fsum(nw.values()))
    pw={k:energy(v) for k,v in physical_weights.items()}
    if any(v<=0 for v in pw.values()) or energy(expected_hours)<=0:
        raise ValueError('Physical weights must be positive')
    same(expected_hours,math.fsum(pw.values()))
    shape={k:energy(v) for k,v in shapes.items()}
    den=math.fsum(pw[k]*shape[k] for k in pw)
    if den<=0: raise ValueError('Empty temporal profile')
    result={n:{t:annual*a*shape[t]/den for t in shape} for n,a in nw.items()}
    for n,a in nw.items(): same(annual*a,math.fsum(result[n][t]*pw[t] for t in pw))
    same(annual,math.fsum(result[n][t]*pw[t] for n in nw for t in pw))
    return result


def validate_ledger(rows):
    """Reject invalid structures; return coverage blockers for honest pending rows."""
    if not rows:raise ValueError('Empty demand ledger')
    identities=set(); owners=set(); blockers=[]
    for r in rows:
        if set(FIELDS)-r.keys(): raise ValueError('Missing ledger fields')
        rid=r['RowID']
        if not rid or rid in identities: raise ValueError('Duplicate demand identity')
        identities.add(rid)
        if r['Country'] not in COUNTRIES or r['Status'] not in STATUSES or r['DemandType'] not in TYPES:
            raise ValueError('Invalid country/status/demand type')
        if type(r['Year']) is not int or r['Year']<=0:raise ValueError('Invalid accounting year')
        for field in ('Posting','Required','NumericAccepted','IncludedInAstar','TransferredFromAstar','ExistingEnergyLoad','EmissionsPresent'):
            if type(r[field]) is not bool:raise ValueError('Untyped ledger boolean: '+field)
        if r['RawValue'] not in ('',None):energy(r['RawValue'])
        value=r['ConvertedMWh']
        if value is not None:
            value=energy(value)
            if value==0 and r['ZeroEvidence'] not in ('REPORTED_ZERO','NOT_APPLICABLE'):
                raise ValueError('Zero without source or representation evidence')
        if r['Representation']=='EMBEDDED' and r['Posting']:
            raise ValueError('Embedded/explicit duplicate')
        if r['IncludedInAstar'] and r['Posting'] and r['ChildAccount']!='Astar' and not r['TransferredFromAstar']:
            raise ValueError('Astar plus untransferred child duplicate')
        if r['TransferredFromAstar'] and (not r['IncludedInAstar'] or not r['Posting']):
            raise ValueError('Invalid Astar transfer flags')
        if r['DemandType']=='ENDOGENOUS_CONVERSION_INPUT':
            if r['FixedOrEndogenous']!='ENDOGENOUS' or r['IncludedInAstar'] or r['Posting'] or value is not None:
                raise ValueError('Endogenous conversion cannot be a fixed direct demand')
        elif r['Posting'] and r['FixedOrEndogenous']!='FIXED':
            raise ValueError('Fixed/endogenous ownership conflict')
        is_bunker=r['DemandType']=='BUNKER_FUEL'
        if is_bunker != (r['Sector']=='Bunker'):
            raise ValueError('Bunker/domestic scope conflict')
        if r['Posting']:
            key=(r['Country'],r['Year'],r['Carrier'],r['OwnerAccount'])
            if not r['OwnerAccount'] or key in owners: raise ValueError('Duplicate carrier ownership')
            owners.add(key)
            if not r['LogicalDestination']: blockers.append((rid,'NO_VALID_CARRIER_DESTINATION'))
        if r['Required'] and (value is None or not r['NumericAccepted']):
            blockers.append((rid,'MISSING_ANNUAL_DATA' if value is None else 'NUMERIC_ACCEPTANCE_PENDING'))
        if r['EmissionsPresent'] and not r['ExistingEnergyLoad']:
            blockers.append((rid,'MISSING_ENERGY_OBLIGATION'))
        if r['NumericAccepted'] and (r['Status']!='HUMAN_ACCEPTED' or not r['SourceSHA256'] or value is None):
            raise ValueError('Invalid numeric acceptance assertion')
    for country,year in {(r['Country'],r['Year']) for r in rows}:
        scope=[r for r in rows if (r['Country'],r['Year'])==(country,year)]
        moved=[r for r in scope if r['TransferredFromAstar']]
        if moved:
            parents=[r for r in scope if r['ChildAccount']=='Astar']
            if len(parents)!=1:raise ValueError('Transferred children lack unique parent')
            p=parents[0]
            same(p['ParentBefore'],p['IndependentReference'])
            same(p['TransferredChild'],math.fsum(energy(r['ConvertedMWh']) for r in moved))
            same(p['ParentAfter'],p['ConvertedMWh'])
            same(p['ParentBefore'],p['ParentAfter']+p['TransferredChild'])
    return blockers


def apply_astar_transfers(rows, country, year, child_ids, independent_reference):
    """Return a new ledger only after accepted membership and numeric checks."""
    validate_ledger(rows)
    out=deepcopy(rows)
    parents=[r for r in out if r['Country']==country and r['Year']==year and r['ChildAccount']=='Astar']
    if len(parents)!=1: raise ValueError('Astar parent identity missing or ambiguous')
    p=parents[0]
    if any(r['TransferredFromAstar'] for r in out if (r['Country'],r['Year'])==(country,year)):
        raise ValueError('Transfers are one atomic batch per parent; rebuild before changing membership')
    if len(set(child_ids))!=len(child_ids): raise ValueError('Duplicate transfer request')
    children=[]
    for rid in child_ids:
        matches=[r for r in out if r['RowID']==rid]
        if len(matches)!=1: raise ValueError('Transferred child missing')
        r=matches[0]
        if (r['Country'],r['Year'],r['Carrier'])!=(country,year,'electricity') or not r['IncludedInAstar'] or r['TransferredFromAstar']:
            raise ValueError('Invalid/repeated historical subset transfer')
        if not r['NumericAccepted'] or r['HumanAcceptance']!='VALUE_AND_ASTAR_MEMBERSHIP_ACCEPTED':
            raise ValueError('Historical child membership not accepted')
        children.append(r)
    proof=parent_transfer(p['ConvertedMWh'],[(r['RowID'],r['ConvertedMWh']) for r in children],
                          independent_reference,accepted=p['NumericAccepted'])
    p['ConvertedMWh']=proof['ParentAfter']
    p.update({k:proof[k] for k in ('ParentBefore','TransferredChild','ParentAfter','IndependentReference')})
    if p['ConvertedMWh']==0:p['ZeroEvidence']='NOT_APPLICABLE'
    for r in children:
        r.update(TransferredFromAstar=True,Posting=True,Representation='EXPLICIT',Required=True,OwnerAccount=r['ChildAccount'])
    validate_ledger(out)
    return out,proof


def materialise(rows, country, year, destinations):
    """Compile ONLY accepted annual obligations for later network assembly.

    destinations maps logical keys to explicit country/carrier records. It is a
    contract, not a bus builder. Entire requested country/year fails atomically
    when required evidence is pending. Embedded rows never create extra Loads.
    """
    chosen=[r for r in rows if r['Country']==country and r['Year']==year]
    if not chosen: raise ValueError('Missing country/year coverage')
    blockers=validate_ledger(chosen)
    # Existing upstream component omissions are recorded, but the new obligation
    # can be compiled once a valid destination and human accepted energy exist.
    fatal=[b for b in blockers if b[1]!='MISSING_ENERGY_OBLIGATION']
    if fatal: raise ValueError('Demand layer blocked: '+str(fatal[:4]))
    output=[]
    for r in chosen:
        if not r['Posting']:continue
        if not r['NumericAccepted'] or r['Status']!='HUMAN_ACCEPTED':
            raise ValueError('Unaccepted obligation')
        dest=destinations.get(r['LogicalDestination'])
        if not dest or (dest['country'],dest['carrier'])!=(country,r['Carrier']):
            raise ValueError('Energy obligation has no valid country/carrier destination')
        output.append(dict(identity=r['RowID'],country=country,year=year,carrier=r['Carrier'],
                           annual_mwh=energy(r['ConvertedMWh']),destination=dest['id']))
    return output
