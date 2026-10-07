"""Linux cgroup transport adapter. No model or numerical option changes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import shutil
import psutil
from gate5_resources import budget, GIB, MIB


def cgroup_rows(base=Path('/sys/fs/cgroup'), membership=Path('/proc/self/cgroup')):
    """Walk the process cgroup and every visible ancestor, including namespaces."""
    group=next((s.split(':',2)[2] for s in membership.read_text().splitlines() if s.startswith('0::')),None)
    if group is None:raise ValueError('Cloud admission requires readable cgroup v2 limits')
    base=Path(base).resolve(); current=(base/group.lstrip('/')).resolve()
    if current!=base and base not in current.parents:raise ValueError('Invalid cgroup membership')
    if not current.is_dir():raise ValueError('Process cgroup is not visible')
    rows=[]
    while True:
        row={'path':str(current)}
        for key in ['memory.max','memory.current','memory.swap.max','memory.swap.current','memory.events','cpu.max','cpuset.cpus.effective']:
            p=current/key
            if p.exists():row[key]=p.read_text().strip()
        rows.append(row)
        if current==base:break
        current=current.parent
    return rows


def effective_resources(rows, total, available, affinity):
    limits=[];headrooms=[];cpus=[float(affinity)]
    for row in rows:
        maximum=row.get('memory.max')
        if maximum not in (None,'max'):
            if 'memory.current' not in row:raise ValueError('Missing cgroup memory.current')
            limit=int(maximum); used=int(row['memory.current'])
            if limit<=0 or used<0:raise ValueError('Invalid cgroup memory counters')
            limits.append(limit);headrooms.append(max(0,limit-used))
        if 'cpu.max' in row:
            quota,period=row['cpu.max'].split()
            if int(period)<=0:raise ValueError('Invalid cgroup CPU period')
            if quota!='max':cpus.append(int(quota)/int(period))
    if not limits:raise ValueError('No finite cloud cgroup memory limit; host free memory is insufficient evidence')
    return dict(effective_memory_limit_bytes=min([int(total)]+limits),
                effective_available_bytes=min([int(available)]+headrooms),effective_cpu_cores=min(cpus))


def snapshot(data_root):
    rows=cgroup_rows(); vm=psutil.virtual_memory(); swap=psutil.swap_memory()
    affinity=len(os.sched_getaffinity(0))
    result=dict(scope='CURRENT_LINUX_CGROUP',observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        cgroups=rows,nproc_affinity=affinity,logical_cpu_count=os.cpu_count(),
        host_memtotal_diagnostic_only_bytes=vm.total,host_memavailable_diagnostic_only_bytes=vm.available,
        swap_total_bytes=swap.total,swap_free_bytes=swap.free,
        disk=dict(zip(('total_bytes','used_bytes','free_bytes'),shutil.disk_usage(data_root))),
        platform=platform.platform(),kernel=platform.release(),architecture=platform.machine(),
        ulimits={name:list(resource.getrlimit(getattr(resource,name))) for name in ['RLIMIT_AS','RLIMIT_CPU','RLIMIT_FSIZE','RLIMIT_NOFILE','RLIMIT_STACK']},
        windows_commit_headroom_bytes=None,windows_commit_not_applicable=True)
    result.update(effective_resources(rows,vm.total,vm.available,affinity))
    return result


def admission(evidence, observation, guest_available=None, tree_rss=0, cgroups=()):
    b=budget(evidence);fail=[]
    if observation.get('scope')!='CURRENT_LINUX_CGROUP':raise ValueError('Cloud scope mismatch')
    # Retain the stricter original physical requirement, including the 2 GiB
    # host guard. Linux cgroup headroom is not Windows commit headroom.
    required=b['required_guest_available_bytes']+b['host_available_guard_bytes']
    if observation['effective_available_bytes']<required:fail.append('INSUFFICIENT_EFFECTIVE_CGROUP_PHYSICAL_HEADROOM')
    if observation['effective_cpu_cores']<2:fail.append('LESS_THAN_FROZEN_TWO_CPU_THREADS')
    if observation['disk']['free_bytes']<20*GIB:fail.append('LESS_THAN_20_GIB_DATA_DISK_PLANNING_RESERVE')
    return dict(status='PASS' if not fail else 'NOT_READY',reasons=fail,budget=b,
        resource_scope='CURRENT_LINUX_CGROUP',required_effective_available_bytes=required,
        effective_available_bytes=observation['effective_available_bytes'],
        effective_memory_limit_bytes=observation['effective_memory_limit_bytes'],
        process_tree_rss_bytes=tree_rss,scientific_input_changes=0,solver_calls=0)


def stop_reason(guest_available, observation, elapsed, wall_guard=14400, process_tree_rss=0, process_budget=None):
    if guest_available<512*MIB:return 'GUEST_AVAILABLE_BELOW_512_MIB'
    if observation is None:return 'CLOUD_RESOURCE_MONITOR_UNAVAILABLE'
    if observation.get('scope')!='CURRENT_LINUX_CGROUP':return 'CLOUD_RESOURCE_SCOPE_MISMATCH'
    if observation['effective_available_bytes']<2*GIB:return 'CLOUD_AVAILABLE_BELOW_2_GIB'
    if process_budget and process_tree_rss>process_budget:return 'PROCESS_TREE_EXCEEDS_DECLARED_BUDGET'
    if elapsed>wall_guard:return 'WALL_GUARD'
    return None


def validate_run_path(out):
    out=Path(out).resolve(); cloud_root=out.parent.parent
    if str(cloud_root)!='/root/autodl-tmp/SGP' or out.parent.name!='runs' or not out.name.startswith('cloud_gate5_'):
        raise ValueError('Cloud runs must use a unique /root/autodl-tmp/SGP/runs/cloud_gate5_* directory')
    return cloud_root


def claim_once(authorization, out, cloud_root):
    """Durably consume this human authorization before any native run call."""
    a=json.loads(Path(authorization).read_text())
    identity=a.get('authorization_id','')
    if len(identity)!=64 or any(c not in '0123456789abcdef' for c in identity):raise ValueError('Missing stable human authorization id')
    if a.get('run_id')!=Path(out).name or a.get('max_attempts')!=1:raise ValueError('One-run authorization mismatch')
    record=dict(run_id=a['run_id'],authorization_id=identity,
        authorization_sha256=hashlib.sha256(Path(authorization).read_bytes()).hexdigest(),
        claimed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),
        meaning='Authorization consumed before native call. Never retry automatically, even after a crash.')
    p=Path(cloud_root)/'evidence'/('solver_authorization_'+identity+'.consumed.json')
    with p.open('x') as f:
        json.dump(record,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    directory=os.open(str(p.parent),os.O_RDONLY)
    try:os.fsync(directory)
    finally:os.close(directory)
    return record
