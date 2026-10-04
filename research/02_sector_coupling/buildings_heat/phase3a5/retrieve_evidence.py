"""Bounded public-source recovery; all downloads are evidence, never model inputs."""
from pathlib import Path
import concurrent.futures,datetime,hashlib,json,shutil,urllib.request
R=Path(__file__).resolve().parent
RAW=R/'data/raw/buildings';RAW.mkdir(parents=True,exist_ok=True)
manifest=[]
def sha(b):return hashlib.sha256(b).hexdigest()
for folder,wanted in [('buildings_phase3a3',['MY_NEB2016','ERIA_PILOT2013','BELDA2017','VN_WATER2018']),
                       ('buildings_heat_alignment',['AEO8','AEO8_CORRIGENDUM','ESDM2019','KH2019','NEA2017'])]:
    old=R.parent.parent/folder
    for rec in json.loads((old/'data/raw/buildings/RETRIEVAL_MANIFEST.json').read_text()):
        if rec['source_id'] not in wanted:continue
        p=old/rec['filename'];b=p.read_bytes();assert sha(b)==rec['sha256']
        dest=RAW/p.name;dest.write_bytes(b)
        manifest.append(dict(source_id=rec['source_id'],url=rec['official_url'],resolved_url=rec.get('resolved_url'),
          file=str(dest.relative_to(R)).replace('\\','/'),sha256=sha(b),bytes=len(b),access='REUSED_VERIFIED_CACHE',
          version='See original title/reference year; no edition update',year='See source-specific location records',
          license='Original publisher rights; open-data reuse license not assumed unless stated in source',
          purpose='E3 source-scope/end-use/boundary evidence only',status='UNVERIFIED'))
urls=[
 ('DEMANDCAST_PAPER','https://arxiv.org/html/2510.08000v1','demandcast-v1.html','2025 v1','CC BY4.0'),
 ('DEMANDCAST_RELEASE','https://zenodo.org/api/records/18374352','demandcast-zenodo18374352.json','record18374352','Read record license'),
 ('DEMANDCAST_TAG','https://api.github.com/repos/open-energy-transition/demandcast/git/trees/v0.9.0?recursive=1','demandcast-v090-tree.json','v0.9.0','Repository license; code audit'),
 ('EMBER_METHOD','https://files.ember-energy.org/public-downloads/ember_electricity_data_methodology.pdf','ember-methodology.pdf','retrieved2026-10-02; exact internal version inspected separately','Read publisher terms'),
 ('PH_DOE_LEGACY','https://legacy.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf','ph-doe-legacy.pdf','Compendium1990-2021','Government publication; license unverified'),
 ('PH_DOE_CURRENT','https://www.doe.gov.ph/sites/default/files/pdf/energy_statistics/doe_compendium_energy_statistics-1990-2021.pdf','ph-doe-current.pdf','Compendium1990-2021','Government publication; license unverified'),
 ('PH_HECS2023_NOTES','https://psa.gov.ph/statistics/technical-notes/1684076304','ph-hecs2023-notes.html','2023 survey technical notes','Government publication; license unverified'),
]
def get(item):
    id,url,name,version,license=item
    row=dict(source_id=id,url=url,file='',sha256='',version=version,year='',license=license,
             purpose='Targeted E3 evidence closure; not automatic data update',status='UNVERIFIED')
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Research-provenance-audit/1.0','Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=30) as res:
            b=res.read();row.update(resolved_url=res.url,content_type=res.headers.get('Content-Type',''))
        if name.endswith('.pdf') and not b.startswith(b'%PDF'):raise ValueError('Response is not a PDF')
        if name.endswith('.json'):json.loads(b)
        dest=RAW/name;dest.write_bytes(b)
        row.update(file=str(dest.relative_to(R)).replace('\\','/'),sha256=sha(b),bytes=len(b),access='RETRIEVED')
    except Exception as exc:row.update(access='UNAVAILABLE',error=str(exc))
    row['retrieved_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    manifest+=list(pool.map(get,urls))
(RAW/'SOURCE_REGISTRY.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{k:r.get(k) for k in ['source_id','access','bytes','error']} for r in manifest]))
