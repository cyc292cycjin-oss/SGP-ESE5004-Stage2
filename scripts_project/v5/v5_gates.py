"""V5 gate skeleton (S1-7). Group A reuses the frozen V4 algebra and physics; group B is new.

Every gate returns a dict with `passed` and evidence. Results are labelled by the contract
(`RESEARCH_V5_SKELETON`): a passing skeleton run is not a formal acceptance.
"""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
import sys
if str(HERE.parent) not in sys.path:sys.path.insert(0,str(HERE.parent))
from v5.kkt_algebra import complete_kkt,require_contract
from carrier_architecture import COUNTRIES,atmosphere_bus

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_contract():
    c=json.loads((HERE/'V5_CONTRACT.json').read_text());require_contract(c);return c
def config_sha(cfg):return hashlib.sha256(json.dumps(cfg,sort_keys=True,default=str).encode()).hexdigest()

# ------------------------------------------------------------------ group A
def gate_a1_a2_kkt(lp_dir,sol_dir,out_dir,contract):
    """A1 KKT algebra + A2 row/column budgets on the exported LP (D=R=1: original units)."""
    lp_dir,sol_dir=Path(lp_dir),Path(sol_dir);meta=json.loads((lp_dir/'MATH_PROBLEM.json').read_text())
    a={k:np.load(lp_dir/(k+'.npy'),mmap_mode='r') for k in ['cost','col_lower','col_upper','row_lower','row_upper','start','index','value']}
    for k,item in meta['arrays'].items():
        if sha(lp_dir/item['file'])!=item['sha256']:raise ValueError('LP array hash mismatch: '+k)
    z,pi,rc=[np.load(sol_dir/(k+'.npy'),mmap_mode='r') for k in ['X','Pi','RC']]
    D=np.ones(meta['num_col']);R=np.ones(meta['num_row'])
    kkt=complete_kkt(meta,a,z,pi,rc,D,R,Path(out_dir)/'kkt',contract)
    return dict(gate='A1_A2_KKT_AND_BUDGETS',passed=bool(kkt['independent_kkt_pass']),row_fail_count=kkt['row_fail_count'],column_fail_count=kkt['column_fail_count'],stationarity_fail_count=kkt['stationarity_fail_count'],dual_sign_fail_count=kkt['dual_sign_fail_count'],relative_gap=kkt['relative_gap'],primal_objective=kkt['primal_objective'],dual_objective_numeric=kkt['dual_objective_numeric'],stationarity_normalized_max=kkt['stationarity_normalized_max'],complementarity_l1=kkt['complementarity_l1'],scale=dict(num_col=meta['num_col'],num_row=meta['num_row'],nnz=meta['nnz']))

def gate_a3_a5_physics(n):
    """A3 physical equations + A5 FOM counted once (objective reconciliation) on the solved network."""
    from validation_dynamics import dynamic_checks
    rows,details=dynamic_checks(n)
    failed=[r for r in rows if r['Status']!='PASS']
    fom=next((r for r in rows if r['Check']=='OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE'),None)
    return dict(gate='A3_PHYSICS',passed=not failed,checks=len(rows),failed=[dict(check=r['Check'],residual=r['MaxAbsoluteResidual']) for r in failed][:20],details=details),dict(gate='A5_FOM_ONCE',passed=bool(fom and fom['Status']=='PASS'),reconciliation=details['objective_reconciliation'],known_constants=dict(existing_asset_fom=float(n.meta.get('existing_annual_fixed_om_eur',0.)),existing_cross_border_fom=float(n.meta.get('existing_cross_border_fom_eur',0.))))

def gate_a4_readback(n,path):
    from netcdf_readback import netcdf_readback
    try:back,info=netcdf_readback(n,path);ok=True;err=None
    except Exception as e:ok=False;err=str(e)[:500];info={}
    return dict(gate='A4_NETCDF_READBACK',passed=ok,error=err,file=str(path),sha256=sha(path),**info)

def gate_a6_binding(receipt,lp_meta,network_sha_before):
    ok=receipt['lp']['num_col']==lp_meta['num_col'] and receipt['lp']['num_row']==lp_meta['num_row'] and receipt['lp']['nnz']==lp_meta['nnz'] and receipt['input_network']['sha256']==network_sha_before
    return dict(gate='A6_SCALE_BINDING',passed=bool(ok),lp=receipt['lp'],input_network_sha256=receipt['input_network']['sha256'])

