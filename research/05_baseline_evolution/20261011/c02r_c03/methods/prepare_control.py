from pathlib import Path
import ast,subprocess,shutil
W=Path('/mnt/d/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012');R=W/'release'
src=(R/'production_control_original.py').read_text();tree=ast.parse(src)
def replace_function(src,name,new):
    f=next(x for x in ast.parse(src).body if isinstance(x,ast.FunctionDef) and x.name==name)
    return src.replace(ast.get_source_segment(src,f),new,1)
src=replace_function(src,'resources','''def resources(pid,root,limits,require_cgroup=True):
 from c02_common import resources as current
 r=current(root);p=psutil.Process(pid);rss=cpu=0
 for q in [p,*p.children(recursive=True)]:
  try:rss+=q.memory_info().rss;cpu+=sum(q.cpu_times()[:2])
  except psutil.NoSuchProcess:pass
 reason='RSS' if rss>=limits['rss_bytes'] else 'DISK' if r['disk_free']<limits['disk_free_bytes'] else 'CGROUP' if r['memory_headroom']<limits['cgroup_headroom_bytes'] else None
 return dict(epoch=time.time(),rss_bytes=rss,cpu_seconds=cpu,disk_free_bytes=r['disk_free'],cgroup_headroom_bytes=r['memory_headroom'],cgroup=r['ancestors'],effective_memory_limit=r['effective_memory_limit'],reason=reason)
''')
src=replace_function(src,'phase_deadline','''def phase_deadline(stage,a):
 phase=stage.get('phase','BUILD');entered=stage['entered_epoch']
 if phase=='BUILD':return min(entered+1800,a['build_absolute_deadline_epoch'])
 if phase=='BRIDGE':return min(entered+900,a['load_absolute_deadline_epoch'])
 if phase=='NATIVE':return min(entered+3600,a['native_absolute_deadline_epoch'])
 if phase=='RAW_SAVE':return min(entered+300,a['raw_absolute_deadline_epoch'])
 if phase=='POSTPROCESS':return min(entered+1200,a['post_absolute_deadline_epoch'])
 if phase in ('DONE','FAILED'):return a['post_absolute_deadline_epoch']
 raise ValueError('unknown protected phase '+phase)
''')
# No inherited closeout helper: this run uses its own bounded seal worker after all writers exit.
(R/'production_control.py').write_text(src)
repo=Path('/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model')
p=repo/'research/05_baseline_evolution/20261011/b03_c00/evidence/FIRST_RUN_EFFECTIVE_MODEL_PARAMETERS.json'
shutil.copyfile(p,R/p.name)
# Source and input manifest remain immutable; current complete release has a separate allowlist.
shutil.copyfile(W/'C02R_C03_CONDITIONAL_EXECUTION_INSTRUCTION.md',R/'USER_COMBINED_AUTHORIZATION.md')
shutil.copyfile(W.parent/'c02_daily_build_20261012/C02_ZERO_ROW_BOUNDARY_CHECK.json',R/'ZERO_ROW_PRIOR_EVIDENCE.json')
