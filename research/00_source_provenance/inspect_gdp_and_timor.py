"""Bounded checks of original GDP coverage and Timor-Leste UNSD records."""
from diagnose_industry import ROOT,REPO,stats
import pandas as pd,xarray as xr,json,hashlib
def main():
    nc=REPO/'data/GDP/GDP_PPP_1990_2015_5arcmin_v2.nc';tif=nc.with_suffix('.tif')
    out={'files':[]}
    for p in [nc,tif]:
        with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
        out['files'].append({'path':str(p),'size':p.stat().st_size,'sha256':h})
    with xr.open_dataset(nc) as ds:
        a=ds.GDP_PPP.sel(time=2015,longitude=slice(90,142),latitude=slice(30,-12))
        out['raw_2015_asean_rectangle']=stats(a)
    records=[];countries=set()
    for p in (REPO/'data/demand/unsd/data').glob('*.txt'):
        d=pd.read_csv(p,sep=';',encoding='utf-8',low_memory=False)
        countries.update(str(v) for v in d['Country or Area'].unique() if 'Timor' in str(v))
        s=d[d['Country or Area'].astype(str).str.contains('Timor',case=False) & (pd.to_numeric(d['Year'],errors='coerce')==2019)]
        if len(s):
            s=s.copy();s['source_file']=p.name;records.extend(s.to_dict('records'))
    out['timor_names']=sorted(countries);out['timor_2019_record_count']=len(records)
    out['timor_2019_transactions']=sorted(set(str(r['Commodity - Transaction']) for r in records))
    (ROOT/'GDP_TIMOR_EVIDENCE.json').write_text(json.dumps(out,indent=2,default=str))
    if records:pd.DataFrame(records).to_csv(ROOT/'diagnostic_inputs/timor_UNSD_2019_rows.csv',index=False)
    print(json.dumps(out,indent=2)[:4000])
if __name__=='__main__':main()
