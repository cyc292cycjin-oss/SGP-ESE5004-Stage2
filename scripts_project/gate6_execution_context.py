"""Claim-bound Gate6 capability; metadata is provenance, never permission.

Only a live context minted after actual identity/resource/authorization checks
may build/install hooks or cross the single native-run boundary. TEST_ONLY
contexts exercise the same checks in temporary repositories and cannot run a
real Highs instance. The frozen input's solver_allowed flag is never changed.
"""
import copy,datetime,json,os,re,subprocess,weakref
from pathlib import Path
from gate5_resources import sha

_MINT=object()
_LIVE=weakref.WeakSet()
PROTECTED_ROLES={'FULL_SC_RESEARCH_BASELINE_UNSOLVED','GATE6_TEST_ONLY_FROZEN_INPUT'}

def require(ok,message):
    if not ok:raise ValueError(message)
def read(path):return json.loads(Path(path).read_text())
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,text=True).strip()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def validate_authorization(root,cfg,mode,out,path,expected_input_sha,runs_root):
    root=Path(root).resolve();out=Path(out).resolve();runs_root=Path(runs_root).resolve()
    require(mode in ('build','solve'),'Build/solve stage required')
    require(path is not None,'Independent Gate6 authorization required before full build/solve')
    a=read(path)
    require(a.get('gate')=='GATE6' and a.get('scenario')=='BASELINE' and a.get('stage')==mode,'Old Gate5 or wrong-stage authorization rejected')
    require(a.get('human_authorized') is True and bool(a.get('human_decision_reference')) and a.get('max_attempts')==1,'Future explicit one-attempt human authorization required')
    require(a.get('budget_approved') is True and a.get('budget')==cfg['proposed_budget'],'Resource/time/cost budget not approved')
    require(a.get('input_sha256')==cfg['input_sha256']==expected_input_sha and sha(root/cfg['input'])==expected_input_sha,'Authorized scientific/input identity differs')
    require(a.get('code_sha')==git(root,'rev-parse','HEAD') and not git(root,'status','--porcelain'),'Clean authorized code identity required')
    require(a.get('input_lock_sha256')==sha(root/cfg['lock']),'Authorization lock differs')
    lock=read(root/cfg['lock']);require(lock.get('gate')=='GATE6' and lock.get('input_sha256')==expected_input_sha,'Wrong Gate6 dependency identity')
    for row in lock['files']:
        p=root/row['path'];require(p.stat().st_size==row['size_bytes'] and sha(p)==row['sha256'],'Locked dependency changed: '+row['path'])
    require(a.get('tests_sha256')==sha(root/cfg['tests']),'Authorization test evidence differs')
    tests=read(root/cfg['tests'])
    require(tests.get('status')=='PASS' and tests.get('solver_calls')==tests.get('presolve_calls')==tests.get('getSolution_calls')==0,'No-solver prerequisite missing')
    require(tests['input_lock_sha256']==sha(root/cfg['lock']),'Tests are stale for execution lock')
    for rel,digest in tests['tested_code_sha256'].items():require(sha(root/rel)==digest,'Tested code changed: '+rel)
    require(a.get('run_id')==out.name and re.fullmatch(r'[0-9a-f]{64}',a.get('authorization_id','')),'Invalid authorization identity/run')
    require(out.parent==runs_root and out.name.startswith('cloud_gate6_'),'Gate6 non-overwrite run directory required')
    require(not out.exists(),'Existing run cannot be overwritten')
    claim=runs_root.parent/'evidence'/('gate6_authorization_'+a['authorization_id']+'.consumed.json')
    require(not claim.exists(),'Authorization already consumed')
    return a

