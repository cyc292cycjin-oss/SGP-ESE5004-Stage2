"""Download only new targeted official sources; never overwrite existing files."""
from pathlib import Path
import hashlib,json,urllib.request,datetime,concurrent.futures
R=Path(__file__).resolve().parent;raw=R/'data/raw';raw.mkdir(parents=True,exist_ok=True)
specs=[('MY_NEB2019','malaysia-neb2019.pdf','https://www.st.gov.my/sites/default/files/2026-02/NEB_2019.pdf','National Energy Balance2019; ST(P)02/02/2022','2019 with historical series','Official national energy balance, electricity boundary and2016-2019 trend'),
 ('MY_WATER_GUIDELINE2016','my-water-guideline2016.pdf','https://www.st.gov.my/en/eng/general/add_counter/646/download/read_count','GP/ST/No.6/2016; dated2017-04-07','2016/2017','Device definitions and historical performance evidence screening'),
 ('MY_ENERGY_MAG9','my-energy-mag9-2016.pdf','https://www.st.gov.my/sites/default/files/2026-02/Energy-Malaysia%2C-Volume-9%2C-2016.pdf','Energy Malaysia volume9,2016','2016','Water-heater device coverage; approval counts not stock energy shares')]
def get(t):
 sid,name,url,ver,yr,purpose=t;p=raw/name
 rec=dict(source_id=sid,url=url,file='data/raw/'+name,version=ver,year=yr,purpose=purpose,access_date='2026-10-02',license='Energy Commission rights reserved; source attribution; no open licence inferred',status='UNVERIFIED')
 try:
    if p.exists():b=p.read_bytes();rec['access']='REUSED_PHASE3A6_CACHE'
    else:
      with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=90) as z:b=z.read();rec['resolved_url']=z.url
      assert b.startswith(b'%PDF'),'Not a PDF response'
      p.write_bytes(b);rec['access']='RETRIEVED'
    rec.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 except Exception as e:rec.update(access='UNAVAILABLE',error=str(e),file='',sha256='')
 return rec
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:records=list(ex.map(get,specs))
(raw/'NEW_SOURCE_REGISTRY.json').write_text(json.dumps(records,indent=2),encoding='utf8')
print(json.dumps(records,indent=2))
