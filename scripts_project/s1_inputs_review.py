"""S1-3 stock review and S1-6 corridor table. Read-only against every frozen file.

stock:     geothermal survival re-run with the S1 lifetime decision, Bataan exclusion
           evidence, hydro capacity comparison against the GEM raw tracker. Writes new
           files only; the frozen SELECTED_ASSET_SURVIVAL_2050.json is never modified.
corridors: research_inputs/corridors/cross_border_corridors.csv filled with the 24
           existing cross-border electricity edges read from the frozen electric base.
"""
from pathlib import Path
from collections import defaultdict
import argparse,copy,hashlib,json,math
import pandas as pd

ASEAN={'Brunei':'BN','Cambodia':'KH','Indonesia':'ID','Laos':'LA','Malaysia':'MY','Myanmar':'MM','Philippines':'PH','Singapore':'SG','Thailand':'TH','Timor-Leste':'TL','East Timor':'TL','Vietnam':'VN'}
GEM_HYDRO_TYPES={'conventional storage':'Reservoir','run-of-river':'Run-Of-River','pumped storage':'Pumped Storage','conventional and run-of-river':'Reservoir+Run-Of-River (mixed)','unknown':'unknown'}
BATAAN_UNIT='GEM:G100000501234'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def numeric(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def rerun_geothermal(stock,decisions):
    """Unit-level re-selection for Geothermal only; mirrors unit_asset_survival/apply_selected_stock rules."""
    from asset_survival import select_asset
    from selected_closure import retirement_upper_bound
    d=decisions['technologies']['Geothermal']
    accepted=d.get('ApprovalStatus')=='HUMAN_ACCEPTED' and bool(d.get('DecisionReference')) and bool(d.get('Source'))
    if not accepted:raise ValueError('S1 geothermal lifetime decision is not accepted')
    out=copy.deepcopy(stock);transitions=[]
    for i,r in enumerate(out['unit_evidence']['records']):
        if r['Technology']!='Geothermal':continue
        u=dict(r,Lifetime=d['Lifetime'],LifetimeAccepted=True,LifetimeSource=d['Source'],LifetimeDecisionReference=d['DecisionReference'],LifetimeEvidenceGrade=d['EvidenceGrade'],LifetimeMethodID=d['MethodID'])
        for key in ['SurvivalStatus','RetainedCapacity2050','RetirementYear','RetirementDerivation','DecisionBasis','CommissioningUpperBound','RetirementUpperBound']:u.pop(key,None)
        if r.get('RetirementEvidenceVerified'):u['RetirementYear']=r['RetirementYear']
        u['RetainedCapacity2050']=None
        if r['SurvivalStatus']=='RETIREMENT_PROVEN_BY_COMMISSIONING_UPPER_BOUND':
            # Dated operating observation retained; the bound is re-evaluated with the new lifetime.
            bound=retirement_upper_bound(dict(u,SurvivalStatus='UNRESOLVED_COMMISSIONING'))
            chosen=bound if bound else select_asset(u)
        elif r['SurvivalStatus'].startswith('NOT_INHERITED') or r['SurvivalStatus']=='UNRESOLVED_UNIT_CAPACITY':
            chosen=dict(u,SurvivalStatus=r['SurvivalStatus'],RetainedCapacity2050=r['RetainedCapacity2050'])
        else:
            chosen=select_asset(u)
            if r.get('CapacityReconciliation')!='MATCHED_PARENT' and chosen['SurvivalStatus']=='SURVIVES_2050':
                chosen.update(SurvivalStatus='UNRESOLVED_PARENT_CAPACITY_RECONCILIATION',RetainedCapacity2050=None)
        if numeric(r.get('OriginalCapacity')):
            candidate=select_asset(dict(u,LifetimeAccepted=True))
            chosen.update(ConditionalSurvivalStatus=candidate['SurvivalStatus'],ConditionalRetainedMW=candidate['RetainedCapacity2050'],ConditionalCalculation='NOT_ACCEPTED_PRODUCTION_CAPACITY',ConditionalCapacityQualified=r.get('ConditionalCapacityQualified'))
        chosen['S1LifetimeRerun']=dict(PreviousLifetime=r.get('Lifetime'),PreviousStatus=r['SurvivalStatus'],PreviousRetainedMW=r.get('RetainedCapacity2050'))
        out['unit_evidence']['records'][i]=chosen
        transitions.append(dict(AssetID=r['AssetID'],Country=r['Country'],CapacityMW=r.get('OriginalCapacity'),CommissioningYear=r.get('CommissioningYear'),Before=r['SurvivalStatus'],After=chosen['SurvivalStatus'],RetainedMW2050=chosen.get('RetainedCapacity2050'),RetirementYear=chosen.get('RetirementYear'),SourceRow=r.get('SourceRow')))
    from collections import Counter
    out['unit_evidence']['status_counts']=dict(Counter(u['SurvivalStatus'] for u in out['unit_evidence']['records']))
    return out,transitions

def bataan_evidence(cache,stock):
    """Raw GEM nuclear tracker row for the Bataan unit; fields are copied, not interpreted beyond the exclusion rule."""
    path=Path(cache)/'Global-Nuclear-Power-Tracker-July-2024.xlsx'
    df=pd.read_excel(path,sheet_name='Data')
    row=df[df['GEM unit ID']==BATAAN_UNIT.split(':')[1]]
    if len(row)!=1:raise ValueError('Bataan GEM unit row not unique')
    r=row.iloc[0]
    fields=['Country/Area','Project Name','Unit Name','Capacity (MW)','Status','Reactor Type','Start Year','Retirement Year','Construction Start Date','First Criticality Date','First Grid Connection','Commercial Operation Date','Owner','GEM location ID','GEM unit ID','Wiki URL','Date Last Researched']
    raw={k:(None if pd.isna(r[k]) else (r[k].item() if hasattr(r[k],'item') else str(r[k]))) for k in fields}
    never_operated=str(raw['Status']).lower()!='operating' and raw['Start Year'] is None and raw['Commercial Operation Date'] is None and raw['First Grid Connection'] is None
    unit=next((u for u in stock['unit_evidence']['records'] if u['AssetID']==BATAAN_UNIT),None)
    return dict(AssetID=BATAAN_UNIT,RawSource=path.name,RawSourceSHA256=sha(path),RawRow=raw,
                FrozenStockStatus=unit['SurvivalStatus'] if unit else None,FrozenStockAssetClass=unit['AssetClass'] if unit else None,
                NeverCommerciallyOperated=bool(never_operated),
                S1Decision='EXCLUDED_NEVER_COMMERCIAL_OPERATION' if never_operated else 'REVIEW_REQUIRED',
                Rule='S1-3: exclude from existing stock when the GEM raw record shows no commercial operation (status not operating, no start year, no commercial operation date, no grid connection)')

def gem_hydro_by_country(cache):
    path=Path(cache)/'Global-Hydropower-Tracker-April-2025.xlsx'
    h=pd.read_excel(path,sheet_name='Data')
    h=h[h['Country/Area 1'].isin(ASEAN)|h['Country/Area 2'].isin(ASEAN)]
    op=h[h['Status'].str.lower()=='operating']
    tab=defaultdict(float);rows=0
    for _,r in op.iterrows():
        rows+=1
        for ccol,capcol in [('Country/Area 1','Country/Area 1 Capacity (MW)'),('Country/Area 2','Country/Area 2 Capacity (MW)')]:
            c=r[ccol]
            if c not in ASEAN:continue
            v=r[capcol]
            if pd.isna(v):
                if ccol=='Country/Area 1' and str(r['Binational']).lower()!='yes':v=r['Capacity (MW)']
                else:v=0.
            tab[(ASEAN[c],GEM_HYDRO_TYPES.get(str(r['Technology Type']).lower(),str(r['Technology Type'])))]+=float(v)
    return dict(RawSource=path.name,RawSourceSHA256=sha(path),OperatingRows=rows,ByCountryType={c+'|'+t:round(v,3) for (c,t),v in sorted(tab.items())})

def gem_geothermal_by_country(cache):
    path=Path(cache)/'Geothermal-Power-Tracker-March-2025-Final.xlsx'
    g=pd.read_excel(path,sheet_name='Data');g=g[g['Country/Area'].isin(ASEAN)]
    op=g[g['Status'].str.lower()=='operating']
    return dict(RawSource=path.name,RawSourceSHA256=sha(path),OperatingUnits=int(len(op)),OperatingMWByCountry={ASEAN[c]:round(float(v),3) for c,v in op.groupby('Country/Area')['Unit Capacity (MW)'].sum().items()})

def research_hydro_by_country(electric_base):
    import pypsa,logging
    logging.disable(logging.CRITICAL)
    n=pypsa.Network(str(electric_base));tab=defaultdict(float)
    for typ in ['Generator','StorageUnit']:
        df=n.df(typ)
        if 'hydro_subtype' not in df:continue
        ex=df[(df.get('asset_role','')=='existing_survivor')&df.hydro_subtype.fillna('').ne('')]
        for (c,s),v in ex.groupby(['country','hydro_subtype']).p_nom.sum().items():tab[(c,s)]+=float(v)
    return {c+'|'+s:round(v,3) for (c,s),v in sorted(tab.items())}

def stock(repo,electric_base,cache,output):
    repo=Path(repo);frozen=repo/'results_project/assembly_v1/final_assets/SELECTED_ASSET_SURVIVAL_2050.json'
    stock=json.loads(frozen.read_text());decisions=json.loads((repo/'research_inputs/asset_survival/lifetime_decisions_s1.json').read_text())
    old=json.loads((repo/'research_inputs/asset_survival/lifetime_decisions.json').read_text())
    if decisions['supersedes_sha256']!=sha(repo/'research_inputs/asset_survival/lifetime_decisions.json'):raise ValueError('Superseded lifetime file changed')
    for t,v in old['technologies'].items():
        if t!='Geothermal' and decisions['technologies'][t]!=v:raise ValueError('S1 lifetime file differs outside Geothermal: '+t)
    new,transitions=rerun_geothermal(stock,decisions)
    by_country=defaultdict(float);before=defaultdict(float)
    for t in transitions:
        if t['After']=='SURVIVES_2050':by_country[t['Country']]+=t['RetainedMW2050']
    for u in stock['unit_evidence']['records']:
        if u['Technology']=='Geothermal' and u['SurvivalStatus']=='SURVIVES_2050':before[u['Country']]+=u['RetainedCapacity2050']
    contract=json.loads((repo/'results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json').read_text())
    geo_perf=contract.get('performance',{}).get('Geothermal')
    bataan=bataan_evidence(cache,stock)
    for i,u in enumerate(new['unit_evidence']['records']):
        if u['AssetID']==BATAAN_UNIT and bataan['S1Decision']=='EXCLUDED_NEVER_COMMERCIAL_OPERATION':
            new['unit_evidence']['records'][i]=dict(u,SurvivalStatus='EXCLUDED_NEVER_COMMERCIAL_OPERATION',RetainedCapacity2050=0.,S1Exclusion=bataan)
    from collections import Counter
    new['unit_evidence']['status_counts']=dict(Counter(u['SurvivalStatus'] for u in new['unit_evidence']['records']))
    new['s1_provenance']=dict(frozen_source=str(frozen),frozen_source_sha256=sha(frozen),lifetime_decisions_s1_sha256=sha(repo/'research_inputs/asset_survival/lifetime_decisions_s1.json'),method='S1 unit-level geothermal re-selection + Bataan exclusion; all other records verbatim',frozen_file_modified=False)
    import pypsa,logging
    logging.disable(logging.CRITICAL)
    base=pypsa.Network(str(electric_base));existing=base.meta.get('existing_unit_components',{})
    review=dict(
        frozen_stock_sha256=sha(frozen),electric_base_sha256=sha(electric_base),
        geothermal=dict(lifetime_before=15,lifetime_after=decisions['technologies']['Geothermal']['Lifetime'],decision=decisions['technologies']['Geothermal'],
            units=len(transitions),transitions=transitions,surviving_mw_2050_by_country_before={k:round(v,3) for k,v in sorted(before.items())},
            surviving_mw_2050_by_country_after={k:round(v,3) for k,v in sorted(by_country.items())},
            integration_contract_has_geothermal_performance=geo_perf is not None,
            integration_status='NOT_INTEGRATED_PERFORMANCE_CONTRACT_PENDING' if by_country and geo_perf is None else ('INTEGRABLE' if by_country else 'NO_SURVIVORS'),
            gem_operating=gem_geothermal_by_country(cache),
            matched_units_in_frozen_powerplants=len(transitions)),
        bataan=dict(bataan,in_electric_base_existing_units=BATAAN_UNIT in existing),
        hydro=dict(research_layer_existing_mw_by_country_subtype=research_hydro_by_country(electric_base),gem_operating=gem_hydro_by_country(cache),modification='NONE_REPORT_ONLY'),
        solver_runs=0)
    rl=review['hydro']['research_layer_existing_mw_by_country_subtype'];gm=review['hydro']['gem_operating']['ByCountryType']
    diff=[]
    for key in sorted(set(rl)|set(gm)):
        a=rl.get(key,0.);b=gm.get(key,0.);diff.append(dict(CountrySubtype=key,ResearchLayerMW=a,GEMOperatingMW=b,DifferenceMW=round(a-b,3)))
    totals=defaultdict(lambda:[0.,0.])
    for row in diff:
        c=row['CountrySubtype'].split('|')[0];totals[c][0]+=row['ResearchLayerMW'];totals[c][1]+=row['GEMOperatingMW']
    review['hydro']['difference_by_country_subtype']=diff
    review['hydro']['country_totals']={c:dict(ResearchLayerMW=round(v[0],3),GEMOperatingMW=round(v[1],3),DifferenceMW=round(v[0]-v[1],3)) for c,v in sorted(totals.items())}
    output=Path(output);save(output/'S1_STOCK_REVIEW.json',review);save(output/'S1_SELECTED_ASSET_SURVIVAL_2050.json',new)
    print(json.dumps(dict(geothermal_after=review['geothermal']['surviving_mw_2050_by_country_after'],integration=review['geothermal']['integration_status'],bataan=bataan['S1Decision'],hydro_totals=review['hydro']['country_totals'])))
    return review

def corridors(repo,electric_base,output):
    """Fill the corridor table from the frozen electric base and the Gate4 control set; nothing is invented."""
    import pypsa,logging
    logging.disable(logging.CRITICAL)
    repo=Path(repo);n=pypsa.Network(str(electric_base))
    control=pd.read_csv(repo/'research/04_model_assembly/gate4/ELECTRICITY_INTERCONNECT_CONTROL_SET.csv',encoding='utf-8-sig')
    control=control[control.Classification=='CROSS_BORDER'];rows=[]
    for _,r in control.iterrows():
        typ=r.ComponentType;name=str(r.Component);df=n.df(typ);z=df.loc[name]
        if {n.buses.at[z.bus0,'country'],n.buses.at[z.bus1,'country']}!={r.Country0,r.Country1}:raise ValueError('Control set country mismatch '+name)
        nom='s_nom' if typ=='Line' else 'p_nom';cap=float(z[nom+'_min']);nominal=float(z[nom])  # lower bound carried by the frozen reference; s_nom may differ by float noise
        uw=z.get('underwater_fraction') if typ=='Link' else None
        subsea=0. if uw is None or (isinstance(uw,float) and math.isnan(uw)) else float(uw)
        rows.append({'from':z.bus0,'to':z.bus1,'carrier':z.carrier,'length_km':float(z.length),'subsea_share':subsea,
                     'source':'frozen electric base '+Path(electric_base).name+' SHA256 '+sha(electric_base)+'; Gate4 ELECTRICITY_INTERCONNECT_CONTROL_SET.csv; capacity_2025_mw from '+('Line.s_nom_min' if typ=='Line' else 'Link.p_nom_min')+' (frozen lower bound); subsea_share='+('underwater_fraction absent in frozen base -> 0 as in build_electric capital-cost rule' if (uw is None or (isinstance(uw,float) and math.isnan(uw))) else 'Link.underwater_fraction'),
                     'component_type':typ,'component':name,'country_from':n.buses.at[z.bus0,'country'],'country_to':n.buses.at[z.bus1,'country'],'capacity_2025_mw':cap,'nominal_mw_in_base':nominal,'nominal_minus_lower_bound_mw':nominal-cap,'status':'EXISTING_2025'})
    if len(rows)!=24:raise ValueError('Expected 24 existing cross-border edges, found '+str(len(rows)))
    out=pd.DataFrame(rows,columns=['from','to','carrier','length_km','subsea_share','source','component_type','component','country_from','country_to','capacity_2025_mw','nominal_mw_in_base','nominal_minus_lower_bound_mw','status'])
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True);out.to_csv(output,index=False,lineterminator='\n')
    print(json.dumps(dict(rows=len(out),sha256=sha(output))))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['stock','corridors']);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--electric-base',type=Path,default=None);p.add_argument('--cache',type=Path,default=Path('/home/jin/.local/share/powerplantmatching/data/in'));p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();eb=a.electric_base or a.repo/'results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc'
    if a.command=='stock':stock(a.repo,eb,a.cache,a.output)
    else:corridors(a.repo,eb,a.output)
