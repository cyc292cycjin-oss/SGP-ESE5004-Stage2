from pathlib import Path
import subprocess,time,json,psutil,os
ROOT=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
E=Path('/mnt/c/Users/20122/Documents/ChatGPT/ASEAN/work/phase4_final_validation/evidence')
output=ROOT/'results_project/validation/gate5_20261006_01'
command=['/home/jin/miniforge3/envs/pypsa-earth/bin/python','-u','scripts_project/run_gate5_validation.py','--output',str(output)]
(E/'GATE5_EXECUTION_COMMAND.json').write_text(json.dumps({'command':command,'cwd':str(ROOT),'output':str(output)},indent=2))
start=time.monotonic();samples=[];reason=None
with (E/'gate5_execution.log').open('w') as log:
 p=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,PYTHONUNBUFFERED='1'))
 while p.poll() is None:
  mem=psutil.virtual_memory();samples.append({'elapsed_seconds':time.monotonic()-start,'available_ram_bytes':mem.available,'process_rss_bytes':psutil.Process(p.pid).memory_info().rss})
  if mem.available<512*1024**2 or time.monotonic()-start>7200:
   reason='ENGINEERING_MEMORY_GUARD' if mem.available<512*1024**2 else 'ENGINEERING_WALL_TIME_LIMIT';p.terminate();break
  time.sleep(3)
 try:code=p.wait(timeout=30)
 except subprocess.TimeoutExpired:p.kill();code=p.wait()
r={'exit_code':code,'stop_reason':reason,'elapsed_seconds':time.monotonic()-start,'peak_process_rss_bytes':max(x['process_rss_bytes'] for x in samples),'samples':samples}
(E/'GATE5_SUPERVISOR_RECEIPT.json').write_text(json.dumps(r,indent=2))
print(json.dumps({k:v for k,v in r.items() if k!='samples'},indent=2))
print((E/'gate5_execution.log').read_text()[-7000:])
