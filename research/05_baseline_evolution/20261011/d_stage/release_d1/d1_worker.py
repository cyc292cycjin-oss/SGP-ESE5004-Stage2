"""D-1 sequential dispatch: one firewalled build process, CSR->CSC bridge, D-1 gates, artifact SHA index. No optimize."""
from pathlib import Path
import sys,time,os,subprocess,traceback,json
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'helpers'))
from c02_common import read,write,sha,resource_gate,resources
from d_production_control import alive,phase_deadline
import numpy as np
from fractions import Fraction as F


def build_gates(run,progress):
    art=run/'artifacts';br=run/'bridge';a=read(run/'AUTHORIZATION.json');T=a.get('test_snapshots') or 2920
    groups=read(art/'SCHEME_A_2920_EXACT_GROUPS.json');diff=read(art/'D1_NETWORK_LP_DIFF_REGISTER.json');nr=read(art/'NETWORK_READBACK.json')
    g=groups['groups'];slack=[F(x['Q'])-F(x['D']) for x in g]
    gate={'scheme_A_385_D_le_Q':len(g)==385 and all(s>=0 for s in slack) and all(F(x['D'])<=F(x['Q']) for x in g),
          'scheme_A_180_changed_627_unchanged':diff['changed_accounts']==180 and len(diff['changes'])==180 and diff['unchanged_accounts']==627,
          'loads_1737_equal_frozen':nr['loads_reference_rechecked_after_readback']==1737 and nr['status']=='EXACT_VALUES_PASS'}
    progress('GATE_SCHEME_A')
    # Label coverage: every LP column/row label appears in exactly one exported Linopy label array, and vice versa.
    labels=read(art/'mapping/LABELS.json');vl=np.load(br/'mapping/vlabels.npy');cl=np.load(br/'mapping/clabels.npy')
    cover={}
    for kind,ref in (('variables',vl),('constraints',cl)):
        parts=[]
        for b in labels[kind]:
            p=art/'mapping'/b['labels_file'];assert sha(p)==b['sha256'];x=np.load(p).ravel();parts.append(x[x>=0])
        allv=np.sort(np.concatenate(parts));srt=np.sort(ref)
        cover[kind]={'exported_labels':int(len(allv)),'lp_labels':int(len(ref)),'unique':bool(len(np.unique(allv))==len(allv)),'equal_sets':bool(np.array_equal(allv,srt))}
        progress('GATE_LABELS_'+kind)
    gate['labels_complete']=all(v['unique'] and v['equal_sets'] for v in cover.values())
    rec=read(br/'BRIDGE_RECEIPT.json');m=read(br/'math_problem/MATH_PROBLEM.json')
    from adapter import open_problem,validate
    mm,aa=open_problem(br/'math_problem',verify=True);dims=validate(mm,aa)
    gate['CSC_readback_exact']=rec['status']=='EXACT_CSR_CSC_REVERSE_PERMUTATION_PASS' and rec['row_order_checked'] and rec['all_values_bounds_objective_preserved']
    b=read(art/'GATE6_2920_V4_BINDING.json')
    gate['V4_binding_2920_thresholds_unchanged']=b['snapshots']==T and b['V4_formulas_changed'] is False and b['parent_V4_SHA256']==sha(HERE/'V4_APPROVED.json') and b['annual_resource_budget_multiplier']==1
    out={'status':'D1_BUILD_GATES_PASS' if all(gate.values()) else 'D1_BLOCKED_WITH_SPECIFIC_EVIDENCE','gates':gate,'label_coverage':cover,
         'dimensions':{'columns':m['num_col'],'rows':m['num_row'],'nnz':m['nnz'],'snapshots':m['snapshots']},'validate':dims,
         'scheme_A_slack_MWh':{'min':str(min(slack)),'max':str(max(slack)),'zero_slack_groups':sum(s==0 for s in slack)},
         'native_manifest_sha256':sha(br/'math_problem/MATH_PROBLEM.json'),'mapping_manifest_sha256':sha(br/'mapping/MAPPING_MANIFEST.json'),
         'labels_sha256':sha(art/'mapping/LABELS.json'),'solver_calls':0}
    write(run/'D1_BUILD_GATES.json',out);return out


def artifact_index(run,progress):
    files=[]
    for top in ('artifacts','bridge'):
        for p in sorted((run/top).rglob('*')):
            if p.is_file():
                with p.open('rb') as f:os.fsync(f.fileno())
                files.append({'relative':str(p.relative_to(run)),'bytes':p.stat().st_size,'sha256':sha(p)})
                if len(files)%200==0:progress('ARTIFACT_SHA')
    write(run/'ARTIFACT_SHA_INDEX.json',{'files':files,'file_count':len(files),'bytes':sum(f['bytes'] for f in files),'cloud_originals_preserved':True,'solution_vectors':'NOT_AVAILABLE_NO_SOLVE'})


def main(run):
    a=read(run/'AUTHORIZATION.json');write(run/'PHASE.json',{'phase':'BUILD','entered_epoch':time.time()});write(run/'WORKER_READY.json',{'pid':os.getpid(),'run_id':a['run_id']})
    start=time.time()
    while not (run/'PROCESS_IDENTITY.json').exists():
        if time.time()-start>10:raise RuntimeError('GUARD_STARTUP_FAILED')
        time.sleep(.05)
    assert alive(read(run/'GUARD_READY.json'))
    def progress(s):
        if (run/'STOP_REQUEST.json').exists():raise RuntimeError('STOP_BEFORE_'+s)
        if not alive(read(run/'GUARD_READY.json')) or time.time()-read(run/'GUARD_HEARTBEAT.json')['epoch']>8:raise RuntimeError('GUARD_NOT_FRESH')
        if time.time()>=phase_deadline(read(run/'PHASE.json'),a):raise TimeoutError('PHASE_DEADLINE_'+s)
        resource_gate(resources(run))
    try:
        progress('BUILD')
        subprocess.run([sys.executable,'-B',str(HERE/'d1_build.py'),str(run)],check=True)
        assert read(run/'BUILD_RESULT.json')['status']=='D1_BUILD_STATIC_ACCEPTED_NO_SOLVE'
        write(run/'PHASE.json',{'phase':'BRIDGE','entered_epoch':time.time()});progress('BRIDGE')
        from d1_bridge import bridge
        bridge(run/'artifacts',run/'bridge',progress)
        write(run/'PHASE.json',{'phase':'POSTPROCESS','entered_epoch':time.time()});progress('GATES')
        g=build_gates(run,progress)
        artifact_index(run,progress)
        write(run/'WORKER_EXIT.json',{'run_id':a['run_id'],'status':g['status'],'epoch':time.time(),'builds':1,'solver_calls':0,'retry':False})
        write(run/'PHASE.json',{'phase':'DONE','entered_epoch':time.time()})
        if g['status']!='D1_BUILD_GATES_PASS':raise SystemExit(3)
    except BaseException as e:
        write(run/'WORKER_FAILURE.json',{'run_id':a['run_id'],'error':type(e).__name__,'detail':str(e)[:20000],'traceback':traceback.format_exc()[-20000:],'epoch':time.time(),'solver_calls':0,'retry':False})
        write(run/'PHASE.json',{'phase':'FAILED','entered_epoch':time.time()});raise
if __name__=='__main__':main(Path(sys.argv[1]))
