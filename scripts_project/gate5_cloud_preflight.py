"""Read/build/test-only cloud gates. This module never invokes a real solver."""
import argparse,datetime,gc,hashlib,importlib.metadata as metadata,json,math,os,platform,re,subprocess,sys,traceback
from pathlib import Path
from unittest.mock import patch
from gate5_resources import current_evidence,sha
from gate5_cloud_resources import snapshot,admission

TESTS=['test_chunk_build','test_precision_handoff_no_solve','test_lossless_gate5_lifecycle',
       'test_gate5_lossless_integration','test_lossless_export','test_gate5_resources',
       'test_solver_result_qualification','test_gate5_cloud_resources']


def json_write(path,value):
    p=Path(path);t=p.with_suffix(p.suffix+'.tmp')
    t.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');os.replace(t,p)


def require(condition,description):
    if not condition:raise ValueError(description)


def checked_file(base,relative,expected):
    p=Path(base)/relative
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,'Unsafe manifest relative path')
    require(p.is_file(),'Required file missing: '+relative)
    require(sha(p)==expected,'Required file SHA mismatch: '+relative)
    return p


def environment_identity(expected):
    import highspy,h5py,netCDF4
    normalize=lambda s:re.sub(r'[-_.]+','-',s).lower()
    actual={normalize(d.metadata['Name']):d.version for d in metadata.distributions()}
    missing=[d for d in expected['distributions'] if actual.get(normalize(d['name']))!=d['version']]
    require(not missing,'Python distribution mismatches: '+str(missing))
    require(platform.python_version()==expected['python'],'Python version changed')
    core={name:metadata.version(name) for name in expected['core']}
    require(core==expected['core'],'Frozen core versions changed')
    require(highspy.Highs().version()==expected['core']['highspy'],'Native HiGHS version changed')
    installed={p['name']:p for p in (json.loads(f.read_text()) for f in (Path(sys.prefix)/'conda-meta').glob('*.json'))}
    mismatches=[]
    for p in expected['conda_packages']:
        if p['channel']=='pypi':continue
        a=installed.get(p['name'],{})
        if (a.get('version'),a.get('build'))!=(p['version'],p['build_string']):mismatches.append(p['name'])
    require(not mismatches,'Exact conda build mismatches: '+str(mismatches))
    native=dict(highs=highspy.Highs().version(),hdf5=h5py.version.hdf5_version,
                netcdf_c=netCDF4.getlibversion(),netcdf_hdf5=netCDF4.__hdf5libversion__)
    if 'native_libraries' in expected:require(native==expected['native_libraries'],'Native library identity changed')
    return dict(status='PASS',python=platform.python_version(),core=core,native_libraries=native,
                conda_builds_checked=len(installed),python_distributions_checked=len(expected['distributions']),
                platform=platform.platform(),libc=platform.libc_ver(),prefix=sys.prefix)


def scientific_identity(n,root,build_model=True):
    import numpy as np
    from assembly_components import validate_hooks,check_global_constraints,install_research_constraint_hooks
    from fixed_accounts import validate_exported_accounting
    from inventory_audit import audit
    from run_gate5_validation import hook_receipt
    from lossless_gate5_lifecycle import bounded_build_allocator
    validate_hooks(n);check_global_constraints(n);validate_exported_accounting(n)
    identity=audit(n,root)
    prior=json.loads((root/'results_project/validation/inventory_local_20261006_02/FORMULATION_MAPPING_AND_ROUNDING_AUDIT.json').read_text())
    require(identity==prior,'Frozen source-operation bounds changed')
    stock=math.fsum(float(v['capacity_mw']) for v in n.meta['existing_unit_components'].values())
    actual=dict(snapshots=len(n.snapshots),geographical_nodes=int(n.buses.carrier.isin(['AC','DC']).sum()),
                accounts=int(n.loads.source_account_id.nunique()),loads=len(n.loads),stock_mw=stock,
                pending_fixed_terms=len(n.meta['external_pending_fixed_accounts']),
                null_policy_weights=sum(v['policy_weight'] is None for v in n.meta['physical_carbon_map']),
                policy_enabled=n.meta['policy_enabled'],native_lv_limit=dict(type=str(n.global_constraints.at['lv_limit','type']),
                carrier_attribute=str(n.global_constraints.at['lv_limit','carrier_attribute']),
                sense=str(n.global_constraints.at['lv_limit','sense']),constant=float(n.global_constraints.at['lv_limit','constant'])))
    expected=dict(snapshots=365,geographical_nodes=100,accounts=171,loads=1737,stock_mw=187400.4,
                  pending_fixed_terms=807,null_policy_weights=200,policy_enabled=False)
    for key,value in expected.items():require(actual[key]==value,'Scientific identity mismatch: '+key+'='+str(actual[key]))
    require(actual['native_lv_limit']['type']=='transmission_volume_expansion_limit','Native lv_limit type changed')
    require(actual['native_lv_limit']['carrier_attribute']=='AC, DC','Native lv_limit carrier boundary changed')
    require(actual['native_lv_limit']['sense']=='<=','Native lv_limit sense changed')
    if build_model:
        with bounded_build_allocator():
            n.optimize.create_model();before=set(n.model.constraints);install_research_constraint_hooks(n)
        hooks=hook_receipt(n,before)
        actual.update(research_hook_groups=len(hooks['research_constraint_names']),variables=int(n.model.nvars),constraints=int(n.model.ncons))
        require(actual['research_hook_groups']==1003,'Research hook identity changed')
        require((actual['variables'],actual['constraints'])==(2450005,6042238),'Frozen model dimensions changed')
        actual['constraint_attachment_receipt']=hooks
    actual['source_operation_identity']='EXACT_MATCH'
    return actual


