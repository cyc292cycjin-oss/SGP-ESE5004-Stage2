"""Preserve the existing download registry, without using any download link."""
from diagnose_industry import ROOT,REPO
import hashlib,json,pandas as pd
p=REPO/'data/demand/unsd/paths/Energy_Statistics_Database.xlsx'
b=p.read_bytes();(ROOT/'diagnostic_inputs/Energy_Statistics_Database.xlsx').write_bytes(b)
d=pd.read_excel(p,index_col=0)
rec={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'links':d.dropna(subset=['Link'])['Link'].to_dict(),'current_update_data':False,'fallback_google_drive_id_from_code':'1VUV0X-tTQECi2pHdE5EWXjPI2yeCdk6F','retrieval_executed':False}
(ROOT/'UNSD_REGISTRY_EVIDENCE.json').write_text(json.dumps(rec,indent=2))
print('Registry rows',len(d),'link entries',len(rec['links']))
print(list(rec['links'].items())[:2])
