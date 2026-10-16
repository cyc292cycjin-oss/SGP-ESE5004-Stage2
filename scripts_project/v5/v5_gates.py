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
    Path(out_dir).mkdir(parents=True,exist_ok=True);(Path(out_dir)/'kkt_summary.json').write_text(json.dumps({k:(float(v) if isinstance(v,(np.floating,)) else v) for k,v in kkt.items()},default=str))
    return dict(gate='A1_A2_KKT_AND_BUDGETS',passed=bool(kkt['independent_kkt_pass']),row_fail_count=kkt['row_fail_count'],column_fail_count=kkt['column_fail_count'],stationarity_fail_count=kkt['stationarity_fail_count'],dual_sign_fail_count=kkt['dual_sign_fail_count'],relative_gap=kkt['relative_gap'],primal_objective=kkt['primal_objective'],dual_objective_numeric=kkt['dual_objective_numeric'],stationarity_normalized_max=kkt['stationarity_normalized_max'],complementarity_l1=kkt['complementarity_l1'],scale=dict(num_col=meta['num_col'],num_row=meta['num_row'],nnz=meta['nnz']))

def gate_a1_a2_interior(lp_dir,sol_dir,out_dir,contract,barconvtol,gap_factor=10.,dual_factor=100.):
    """S3B R4 (decision 69): A1/A2 for barrier solutions without crossover. The frozen V4 algebra (complete_kkt, unchanged) supplies the
    original-unit residuals; the decision uses three criteria tied to BarConvTol:
      primal feasibility  - every row/column within the V4 physical budget 1e-3 + 1e-7 x reference, where 1e-7 = gap_factor x BarConvTol;
      dual feasibility    - stationarity_normalized_max and the normalized dual-sign error <= dual_factor x BarConvTol (= 1e-6, the V4 KKT budget
                            and Gurobi's default OptimalityTol);
      relative primal-dual gap <= gap_factor x BarConvTol (and complementarity_l1 / scale <= the same).
    Interior solutions may split degenerate alternatives across equal-cost options; this gate does not ask for a vertex."""
    kkt=gate_a1_a2_kkt(lp_dir,sol_dir,out_dir,contract)
    d=json.loads((Path(out_dir)/'kkt_summary.json').read_text()) if (Path(out_dir)/'kkt_summary.json').exists() else None
    gap_tol=gap_factor*barconvtol;dual_tol=dual_factor*barconvtol
    k=dict(kkt,**(d or {}))
    scale=max(1.,abs(k.get('primal_objective',0.)),abs(k.get('dual_objective_numeric',0.)))
    crit=dict(primal_rows_within_budget=k.get('row_fail_count',1)==0,primal_columns_within_budget=k.get('column_fail_count',1)==0,
              dual_stationarity=float(k.get('stationarity_normalized_max',1.))<=dual_tol and k.get('stationarity_fail_count',1)==0,
              dual_sign=float(k.get('dual_sign_normalized_max',1.))<=dual_tol,
              relative_gap=float(k.get('relative_gap',1.))<=gap_tol,
              complementarity=float(k.get('complementarity_l1',scale))/scale<=gap_tol)
    return dict(gate='A1_A2_INTERIOR_POINT',passed=bool(all(crit.values())),criteria=crit,thresholds=dict(barconvtol=barconvtol,relative_gap=gap_tol,complementarity_over_scale=gap_tol,
                dual_normalized=dual_tol,primal='1e-3 + 1e-7 x reference (V4 budget; 1e-7 = %g x BarConvTol)'%gap_factor),
                metrics={kk:k.get(kk) for kk in ['row_violation_max','column_violation_max','row_fail_count','column_fail_count','stationarity_normalized_max','stationarity_fail_count',
                                                  'dual_sign_normalized_max','dual_sign_fail_count','relative_gap','complementarity_l1','primal_objective','dual_objective_numeric']},
                v4_independent_kkt_pass=k.get('independent_kkt_pass'),note='interior solution: degenerate equal-cost alternatives may be split across options')

