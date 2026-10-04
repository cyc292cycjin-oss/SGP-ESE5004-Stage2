"""Bounded raw-file identity/license check, not a model-input regeneration."""
from pathlib import Path
import urllib.request,zipfile,io,hashlib,json,csv
ROOT=Path(__file__).resolve().parent;E=ROOT/'evidence/license_review'
url='https://simplemaps.com/static/data/us-cities/1.93/basic/simplemaps_uscities_basicv1.93.zip'
out={'url':url}
try:
 with urllib.request.urlopen(url,timeout=40) as r:
  content=r.read();out.update(status=r.status,final_url=r.url,bytes=len(content),sha256=hashlib.sha256(content).hexdigest())
 z=zipfile.ZipFile(io.BytesIO(content));out['members']=z.namelist()
 for name in z.namelist():
  if 'license' in name.lower() or 'readme' in name.lower():
   b=z.read(name);out.setdefault('notices',[]).append({'name':name,'text':b.decode('utf8','replace')})
 name=next(n for n in z.namelist() if n.endswith('.csv'))
 source=list(csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))))
 local=ROOT.parents[2]/'research/00_model_audit/input_snapshot/data/industry/us_cities.csv'
 target=list(csv.DictReader(local.open(encoding='utf-8-sig',newline='')))
 out['source_rows']=len(source);out['local_rows']=len(target);out['columns_match']=list(source[0])==list(target[0])
 # Strings preserve exact fields; tolerate only numerical CSV serialization.
 from decimal import Decimal, InvalidOperation
 differences=[]
 if len(source)==len(target) and out['columns_match']:
  for i,(a,b) in enumerate(zip(source,target)):
   for key in a:
    expected=a[key].lower() if key=='city' else a[key]
    if expected==b[key]:continue
    try:
     if Decimal(expected)==Decimal(b[key]):continue
    except InvalidOperation:pass
    differences.append({'row':i+2,'column':key})
 out['differences_count']=len(differences);out['difference_locations_sample']=differences[:10]
 out['identity_after_documented_city_lowercase_and_numeric_serialization']=out['columns_match'] and len(source)==len(target) and not differences
except Exception as exc:out['error']=str(exc)
(E/'CITY_SOURCE_CHECK.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k!='notices'}))
