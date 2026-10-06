"""Revocable qualification for externally pending, strictly fixed commodities.

Null scientific prices/emission factors are kept outside the priced objective.
Zero implementation costs MUST carry this contract; they are not free supply.
"""
from collections import defaultdict
import hashlib,json
import numpy as np

COMMODITIES={'Bagasse','Biodiesel','Biogases','Biogasoline','Charcoal','Fuelwood'}
METHOD='ASSEMBLY_V1_EXTERNAL_PENDING_FIXED_ACCOUNTS'
QUALIFICATION='EXTERNAL_PENDING_FIXED_ACCOUNT'
DECISION='GATE4-20261006-FIXED-ACCOUNTS-EUR2020#A'

def _same(a,b):return bool(np.isclose(a,b,rtol=1e-10,atol=1e-6))

def validate_fixed_accounts(n,*,structure_only=False):
    from assembly_components import validate_hooks
    validate_hooks(n)
    routes=n.meta.get('biomass_obligation_routes',{})
    if not routes:return []
    w=n.snapshot_weightings
    if not w.generators.equals(w.stores) or not w.generators.equals(w.objective) or not np.isfinite(w.to_numpy()).all() or not w.gt(0).all().all():raise ValueError('Fixed quantity/objective weights differ')
    if 'install_fragment_constraints' not in n.meta.get('required_constraint_hooks',[]):raise ValueError('Fixed-account direction hook missing')
    groups=defaultdict(list)
    for name,r in routes.items():
        from fixed_account_scope import matching_scope
        scope=matching_scope(n,r['commodity'],n.buses.at[n.stores.at[name,'bus'],'country'],r['input_id'],r['source_row'])
        if r['commodity'] not in COMMODITIES and scope is None and not structure_only:raise ValueError('Commodity has no accepted fixed-account proof: '+r['commodity'])
        # Structural proof can be inspected for a newly materialised commodity;
        # acceptance remains a separate gate below and is never implied by proof.
        groups[tuple(sorted(r['buses']))].append(name)
    rows=[]
    for allowed,names in groups.items():
        final=set(allowed);loadids=n.loads.index[n.loads.bus.isin(final)]
        if not len(loadids):raise ValueError('No physical fixed obligation')
        if set(n.loads.loc[loadids,'source_account_id'])!={routes[k]['input_id'] for k in names}:raise ValueError('Fixed obligation identity mismatch')
        demand=n.get_switchable_as_dense('Load','p_set')[loadids]
        if not np.isfinite(demand.to_numpy()).all() or (demand<0).any().any():raise ValueError('Invalid obligation quantity')
        total=float(demand.sum(axis=1).mul(w.generators).sum())
        if not _same(sum(n.stores.at[k,'e_nom'] for k in names),total):raise ValueError('Resource quantity is not strictly fixed by own obligation')
        if n.generators.bus.isin(final).any() or n.stores.bus.isin(final).any() or n.storage_units.bus.isin(final).any():raise ValueError('Alternative supply or inventory at fixed destination')
        incoming=set()
        for name in names:
            r=routes[name];z=n.stores.loc[name];bus=z.bus
            if z.carrier!=r['commodity'] or n.buses.at[bus,'carrier']!=r['commodity']:raise ValueError('Commodity identity lost')
            if z.e_nom_extendable or z.e_cyclic or not _same(z.e_initial,z.e_nom) or not _same(z.e_nom,r['annual_cap_mwh']) or z.standing_loss!=0 or z.e_min_pu!=0 or z.e_max_pu!=1:raise ValueError('Fixed stock/storage boundary changed')
            if n.meta.get('store_power_rules',{}).get(name)!='discharge_only':raise ValueError('Discharge-only hook missing')
            if n.generators.bus.eq(bus).any() or n.loads.bus.eq(bus).any() or n.storage_units.bus.eq(bus).any() or sum(n.stores.bus.eq(bus))!=1:raise ValueError('Alternative supply or resource use')
            touch=n.links[n.links.filter(regex=r'^bus\d+$').eq(bus).any(axis=1)]
            if len(touch)!=1:raise ValueError('Fixed resource diversion or alternative supply')
            k=touch.index[0];a=touch.iloc[0];incoming.add(k)
            ports=[v for col,v in a.items() if col.startswith('bus') and col[3:].isdigit() and v]
            if len(ports)!=2 or a.bus0!=bus or a.bus1 not in final or a.efficiency!=1 or a.p_min_pu<0:raise ValueError('Diversion, substitution or carbon-credit port')
            for typ,comp in [('Store',name),('Link',k)]:
                zc=n.df(typ).loc[comp]
                if zc.capital_cost!=0 or zc.marginal_cost!=0:raise ValueError('Pending price placeholder changed without source qualification')
                for attr,frame in n.pnl(typ).items():
                    if comp in frame and (attr in ['marginal_cost','standing_loss','e_min_pu','e_max_pu','e_set','efficiency','p_min_pu','p_max_pu']):raise ValueError('Time-varying fixed-account control needs new qualification')
            for comp in [n.lines,n.transformers]:
                if comp.filter(regex=r'^bus\d+$').isin(final|{bus}).any().any():raise ValueError('Fixed commodity connected to another network')
            rows.append(dict(FixedAccountID=name,Commodity=r['commodity'],Country=n.buses.at[bus,'country'],SourceAccountID=r['input_id'],SourceRow=r['source_row'],QuantityMWh=float(z.e_nom),UnitPriceEUR2020PerMWh=None,PhysicalCO2_tPerMWh=None,PendingFixedCostTerm='Q * unknown_price',PendingFixedPhysicalEmissionTerm='Q * unknown_physical_factor',cost_qualification=QUALIFICATION,PhysicalQuantityQualified=True,PhysicalEmissionFactorQualified=False,DecisionReference=DECISION,ResourceBus=bus,FinalBuses=sorted(final),Meter=k))
        touching=n.links[n.links.filter(regex=r'^bus\d+$').isin(final).any(axis=1)]
        if set(touching.index)!=incoming or not touching.bus1.isin(final).all():raise ValueError('Extra final supply/use or reverse route')
    unknown=[]
    for r in rows:
        scope=matching_scope(n,r['Commodity'],r['Country'],r['SourceAccountID'],r['SourceRow'])
        if scope is not None:
            r.update(DecisionReference=scope['DecisionReference'],BoundaryAcceptance='HUMAN_ACCEPTED_CONDITIONAL_ON_CURRENT_STRUCTURE')
        elif r['Commodity'] not in COMMODITIES:unknown.append(r)
    for scope in n.meta.get('additional_fixed_account_scope',[]):
        selected=[r for r in rows if r['DecisionReference']==scope['DecisionReference']]
        if selected and not _same(sum(r['QuantityMWh'] for r in selected),float(scope['ExpectedAnnualMWh'])):raise ValueError('Additional fixed-account source quantity changed')
    for r in unknown:r.update(DecisionReference=None,BoundaryAcceptance='PENDING_ADDITIONAL_COMMODITY_BOUNDARY',cost_qualification='PENDING_FIXED_ACCOUNT_BOUNDARY')
    if unknown and not structure_only:raise ValueError('Structurally fixed but commodity boundary not yet accepted: '+','.join(sorted({r['Commodity'] for r in unknown})))
    return sorted(rows,key=lambda r:r['FixedAccountID'])