def gate_a3_a5_physics(n,known_terms=None,ignore_checks=()):
    """A3 physical equations + A5 FOM counted once (objective reconciliation) on the solved network.
    known_terms (R7, diagnostic runs only): {label: EUR} objective terms added by hooks (gap slack x penalty) counted as known constants;
    ignore_checks: check names that are expected to fail in a diagnostic run (per-country CO2 caps replaced by slack) and are reported separately."""
    from validation_dynamics import dynamic_checks
    extra=float(sum((known_terms or {}).values()))
    rows,details=dynamic_checks(n,extra_known_objective=extra,extra_known_label=';'.join(known_terms or {}))
    failed=[r for r in rows if r['Status']!='PASS' and not any(r['Check'].startswith(p) for p in ignore_checks)]
    diagnostic=[r for r in rows if r['Status']!='PASS' and any(r['Check'].startswith(p) for p in ignore_checks)]
    fom=next((r for r in rows if r['Check']=='OBJECTIVE_RECONCILIATION_KNOWN_FOM_ONCE'),None)
    details=dict(details,known_terms=known_terms or {},diagnostic_expected_failures=[dict(check=r['Check'],residual=r['MaxAbsoluteResidual']) for r in diagnostic])
    return dict(gate='A3_PHYSICS',passed=not failed,checks=len(rows),failed=[dict(check=r['Check'],residual=r['MaxAbsoluteResidual']) for r in failed][:20],details=details),dict(gate='A5_FOM_ONCE',passed=bool(fom and fom['Status']=='PASS'),reconciliation=details['objective_reconciliation'],known_constants=dict(existing_asset_fom=float(n.meta.get('existing_annual_fixed_om_eur',0.)),existing_cross_border_fom=float(n.meta.get('existing_cross_border_fom_eur',0.)),**(known_terms or {})))

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
    # S3-6: B1 covers fuels and imports - every import/production generator carrier has zero CO2 intensity (U4), the S3 fuel ports are national atmosphere ports
    imp=[c for c in IMPORT_CARRIERS if c in n.carriers.index];imp_zero=bool((n.carriers.loc[imp,'co2_emissions'].fillna(0.)==0).all()) if imp else True
    L=n.links;atmo_cols=[c for c in L if c.startswith('bus') and c[3:].isdigit() and c!='bus0']
    port_carriers=sorted(set(L.carrier[L[atmo_cols].apply(lambda col:col.astype(str).str.startswith('co2 atmosphere')).any(axis=1)]))
    s3_ports={k:(k in port_carriers) for k in ['gas production delivery','Fischer-Tropsch','methanolisation','shipping methanol','industry methanol','OCGT methanol','BtL','biomass-to-methanol']}
    ok&=imp_zero
    return dict(gate='B1_COUNTRY_NET_ZERO',passed=bool(ok),s3_scope=dict(import_carriers_zero_co2=imp_zero,import_carriers=imp,atmosphere_port_carriers=port_carriers,s3_fuel_ports_present=s3_ports,fuel_carbon_mode=n.meta.get('research_fuel_carbon',{}).get('mode')),scope=cfg['constraint_scope'],countries=rows,every_tonne_booked_once=rep['every_tonne_booked_once'],by_country_source=rep['by_country_source'],asean_total_tco2=rep['asean_total'],scope_note='only the emission sources built in S1 (existing fossil power, OCGT/CCGT, SMR, SMR CC)')

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
    import copy
    R=copy.deepcopy(cfg['research']);overrides=list(n.meta.get('research_config',{}).get('config_overrides',[]))
    for ov in overrides:  # S3-6: sensitivity builds record their --override list; the expected hash is the file config with the same overrides applied (s2_network.py)
        key,val=ov.split('=',1);d=R;parts=key.split('.')
        for k in parts[:-1]:d=d[k]
        old=d[parts[-1]];d[parts[-1]]=type(old)(val) if not isinstance(old,bool) else (val.lower() in ('1','true','yes'))
    if 'config_overrides' in n.meta.get('research_config',{}):R['config_overrides']=overrides  # S3 builds carry the key (possibly empty); S1/S2 networks do not
    expected=config_sha(R);actual=n.meta.get('research_config_sha256')
    allowed_status={'INTERIM_S1_SKELETON',R.get('s2',{}).get('status')}
    checks=dict(research_config_sha256_matches=actual==expected,scenario_tag_matches=n.meta.get('scenario')==R['scenario'],switch_metadata_matches=n.meta.get('research_cross_border',{}).get('switches')=={k:bool(v) for k,v in R['cross_border'].items()},skeleton_flag=n.meta.get('skeleton_status') in allowed_status)
    if network_path is not None and receipt is not None:checks['network_file_sha256_matches_receipt']=sha(network_path)==receipt['network']['sha256']
    # R4 (decision 58): register the snapshot weightings (sum must be 8760 h for any horizon; the three columns must agree)
    w=n.snapshot_weightings;wsum={c:float(w[c].sum()) for c in w.columns}
    research_horizon=len(n.snapshots)>1  # synthetic single-snapshot test networks are exempt; research networks (full year or R4 representative weights) must sum to 8760 h
    checks['weights_sum_8760_h']=(not research_horizon) or all(abs(v-8760.)<1e-6 for v in wsum.values());checks['weights_columns_agree']=bool((w.nunique(axis=1)==1).all())
    weights=dict(snapshots=int(len(n.snapshots)),sums_h=wsum,unique_values={c:sorted(set(float(x) for x in w[c].unique())) for c in w.columns},
                 sha256=hashlib.sha256(np.ascontiguousarray(w.to_numpy(dtype='<f8')).tobytes()).hexdigest(),representative=n.meta.get('representative_weights'))
    s3=n.meta.get('research_config',{}).get('s3',{});ind=n.meta.get('research_config',{}).get('s2',{}).get('industry',{})
    s3_switches=dict(fuel_carbon_mode=s3.get('fuel_carbon_mode'),import_price_sensitivity=(s3.get('imports') or {}).get('price_sensitivity'),cross_border_gas=n.meta.get('research_config',{}).get('cross_border',{}).get('gas'),
                     ammonia_methanol_mode=ind.get('ammonia_methanol_mode'),industry_ratio_source=ind.get('ratio_source'),config_overrides=overrides,
                     demand_growth_method=(n.meta.get('research_config',{}).get('demand',{}).get('growth_method') or 'level (key absent: built before S3B R1)'),
                     industry_other_bucket=((s3.get('industry') or {}).get('other_bucket') or 'pypsa_eur_2050 (key absent: built before S3B R2)'),
                     lng_expansion=((s3.get('gas') or {}).get('lng_expansion') or 'cap_factor (key absent: built before S3B R3)'),
                     renewable_profile_variant=((n.meta.get('research_config',{}).get('renewable') or {}).get('profile_variant') or 'original (key absent: built before S4A-1)'),
                     renewable_resource_classes=((n.meta.get('research_config',{}).get('renewable') or {}).get('resource_classes') or 1))
    checks['s3_switches_recorded']=(not s3) or all(v is not None for k,v in s3_switches.items() if k!='config_overrides')  # S1/S2 networks without an s3 config section are exempt
    return dict(gate='B12_CONFIG_SWITCH_HASH_CONSISTENCY',passed=all(checks.values()),checks=checks,research_config_sha256=expected,s3_switches=s3_switches,snapshot_weightings=weights)

