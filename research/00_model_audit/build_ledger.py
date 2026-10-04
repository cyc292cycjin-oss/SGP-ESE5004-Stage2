"""Deterministically extract auditable records, without evaluating the workflow."""
import csv,json,re,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
snap=root/'input_snapshot'
fields=['Parameter_ID','Sector','Technology','Parameter','Raw_Value','Raw_Unit','Reference_Year','Source_Name','Source_URL','Source_File','Sheet/Table/Page','PyPSA_Value','Transformation','Final_Value','Status','Reason','Verified_By','Evidence_Level','Value_Stage','Currency_Year','Upstream_Compiled_Value','Upstream_Unit','Appended_Value','Appended_Unit','PyPSA_Unit','File_SHA256','Country_or_Node','Scope']
rows=[]
def emit(**kw):
    r={f:'' for f in fields};r.update(Status='UNVERIFIED',Reason='Model/file read verified; original-source alignment and human confirmation pending',Evidence_Level='DIRECT_FILE_READ');r.update(kw); rows.append(r)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
for yr in [2030,2040,2050]:
    rel=Path(f'resources/baseline-aims-3H-tutorial/costs_{yr}.csv');app=read(snap/rel)
    pre={(r['technology'],r['parameter']):r for r in read(snap/rel.with_name(f'pre_costs_{yr}.csv'))}
    sec={r['technology']:r for r in read(snap/rel.with_name(f'costs_{yr}_sec.csv'))}
    for i,r in enumerate(app,2):
        t,p=r['technology'],r['parameter'];s=r.get('source','');old=pre.get((t,p),{})
        value=sec.get(t,{}).get(p,'');unit=r['unit'].replace('/kW','/MW')
        emit(Parameter_ID=f'COST-{yr}-{i:04d}',Sector='cross-sector',Technology=t,Parameter=p,Reference_Year=yr,Raw_Unit='',
             Source_Name=s,Source_URL='; '.join(re.findall(r'https?://[^\s,]+',s)),Source_File=str(rel),
             **{'Sheet/Table/Page':f'CSV record {i}; '+r.get('further description','')},PyPSA_Value=value,
             Transformation='technology-data compiled output -> append_cost_data.py (AEO8 investment/FOM/VOM where mapped) -> process_cost_data.py prepare_costs; kW/kWh to MW/MWh; currency; defaults/overrides; component assignment separate',
             Value_Stage='processed sector cost input, NOT necessarily active final component',Currency_Year=r.get('currency_year',''),
             Upstream_Compiled_Value=old.get('value',''),Upstream_Unit=old.get('unit',''),Appended_Value=r['value'],Appended_Unit=r['unit'],PyPSA_Unit=unit,File_SHA256=sha(snap/rel),Scope='tutorial '+str(yr),
             Reason='Raw_Value left empty: primary publication/workbook cell not checked. Upstream and appended values are compiled/model inputs; not human approved')
    for t,r in sec.items():
        for p in ['fixed','marginal_cost']:
            if r.get(p,'')!='':
                emit(Parameter_ID=f'DERIVED-{yr}-{len(rows):05d}',Sector='cross-sector',Technology=t,Parameter=p,Reference_Year=yr,Source_Name='Existing processed model cost table',Source_File=str(rel.with_name(f'costs_{yr}_sec.csv')),PyPSA_Value=r[p],Transformation='fixed=(annuity(lifetime,discount rate)+FOM/100)*investment*Nyears; marginal_cost=VOM+fuel/efficiency; composite storage may combine technologies',Value_Stage='derived cost coefficient; component basis must be checked',PyPSA_Unit='EUR/(MW or MWh capacity)/model period' if p=='fixed' else 'EUR/MWh dispatch',File_SHA256=sha(snap/rel.with_name(f'costs_{yr}_sec.csv')),Scope='tutorial '+str(yr))
ev=json.loads((root/'AUDIT_RUNTIME_EVIDENCE.json').read_text())
def walk(d,p=''):
    if isinstance(d,dict):
        for k,v in d.items():yield from walk(v,p+'.'+str(k) if p else str(k))
    else:yield p,d
for p,v in walk(ev['networks'][0]['meta']):
    emit(Parameter_ID=f'CONFIG-{len(rows):05d}',Sector=p.split('.')[0],Parameter=p,Source_Name='2030 saved network metadata',Source_File=ev['networks'][0]['file'],PyPSA_Value=json.dumps(v,ensure_ascii=False),Transformation='Stored effective runtime metadata; legacy keys can coexist with consumed keys',Value_Stage='effective tutorial configuration',Scope='2030 tutorial',File_SHA256=ev['networks'][0]['sha256'])