def qualify_fixed_accounts(n):
    """Re-evaluate the current actual network, including after merge/readback."""
    n.meta['external_fixed_account_status']='REVOKED_PENDING_CURRENT_VALIDATION'
    n.meta['external_pending_fixed_accounts']=[]
    try:rows=validate_fixed_accounts(n)
    except (ValueError,KeyError) as exc:
        n.meta['external_fixed_account_failure']=str(exc)
        for name in n.meta.get('biomass_obligation_routes',{}):
            if name in n.stores.index:n.stores.loc[name,'cost_qualification']='REVOKED'
        raise
    for r in rows:
        for typ,k in [('Store',r['FixedAccountID']),('Link',r['Meter'])]:
            n.df(typ).loc[k,'cost_qualification']=QUALIFICATION
            n.df(typ).loc[k,'physical_emissions_qualification']='EXTERNAL_PENDING_FIXED_ACCOUNT'
            n.df(typ).loc[k,'fixed_account_id']=r['FixedAccountID']
    n.meta.pop('external_fixed_account_failure',None)
    n.meta.update(external_fixed_account_status='QUALIFIED_FOR_PHYSICAL_ASSEMBLY_ONLY',external_fixed_account_method=METHOD,external_pending_fixed_accounts=rows,full_system_cost_complete=False,full_system_emissions_complete=False)
    n.meta['external_fixed_account_fingerprint']=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
    return rows

def accounting_report(n,priced_objective=None,claim_full_cost=False,claim_full_emissions=False):
    rows=qualify_fixed_accounts(n)
    if claim_full_cost or claim_full_emissions:raise ValueError('Cannot label incomplete pending accounts as full system cost/emissions')
    known=n.meta.get('existing_annual_fixed_om_eur')
    model=getattr(n,'model',None)
    included=bool(model is not None and getattr(n,'_research_existing_assets_model',None) is model)
    if priced_objective is not None and known and not included:
        raise ValueError('Known fixed cost inclusion in supplied objective is unverified; do not add it by default')
    return dict(PricedObjective=priced_objective,KnownFixedCost=known,KnownFixedCostIncludedInPricedObjective=included if priced_objective is not None else None,KnownFixedCostToAddToPricedObjective=0. if priced_objective is not None else None,PricedObjectiveDefinition='Model objective including installed known fixed FOM once; may contain unresolved numerical coefficients, not automatically a pure economic total',PendingFixedCostIncludedInPricedObjective=False,PendingFixedCostTerms=[{k:r[k] for k in ['FixedAccountID','QuantityMWh','UnitPriceEUR2020PerMWh']} for r in rows],FullSystemCostComplete=False,PendingFixedPhysicalEmissions=[{k:r[k] for k in ['FixedAccountID','QuantityMWh','PhysicalCO2_tPerMWh']} for r in rows],FullSystemEmissionsComplete=False,CostCurrencyYear=2020 if n.meta.get('model_price_year')==2020 else None,Scope='Priced subset and external pending fixed terms; not a full total')

def validate_exported_accounting(n):
    expected=n.meta.get('external_pending_fixed_accounts')
    actual=validate_fixed_accounts(n)
    if expected!=actual:raise ValueError('Fixed external ledger does not match current exported physical network')
    for r in actual:
        for typ,k in [('Store',r['FixedAccountID']),('Link',r['Meter'])]:
            if n.df(typ).at[k,'cost_qualification']!=QUALIFICATION:raise ValueError('Unknown price read as free supply after export')
    if n.meta.get('full_system_cost_complete') is not False or n.meta.get('full_system_emissions_complete') is not False:raise ValueError('False complete accounting claim')
    return True