# ------------------------------------------------------------------ group B, S2 additions
def gate_b2_storage_cap(n):
    """B2: final level of every national co2 sequestered Store <= cap x horizon fraction; stores charge-only."""
    cfg=n.meta.get('research_co2_storage',{});frac=float(cfg.get('horizon_fraction',1.));rows={};ok=True;w=n.snapshot_weightings.stores
    for c,cap in cfg.get('caps_t_per_year',{}).items():
        sb=f'co2 sequestered {c}'
        if sb not in n.stores.index:rows[c]=dict(cap_t=0.,store=None,within=True);continue
        level=float(n.stores_t.e[sb].iloc[-1]);limit=float(cap)*frac;p=n.stores_t.p[sb]
        charge_only=bool((p<=1e-6).all())  # Store p>0 would be a withdrawal
        within=level<=limit*(1+1e-9)+1e-3
        rows[c]=dict(cap_t_per_year=float(cap),horizon_limit_t=limit,final_level_t=level,utilisation=(level/limit if limit else None),within_cap=bool(within),charge_only=charge_only)
        ok&=bool(within and charge_only)
    return dict(gate='B2_STORAGE_CAP',passed=bool(ok),horizon_fraction=frac,countries=rows)

def gate_b3_biomass(n):
    """B3: every finite biomass pool is used within its potential and never refilled."""
    rows=[];ok=True
    if 'research_role' in n.stores:
        for name,z in n.stores[n.stores.research_role=='FINITE_RESOURCE'].iterrows():
            e=n.stores_t.e[name];used=float(z.e_initial-e.iloc[-1]);refill=bool((n.stores_t.p[name]<-1e-6).any())
            within=used<=float(z.e_nom)*(1+1e-9)+1e-3 and float(e.min())>=-1e-3
            rows.append(dict(store=name,country=str(z.country),category=str(z.get('s2_category','')),potential_mwh=float(z.e_nom),used_mwh=used,share_used=(used/float(z.e_nom) if z.e_nom else None),within=bool(within),refilled=refill))
            ok&=bool(within and not refill)
    by_country={}
    for r in rows:by_country.setdefault(r['country'],dict(potential_mwh=0.,used_mwh=0.));by_country[r['country']]['potential_mwh']+=r['potential_mwh'];by_country[r['country']]['used_mwh']+=r['used_mwh']
    return dict(gate='B3_BIOMASS_WITHIN_POTENTIAL',passed=bool(ok),stores=len(rows),by_country=by_country,rows=rows)

