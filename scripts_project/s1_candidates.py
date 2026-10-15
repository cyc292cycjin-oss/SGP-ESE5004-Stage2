"""S1-4 generation/storage candidates and the per-technology cost scaling layer (decisions 37, 38, 39, 41).

Nuclear (large PWR + SMR) candidates are placed by a configured siting table, not by the
upstream rule that only adds a candidate where a plant of the same carrier already exists
(scripts/add_electricity.py:772). Site-bound candidates (geothermal, new ror/hydro, PHS)
are built as structures with p_nom_max=0 and the tag DATA_PENDING until potentials arrive.
"""
import numpy as np
import pandas as pd
from carrier_architecture import COUNTRIES,finite

PENDING='DATA_PENDING'

def _cost(costs,tech,key):
    v=costs.at[tech,key]
    if not np.isfinite(float(v)):raise ValueError('Cost row missing: '+tech+'.'+key)
    return float(v)

def add_nuclear(n,costs,cfg,nodes):
    """Large PWR from technology-data `nuclear`; SMR structure only (technology-data has no reactor SMR)."""
    ledger=[]
    for kind in ['large_pwr','smr']:
        k=cfg[kind];allowed=set(k['allowed_countries'])
        if not allowed<=COUNTRIES:raise ValueError('Unknown country in nuclear siting table')
        carrier=k['carrier']
        if carrier not in n.carriers.index:n.add('Carrier',carrier,co2_emissions=0.)
        for node in nodes:
            country=n.buses.at[node,'country']
            if country not in allowed:continue
            name=node+' '+carrier
            if name in n.generators.index:raise ValueError('Duplicate candidate '+name)
            if k.get('cost_technology'):
                tech=k['cost_technology']
                n.add('Generator',name,bus=node,carrier=carrier,p_nom_extendable=True,p_nom=0.,p_nom_min=0.,p_nom_max=np.inf,
                      capital_cost=_cost(costs,tech,'fixed'),marginal_cost=_cost(costs,tech,'marginal_cost'),efficiency=_cost(costs,tech,'efficiency'),lifetime=_cost(costs,tech,'lifetime'),build_year=2050)
                status='PRICED'
            else:
                n.add('Generator',name,bus=node,carrier=carrier,p_nom_extendable=True,p_nom=0.,p_nom_min=0.,p_nom_max=finite(k['p_nom_max']),capital_cost=0.,marginal_cost=0.,build_year=2050)
                n.generators.loc[name,'cost_qualification']=PENDING;status=PENDING
            n.generators.loc[name,['asset_role','country','siting_evidence_grade','s1_candidate_status']]=['new_build_candidate',country,cfg['evidence_grade'],status]
            ledger.append(dict(component='Generator',name=name,carrier=carrier,country=country,status=status,cost_technology=k.get('cost_technology')))
    return ledger

def add_site_candidates(n,costs,cfg,nodes,phs_max_hours_decision):
    """Geothermal, new ror/hydro, new PHS: one candidate per node, p_nom_max=0, DATA_PENDING."""
    ledger=[]
    for key,k in cfg.items():
        carrier=k['carrier'];typ=k['component'];tech=k['cost_technology']
        if carrier not in n.carriers.index:n.add('Carrier',carrier,co2_emissions=0.)
        for node in nodes:
            country=n.buses.at[node,'country'];name=node+' '+key
            if name in n.df(typ).index:raise ValueError('Duplicate candidate '+name)
            common=dict(bus=node,carrier=carrier,p_nom_extendable=True,p_nom=0.,p_nom_min=0.,p_nom_max=finite(k['p_nom_max']),capital_cost=_cost(costs,tech,'fixed'),marginal_cost=_cost(costs,tech,'marginal_cost'),lifetime=_cost(costs,tech,'lifetime'),build_year=2050)
            if typ=='Generator':n.add('Generator',name,efficiency=_cost(costs,tech,'efficiency'),**common)
            elif typ=='StorageUnit':
                # Energy duration is part of the pending site data. PHS uses the accepted 6 h proxy
                # of the existing-PHS decision as a provisional value; reservoir hydro has none (0 h).
                hours=float(phs_max_hours_decision['PHSMaxHours']) if carrier=='PHS' else 0.
                eff=_cost(costs,tech,'efficiency')
                n.add('StorageUnit',name,efficiency_dispatch=eff,efficiency_store=eff if carrier=='PHS' else 1.,max_hours=hours,cyclic_state_of_charge=True,**common)
                n.storage_units.loc[name,'max_hours_basis']=(phs_max_hours_decision['DecisionReference']+' provisional for new PHS') if carrier=='PHS' else 'DATA_PENDING_RESERVOIR_DURATION'
            else:raise ValueError('Unsupported candidate component '+typ)
            df=n.df(typ);df.loc[name,['asset_role','country','s1_candidate_status','cost_qualification']]=['new_build_candidate',country,PENDING,'PRICED_STRUCTURE_PENDING_POTENTIAL']
            ledger.append(dict(component=typ,name=name,carrier=carrier,country=country,status=PENDING,cost_technology=tech,pending_fields=['p_nom_max','site','profile' if typ=='Generator' and carrier!='geothermal' else 'none']+(['inflow','max_hours'] if typ=='StorageUnit' and carrier!='PHS' else [])))
    return ledger

def confirm_extendable(n,carriers):
    """S1-4: H2 turbine, fuel cell, H2 tank, battery, home battery must be extendable candidates."""
    out={}
    for carrier in carriers:
        found=False
        for typ,nom in [('Link','p_nom_extendable'),('Store','e_nom_extendable'),('Generator','p_nom_extendable'),('StorageUnit','p_nom_extendable')]:
            df=n.df(typ);sel=df[df.carrier==carrier]
            if len(sel):
                found=True
                if not sel[nom].all():raise ValueError('Candidate not extendable: '+carrier)
                out[carrier]=dict(component=typ,count=int(len(sel)),all_extendable=True,capital_cost_min=float(sel.capital_cost.min()),capital_cost_max=float(sel.capital_cost.max()))
        if not found:raise ValueError('Required candidate carrier missing: '+carrier)
    return out

def apply_cost_scaling(n,factors):
    """Multiply capital_cost of new-build candidates by the per-carrier factor (default 1.0).
    Existing survivors (capital_cost 0, FOM once) are never touched. A factor of exactly 1.0
    leaves every stored value bit-identical, so the exported NetCDF hash is unchanged."""
    ledger=[]
    for carrier,f in factors.items():
        f=finite(f)
        for typ in ['Generator','Link','Store','StorageUnit','Line']:
            df=n.df(typ)
            if not len(df):continue
            sel=df.index[(df.carrier==carrier)&(df.get('asset_role',pd.Series('',index=df.index)).fillna('')!='existing_survivor')]
            if not len(sel):continue
            before=float(df.loc[sel,'capital_cost'].sum())
            if f!=1.0:df.loc[sel,'capital_cost']=df.loc[sel,'capital_cost']*f
            ledger.append(dict(carrier=carrier,component=typ,count=int(len(sel)),factor=f,capital_cost_sum_before=before,capital_cost_sum_after=float(df.loc[sel,'capital_cost'].sum()),applied=f!=1.0))
    return ledger
