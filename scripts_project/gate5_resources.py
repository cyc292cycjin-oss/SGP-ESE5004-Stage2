"""Read-only Gate5 admission, bounded monitoring and current-history selection."""
import json,hashlib,os,time,re,datetime
from pathlib import Path
import psutil
MIB=1024**2
GIB=1024**3

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for x in iter(lambda:f.read(MIB),b''):h.update(x)
    return h.hexdigest()

def current_evidence(root):
    reports=Path(root)/'research/04_model_assembly/final_validation'
    history=json.loads((reports/'GATE5_RUN_HISTORY.json').read_text())
    run=next(r for r in history['runs'] if r['run_id']==history['latest_run_id'])
    manifest=Path(root)/run['manifest']
    if sha(manifest)!=run['manifest_sha256']:raise ValueError('Latest manifest identity mismatch')
    m=json.loads(manifest.read_text())
    monitor=manifest.parent/'RESOURCE_MONITOR.jsonl'
    peak=0;stages={}
    with monitor.open() as f:
        for line in f:
            x=json.loads(line);peak=max(peak,x['rss_bytes'])
            s=stages.setdefault(x['stage'],dict(samples=0,peak_rss_bytes=0,min_available_bytes=None))
            s['samples']+=1;s['peak_rss_bytes']=max(s['peak_rss_bytes'],x['rss_bytes'])
            s['min_available_bytes']=x['available_bytes'] if s['min_available_bytes'] is None else min(s['min_available_bytes'],x['available_bytes'])
    return dict(run_id=run['run_id'],manifest_path=str(manifest.relative_to(root)),manifest_sha256=sha(manifest),status=m['status'],observed_peak_bytes=max(peak,int(m['peak_rss_mib']*MIB)),peak_is_lower_bound=True,native_qualification=m.get('native_solution_qualification','NOT_CAPTURED_PROCESS_INTERRUPTED' if m['status']=='STOPPED_RESOURCE_GUARD' else 'NOT_RECORDED'),objective=m['objective'],result_network=m['result_network'],dynamic_checks=m['dynamic_checks'],historical_execution_counts=history['execution_counts'],historical_stage_labels_unchanged=stages,monitor_path=str(monitor.relative_to(root)),monitor_sha256=sha(monitor),variables=m['variables'],constraints=m['constraints'])

def budget(evidence):
    # Explicit engineering reserve, NOT a predicted peak or a scientific input.
    # 4 native value/dual vectors as Python float lists + pandas arrays + mapping
    # scratch, conservatively 80 bytes per combined variable/row label.
    result_envelope=80*(evidence['variables']+evidence['constraints'])
    unknown_reserve=max(2*GIB,result_envelope)
    return dict(observed_lower_bound_bytes=evidence['observed_peak_bytes'],result_conversion_planning_envelope_bytes=result_envelope,unmeasured_postsolve_reserve_bytes=unknown_reserve,guest_available_guard_bytes=512*MIB,host_available_guard_bytes=2*GIB,required_guest_available_bytes=evidence['observed_peak_bytes']+unknown_reserve+512*MIB,basis='latest observed peak LOWER BOUND + max(2 GiB explicit unmeasured-phase allowance, 80 bytes per variable/row) + unchanged 512 MiB guest guard',phase_coverage=['crossover','original_model_postsolve','native_result_return','original_unit_mapping','PyPSA_assignment','dynamic_validation','export'],acceptance_status='PROPOSED_ENGINEERING_BUDGET_REQUIRES_HUMAN_ACCEPTANCE',swap_counts_as_physical_ram=False)

def host_read(path,max_age=120):
    x=json.loads(Path(path).read_text(encoding='utf-8-sig'))
    t=datetime.datetime.fromisoformat(x['observed_at'].replace('Z','+00:00'))
    age=(datetime.datetime.now(datetime.timezone.utc)-t).total_seconds()
    if age< -5 or age>max_age:raise ValueError('Host observation stale or future-dated')
    if x.get('scope')!='CURRENT_WINDOWS_HOST':raise ValueError('Unqualified host probe')
    return x

def process_tree_sample(process=None,include_pss=False):
    p=process or psutil.Process();items=[]
    try:processes=[p]+p.children(recursive=True)
    except psutil.Error:processes=[p]
    for item in processes:
        try:
            row=dict(pid=item.pid,rss_bytes=item.memory_info().rss)
            if include_pss:row['pss_bytes']=getattr(item.memory_full_info(),'pss',None)
            items.append(row)
        except psutil.Error:continue
    return dict(processes=items,process_tree_rss_bytes=sum(x['rss_bytes'] for x in items),process_tree_rss_is_shared_page_upper_bound=True)