def gate_b8_demand_consistency(n):
    """B8: every Load owned once; S2 loads conserve the demand table (sum over nodes = country value x horizon); Astar deductions recorded."""
    owners=n.meta.get('demand_owners',{});led=n.meta.get('s2_demand_ledger',{});w=n.snapshot_weightings.generators;frac=float(w.sum()/8760.)
    pset=n.get_switchable_as_dense('Load','p_set');annual=(pset.mul(w,axis=0)).sum()
    checks=dict(every_load_owned=set(owners)==set(n.loads.index),no_duplicate_owner_names=len(owners)==len(n.loads.index))
    by_sector={}
    for name,z in n.loads.iterrows():
        if z.get('demand_owner_kind')=='S2_DEMAND_TABLE':by_sector[str(z.sector)]=by_sector.get(str(z.sector),0.)+float(annual.get(name,0.))
    expected={k:float(v)*frac for k,v in led.get('totals_by_sector_mwh',{}).items() if k!='ProcessEmissions'}
    diffs={k:dict(expected_mwh=v,actual_mwh=by_sector.get(k,0.),rel=(by_sector.get(k,0.)/v-1 if v else None)) for k,v in expected.items()}
    checks['s2_sector_totals_conserved']=all(abs(d['rel'] or 0.)<1e-6 for d in diffs.values())
    neg=bool((pset.values<-1e-9).any());checks['no_negative_loads']=not neg
    dedu=led.get('deductions',[]);checks['astar_deductions_recorded']=isinstance(dedu,list)
    return dict(gate='B8_DEMAND_CONSISTENCY',passed=all(checks.values()),checks=checks,sector_totals=diffs,horizon_fraction=frac,deductions=dedu,deferred=led.get('deferred',[]))

