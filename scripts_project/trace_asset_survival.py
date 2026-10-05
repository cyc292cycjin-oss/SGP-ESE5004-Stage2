from pathlib import Path
import ast,json,hashlib,sys,argparse
import pandas as pd,openpyxl,yaml
parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--plants',type=Path,required=True);parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--lifetimes',type=Path);args=parser.parse_args();R=args.repo;P=args.plants
sys.path.insert(0,str(R/'scripts_project'));from asset_survival import select_asset
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plants=pd.read_csv(P);wanted=set();identities={}
for i,r in plants.iterrows():
 ids=ast.literal_eval(r.projectID);ids=set(ids.get('GEM',[]));identities[i]=ids;wanted|=ids
found={};sources={};cache=args.cache
for file in sorted(cache.glob('*.xlsx')):
 sources[file.name]=sha(file);wb=openpyxl.load_workbook(file,read_only=True,data_only=True)
 for ws in wb.worksheets:
  rows=ws.iter_rows(values_only=True)
  try:header=next(rows)
  except StopIteration:continue
  columns=[str(x).strip() if x is not None else '' for x in header]
  ident=[i for i,c in enumerate(columns) if c.lower() in ['gem unit id','gem phase id','gem unit/phase id']]
  if not ident:continue
  for line,row in enumerate(rows,2):
   if len(row)<=ident[0] or row[ident[0]] not in wanted:continue
   data={str(k).lower():v for k,v in zip(columns,row)}
   pick=lambda names:next((data[x] for x in names if x in data and data[x] is not None),None)
   key=row[ident[0]];z=dict(ID=key,Status=pick(['status']),StartYear=pick(['start year']),RetiredYear=pick(['retired year','retirement year']),Capacity=pick(['capacity (mw)','unit capacity (mw)']),Source=file.name,SourceSHA256=sources[file.name],Sheet=ws.title,ExcelRow=line)
   if key in found and found[key]!=z:raise ValueError('Conflicting GEM identity '+key)
   found[key]=z
 wb.close();print(file.name,'matched total',len(found),flush=True)
life=yaml.safe_load((R/'configs/powerplantmatching_config.yaml').read_text())['fuel_to_lifetime'];out=[]
for i,r in plants.iterrows():
 ids=identities[i];matches=[found[k] for k in sorted(ids) if k in found];complete=bool(ids) and len(matches)==len(ids)
 statuses={str(z['Status']).lower() for z in matches}
 role='OBSERVED_EXISTING' if complete and statuses<={'operating'} else 'COMMITTED_OR_PLANNED' if complete and statuses<={'announced','pre-construction','construction','shelved','cancelled','proposed'} else 'UNKNOWN'
 starts={z['StartYear'] for z in matches};start=next(iter(starts)) if complete and len(starts)==1 else None
 if not isinstance(start,(float,int)):start=None
 retirements={z['RetiredYear'] for z in matches};retire=next(iter(retirements)) if complete and len(retirements)==1 else None
 if not isinstance(retire,(float,int)):retire=None
 tech=r.Fueltype;candidate_life=life.get('Natural Gas' if tech=='CCGT' else tech)
 asset=dict(AssetID='PPM:'+str(i),Country=r.Country,Technology=tech,OriginalCapacity=float(r.Capacity),CommissioningYear=start,RetirementYear=retire,Lifetime=candidate_life,LifetimeSource='Frozen powerplantmatching_config fuel_to_lifetime; numeric acceptance not silently inferred',LifetimeAccepted=False,CommissioningEvidenceVerified=start is not None,RetirementEvidenceVerified=retire is not None,AssetClass=role,Source=str(P),SourceVersion=sha(P),DecisionBasis='ASSEMBLY_V1_2050_SINGLE_YEAR_SURVIVING_ASSETS',CostTreatment='Existing fixed O&M/VOM/efficiency must be source-qualified separately; no repeat2050 new CAPEX',ResourceLimitTreatment='Pending verified100-node mapping and total/additional resource semantics',OriginalMappedBus=str(r.bus),OriginalTableDateIn=float(r.DateIn),OriginalTableDateOut=float(r.DateOut),SourceSubassets=matches,SourceIDs=sorted(ids))
 out.append(select_asset(asset))
from unit_asset_survival import reconcile_units
decisions=json.loads(args.lifetimes.read_text()).get('technologies',{}) if args.lifetimes else {}
unit_evidence=reconcile_units(out,decisions)
jsonout=dict(schema='frozen-asset-survival-evidence-2',target_year=2050,weather_year=2013,asset_source=str(P),asset_source_sha256=sha(P),raw_source_hashes=sources,original_table_rows=len(plants),raw_evidence_matches=len(found),records=out,unit_evidence=unit_evidence,lifetime_decision_file=str(args.lifetimes) if args.lifetimes else None,lifetime_decision_sha256=sha(args.lifetimes) if args.lifetimes else None,note='Parent records retained for provenance only. Production selection uses unit_evidence after individual status/year/capacity checks, before aggregation. Original PPM dates may be imputed. Conditional lifetime results never activate production capacity.')
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(jsonout,indent=2,default=str)+'\n')
from collections import Counter
print(Counter(z['SurvivalStatus'] for z in out));print(Counter(z['AssetClass'] for z in out))
