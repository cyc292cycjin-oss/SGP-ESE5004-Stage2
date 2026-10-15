"""Independent equations for validation solves (V5 group A physics). Never claims complete cost/CO2.

S1: fixed-account checks removed (R13). Per-country atmosphere levels are checked against
the configured caps; the objective reconciliation accepts the two fixed-at-1 constants
(existing-asset FOM, existing cross-border transmission FOM) exactly once each.
"""
import json
import numpy as np
import pandas as pd

def dynamic_checks(n):
    rows=[];weights=n.snapshot_weightings;h=weights.stores
    def check(name,residual,scale=1.,unit='MW',detail=''):
        a=np.asarray(residual,dtype=float);s=np.asarray(scale,dtype=float)
        finite=bool(np.isfinite(a).all());maximum=float(np.max(np.abs(a))) if a.size else 0.
        # Strict engineering tolerance: absolute1e-3 in physical units +relative1e-7.
        lim=1e-3+1e-7*np.abs(s)
        ok=finite and bool(np.all(np.abs(a)<=lim))
        rows.append(dict(Check=name,Status='PASS' if ok else 'FAIL',MaxAbsoluteResidual=maximum,Unit=unit,Tolerance='1e-3 + 1e-7*abs(reference)',Detail=detail))
    def dense(c,a):return n.get_switchable_as_dense(c,a)
    balance=pd.DataFrame(0.,index=n.snapshots,columns=n.buses.index)
    magnitude=balance.copy()
    for typ in ['Generator','Load','Store','StorageUnit']:
        df=n.df(typ);p=n.pnl(typ).p.reindex(columns=df.index)*df.sign
        for bus,ids in df.groupby('bus').groups.items():
            value=p[ids].sum(axis=1);balance[bus]+=value;magnitude[bus]+=p[ids].abs().sum(axis=1)
    for typ in ['Link','Line','Transformer']:
        df=n.df(typ)
        for col in [x for x in df if x.startswith('bus') and x[3:].isdigit()]:
            port='p'+col[3:];p=n.pnl(typ)[port]
            for bus,ids in df[df[col]!=''].groupby(col).groups.items():
                balance[bus]-=p[ids].sum(axis=1);magnitude[bus]+=p[ids].abs().sum(axis=1)
    check('BUS_BALANCES',balance,magnitude)
    check('ALL_FIXED_DEMANDS',n.loads_t.p-dense('Load','p_set'),dense('Load','p_set'))
    for col in [x for x in n.links if x.startswith('bus') and x[3:].isdigit() and x!='bus0']:
        ids=n.links.index[n.links[col]!=''];suffix=col[3:];eff='efficiency'+('' if suffix=='1' else suffix)
        residual=n.links_t['p'+suffix][ids]+n.links_t.p0[ids]*dense('Link',eff)[ids]
        check('LINK_MULTIPORT_'+suffix,residual,n.links_t.p0[ids])
    for typ,state,initial,cyclic in [('Store','e','e_initial','e_cyclic'),('StorageUnit','state_of_charge','state_of_charge_initial','cyclic_state_of_charge')]:
        df=n.df(typ);ts=n.pnl(typ);end=ts[state].reindex(columns=df.index);prev=end.shift(1)
        prev.iloc[0]=np.where(df[cyclic],end.iloc[-1],df[initial])
        decay=(1-dense(typ,'standing_loss')).pow(h,axis=0)
        if typ=='Store':rhs=prev*decay-ts.p.mul(h,axis=0)
        else:
            rhs=prev*decay+(ts.p_store*dense(typ,'efficiency_store')-ts.p_dispatch/dense(typ,'efficiency_dispatch')+dense(typ,'inflow')-ts.spill.reindex(columns=df.index,fill_value=0)).mul(h,axis=0)
        check(typ.upper()+'_STATE_EQUATIONS_CYCLIC_AND_INITIAL',end-rhs,np.maximum(end.abs(),rhs.abs()),'MWh')
    # Component dispatch and energy capacity bounds, and nominal limits.
    for typ,nom in [('Generator','p_nom'),('Link','p_nom'),('Line','s_nom'),('StorageUnit','p_nom'),('Store','e_nom')]:
        df=n.df(typ);cap=df[nom+'_opt'];ext=df[nom+'_extendable']
        check(typ+'_NOMINAL_LOWER',np.minimum(cap[ext]-df.loc[ext,nom+'_min'],0),cap[ext])
        finite=df[nom+'_max'].replace(np.inf,np.nan).notna()&ext
        check(typ+'_NOMINAL_UPPER',np.maximum(cap[finite]-df.loc[finite,nom+'_max'],0),cap[finite])
        check(typ+'_FIXED_CAPACITY',cap[~ext]-df.loc[~ext,nom],df.loc[~ext,nom])
        if typ in ['Generator','Link']:
            flow=n.pnl(typ)['p' if typ=='Generator' else 'p0']
            check(typ+'_DISPATCH_UPPER',np.maximum(flow-dense(typ,'p_max_pu')*cap,0),flow)
            check(typ+'_DISPATCH_LOWER',np.minimum(flow-dense(typ,'p_min_pu')*cap,0),flow)
        elif typ=='Line':check('TRANSMISSION_THERMAL_BOUNDS',np.maximum(n.lines_t.p0.abs()-dense('Line','s_max_pu')*cap,0),n.lines_t.p0)
        elif typ=='Store':
            check('STORE_ENERGY_UPPER',np.maximum(n.stores_t.e-dense(typ,'e_max_pu')*cap,0),n.stores_t.e,'MWh')
            check('STORE_ENERGY_LOWER',np.minimum(n.stores_t.e-dense(typ,'e_min_pu')*cap,0),n.stores_t.e,'MWh')
        else:
            check('STORAGE_UNIT_ENERGY_UPPER',np.maximum(n.storage_units_t.state_of_charge-cap*df.max_hours,0),n.storage_units_t.state_of_charge,'MWh')
            check('STORAGE_UNIT_ENERGY_LOWER',np.minimum(n.storage_units_t.state_of_charge,0),n.storage_units_t.state_of_charge,'MWh')
            check('STORAGE_UNIT_CHARGE_BOUND',np.maximum(n.storage_units_t.p_store+cap*dense(typ,'p_min_pu'),0),n.storage_units_t.p_store)
            check('STORAGE_UNIT_DISCHARGE_BOUND',np.maximum(n.storage_units_t.p_dispatch-cap*dense(typ,'p_max_pu'),0),n.storage_units_t.p_dispatch)
    for name,rule in n.meta.get('store_power_rules',{}).items():
        v=n.stores_t.p[name];check('DIRECTION:'+name,np.minimum(v,0) if rule=='discharge_only' else np.maximum(v,0),v)
    for pair in n.meta.get('battery_inverter_pairs',[]):
        a,b=pair['charger'],pair['discharger'];check('BATTERY_CAPACITY:'+a,n.links.at[a,'p_nom_opt']-n.links.at[b,'p_nom_opt']*n.links.at[b,'efficiency'],n.links.at[a,'p_nom_opt'])
    for key,g in n.meta.get('existing_resource_groups',{}).items():
        used=sum(n.df(x['ComponentType']).at[x['Name'],'p_nom_opt']*x['CapacityToMW'] for x in g['candidates'])
        check('RESOURCE_LIMIT:'+key,max(0.,used-g['new_build_limit_mw']),g['new_build_limit_mw'])
    for name,cap in n.meta.get('external_annual_caps',{}).items():check('IMPORT_ANNUAL:'+name,max(0.,float(n.generators_t.p[name]@weights.generators)-cap),cap,'MWh')
    if 'lv_limit' in n.global_constraints.index:
        lv=n.global_constraints.loc['lv_limit'];carriers=lv.carrier_attribute.split(', ')
        volume=0.
        for typ,nom in [('Line','s_nom_opt'),('Link','p_nom_opt')]:
            d=n.df(typ);d=d[d.carrier.isin(carriers)&d[nom.replace('_opt','_extendable')]]
            volume+=float((d[nom]*d.length).sum())
        check('LV_LIMIT',max(0.,volume-float(lv.constant)),float(lv.constant),'MW km')
    # S1-5: national atmosphere level at the last snapshot against the configured cap (per
    # country or ASEAN total). Removals make the Store negative (e_min_pu=-1).
    carbon=n.meta.get('research_carbon');levels=None
    if carbon:
        from carrier_architecture import atmosphere_bus,COUNTRIES
        levels={c:float(n.stores_t.e[atmosphere_bus(c)].iloc[-1]) for c in sorted(COUNTRIES)}
        if carbon['constraint_scope']=='per_country':
            for c,v in levels.items():check('COUNTRY_CO2_CAP:'+c,max(0.,v-float(carbon['country_cap_tco2'][c])),max(1.,abs(float(carbon['country_cap_tco2'][c]))),'tCO2')
        else:check('ASEAN_CO2_CAP',max(0.,sum(levels.values())-float(carbon['asean_total_cap_tco2'])),max(1.,abs(float(carbon['asean_total_cap_tco2']))),'tCO2')
    # Native objective subtracts initial nominal capacity from extendable capital terms.
    capital=0.;variable=0.
    for typ,nom in [('Generator','p_nom'),('Link','p_nom'),('Line','s_nom'),('StorageUnit','p_nom'),('Store','e_nom')]:
        d=n.df(typ);ext=d[nom+'_extendable'];capital+=float(((d.loc[ext,nom+'_opt']-d.loc[ext,nom])*d.loc[ext,'capital_cost']).sum())
    for typ,flow in [('Generator','p'),('Link','p0'),('Store','p'),('StorageUnit','p_dispatch')]:
        variable+=float((n.pnl(typ)[flow]*dense(typ,'marginal_cost')).sum(axis=1)@weights.objective)
    known=float(n.meta.get('existing_annual_fixed_om_eur',0.))+float(n.meta.get('existing_cross_border_fom_eur',0.));expected=capital+variable+known
    check('OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE',float(n.objective)-expected,expected,'EUR2020/year',json_detail(capital,variable,known))
    return rows,dict(objective_reconciliation={'capital':capital,'variable':variable,'known_fixed_once':known,'actual':float(n.objective)},country_co2_levels_tco2=levels,carbon_validation='Link multiport equations + CO2 bus balance + national atmosphere Store state; caps checked on final level')

def json_detail(capital,variable,known):
    return json.dumps(dict(annualised_new_capital=capital,variable_cost=variable,known_fixed_om_once=known))