def gate_b11_supply_routes(n,cfg,min_routes=2):
    """B11 (S2, R7): every end-use bus type at every LOAD-BEARING node has at least two supply routes; auxiliary nodes without loads are listed, not failed; DATA_PENDING candidates listed."""
    rows=[];ok=True
    geo=[b for b in n.buses.index if n.buses.at[b,'carrier'] in ('AC','DC')];geo_sorted=sorted(geo,key=len,reverse=True)
    def node_of(bus):
        # the node is the geographical bus the carrier bus is named after ('<node> gas'); the location attribute is a fallback only
        # (converter-node buses carry the location of the co-located AC node, which would hide the auxiliary node)
        if bus in geo:return bus
        pref=next((g for g in geo_sorted if str(bus).startswith(g+' ')),None)
        if pref is not None:return pref
        loc=str(n.buses.at[bus,'location']) if 'location' in n.buses and bus in n.buses.index else ''
        return loc if loc in geo else None
    load_nodes={node_of(b) for b in n.loads.bus}-{None}
    port_cols=[c for c in n.links if c.startswith('bus') and c[3:].isdigit() and c!='bus0']
    def serves_demand(bus):
        """A load-bearing end-use bus has a Load on it or on a bus it feeds directly (one conversion hop); otherwise it is auxiliary."""
        if bool((n.loads.bus==bus).any()):return True
        down=set()
        for col in port_cols:down|=set(n.links.loc[n.links.bus0==bus,col].astype(str))
        down.discard('')
        return bool(n.loads.bus.isin(down).any())
    def suppliers(bus):
        s=set(n.generators.index[n.generators.bus==bus])
        for col in [c for c in n.links if c.startswith('bus') and c[3:].isdigit() and c!='bus0']:
            eff='efficiency' if col=='bus1' else 'efficiency'+col[3:]
            s|=set(n.links.index[(n.links[col]==bus)&(n.links[eff]>0)]) if eff in n.links else set()
        s|=set(n.links.index[(n.links.bus0==bus)&(n.links.p_min_pu<0)])  # bidirectional pipelines
        s|=set(n.stores.index[n.stores.bus==bus])
        twin=str(bus)[:-4]+' oil non-fossil' if str(bus).endswith(' oil') else None  # S3-5: the fossil and non-fossil node oil buses feed the same loads
        if twin and twin in n.buses.index:
            s|=set(n.generators.index[n.generators.bus==twin])|set(n.links.index[(n.links.bus1==twin)&(n.links.efficiency>0)])|set(n.links.index[(n.links.bus0==twin)&(n.links.p_min_pu<0)])
        return s
    carriers={'AC':'electricity','industry heat':'industrial low-temperature heat','clean cooking useful':'clean cooking','oil':'oil (fossil pool + non-fossil pool: FT, BtL, imports)','gas':'gas (LNG, production, pipelines, biogas upgrading)','H2':'hydrogen','ammonia':'ammonia (Haber-Bosch, import)','methanol':'methanol (methanolisation, biomass-to-methanol, import)','co2 stored':'captured CO2 handling','EV battery':'land transport EV'}
    for carrier,label in carriers.items():
        buses=n.buses.index[n.buses.carrier==('Li ion' if carrier=='EV battery' else carrier)]
        with_load=[b for b in buses if (node_of(b) in load_nodes or str(n.buses.at[b,'country'])=='ASEAN') and serves_demand(b)];aux=[b for b in buses if b not in with_load]  # S3-6: regional pools with loads are load-bearing
        short=[b for b in with_load if len(suppliers(b))<min_routes];short_aux=[b for b in aux if len(suppliers(b))<min_routes]
        rows.append(dict(end_use=label,carrier=carrier,buses=int(len(buses)),load_bearing_buses=len(with_load),buses_with_fewer_than_min_routes=short[:10],count_short=len(short),
                         auxiliary_nodes_without_loads=aux[:10],auxiliary_count=len(aux),auxiliary_short=short_aux[:10]))
        ok&=len(short)==0 or carrier in ('EV battery','co2 stored')  # single charger / single buffer are by design
    pending=[]
    for typ in ['Generator','StorageUnit','Link','Store']:
        df=n.df(typ)
        if 's1_candidate_status' in df:
            for k,z in df[df.s1_candidate_status=='DATA_PENDING'].iterrows():pending.append(dict(component=typ,name=k,carrier=str(z.carrier),country=str(z.country)))
    return dict(gate='B11_SUPPLY_ROUTES_PER_END_USE',passed=bool(ok),rows=rows,data_pending_count=len(pending),data_pending_by_carrier=pd.Series([p['carrier'] for p in pending]).value_counts().to_dict() if pending else {})

# ------------------------------------------------------------------ group B, S3 additions (S3-6)
IMPORT_CARRIERS=('LNG import','oil import','ammonia import','methanol import','FT fuel import','H2 import','gas production')
POOL_BUSES=('ASEAN oil','ASEAN oil non-fossil','ASEAN ammonia','ASEAN methanol')