# ------------------------------------------------------------------ group B
def gate_b1_country_net_zero(n):
    from country_carbon import emission_report
    rep=emission_report(n);cfg=n.meta['research_carbon'];rows={}
    ok=True
    for c in sorted(COUNTRIES):
        cap=float(cfg['country_cap_tco2'][c]);level=rep['store_final_level'][c];tol=1e-3+1e-7*max(1.,abs(cap))
        within=level<=cap+tol if cfg['constraint_scope']=='per_country' else True
        rows[c]=dict(final_level_tco2=level,cap_tco2=cap,within_cap=bool(within),sum_of_ports_tco2=rep['by_country'].get(c,0.))
        ok&=bool(within)
    if cfg['constraint_scope']=='asean_total':ok&=rep['asean_total']<=float(cfg['asean_total_cap_tco2'])+1e-3
    ok&=bool(rep['every_tonne_booked_once'])
    return dict(gate='B1_COUNTRY_NET_ZERO',passed=bool(ok),scope=cfg['constraint_scope'],countries=rows,every_tonne_booked_once=rep['every_tonne_booked_once'],by_country_source=rep['by_country_source'],asean_total_tco2=rep['asean_total'],scope_note='only the emission sources built in S1 (existing fossil power, OCGT/CCGT, SMR, SMR CC)')

def _flatten(d,prefix=''):
    out={}
    for k,v in d.items():
        key=prefix+'.'+str(k) if prefix else str(k)
        if isinstance(v,dict):out.update(_flatten(v,key))
        else:out[key]=v
    return out

def gate_b5_single_switch(cfg_int,cfg_dis,n_dis_solved=None,n_int_solved=None):
    a=_flatten(cfg_int);b=_flatten(cfg_dis);diff=sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
    allowed={'research.scenario'}|{'research.cross_border.'+k for k in ['electricity','H2','gas','co2']}
    only_switch=set(diff)<=allowed and len(diff)>0
    out=dict(gate='B5_SINGLE_SWITCH_AND_DISCONNECTED_ZERO',config_differences=diff,differences_within_switch_set=bool(only_switch))
    if n_dis_solved is not None:
        n=n_dis_solved
        xb_lines=n.lines[n.lines.border_class=='cross_border'];xb_links=n.links[n.links.border_class=='cross_border']
        cap=float(xb_lines.s_nom_opt.sum()+xb_links.p_nom_opt.sum()) if len(xb_lines)+len(xb_links) else 0.
        flow=float(sum(n.lines_t.p0[x].abs().sum() for x in xb_lines.index if x in n.lines_t.p0)+sum(n.links_t.p0[x].abs().sum() for x in xb_links.index if x in n.links_t.p0)) if len(xb_lines)+len(xb_links) else 0.
        out.update(disconnected_cross_border_components=int(len(xb_lines)+len(xb_links)),disconnected_cross_border_capacity_mw=cap,disconnected_cross_border_abs_flow_mw=flow)
        only_switch&=(len(xb_lines)+len(xb_links)==0 and cap==0. and flow==0.)
    if n_int_solved is not None:
        n=n_int_solved;xb_lines=n.lines[n.lines.border_class=='cross_border'];xb_links=n.links[n.links.border_class=='cross_border']
        out.update(integrated_cross_border_components=int(len(xb_lines)+len(xb_links)),integrated_cross_border_capacity_mw=float(xb_lines.s_nom_opt.sum()+xb_links.p_nom_opt.sum()))
    out['passed']=bool(only_switch);return out

def gate_b6_cost(obj_int,obj_dis,label_int='integrated',label_dis='disconnected'):
    ok=obj_int<=obj_dis*(1+1e-9)+1e-3
    return dict(gate='B6_INTEGRATED_COST_NOT_ABOVE_DISCONNECTED',passed=bool(ok),objective={label_int:obj_int,label_dis:obj_dis},difference=obj_dis-obj_int,relative=(obj_dis-obj_int)/max(1.,abs(obj_dis)),note='objectives include the fixed-at-1 FOM constants (existing assets, existing cross-border capacity); sunk CAPEX of existing capacity is excluded in both by the PyPSA objective constant')

