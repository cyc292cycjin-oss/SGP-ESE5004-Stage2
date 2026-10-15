"""R12A (read-only): why onshore and offshore wind capacity is zero in the D-stage research model
and in the author's reference model. Nothing is modified; numbers are read from the frozen files.

    python scripts_project/r12a_wind_diagnosis.py --output <json>
"""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
import pandas as pd

WIND=['onwind','offwind-ac','offwind-dc'];SOLAR=['solar','solar rooftop']
D_STAGE='/mnt/d/ResearchWorkspaces/ASEAN/outputs/d_2920_diagnostic/d5_main2920_20261012T212658Z_0162bbf4/cloud_run/postprocess/gate6_2920_candidate_UNQUALIFIED.nc'
REFERENCE='/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/cache/results-asean-paper-v1/baseline-aims-3H/elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export.nc'
COSTS='/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/costs_2050_sec.csv'
COSTS2030='/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/resources/baseline-aims-3H-tutorial/costs_2030_elec.csv'
TECHDATA='/mnt/d/ResearchWorkspaces/ASEAN/research/00_source_provenance/official/technology-data/outputs/costs_2050.csv'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def generator_table(n,carriers,solved):
    g=n.generators[n.generators.carrier.isin(carriers)].copy()
    pmax=n.get_switchable_as_dense('Generator','p_max_pu')[g.index];w=n.snapshot_weightings.generators
    g['cf_annual_mean']=(pmax.mul(w,axis=0).sum()/w.sum()).values
    g['country']=g.bus.map(lambda b:n.buses.at[b if b in n.buses.index else b,'country'] if b in n.buses.index else '')
    cols=['bus','country','carrier','p_nom','p_nom_min','p_nom_max','p_nom_extendable','capital_cost','marginal_cost','cf_annual_mean']+(['p_nom_opt'] if solved else [])
    return g[cols]

def lcoe(capital_cost,marginal_cost,cf):
    """EUR/MWh from the model's own parameters: annualised capex per MW / annual MWh per MW + VOM."""
    energy=cf*8760.
    return np.where(energy>0,capital_cost/np.where(energy>0,energy,np.nan)+marginal_cost,np.inf)

def analyse(path,label,solved):
    import pypsa,logging
    logging.disable(logging.CRITICAL)
    n=pypsa.Network(path);out=dict(label=label,file=path,sha256=sha(path),snapshots=int(len(n.snapshots)),hours=float(n.snapshot_weightings.generators.sum()))
    wind=generator_table(n,WIND,solved);solar=generator_table(n,SOLAR,solved)
    for name,t in [('wind',wind),('solar',solar)]:
        t=t.copy();t['lcoe_eur_per_mwh']=lcoe(t.capital_cost.values,t.marginal_cost.values,t.cf_annual_mean.values)
        out[name]=dict(count=int(len(t)),extendable=int(t.p_nom_extendable.sum()),p_nom_max_zero=int((t.p_nom_max<=0).sum()),p_nom_max_lt_10mw=int((t.p_nom_max<10).sum()),p_nom_max_total_gw=float(t.p_nom_max.replace(np.inf,np.nan).sum()/1e3),
                       p_nom_opt_total_mw=float(t.p_nom_opt.sum()) if solved else None,
                       by_carrier_country=t.groupby(['carrier','country']).agg(n=('bus','size'),p_nom_max_gw=('p_nom_max',lambda x:float(x.replace(np.inf,np.nan).sum()/1e3)),cf_mean=('cf_annual_mean','mean'),cf_min=('cf_annual_mean','min'),cf_max=('cf_annual_mean','max'),capital_cost_mean=('capital_cost','mean'),lcoe_mean=('lcoe_eur_per_mwh','mean'),lcoe_min=('lcoe_eur_per_mwh','min'),**({'p_nom_opt_mw':('p_nom_opt','sum')} if solved else {})).reset_index().to_dict('records'))
        out[name]['per_generator']=t.reset_index().rename(columns={'Generator':'name'}).to_dict('records')
    # constraints that could block wind
    gc=n.global_constraints.reset_index().to_dict('records');out['global_constraints']=gc
    out['existing_resource_groups']=list(n.meta.get('existing_resource_groups',{}).keys()) if isinstance(n.meta,dict) else []
    out['carriers_wind']={c:n.carriers.loc[c].replace({np.nan:None}).to_dict() for c in WIND if c in n.carriers.index}
    return out

def cost_consistency():
    c=pd.read_csv(COSTS,index_col=0);old=pd.read_csv(COSTS2030,index_col=0);td=pd.read_csv(TECHDATA)
    rows={}
    for tech in ['onwind','offwind','offwind-ac-station','offwind-dc-station','offwind-ac-connection-submarine','offwind-ac-connection-underground','offwind-dc-connection-submarine','offwind-dc-connection-underground','solar-utility','solar-rooftop']:
        sub=td[td.technology==tech].set_index('parameter')
        rows[tech]=dict(processed_2050={k:(None if pd.isna(c.at[tech,k]) else float(c.at[tech,k])) for k in ['investment','FOM','VOM','lifetime','discount rate','fixed','efficiency'] if tech in c.index and k in c.columns},
                        technology_data_raw={k:dict(value=float(sub.at[k,'value']),unit=str(sub.at[k,'unit']),source=str(sub.at[k,'source'])[:160],currency_year=(None if pd.isna(sub.at[k,'currency_year']) else float(sub.at[k,'currency_year']))) for k in ['investment','FOM','VOM','lifetime'] if k in sub.index},
                        electric_2030_capital_cost=(float(old.at[tech,'capital_cost']) if tech in old.index and 'capital_cost' in old.columns else None))
        p=rows[tech]['processed_2050'];r=rows[tech]['technology_data_raw']
        if p and 'investment' in r and p.get('investment') is not None:
            unit=r['investment']['unit'];scale=1000. if '/kW' in unit else 1.
            rows[tech]['investment_unit_check']=dict(raw_value=r['investment']['value'],raw_unit=unit,expected_per_mw=r['investment']['value']*scale,processed=p['investment'],consistent=bool(np.isclose(r['investment']['value']*scale,p['investment'],rtol=1e-9)))
            if p.get('fixed') is not None and p.get('lifetime') and p.get('discount rate') is not None:
                dr=p['discount rate'];ann=dr/(1-(1+dr)**(-p['lifetime']));expected=(ann+p['FOM']/100.)*p['investment']
                rows[tech]['annuity_check']=dict(expected_fixed=expected,processed_fixed=p['fixed'],consistent=bool(np.isclose(expected,p['fixed'],rtol=1e-9)))
    return dict(costs_2050_sec_sha256=sha(COSTS),costs_2030_elec_sha256=sha(COSTS2030),technology_data_costs_2050_sha256=sha(TECHDATA),rows=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=dict(qualification='READ_ONLY_DIAGNOSIS_NO_BUILD_NO_SOLVE',d_stage=analyse(D_STAGE,'D-stage research model (gate6_2920_candidate_UNQUALIFIED)',True),reference=analyse(REFERENCE,'author reference model (elec_s_100_ec_lv2.0__3h_2025_0.071_DEC_0export)',True),costs=cost_consistency())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(out,indent=2,default=str,allow_nan=True)+'\n')
    for k in ['d_stage','reference']:
        d=out[k];print(k,'wind p_nom_opt',d['wind']['p_nom_opt_total_mw'],'solar p_nom_opt',d['solar']['p_nom_opt_total_mw'],'wind p_nom_max GW',round(d['wind']['p_nom_max_total_gw'],1),'wind ext',d['wind']['extendable'],'/',d['wind']['count'])