def gate_b13_imports_one_way(n):
    """B13: every extra-ASEAN supply is a one-way Generator (sign +1, p_min_pu >= 0); the regional pools carry only nationally owned loads and
    links whose other ports are model buses; pool stores are cyclic (no sink that could absorb energy as an export)."""
    g=n.generators;imp=g[g.carrier.isin([c for c in IMPORT_CARRIERS if c!='gas production'])]
    checks=dict(import_generators=int(len(imp)),all_sign_positive=bool((imp.sign>0).all()) if len(imp) else True,all_p_min_pu_nonneg=bool((imp.p_min_pu>=0).all()) if len(imp) else True,
                import_links_or_lines=int(n.links.carrier.str.contains('import',case=False).sum()+n.lines.carrier.astype(str).str.contains('import',case=False).sum()))
    pools=[b for b in POOL_BUSES if b in n.buses.index]
    foreign=[l for l in n.loads.index[n.loads.bus.isin(pools)] if ('country' not in n.loads) or str(n.loads.at[l,'country']) not in COUNTRIES]
    checks['pool_loads']=int(n.loads.bus.isin(pools).sum());checks['pool_loads_without_national_owner']=foreign[:10]
    L=n.links;port_cols=[c for c in L if c.startswith('bus') and c[3:].isdigit()];bad=[]
    for name,z in L[L[port_cols].isin(pools).any(axis=1)].iterrows():
        others=[z[c] for c in port_cols if z[c] and z[c] not in pools]
        if not others or any(b not in n.buses.index for b in others):bad.append(name)
    checks['pool_links_without_national_port']=bad[:10]
    st=n.stores[n.stores.bus.isin(pools)];checks['pool_stores_cyclic']=bool(st.e_cyclic.all()) if len(st) else True
    passed=checks['all_sign_positive'] and checks['all_p_min_pu_nonneg'] and checks['import_links_or_lines']==0 and not foreign and not bad and checks['pool_stores_cyclic']
    return dict(gate='B13_IMPORTS_ONE_WAY',passed=bool(passed),checks=checks)

def gate_b14_terminal_caps(n,cap_factor=2.5):
    """B14: LNG regasification capacity within the registered rule. research.s3.gas.lng_expansion (build ledger) = existing_only (S3B R3 main):
    p_nom_max = existing (operating + under construction), proposed-only sites not built; cap_factor (S3-1 rule, sensitivity): <= cap_factor x existing,
    proposed-only sites <= their proposed capacity. Liquid-H2 imports at a node <= the terminal rule cap of that node (h2_import_cap_mw, S3-2; older
    ledgers: the LNG p_nom_max), and in solved networks p_nom_opt <= p_nom_max."""
    g=n.generators;rows=[];ok=True;lng=g[g.carrier=='LNG import']
    L=n.meta.get('research_gas_network',{}).get('lng',{});led=L.get('terminals',{});mode=L.get('expansion','cap_factor');cap_factor=float(L.get('cap_factor',cap_factor))
    def h2_check(node,h2cap):
        h2=g[(g.carrier=='H2 import')&(g.bus==node+' H2')]
        h2_ok=bool((h2.p_nom_max<=h2cap*(1+1e-9)+1e-6).all()) if len(h2) else True
        h2_within=bool((h2.p_nom_opt<=h2.p_nom_max*(1+1e-9)+1e-6).all()) if (len(h2) and 'p_nom_opt' in g) else True
        return len(h2),bool(h2_ok and h2_within)
    for name,z in lng.iterrows():
        existing=float(z.p_nom);pmax=float(z.p_nom_max);opt=float(z.p_nom_opt) if 'p_nom_opt' in g else 0.;node=str(z.bus)[:-4]
        proposed=float(led.get(node,{}).get('proposed_mw',0.))
        limit=existing if mode=='existing_only' else (cap_factor*existing if existing>0 else proposed)
        limit_ok=pmax<=limit*(1+1e-9)+1e-6
        within=opt<=pmax*(1+1e-9)+1e-6
        _,h2_ok=h2_check(node,float(led.get(node,{}).get('h2_import_cap_mw',pmax)))
        rows.append(dict(generator=name,existing_mw=existing,proposed_mw=proposed,p_nom_max_mw=pmax,p_nom_opt_mw=opt,ratio_to_existing=(pmax/existing if existing else None),limit_ok=bool(limit_ok),within_max=bool(within),h2_import_within_lng_cap=h2_ok))
        ok&=bool(limit_ok and within and h2_ok)
    for node,t in led.items():   # S3B R3: H2 import at proposed-only sites without an LNG generator (existing_only mode)
        if f'{node} LNG import' in lng.index:continue
        k,h2_ok=h2_check(node,float(t.get('h2_import_cap_mw',0.)))
        if not k:continue
        rows.append(dict(generator=None,node=node,existing_mw=float(t.get('existing_mw',0.)),proposed_mw=float(t.get('proposed_mw',0.)),p_nom_max_mw=0.,p_nom_opt_mw=0.,ratio_to_existing=None,limit_ok=True,within_max=True,h2_import_within_lng_cap=h2_ok))
        ok&=h2_ok
    return dict(gate='B14_TERMINAL_CAP_2_5X',passed=bool(ok),cap_factor=cap_factor,expansion=mode,terminals=rows)

