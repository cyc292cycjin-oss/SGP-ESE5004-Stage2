"""Bounded historical primary-source recovery; fixed tag then immutable SHA, no main fetch."""
from pathlib import Path
import hashlib,json,urllib.request,subprocess
R=Path(__file__).resolve().parent; E=R/'evidence'; G='/home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline'
def git(*args):return subprocess.check_output(['git','-C',G,*args])
out={}
for label,args in {
 'SPLIT_FULL_HISTORY.txt':['log','--full-history','-m','a3616a68','--format=%H %ad %s','--date=short','-S','space_heat_share','--','*.yaml'],
 'EARTH_SEC_INITIAL_CONFIG.yaml':['show','0ec4af7f7:config.yaml'],
 'BDEW_REPO_REFERENCES.txt':['grep','-n','-i','BDEW','a3616a68','--','doc','docs','scripts','README.md'],
}.items():
    p=subprocess.run(['git','-C',G,*args],capture_output=True);(R/'history'/label).write_bytes(p.stdout);out[label]={'returncode':p.returncode}
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'SGP-Stage2-read-only-audit'})
    return urllib.request.urlopen(req,timeout=35).read()
try:
    tags=json.loads(fetch('https://api.github.com/repos/PyPSA/pypsa-eur-sec/tags?per_page=30'))
    tag=next(x for x in tags if x['name'].lstrip('v')=='0.7.0')
    out['eur_sec_tag']=tag
    url=f"https://api.github.com/repos/PyPSA/pypsa-eur-sec/git/trees/{tag['commit']['sha']}?recursive=1"
    b=fetch(url);tree=json.loads(b);(E/'PYPSA_EUR_SEC_0.7.0_TREE.json').write_bytes(b)
    sha=tree['sha'];out['eur_sec_sha']=sha
    selected=[t['path'] for t in tree['tree'] if (any(k in t['path'].lower() for k in ['bdew','data_sources','build_heat','heat_profile']) or t['path']=='doc/data.csv') and t['type']=='blob']
    out['eur_sec_files']=[]
    for path in selected:
        url=f'https://raw.githubusercontent.com/PyPSA/pypsa-eur-sec/{sha}/{path}'
        data=fetch(url);target=E/'eur_sec_0.7.0'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        out['eur_sec_files'].append({'path':path,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
except Exception as ex:out['error']=repr(ex)
(E/'PROFILE_SOURCE_RECOVERY.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
