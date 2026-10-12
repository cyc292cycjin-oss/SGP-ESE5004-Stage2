from pathlib import Path
import json, hashlib, time, os
import numpy as np, psutil
run=Path('/root/autodl-tmp/SGP/runs/c02_daily_build_20261012T025604Z_fcc0f784')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
ids=read(run/'ALL_PROCESS_IDENTITIES.json');process=[]
for role,i in ids.items():
 try:
  p=psutil.Process(i['pid']);process.append({'role':role,'pid':i['pid'],'recorded_ctime':i['ctime'] if 'ctime' in i else i.get('create_time'),'exists':True,'actual_create_time':p.create_time(),'status':p.status(),'cmd_sha256':hashlib.sha256('\0'.join(p.cmdline()).encode()).hexdigest()})
 except psutil.NoSuchProcess:process.append({'role':role,'pid':i['pid'],'exists':False})
files=[]
for p in sorted(run.rglob('*')):
 if p.is_file():
  st=p.stat(); row={'path':str(p.relative_to(run)),'bytes':st.st_size,'sha256':digest(p),'mtime_ns':st.st_mtime_ns}
  if p.suffix=='.npy':
   a=np.load(p,mmap_mode='r',allow_pickle=False);row.update(shape=list(a.shape),dtype=str(a.dtype))
  files.append(row)
labels=read(run/'artifacts/mapping/LABELS.json'); families=[]
for kind in ['variables','constraints']:
 for b in labels[kind]:
  a=np.load(run/'artifacts/mapping'/b['labels_file'],mmap_mode='r'); families.append({'kind':kind,'name':b['name'],'shape':list(a.shape),'active_labels':int(np.count_nonzero(a>=0)),'min_label':int(a.min()),'max_label':int(a.max())})
p=Path('/root/autodl-tmp/SGP/env/gate5/lib/python3.11/site-packages/pypsa/optimization/constraints.py')
lines=p.read_text().splitlines(); source=[{'line':i+1,'text':s} for i,s in enumerate(lines) if 825<=i+1<=965]
samples=[json.loads(x) for x in (run/'RESOURCE_SAMPLES.jsonl').read_text().splitlines()]
print(json.dumps({'time':time.time(),'run':str(run),'mode':'READ_ONLY_POST_FAILURE_NO_MODEL_REBUILD','processes':process,'files':files,'families':families,'pypsa_constraints_source':{'path':str(p),'sha256':digest(p),'lines':source},'resources':{'sample_count':len(samples),'first':samples[0],'last':samples[-1],'max_worker_tree_rss':max(x['rss_bytes'] for x in samples),'min_disk_free':min(x['disk_free'] for x in samples)}}))
