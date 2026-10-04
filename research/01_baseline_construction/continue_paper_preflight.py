"""Make only two existing raw inputs visible for a deeper DAG dry-run."""
from engineering_review import *
from datetime import datetime, timezone
import requests

ev=HERE/'evidence';repo=BASE/'paper_reference'
linked=[]
for rel in ['data/eez/eez_v11.gpkg','data/natura/natura.tiff']:
    source=OLD/rel;target=repo/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.symlink_to(source)
    with open(source,'rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    linked.append({'path':rel,'source':str(source),'sha256':h,'status':'LOCAL_UNVERIFIED_INPUT_FOR_DRYRUN_ONLY'})
pre=json.loads((HERE/'PAPER_PREFLIGHT.json').read_text())
env=dict(os.environ,PROJ_DATA=str(Path(sys.executable).parents[1]/'share/proj'),PROJ_LIB=str(Path(sys.executable).parents[1]/'share/proj'))
p=subprocess.run(pre['command'],cwd=repo,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=90)
(ev/'PAPER_DRYRUN_WITH_LOCAL_GEODATA.log').write_text(p.stdout)
out={'linked_inputs':linked,'command':pre['command'],'returncode':p.returncode,'date_utc':datetime.now(timezone.utc).isoformat()}
url='https://drive.usercontent.google.com/download?id=11-Ax9tVks7oPjrZwG5v3C0x4OmMT_Pv8&export=download&confirm=t'
try:
    with requests.get(url,headers={'Range':'bytes=0-4095'},stream=True,timeout=30) as r:
        chunk=r.raw.read(4096)
        out['official_asia_cutout_probe']={'source':'paper configs/bundle_config.yaml bundle_cutouts_asia','status':r.status_code,
          'headers':{k:v for k,v in r.headers.items() if k.lower() in ['content-length','content-range','content-type','content-disposition']},
          'first_four_bytes_hex':chunk[:4].hex(),'downloaded_prefix_bytes':len(chunk),'paper_exact_identity':'Filename candidate cutout-2013-era5.nc matches effective paper metadata; complete file and author SHA256 unverified'}
except Exception as e:out['official_asia_cutout_probe']={'error':str(e)}
(HERE/'PAPER_PREFLIGHT_FOLLOWUP.json').write_text(json.dumps(out,indent=2))
print(p.stdout[-4500:]);print(json.dumps(out,indent=2))