def run(manifest_path,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1];cloud_root=root.parent
    result=dict(status='FAIL',run_authorized=False,solver_runs=0,presolve_calls=0,gate6_runs=0,
                observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        manifest=json.loads(Path(manifest_path).read_text());head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
        require(head==manifest['code_sha'],'Deployment Git HEAD mismatch')
        require(subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip()=='research/full-sc-baseline','Wrong branch')
        require(not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(),'Cloud Git tree is dirty')
        subprocess.run(['git','merge-base','--is-ancestor',manifest['scientific_freeze_sha'],head],cwd=root,check=True)
        for r in manifest['files']:checked_file(cloud_root,r['TargetRelativePath'],r['CloudExpectedSHA256'])
        for r in manifest['environment_files']:checked_file(cloud_root,r['TargetRelativePath'],r['SHA256'])
        result.update(code_identity='PASS',input_identity='PASS',code_sha=head,input_sha256=manifest['input_sha256'])
        frozen_env=json.loads((cloud_root/'env/spec/CLOUD_ENVIRONMENT_VERSIONS.json').read_text())
        env=environment_identity(frozen_env);json_write(output/'CLOUD_ENVIRONMENT_MANIFEST.json',env)
        result['environment_identity']='PASS'
        resource_snapshot=snapshot(cloud_root);json_write(output/'CLOUD_RESOURCE_SNAPSHOT.json',resource_snapshot)
        ready=admission(current_evidence(root),resource_snapshot);result['resource_admission']=ready
        require(ready['status']=='PASS','Cloud resource admission failed: '+str(ready['reasons']))
        test_dir=output/'no_solve_tests';test_dir.mkdir();temp=test_dir/'tmp';temp.mkdir()
        tests=[]
        for name in TESTS:
            print('NO_SOLVE_TEST '+name,flush=True)
            receipt=test_dir/(name+'.json')
            with (test_dir/(name+'.log')).open('w') as log:
                p=subprocess.run([sys.executable,str(root/'scripts_project'/(name+'.py')),str(receipt)],cwd=root,
                                 env=dict(os.environ,TMPDIR=str(temp),PYTHONDONTWRITEBYTECODE='1'),stdout=log,stderr=subprocess.STDOUT,timeout=240)
            require(p.returncode==0 and receipt.is_file(),'No-solve test failed: '+name)
            r=json.loads(receipt.read_text());require(r.get('status')=='PASS','Test receipt failed: '+name)
            tests.append(dict(test=name,sha256=sha(receipt),status='PASS'))
        result['no_solve_tests']=tests
        print('FROZEN_INPUT_AND_HOOK_BUILD_VALIDATION_NO_SOLVER',flush=True)
        import pypsa,highspy
        with patch.object(highspy.Highs,'run',side_effect=AssertionError('PREFLIGHT_NO_SOLVE')),patch.object(highspy.Highs,'presolve',side_effect=AssertionError('PREFLIGHT_NO_PRESOLVE')):
            source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
            require(sha(source)==manifest['input_sha256'],'Frozen input mismatch')
            n=pypsa.Network(source);science=scientific_identity(n,root)
            json_write(output/'CLOUD_SCIENTIFIC_IDENTITY.json',science)
            del n;gc.collect()
        result.update(status='PASS',scientific_identity='PASS',resource_ready=True,eligible_for_one_pre_authorized_gate5=True,
                      authorization_note='The separate human authorization and durable one-call claim remain required by the runner.')
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error))
        (output/'failure_traceback.txt').write_text(traceback.format_exc())
    finally:json_write(output/'CLOUD_PREFLIGHT_RESULT.json',result)
    print(json.dumps(result,indent=2),flush=True)
    return 0 if result['status']=='PASS' else 2

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();raise SystemExit(run(a.manifest,a.output))