def gate_b15_domestic_production_caps(n):
    """B15: every domestic gas production generator carries an annual cap (meta external_annual_caps -> ResearchImportAnnual constraints through the
    install_fragment_constraints hook) and, in solved networks, its annual energy stays within the cap; caps sum to the UNSD 2019 production per country."""
    g=n.generators;prod=g[g.carrier=='gas production'];caps=n.meta.get('external_annual_caps',{});w=n.snapshot_weightings.generators;rows=[];ok=True
    hook_ok='install_fragment_constraints' in n.meta.get('required_constraint_hooks',[])
    solved='p' in n.generators_t and len(n.generators_t.p.columns)>0
    for name in prod.index:
        cap=caps.get(name);energy=float((n.generators_t.p[name]*w).sum()) if (solved and name in n.generators_t.p) else None
        within=(energy<=float(cap)*(1+1e-6)+1e-3) if (cap is not None and energy is not None) else (cap is not None)
        rows.append(dict(generator=name,country=str(g.at[name,'country']),cap_mwh=(float(cap) if cap is not None else None),annual_mwh=energy,within=bool(within)));ok&=bool(within)
    df=pd.DataFrame(rows)
    by_c={c:dict(cap_mwh=float(d.cap_mwh.sum()),annual_mwh=(float(d.annual_mwh.sum()) if solved else None),generators=int(len(d))) for c,d in df.groupby('country')} if len(df) else {}
    return dict(gate='B15_DOMESTIC_PRODUCTION_CAPS',passed=bool(ok and hook_ok),hook_registered=hook_ok,solved=bool(solved),generators=len(rows),by_country=by_c,short=[r for r in rows if not r['within']][:10])

def gate_b16_import_prices_identical(n_a,n_b,label_a='integrated',label_b='disconnected'):
    """B16: the import prices (marginal costs of the import and production generators) and the S3 switches are identical in the two scenarios."""
    rows={};ok=True
    for car in IMPORT_CARRIERS:
        a=n_a.generators[n_a.generators.carrier==car].marginal_cost.sort_index();b=n_b.generators[n_b.generators.carrier==car].marginal_cost
        same=(set(a.index)==set(b.index)) and (len(a)==0 or bool(np.allclose(a.values,b.reindex(a.index).values,rtol=1e-12,atol=1e-9)))
        rows[car]=dict(count={label_a:int(len(a)),label_b:int(len(b))},unique_prices={label_a:sorted(set(round(float(x),6) for x in a)),label_b:sorted(set(round(float(x),6) for x in b))},identical=bool(same));ok&=bool(same)
    sa=n_a.meta.get('research_config',{}).get('s3',{});sb=n_b.meta.get('research_config',{}).get('s3',{})
    same_sw=sa==sb;ok&=same_sw
    return dict(gate='B16_IMPORT_PRICES_IDENTICAL_ACROSS_SCENARIOS',passed=bool(ok),carriers=rows,s3_config_identical=bool(same_sw))

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