# Preserve every cell, including missing industrial data. Do not impute.
patterns=['resources/baseline-aims-3H-tutorial/energy_totals*.csv','resources/baseline-aims-3H-tutorial/demand/industrial_energy_demand_per_node*.csv','data/demand/*.csv','data/AEO8-input/*.csv']
diagnostics=[]
for pattern in patterns:
    for path in sorted(snap.glob(pattern)):
        with path.open(encoding='utf-8-sig',newline='') as f:
            matrix=list(csv.reader(f))
        headers=matrix[0];blank=0;filled=0
        for i,r in enumerate(matrix[1:],2):
            for j,value in enumerate(r[1:],1):
                blank+=value=='';filled+=value!=''
                param=headers[j] if j<len(headers) else f'column{j+1}'
                primary=path.parts[-2]=='AEO8-input' or path.parent==snap/'data/demand'
                emit(Parameter_ID=f'CELL-{len(rows):06d}',Sector='sector demand' if 'AEO8' not in str(path) else 'technology cost',Parameter=param,Country_or_Node=r[0],Raw_Value=value if primary else '',PyPSA_Value='' if primary else value,Source_Name='Existing model input (publication provenance pending)',Source_File=str(path.relative_to(snap)),**{'Sheet/Table/Page':f'CSV record {i}, column {j+1}'},Value_Stage='raw model-input cell (not verified publication value)' if primary else 'derived demand input cell',Transformation='See MODEL_INPUT_MAP; missing cells preserved',File_SHA256=sha(path),Reason='Missing cell: stop before scientific run' if value=='' else 'Primary source, units and geographical suitability require confirmation',Scope='cell inventory')
        diagnostics.append({'file':str(path.relative_to(snap)),'records':len(matrix)-1,'columns':len(headers),'blank_data_cells':blank,'populated_data_cells':filled,'duplicate_headers':sorted({x for x in headers if headers.count(x)>1})})
for name,desc in [('FLEET','GPD/GEM/EESI and powerplants.csv'),('WEATHER','ERA5 cutouts and renewable profiles'),('POTENTIAL','Copernicus/GEBCO/natura/geographical masks'),('GRID','osm-plus-prebuilt/0.1.1 and transmission projects'),('POPULATION','UN WPP2024 cache named worldbank_pop_forecast.csv'),('PAPER','Local IOP paper found; exact code/data mapping pending'),('DEA_PRIMARY','User DEA workbooks found; frozen technology-data v0.13.2 source match pending')]:
    emit(Parameter_ID='GAP-'+name,Sector=name,Parameter=desc,Status='PENDING',Reason='Family-level record. See MODEL_INPUT_MAP and INPUT_INVENTORY; not a complete row-by-row primary-source audit',Scope='source family')
if (root/'USER_SOURCE_INVENTORY.json').exists():
    for i,r in enumerate(json.loads((root/'USER_SOURCE_INVENTORY.json').read_text(encoding='utf-8'))['workbooks'],1):
        emit(Parameter_ID=f'USER-DEA-{i:02d}',Sector='technology cost',Parameter='User-provided workbook version candidate',Source_Name='Danish Energy Agency user-held workbook',Source_File=r['file'],File_SHA256=r['sha256'],Value_Stage='candidate reference file; NOT selected as model input',Reason='Version/sheet identity differs or has not been matched to frozen technology-data v0.13.2',Scope=json.dumps(r['properties'],ensure_ascii=False))
assert len({r['Parameter_ID'] for r in rows})==len(rows)
assert all(r['Status'] in ['PENDING','UNVERIFIED'] and not r['Final_Value'] and not r['Verified_By'] for r in rows)
(root/'ledger_records.json').write_text(json.dumps({'fields':fields,'rows':rows},ensure_ascii=False),encoding='utf-8')
(root/'LEDGER_VALIDATION.json').write_text(json.dumps({'rows':len(rows),'status_counts':{s:sum(r['Status']==s for r in rows) for s in ['PENDING','UNVERIFIED']},'unique_ids':True,'final_values_blank':True,'human_confirmation_blank':True,'input_cell_diagnostics':diagnostics},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rows':len(rows),'diagnostics':[d for d in diagnostics if 'industrial_energy' in d['file']]}))