def gate_b11_completeness(n,cfg):
    from build_research_network import REQUIRED_PER_NODE
    R=cfg['research'];geo=n.buses[n.buses.carrier.isin(['AC','DC'])]
    b2b=n.links[n.links.carrier=='B2B'];coupled=set(b2b.bus0)|set(b2b.bus1)
    smr_allowed=set(R['nuclear']['smr']['allowed_countries']);pwr_allowed=set(R['nuclear']['large_pwr']['allowed_countries'])
    missing=[];present={}
    loc=n.buses.location.where(n.buses.location.fillna('')!='',pd.Series(n.buses.index,index=n.buses.index)) if 'location' in n.buses else pd.Series(n.buses.index,index=n.buses.index)
    for typ,carriers in REQUIRED_PER_NODE.items():
        df=n.df(typ)
        for carrier in carriers+(['nuclear'] if typ=='Generator' else []):
            if typ=='Link':ports=set(df.bus0[df.carrier==carrier])|set(df.bus1[df.carrier==carrier])
            else:ports=set(df.bus[df.carrier==carrier])
            buses={loc.get(b,b) for b in ports};present[typ+':'+carrier]=int(len(buses))
            for node in geo.index:
                if node in coupled or node in buses:continue
                if carrier in ('solar','onwind'):continue
                if carrier=='nuclear SMR' and geo.at[node,'country'] not in smr_allowed:continue
                if carrier=='nuclear' and geo.at[node,'country'] not in pwr_allowed:continue
                missing.append(dict(component=typ,carrier=carrier,node=node))
    pending=[]
    for typ in ['Generator','StorageUnit','Link','Store']:
        df=n.df(typ)
        if 's1_candidate_status' in df:
            for k,z in df[df.s1_candidate_status=='DATA_PENDING'].iterrows():pending.append(dict(component=typ,name=k,carrier=str(z.carrier),country=str(z.country)))
    by=pd.Series([p['carrier'] for p in pending]).value_counts().to_dict() if pending else {}
    return dict(gate='B11_TECHNOLOGY_PATH_COMPLETENESS',passed=not missing,present_nodes_by_carrier=present,missing=missing[:50],missing_count=len(missing),data_pending_count=len(pending),data_pending_by_carrier=by,data_pending=pending,scope_note='only the technologies built in S1; biomass power, gas CCS, floating offshore, CO2/gas networks are later steps')

def gate_b12_hash(n,cfg,network_path=None,receipt=None):
    R=cfg['research'];expected=config_sha(R);actual=n.meta.get('research_config_sha256')
    checks=dict(research_config_sha256_matches=actual==expected,scenario_tag_matches=n.meta.get('scenario')==R['scenario'],switch_metadata_matches=n.meta.get('research_cross_border',{}).get('switches')=={k:bool(v) for k,v in R['cross_border'].items()},skeleton_flag=n.meta.get('skeleton_status')=='INTERIM_S1_SKELETON')
    if network_path is not None and receipt is not None:checks['network_file_sha256_matches_receipt']=sha(network_path)==receipt['network']['sha256']
    return dict(gate='B12_CONFIG_SWITCH_HASH_CONSISTENCY',passed=all(checks.values()),checks=checks,research_config_sha256=expected)

# ------------------------------------------------------------------ outputs
CAPACITY_VARS=[('Generator-p_nom','Generator','p_nom'),('Link-p_nom','Link','p_nom'),('Line-s_nom','Line','s_nom'),('StorageUnit-p_nom','StorageUnit','p_nom'),('Store-e_nom','Store','e_nom')]

def capacity_reduced_costs(n,m,rc_by_label):
    rows=[]
    for var,typ,nom in CAPACITY_VARS:
        if var not in m.variables:continue
        labels=m.variables[var].labels.to_series();df=n.df(typ)
        for name,label in labels.items():
            if label<0:continue
            z=df.loc[name]
            rows.append(dict(variable=var,component_type=typ,component=name,carrier=str(z.carrier),country=str(z.get('country','')),reduced_cost=float(rc_by_label.get(int(label),np.nan)),optimal=float(z[nom+'_opt']),lower=float(z[nom+'_min']),upper=float(z[nom+'_max']),capital_cost=float(z.capital_cost),status=str(z.get('s1_candidate_status','')),border_class=str(z.get('border_class',''))))
    return pd.DataFrame(rows)

def nodal_prices(n):
    mp=n.buses_t.marginal_price;w=n.snapshot_weightings.objective
    rows=[]
    for bus in mp.columns:
        z=n.buses.loc[bus];v=mp[bus]
        rows.append(dict(bus=bus,carrier=str(z.carrier),country=str(z.get('country','')),time_weighted_mean=float((v*w).sum()/w.sum()),minimum=float(v.min()),maximum=float(v.max())))
    return pd.DataFrame(rows),mp

def cross_border_flows(n):
    rows=[];w=n.snapshot_weightings.objective
    for typ,nom in [('Line','s_nom'),('Link','p_nom')]:
        df=n.df(typ)
        if not len(df) or 'border_class' not in df:continue
        for name,z in df[df.border_class=='cross_border'].iterrows():
            p0=n.pnl(typ).p0[name]
            rows.append(dict(component_type=typ,component=name,carrier=str(z.carrier),transport_carrier=str(z.transport_carrier),bus0=z.bus0,bus1=z.bus1,country0=str(n.buses.at[z.bus0,'country']),country1=str(n.buses.at[z.bus1,'country']),capacity_opt_mw=float(z[nom+'_opt']),capacity_initial_mw=float(z[nom]),energy_0_to_1_mwh=float((p0.clip(lower=0)*w).sum()),energy_1_to_0_mwh=float((-p0.clip(upper=0)*w).sum()),max_abs_flow_mw=float(p0.abs().max())))
    return pd.DataFrame(rows)
