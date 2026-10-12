"""Build-only evidence and process protection utilities. No solver imports."""
from pathlib import Path
import hashlib,json,os,time,shutil,platform,importlib.metadata as md

GIB=1024**3
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,obj):
    p=Path(path); tmp=p.with_name(p.name+'.tmp')
    with tmp.open('x',encoding='utf8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)
def verify_payload(root):
    manifest=read(root/'PAYLOAD_MANIFEST.json')
    for rel,v in manifest['files'].items():
        p=(root/rel).resolve(strict=True)
        assert p.is_relative_to(root.resolve()) and p.is_file(),rel
        assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'],rel
    return manifest
def resources(path):
    import psutil
    entries=Path('/proc/self/cgroup').read_text().splitlines()
    mounts=[s.split() for s in Path('/proc/self/mountinfo').read_text().splitlines() if ' - cgroup' in s]
    controllers={key:line.split(':',2)[2] for line in entries for key in line.split(':',2)[1].split(',') if key}
    # AutoDL 122 is a namespaced cgroup-v1 mount. Resolve against mountinfo root,
    # not by concatenating a host /docker path underneath the container mount.
    if 'memory' in controllers:
        def leaf_for(controller):
            matches=[r for r in mounts if r[r.index('-')+1]=='cgroup' and controller in r[-1].split(',')]
            if len(matches)!=1:raise RuntimeError('ambiguous cgroup mount: '+controller)
            mount=matches[0];rel=Path(controllers[controller]).relative_to(Path(mount[3]));base=Path(mount[4]);return base,base/rel
        mb,ml=leaf_for('memory');cb,cl=leaf_for('cpu');sb,sl=leaf_for('cpuset')
        vals=[];p=ml
        while p.is_relative_to(mb):
            if (p/'memory.limit_in_bytes').exists():
                stat=dict(x.split() for x in (p/'memory.stat').read_text().splitlines());oom=dict(x.split() for x in (p/'memory.oom_control').read_text().splitlines())
                lim=min(int((p/'memory.limit_in_bytes').read_text()),int(stat.get('hierarchical_memory_limit',2**63-1)))
                events='max '+(p/'memory.failcnt').read_text().strip()+'\noom '+oom.get('under_oom','0')+'\noom_kill '+oom.get('oom_kill','0')+'\n'
                vals.append({'path':str(p),'limit':lim if lim<2**60 else None,'current':int((p/'memory.usage_in_bytes').read_text()),'memory_peak':int((p/'memory.max_usage_in_bytes').read_text()),'memory_events':events,'hierarchical_memory_limit':int(stat.get('hierarchical_memory_limit',2**63-1))})
            if p==mb:break
            p=p.parent
        quota=[];p=cl
        while p.is_relative_to(cb):
            if (p/'cpu.cfs_quota_us').exists():
                q=int((p/'cpu.cfs_quota_us').read_text());period=int((p/'cpu.cfs_period_us').read_text())
                if q>0:quota.append(q/period)
            if p==cb:break
            p=p.parent
        finite=[r for r in vals if r['limit'] is not None]
        if not finite:raise RuntimeError('No finite v1 memory boundary')
        affinity=len(os.sched_getaffinity(0))
        return dict(timestamp=time.time(),hostname=platform.node(),cgroup_version=1,ancestors=vals,effective_memory_limit=min(r['limit'] for r in finite),
            memory_headroom=min(r['limit']-r['current'] for r in finite),effective_cpu_cores=min([float(affinity)]+quota),cpu_affinity=affinity,
            cpuset=(sl/'cpuset.cpus').read_text().strip(),ancestor_scope='visible namespace ancestors plus kernel hierarchical_memory_limit; host ancestors outside mount not directly exposed',
            disk_free=shutil.disk_usage(path).free,host_available=psutil.virtual_memory().available)
    rel=next((s.split(':',2)[2] for s in entries if s.startswith('0::')),None)
    if rel is None:raise RuntimeError('CGROUP_V2_NOT_PRESENT: no unverified v1 fallback')
    base=Path('/sys/fs/cgroup'); leaf=base/rel.lstrip('/')
    if not leaf.exists():raise RuntimeError('cgroup mount/namespace cannot be resolved')
    vals=[];p=leaf
    while p.is_relative_to(base):
        if (p/'memory.max').exists():
            mx=(p/'memory.max').read_text().strip();cur=int((p/'memory.current').read_text())
            cpu=(p/'cpu.max').read_text().split();cpus=(p/'cpuset.cpus.effective').read_text().strip()
            vals.append(dict(path=str(p),limit=None if mx=='max' else int(mx),current=cur,
                cpu_quota=None if cpu[0]=='max' else int(cpu[0])/int(cpu[1]),cpuset=cpus,
                memory_events=(p/'memory.events').read_text(),memory_peak=int((p/'memory.peak').read_text()) if (p/'memory.peak').exists() else None))
        if p==base:break
        p=p.parent
    finite=[r for r in vals if r['limit'] is not None]
    if not finite:raise RuntimeError('No verified finite cgroup memory boundary')
    affinity=len(os.sched_getaffinity(0));quota=min([float(affinity)]+[r['cpu_quota'] for r in vals if r['cpu_quota'] is not None])
    return dict(timestamp=time.time(),hostname=platform.node(),ancestors=vals,cpu_affinity=affinity,effective_cpu_cores=quota,
       effective_memory_limit=min(r['limit'] for r in finite),memory_headroom=min(r['limit']-r['current'] for r in finite),
       disk_free=shutil.disk_usage(path).free,host_available=psutil.virtual_memory().available)
def resource_gate(r,start=False):
    if r['effective_memory_limit']<90*GIB:raise RuntimeError('effective cgroup memory below 90 GiB')
    if r['effective_cpu_cores']<4:raise RuntimeError('effective CPU quota below 4 cores')
    if r['memory_headroom']<12*GIB or r['host_available']<12*GIB:raise RuntimeError('memory safety margin below 12 GiB')
    if r['disk_free']<(20 if start else 8)*GIB:raise RuntimeError('disk threshold')
    if start and r['disk_free']-6*GIB<8*GIB:raise RuntimeError('6 GiB output reserve unavailable')
def identity(pid):
    import psutil
    p=psutil.Process(pid)
    return dict(pid=pid,ctime=p.create_time(),pgid=os.getpgid(pid),sid=os.getsid(pid),
       cmdhash=hashlib.sha256('\0'.join(p.cmdline()).encode()).hexdigest())
def same_identity(i):
    try:return identity(i['pid'])==i
    except Exception:return False
def versions():
    return {x:md.version(x) for x in ['pypsa','linopy','numpy','scipy','pandas','xarray','netCDF4','psutil']}
