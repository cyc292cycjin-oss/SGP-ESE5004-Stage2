"""Read-only provenance recovery. Does not import or execute model workflow."""
from pathlib import Path
import concurrent.futures, datetime, hashlib, json, subprocess, urllib.request

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Users/20122/.codex/.chatgpt-projects/g-p-6ab8040523e881918c18587a52a2527d/audit_repo')
def save(name, data):
    p=ROOT/name; p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data,bytes) else data.encode('utf-8'))
def git(*args):
    p=subprocess.run(['git','-C',str(REPO),*args],capture_output=True)
    return p.stdout.decode('utf-8',errors='replace') if p.returncode==0 else p.stderr.decode('utf-8',errors='replace')
def fetch(item):
    name,url=item
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'ASEAN-Source-Provenance-Audit','Accept':'application/vnd.github+json' if 'api.github' in url else '*/*'})
        with urllib.request.urlopen(req,timeout=60) as r:
            b=r.read(); status=r.status; headers=dict(r.headers); final=r.url
        save('official/'+name,b)
        return dict(name=name,url=url,final_url=final,status=status,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),headers=headers)
    except Exception as e: return dict(name=name,url=url,error=str(e))
def main():
    logspec={
      'asean_history':['log','--all','--date=iso-strict','--format=%H %ad %s','--','configs/config.asean.yaml','configs/scenarios.asean.yaml','doc-asean/docs/index.md'],
      'sector_origin':['log','--all','--follow','--reverse','--date=short','--format=%H %ad %s','--','scripts/prepare_sector_network.py'],
      'industry_history':['log','--all','--date=short','--format=%H %ad %s','--','scripts/build_industry_demand.py','scripts/build_base_industry_totals.py'],
      'carbon_migration':['log','--all','--date=short','--format=%H %ad %s','-S','_migrate_co2_budget_base_value','--','scripts/_helpers.py'],
      'carbon_keys':['log','--all','--date=short','--format=%H %ad %s','-G','co2base_value|base_value','--','configs/config.asean.yaml','scripts/prepare_sector_network.py'],
      'paper_commit':['show','--stat','99159edb7298b847fea517bf05c3f388493501c9'],
      'refs':['show-ref'],
    }
    for n,a in logspec.items():save('history/'+n+'.txt',git(*a))
    historical_errors=[]
    for sha in ['99159edb7298b847fea517bf05c3f388493501c9','1b22a0996cfe9cddf0acb2876d16c065c21f1a68','c1d99d0617e027ebe01fa2dd1ce1f7160eaddd6e']:
        for f in ['configs/config.asean.yaml','configs/scenarios.asean.yaml','config.default.yaml','scripts/prepare_sector_network.py','doc-asean/docs/index.md']:
            result=git('show',sha+':'+f)
            if result.startswith('fatal:'):historical_errors.append({'commit':sha,'path':f,'error':result})
            else:save('historical/'+sha[:8]+'/'+f,result)
    save('LOCAL_HISTORY_READ_ERRORS.json',json.dumps(historical_errors,indent=2))
    base='https://api.github.com/repos/'
    queries=[('asean_repo.json',base+'pypsa-meets-earth/pypsa-asean'),('asean_tags.json',base+'pypsa-meets-earth/pypsa-asean/tags?per_page=100'),('asean_releases.json',base+'pypsa-meets-earth/pypsa-asean/releases?per_page=100'),('asean_branches.json',base+'pypsa-meets-earth/pypsa-asean/branches?per_page=100'),('paper_pr25.json',base+'pypsa-meets-earth/pypsa-asean/pulls/25'),('tech_tag.json',base+'PyPSA/technology-data/git/ref/tags/v0.13.2'),('tech_release.json',base+'PyPSA/technology-data/releases/tags/v0.13.2'),('tech_tree.json',base+'PyPSA/technology-data/git/trees/v0.13.2?recursive=1'),('earthsec_repo.json',base+'pypsa-meets-earth/pypsa-earth-sec'),('drive_view.html','https://drive.google.com/file/d/194my_d3eotQ1GvsGGN5KOZGWOHEivoQy/view'),('drive_download_response.html','https://drive.google.com/uc?export=download&id=194my_d3eotQ1GvsGGN5KOZGWOHEivoQy')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: results=list(pool.map(fetch,queries))
    save('FETCH_LOG.json',json.dumps({'retrieved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'items':results},ensure_ascii=False,indent=2))
    print(json.dumps([{k:v for k,v in x.items() if k not in ('headers',)} for x in results],indent=2))
if __name__=='__main__':main()