def claim_execution(root,cfg,mode,out,path,*,expected_input_sha,runs_root,observation,network_validator,test_only=False):
    """Production passes its fixed root/input validator; tests use TEST_ONLY files."""
    root=Path(root).resolve();out=Path(out).resolve();path=Path(path).resolve()
    if test_only:
        require(out.parent!=Path('/root/autodl-tmp/SGP/runs') and cfg.get('fixture')=='TEST_ONLY','TEST_ONLY scope must be isolated')
    else:
        from inventory_audit_3h import INPUT_SHA
        require(expected_input_sha==INPUT_SHA and Path(runs_root)==Path('/root/autodl-tmp/SGP/runs'),'Production scope cannot be substituted')
    a=validate_authorization(root,cfg,mode,out,path,expected_input_sha,runs_root)
    from run_gate6_baseline import resource_admission
    require(resource_admission(observation,a['budget'])['status']=='PASS','Fresh resource admission failed')
    claim=out.parent.parent/'evidence'/('gate6_authorization_'+a['authorization_id']+'.consumed.json')
    with claim.open('x') as f:
        json.dump(dict(authorization=a,authorization_sha256=sha(path),claimed_at=now(),stage=mode,run_id=out.name,pid=os.getpid(),test_only=test_only),f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    return ExecutionContext(_MINT,root,cfg,out,path,claim,a,network_validator,test_only)

def checked(context):
    require(isinstance(context,ExecutionContext) and context in _LIVE and context._pid==os.getpid(),'Live claimed Gate6 execution context required')
    return context

class ExecutionContext:
    def __init__(self,token,root,cfg,out,path,claim,authorization,validator,test_only):
        require(token is _MINT,'Context can only be minted by validated claim')
        self.root=root;self.cfg=copy.deepcopy(cfg);self.out=out;self.source=root/cfg['input'];self._path=path;self._claim=claim
        self._a=copy.deepcopy(authorization);self._validator=validator;self._test_only=test_only;self._pid=os.getpid()
        self._auth_sha=sha(path);self._claim_sha=sha(claim);self._phase='CLAIMED';self._networks={};_LIVE.add(self)
    def _identity(self):
        checked(self)
        require(sha(self._path)==self._auth_sha and sha(self._claim)==self._claim_sha,'Authorization/claim changed')
        require(git(self.root,'rev-parse','HEAD')==self._a['code_sha'] and not git(self.root,'status','--porcelain'),'Execution code identity changed')
        require(sha(self.source)==self._a['input_sha256'] and sha(self.root/self.cfg['lock'])==self._a['input_lock_sha256'] and sha(self.root/self.cfg['tests'])==self._a['tests_sha256'],'Execution input/lock/tests changed')
    def provenance(self,purpose):
        return dict(gate='GATE6',scenario='BASELINE',run_id=self._a['run_id'],code_sha=self._a['code_sha'],input_sha256=self._a['input_sha256'],
            authorization_id=self._a['authorization_id'],authorization_sha256=self._auth_sha,claim_sha256=self._claim_sha,authorized_stage=self._a['stage'],purpose=purpose,test_only=self._test_only,reusable_permission=False)
    def build_network(self,purpose='initial',source=None):
        self._identity();require(source is None or Path(source).resolve()==self.source.resolve(),'Wrong reconstruction source')
        expected='CLAIMED' if purpose=='initial' else 'RESULTS' if purpose=='reconstruction' else None
        require(expected is not None and self._phase==expected,'Execution stage cannot build/rebuild here')
        import pypsa
        from assembly_components import install_research_constraint_hooks
        from lossless_gate5_lifecycle import bounded_build_allocator
        n=pypsa.Network(self.source);self._validator(n)
        require(n.meta.get('artifact_role') in PROTECTED_ROLES and n.meta.get('solver_allowed') is False,'Frozen production/TEST_ONLY input state required; diagnostic or mutable permission rejected')
        require((n.meta.get('fixture')=='TEST_ONLY')==self._test_only,'Production/test context mismatch')
        require(n.meta.get('scientific_results_allowed') is False and n.meta.get('formal_phase5_allowed') is not True,'Scientific/Phase5 permission forbidden')
        require('gate6_execution_record' not in n.meta,'Exported execution metadata cannot create another run')
        n.meta['gate6_parent_input_state']=dict(input_sha256=self._a['input_sha256'],artifact_role=n.meta['artifact_role'],solver_allowed=False,scientific_results_allowed=False,formal_phase5_allowed=n.meta.get('formal_phase5_allowed'))
        n.meta['gate6_execution_record']=self.provenance(purpose)
        self._phase='BUILDING' if purpose=='initial' else 'REBUILDING';self._networks[id(n)]=dict(ref=weakref.ref(n),purpose=purpose,hooks=False)
        with bounded_build_allocator():
            n.optimize.create_model();before=set(n.model.constraints);install_research_constraint_hooks(n,execution_context=self)
        self._binding(n)['hooks']=True;self._phase='BUILT' if purpose=='initial' else 'MAPPED'
        return n,before
    def _binding(self,n):
        record=self._networks.get(id(n))
        require(record is not None and record['ref']() is n,'Network is not bound to this execution')
        return record
    def permit_hooks(self,n):
        checked(self)
        require(self._phase in ('BUILDING','REBUILDING') and not self._binding(n)['hooks'],'Hook requires this context-bound network and build stage')
        require(n.meta.get('solver_allowed') is False and n.meta.get('gate6_execution_record')==self.provenance(self._binding(n)['purpose']),'Serialized/true metadata cannot replace execution authority')
    def begin_solve(self,native):
        self._identity();require(self._a['stage']=='solve' and self._phase=='BUILT','Solve stage and unused native attempt required')
        import highspy
        if self._test_only:require(not isinstance(native,highspy.Highs),'TEST_ONLY cannot call a real native solver')
        marker=self.out/'GATE6_NATIVE_RUN_ATTEMPT.json'
        with marker.open('x') as f:json.dump(dict(self.provenance('native_run'),attempt=1,at=now()),f);f.flush();os.fsync(f.fileno())
        self._phase='SOLVING'
    def finish_solve(self):
        checked(self);require(self._phase=='SOLVING','No native attempt to finish');self._phase='SOLVED'
    def begin_results(self,native):
        self._identity();require(self._a['stage']=='solve' and self._phase=='SOLVED','Results require the same completed solve attempt')
        import highspy
        if self._test_only:require(not isinstance(native,highspy.Highs),'TEST_ONLY cannot retrieve a real native solution')
        self._phase='RESULTS'
    def seal_network(self,n):
        checked(self);self._binding(n);require(self._phase=='MAPPED','Only this reconstructed network can be sealed')
        n.meta.update(solver_allowed=False,gate6_allowed=False,formal_phase5_allowed=False,scientific_results_allowed=False)
        n.meta['gate6_execution_record']=dict(self.provenance('completed_result'),execution_closed=True)
        self.close()
    def close(self):
        self._networks.clear();self._phase='CLOSED';_LIVE.discard(self)
