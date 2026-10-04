"""Cache the bounded primary-source search without changing any model input.

No source is adopted. Remote bytes are hashed; cached files are never replaced.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import datetime, hashlib, json, urllib.request
R=Path(__file__).resolve().parent
SOURCES=[
 ('ERIA_PILOT2013','eria-pilot2013.pdf','https://www.eria.org/RPR_FY2012_No.19_chapter_1.pdf'),
 ('ERIA_COMMERCIAL2021','eria-commercial2021.pdf','https://www.eria.org/uploads/Technical-Guidelines-Energy-Efficiency-and-Conservation-Commercial-Buildings.pdf'),
 ('MY_NEB2016','malaysia-neb2016.pdf','https://www.st.gov.my/contents/files/download/111/ST-NEB_2016_Booklet.pdf'),
 ('PH_HECS2011','philippines-compendium1990-2021.pdf','https://legacy.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf'),
 ('BELDA2017','belda-eceee2017.pdf','https://www.belda.asia/wp/wp-content/uploads/2017/06/170608ECEEE201_BELDA.pdf'),
 ('VN_WATER2018','vietnam-water2018.html','https://www.scirp.org/journal/paperinformation?paperid=82791'),
 ('VN_TUYHOA2019','vietnam-tuyhoa2019.pdf','https://pure.hud.ac.uk/files/16980968/electrical_appliance_use_and_energy_Vietnamese_households_v3_clean.pdf'),
 ('ACE_MY_SURVEYS','ace-malaysia-surveys.html','https://www.aseanenergy.org/articles/malaysias-energy-survey-benchmarking-effort-gains-insights-from-the-asean-centre-for-energy'),
]
FALLBACKS={
 'MY_NEB2016':['https://www.st.gov.my/sites/default/files/2026-02/ST-NEB_2016_Booklet.pdf'],
 'PH_HECS2011':['https://www.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf'],
}
D=R/'data/raw/buildings';D.mkdir(parents=True,exist_ok=True)
M=D/'RETRIEVAL_MANIFEST.json'
old={r['source_id']:r for r in json.loads(M.read_text())} if M.exists() else {}
def fetch(item):
    sid,name,url=item;p=D/name
    r=dict(source_id=sid,official_url=url,filename=p.relative_to(R).as_posix(),status='UNVERIFIED',human_confirmation='PENDING')
    try:
        if p.exists():
            r.update({k:v for k,v in old.get(sid,{}).items() if k in ['retrieved_utc','resolved_url','content_type']})
            r['retrieval']='REUSED_IMMUTABLE_CACHE'
        else:
            r['attempts']=[]
            for candidate in [url]+FALLBACKS.get(sid,[]):
                try:
                    with urllib.request.urlopen(urllib.request.Request(candidate,headers={'User-Agent':'Mozilla/5.0'}),timeout=45) as f:
                        b=f.read();r.update(resolved_url=f.url,content_type=f.headers.get('Content-Type'))
                    r['attempts'].append(dict(url=candidate,access='RETRIEVED'));break
                except Exception as ex:
                    r['attempts'].append(dict(url=candidate,error=str(ex)))
            else:raise ValueError('All enumerated official URLs failed; see attempts')
            if name.endswith('.pdf') and not b.startswith(b'%PDF'):raise ValueError('Expected PDF, got another response type')
            p.write_bytes(b);r['retrieved_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        b=p.read_bytes();r.update(access='RETRIEVED',bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    except Exception as ex:r.update(access='FAILED',sha256='',error=str(ex))
    print(json.dumps({k:r.get(k) for k in ['source_id','access','bytes','error']}),flush=True)
    return r
results=list(ThreadPoolExecutor(max_workers=3).map(fetch,SOURCES))
M.write_text(json.dumps(results,indent=2),encoding='utf-8')
