"""Read existing artifacts / frozen objects. No downloads, model solves or input writes."""
from pathlib import Path
import ast, hashlib, inspect, json, subprocess
import pandas as pd
import numpy as np
import atlite
from atlite import convert

R=Path(__file__).resolve().parent
E=R/'evidence'; E.mkdir(exist_ok=True)
M=Path('/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean')
G=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline')
U=R/'source_snapshot/upstream'
COUNTRIES=['BN','KH','ID','LA','MY','MM','PH','SG','TH','TL','VN']
manifest=[]
def record(p):
    b=p.read_bytes(); manifest.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
def save(name,obj):
    (E/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,default=str,allow_nan=False))
def clean(df):return json.loads(df.to_json(orient='index'))
annual={}
res=M/'resources/baseline-aims-3H-tutorial'
for y in ['base','2030','2040','2050']:
    p=res/f'energy_totals_{y}.csv';record(p)
    df=pd.read_csv(p,index_col=0,keep_default_na=False,na_values=[''])
    annual[y]=clean(df[[c for c in df if 'residential' in c or 'services' in c or 'district heat' in c]])
save('TUTORIAL_BUILDINGS_ANNUAL.json',annual)
profile=pd.read_csv(U/'data/heat_load_profile_BDEW.csv',index_col=0)
save('BDEW_PROFILE_STATISTICS.json',{'shape':list(profile.shape),'columns':clean(profile.describe().T),'water_all_one':bool((profile.filter(like='water')==1).all().all())})
heat={}
for y in ['2030','2040','2050']:
    p=res/f'demand/heat/heat_demand_s_50_{y}.csv';record(p)
    df=pd.read_csv(p,index_col=0,header=[0,1]);
    heat[y]={'shape':list(df.shape),'nan_cells':int(df.isna().sum().sum()),'all_nan_columns':[list(c) for c in df.columns[df.isna().all()]],'sum_by_use_TWh':df.sum().groupby(level=0).sum().div(1e6).to_dict()}
save('TUTORIAL_HEAT_PROFILE_DIAGNOSTIC.json',heat)
# Read raw exports once, retain ONLY household/services rows for configured countries, year 2019.
import country_converter as coco
raw=[]
for p in sorted((M/'data/demand/unsd/data').glob('*.txt')):
    df=pd.read_csv(p,sep=';',low_memory=False)
    m=df['Commodity - Transaction'].str.contains('consumption by households|services',case=False,na=False)&(df['Year']==2019)
    d=df.loc[m].copy()
    if d.empty:continue
    mapping=dict(zip(d['Country or Area'].unique(),coco.convert(d['Country or Area'].unique(),to='ISO2')))
    d['ISO2']=d['Country or Area'].map(mapping)
    d=d.loc[d.ISO2.map(lambda x: isinstance(x,str) and x in COUNTRIES)]
    if d.empty:continue
    record(p);d['source_file']=p.name;raw.append(d)
raw=pd.concat(raw,ignore_index=True)
save('UNSD_2019_BUILDINGS_ROWS.json',json.loads(raw.to_json(orient='records')))
save('UNSD_2019_BUILDINGS_COVERAGE.json',{'rows':len(raw),'countries':sorted(raw.ISO2.unique()),'by_country':raw.groupby('ISO2').size().to_dict(),'transactions':sorted(raw['Commodity - Transaction'].unique()),'units':sorted(raw['Unit'].unique())})
for name in ['heat_demand','convert_heat_demand']:
    (E/f'installed_atlite_{name}.py').write_text(inspect.getsource(getattr(convert,name)))
save('ENVIRONMENT.json',{'atlite':atlite.__version__,'pandas':pd.__version__,'numpy':np.__version__,'role':'installed tutorial/audit environment; not proof of original author dependency lock'})
# All history commands anchored to frozen upstream SHA; never contact main.
commands={
 'EARTH_SEC_INITIAL.txt':['show','--format=fuller','--stat','0ec4af7f7'],
 'SPLIT_ANCESTRY.txt':['log','a3616a68','--all-match','--format=%H %ad %s','--date=short','-S','space_heat_share','--','config.default.yaml','config.default.yaml.backup','config.default.yaml.template','config.default.yaml.default','configs/config.default.yaml'],
 'SPLIT_IMPORT_DIFF.txt':['show','--format=short','a8987468','--','config.default.yaml'],
 'ASEAN_SPLIT_DIFF.txt':['show','--format=short','d965b422b','--','config.default.yaml'],
 'INITIAL_FILE_TREE.txt':['ls-tree','-r','--name-only','0ec4af7f7'],
 'FUEL_DEFAULT_ORIGIN.txt':['log','a3616a68','--format=%H %ad %s','--date=short','--follow','--','data/demand/fuel_shares.csv'],
}
for name,args in commands.items():
    (R/'history'/name).write_bytes(subprocess.check_output(['git','-C',str(G),*args]))
save('LOCAL_INPUT_HASHES.json',manifest)
print(json.dumps({'raw_rows':len(raw),'raw_countries':sorted(raw.ISO2.unique()),'heat':heat,'atlite':atlite.__version__},indent=2))
