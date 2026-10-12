"""122-only admission: metadata and one licensed environment, no native model."""
from pathlib import Path
import base64,ctypes as C,hashlib,json,os,platform,stat,sys,time
sys.dont_write_bytecode=True
ROOT=Path('/root/autodl-tmp/SGP')
OLD=ROOT/'incoming/c02_build_only_122_20261012_856e9486/release'
sys.path.insert(0,str(OLD))
import c02_common as common
assert platform.node()=='autodl-container-21104cb00b-43be1fed'
pub=Path('/etc/ssh/ssh_host_ed25519_key.pub').read_text().split()
assert pub[0]=='ssh-ed25519'
assert base64.b64encode(hashlib.sha256(base64.b64decode(pub[1])).digest()).decode().rstrip('=')=='liZ36vNCsNcNdXeWs4f+g5ZIhPM/ZihP834vxs8Ulqc'
record={'schema':'C02R_C03_EARLY_ADMISSION_V1','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'hostname':platform.node(),'resources':common.resources(ROOT),'versions':common.versions(),'native_model_created':False,'optimize_calls':0,'build_calls':0,'license_contents_opened_by_probe':False}
out=ROOT/'incoming/c02r_c03_admission_20261012_v1'
out.mkdir(exist_ok=False)
env=C.c_void_p()
lib=None
try:
    common.resource_gate(record['resources'],start=True)
    record['resource_gate']='PASS'
    lp=Path('/root/.config/gurobi/gurobi.lic');s=lp.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_uid==0 and not stat.S_IMODE(s.st_mode)&0o077
    assert os.access(lp,os.R_OK)
    for p in lp.parents:
        q=p.lstat();assert stat.S_ISDIR(q.st_mode) and q.st_uid==0 and not stat.S_IMODE(q.st_mode)&0o022
    os.environ['GRB_LICENSE_FILE']=str(lp)
    record['license_path']={'path':str(lp),'regular_file':True,'mode':oct(stat.S_IMODE(s.st_mode)),'explicit_worker_environment':os.environ['GRB_LICENSE_FILE']==str(lp)}
    dll=Path('/root/autodl-tmp/SGP/env/gate5/lib/libgurobi120.so')
    h=common.sha(dll);assert h=='af7c367e21efc6fe9d273f84cdc5dda3bf62edf8ddcb273be50be3b37a0cec3c'
    record['library']={'path':str(dll),'realpath':str(dll.resolve()),'sha256':h}
    lib=C.CDLL(str(dll))
    lib.GRBversion.argtypes=[C.POINTER(C.c_int)]*3;lib.GRBversion.restype=None
    v=[C.c_int() for _ in range(3)];lib.GRBversion(*(C.byref(x) for x in v))
    record['native_version']=[x.value for x in v];assert record['native_version']==[12,0,3]
    lib.GRBemptyenv.argtypes=[C.POINTER(C.c_void_p)];lib.GRBemptyenv.restype=C.c_int
    lib.GRBsetintparam.argtypes=[C.c_void_p,C.c_char_p,C.c_int];lib.GRBsetintparam.restype=C.c_int
    lib.GRBstartenv.argtypes=[C.c_void_p];lib.GRBstartenv.restype=C.c_int
    lib.GRBfreeenv.argtypes=[C.c_void_p];lib.GRBfreeenv.restype=None
    lib.GRBgeterrormsg.argtypes=[C.c_void_p];lib.GRBgeterrormsg.restype=C.c_char_p
    record['emptyenv_return_code']=int(lib.GRBemptyenv(C.byref(env)))
    assert record['emptyenv_return_code']==0
    assert lib.GRBsetintparam(env,b'OutputFlag',0)==0
    start=time.monotonic();rc=int(lib.GRBstartenv(env))
    record['startenv_return_code']=rc;record['startenv_seconds']=time.monotonic()-start
    record['environment_started']=rc==0
    if rc:
        # Never save vendor text; it may contain credential values.
        raw=(lib.GRBgeterrormsg(env) or b'').decode('utf8','replace').lower()
        terms={'license file':'LICENSE_FILE_CONFIGURATION','expired':'EXPIRED','token':'TOKEN_SERVICE','wls':'WLS_SERVICE','resolve':'DNS_RESOLUTION','connect':'CONNECTION','network':'NETWORK','certificate':'TLS_CERTIFICATE','not valid':'NOT_VALID','invalid':'INVALID','permission':'PERMISSION','hostid':'HOST_ID','size':'SIZE_LIMIT'}
        record['safe_error_categories']=[v for k,v in terms.items() if k in raw] or ['UNCLASSIFIED_NATIVE_LICENSE_ERROR']
        raise RuntimeError('NATIVE_ENVIRONMENT_START_FAILED')
    record['status']='EARLY_ADMISSION_PASS'
except Exception as exc:
    record['status']='EARLY_ADMISSION_BLOCKED';record['failure_type']=type(exc).__name__;record['failure_stage']=('WLS' if 'startenv_return_code' in record else 'RESOURCE_IDENTITY_OR_LICENSE_PATH')
finally:
    if env.value and lib is not None:lib.GRBfreeenv(env);record['environment_freed']=True
    record['resources_after']=common.resources(ROOT)
    common.write(out/'EARLY_ADMISSION.json',record)
    print(json.dumps(record,ensure_ascii=False,indent=2))