def cgroup_memory():
    group=next((x.split(':',2)[2] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::')),None)
    result=[]
    if group is None:return result
    base=Path('/sys/fs/cgroup');current=base/group.lstrip('/')
    while current==base or base in current.parents:
        row={'path':str(current)}
        for key in ['memory.max','memory.current','memory.swap.max','memory.swap.current']:
            f=current/key
            if f.exists():row[key]=f.read_text().strip()
        if len(row)>1:result.append(row)
        if current==base:break
        current=current.parent
    return result

def admission(evidence,host,guest_available,tree_rss=0,cgroups=()):
    b=budget(evidence);required=b['required_guest_available_bytes'];fail=[]
    if guest_available<required:fail.append('INSUFFICIENT_GUEST_AVAILABLE_PHYSICAL_MEMORY')
    # Existing guest pages may already be resident: using full requirement is a
    # conservative host check. Never add host and guest free memory together.
    if host['physical_available_bytes']<required+b['host_available_guard_bytes']:fail.append('INSUFFICIENT_HOST_PHYSICAL_HEADROOM')
    if host['commit_available_bytes']<required:fail.append('INSUFFICIENT_HOST_COMMIT_HEADROOM')
    for x in cgroups:
        if x.get('memory.max') not in (None,'max') and int(x['memory.max'])-int(x.get('memory.current','0'))<required:fail.append('CGROUP_MEMORY_HEADROOM')
    return dict(status='PASS' if not fail else 'NOT_READY',reasons=fail,budget=b,guest_available_bytes=guest_available,host_available_bytes=host['physical_available_bytes'],host_commit_available_bytes=host['commit_available_bytes'],process_tree_rss_bytes=tree_rss,cgroups=list(cgroups),scientific_input_changes=0,solver_calls=0)

ORDER=['UNKNOWN','presolve','IPM','crossover','simplex_cleanup','original_model_postsolve']
class LogPhases:
    """Incremental bounded reads; no solver API and no invented historical times."""
    def __init__(self):self.offset=0;self.stage='UNKNOWN';self.partial=b''
    def feed(self,text):
        for line in text.splitlines():
            low=line.lower();new=None
            if 'presolving model' in low or 'presolve reductions' in low:new='presolve'
            if 'ipx' in low or re.match(r'^\s*\d+\*?\s+[-+\d.e]+\s+[-+\d.e]+\s+[-+\d.e]+\s+[-+\d.e]+\s+[-+\d.e]+\s+\d+s\s*$',line):new='IPM'
            if 'running crossover' in low:new='crossover'
            if 'clean up with simplex' in low or 'using ekk dual simplex' in low:new='simplex_cleanup'
            if 'solving the original lp from the solution after postsolve' in low:new='original_model_postsolve'
            if new and ORDER.index(new)>ORDER.index(self.stage):self.stage=new
        return self.stage
    def read(self,path):
        if not Path(path).exists():return self.stage
        with Path(path).open('rb') as f:
            f.seek(self.offset);block=f.read(65536);self.offset=f.tell()
        data=self.partial+block;split=data.rsplit(b'\n',1)
        if len(split)==2:self.feed(split[0].decode(errors='replace'));self.partial=split[1][-4096:]
        else:self.partial=data[-4096:]
        return self.stage

def stop_reason(guest_available,host,elapsed,wall_guard=14400,process_tree_rss=0,process_budget=None):
    if guest_available<512*MIB:return 'GUEST_AVAILABLE_BELOW_512_MIB'
    if host is None:return 'HOST_MONITOR_UNAVAILABLE_OR_STALE'
    if host['physical_available_bytes']<2*GIB:return 'HOST_AVAILABLE_BELOW_2_GIB'
    if process_budget and process_tree_rss>process_budget:return 'PROCESS_TREE_EXCEEDS_DECLARED_BUDGET'
    if elapsed>wall_guard:return 'WALL_GUARD'
    return None

def persist_resource_stop(out,receipt,record,reason,save,terminate=os._exit):
    # Small receipt first; no network export or solver API at the memory edge.
    p=Path(out)/'RESOURCE_STOP_RECEIPT.json';temp=p.with_suffix('.json.tmp')
    temp.write_text(json.dumps(dict(reason=reason,last_sample=record,no_native_solver_api_called=True))+'\n');os.replace(temp,p)
    receipt.update(status='STOPPED_RESOURCE_GUARD',stop_reason=reason,end_time=datetime.datetime.now(datetime.timezone.utc).isoformat())
    save();terminate(3)
