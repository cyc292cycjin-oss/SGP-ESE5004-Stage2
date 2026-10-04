"""Retrieve explicitly enumerated official candidates. Never write model inputs.
Cached files are not overwritten. A changed remote version requires a new record.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime, hashlib, json, urllib.request

R=Path(__file__).resolve().parent
D=R/'data/raw/buildings'; D.mkdir(parents=True,exist_ok=True)
SOURCES=[
 ('AEO8_CORRIGENDUM','aeo8-corrigendum.pdf','https://storage.googleapis.com/aceweb-bucket-261225/uploads/2024/09/AEO8-Corrigendum-Notice.pdf','https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/'),
 ('AEO8','aeo8.pdf','https://storage.googleapis.com/aceweb-bucket-261225/pdf/publication/8th%20ASEAN%20Energy%20Outlook_SInO1OrPHSdovI5igUIm1SVQHgSGYPAkyoE6aL7R.pdf','https://www.aseanenergy.org/publications/the-8th-asean-energy-outlook/'),
 ('ESDM2019','heesi2019.pdf','https://www.esdm.go.id/assets/media/content/content-handbook-of-energy-and-economic-statistics-of-indonesia-2019.pdf','https://www.esdm.go.id/en/publikasi/handbook-of-energy-economic-statistics-of-indonesia'),
 ('KH2019','cambodia-energy-statistics.pdf','https://www.eria.org/uploads/media/Research-Project-Report/RPR-2022-08/Cambodia-Energy-Statistics-2019-2020.pdf','https://www.eria.org/uploads/media/Research-Project-Report/RPR-2022-08/Cambodia-Energy-Statistics-2019-2020.pdf'),
 ('NEA2017','nea2017.html','https://www.nea.gov.sg/media/news/news/index/four-in-five-households-motivated-to-save-energy-if-they-can-save-money-nea-study','https://www.nea.gov.sg/media/news/news/index/four-in-five-households-motivated-to-save-energy-if-they-can-save-money-nea-study'),
 ('COOLING2022','asean-cooling.html','https://aseanenergy.org/publications/roadmap-towards-sustainable-and-energy-efficient-space-cooling-in-asean/','https://aseanenergy.org/publications/roadmap-towards-sustainable-and-energy-efficient-space-cooling-in-asean/'),
 ('IEAENDUSE2026','iea-enduse.html','https://www.iea.org/data-and-statistics/data-product/energy-end-uses-and-efficiency-indicators','https://www.iea.org/data-and-statistics/data-product/energy-end-uses-and-efficiency-indicators'),
]
def fetch(item):
    sid,name,url,landing=item;p=D/name
    record=dict(source_id=sid,filename=str(p.relative_to(R)),requested_url=url,official_url=landing,status='UNVERIFIED',human_confirmation='PENDING')
    try:
        if not p.exists():
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (research source audit)'})
            with urllib.request.urlopen(req,timeout=45) as f:
                content=f.read();record['resolved_url']=f.url
            if name.endswith('.pdf') and not content.startswith(b'%PDF'):raise ValueError('Response is not PDF')
            p.write_bytes(content)
            record['retrieved_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        else:record['retrieval']='REUSED_LOCAL_CACHE'
        content=p.read_bytes();record.update(bytes=len(content),sha256=hashlib.sha256(content).hexdigest(),access='RETRIEVED')
    except Exception as exc:record.update(access='FAILED',error=str(exc),sha256='NOT_RETRIEVED')
    return record
records=list(ThreadPoolExecutor(max_workers=3).map(fetch,SOURCES))
p=R/'data/raw/buildings/RETRIEVAL_MANIFEST.json'
if p.exists():
    old={r['source_id']:r for r in json.loads(p.read_text())}
    for r in records:
        if r.get('retrieval')=='REUSED_LOCAL_CACHE' and r['source_id'] in old:
            r.update({k:v for k,v in old[r['source_id']].items() if k in ['retrieved_utc','resolved_url']})
p.write_text(json.dumps(records,indent=2))
print(json.dumps([{k:r.get(k) for k in ['source_id','access','bytes','error']} for r in records],indent=2))
