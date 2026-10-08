"""Observable invariants for a FUTURE approved regional comparison; no benefits."""
import hashlib,json
import numpy as np
from fixed_accounts import validate_exported_accounting

def contract(n):
    validate_exported_accounting(n)
    weights={k:[float(x).hex() for x in n.snapshot_weightings[k]] for k in ['objective','generators','stores']}
    rows=[]
    for r in n.meta['external_pending_fixed_accounts']:
        ident=r['FixedAccountID'];route=n.meta['biomass_obligation_routes'][ident];meter=r['Meter']
        bus=r['ResourceBus'];final=r['FinalBuses']
        # Actual incidences expose a new outlet even when stale route metadata is retained.
        edges={col:sorted(n.links.index[n.links[col].isin([bus]+final)].tolist()) for col in n.links if col.startswith('bus')}
        rows.append(dict(source_id=r['SourceRow'],account_id=r['SourceAccountID'],fixed_id=ident,
            commodity=r['Commodity'],quantity_mwh=float(r['QuantityMWh']).hex(),time_weights=weights,
            exclusive_final_buses=final,incidences=edges,route=route,
            price_boundary={k:r[k] for k in ['UnitPriceEUR2020PerMWh','PhysicalCO2_tPerMWh','cost_qualification','DecisionReference']},
            store_direction=n.meta['store_power_rules'][ident],
            store_static={k:str(n.stores.at[ident,k]) for k in ['bus','e_nom','e_initial','e_cyclic','standing_loss']},
            meter_static={k:str(n.links.at[meter,k]) for k in ['bus0','bus1','efficiency','p_min_pu','p_max_pu','p_nom_extendable']},
            required_hooks=list(n.meta['required_constraint_hooks'])))
    # Hash common weights once rather than duplicate 8760 entries for each term.
    weight_sha=hashlib.sha256(json.dumps(weights,sort_keys=True).encode()).hexdigest()
    for r in rows:r['time_weights']=weight_sha
    return dict(schema='GATE6_FIXED_TERM_INVARIANCE_V1',weights_sha256=weight_sha,
        snapshot_labels=[str(x) for x in n.snapshots],terms=sorted(rows,key=lambda x:x['fixed_id']),
        interpretation='Input/structure equality only. Future solved physical qualification is also required; unknown prices and emissions have not been cancelled.')

def compare(a,b):
    if a!=b:raise ValueError('Fixed-term comparison boundary changed')
    return dict(status='PASS_INPUT_STRUCTURE_ONLY',cost_cancellation_proven=False,benefits_calculated=False)
