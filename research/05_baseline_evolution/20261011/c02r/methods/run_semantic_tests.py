"""Small independent exact-value tests; no PyPSA/Linopy or solver import/build."""
from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace
import ast, json, hashlib, sys, tempfile
import numpy as np
import pandas as pd
import xarray as xr
ROOT=Path(__file__).resolve().parent
if not (ROOT/'candidate').is_dir():ROOT=ROOT.parent
sys.path.insert(0,str(ROOT/'candidate'))
from c02_semantics import rhs_exact,bounds_exact,SemanticCheckError

asset='ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 2 :: fixed resource'
checks=[]
temp=Path(tempfile.mkdtemp(prefix='semantic_tests_',dir=ROOT))
def record(name,fn,reason=None):
    try: result=fn()
    except SemanticCheckError as exc:
        assert reason==exc.evidence['reason'],(name,reason,exc.evidence['reason'])
        assert exc.evidence['asset_id']==asset
        assert exc.evidence['constraint_family']
        assert exc.evidence['rows']
        assert exc.evidence['rtol']==exc.evidence['atol']==0
        json.dumps(exc.evidence,allow_nan=False)
        checks.append({'name':name,'result':'PASS_REJECTION','reason':reason})
        return exc.evidence
    else:
        assert reason is None,(name,'unexpected pass')
        checks.append({'name':name,'result':'PASS_ACCEPTANCE'})
        return result
def rhs(a,e,sign='=',shape=None,expected_sign='=',report=None):
    a=np.asarray(a);e=np.asarray(e)
    return rhs_exact(a,e,actual_signs=np.full(a.shape,sign) if shape is None else np.full(shape,sign),expected_sign=expected_sign,
       asset_id=asset,family='Store-energy_balance',row_labels=np.arange(e.size).reshape(e.shape)+101,report_path=report)
def bound(lo,hi,elo,ehi,report=None):
    return bounds_exact(np.asarray(lo,dtype='f8'),np.asarray(hi,dtype='f8'),np.asarray(elo,dtype='f8'),np.asarray(ehi,dtype='f8'),
        asset_id=asset,family='Store-fix-e-lower',row_labels=np.arange(len(elo))+202,report_path=report)

res=record('positive_negative_zero_pass',lambda:rhs(np.array([-0.,0.]),np.array([0.,-0.])))
assert res['signed_zero_pairs']==2
record('finite_exact_nonzero_pass',lambda:rhs(np.array([1.,-2.]),np.array([1.,-2.])))
u=np.nextafter(1.,np.inf)
assert Fraction(float(u))-Fraction(1)==Fraction(1,2**52)
ev=record('nonzero_one_ULP_rejected',lambda:rhs(np.array([u]),np.array([1.]),report=temp/'ulp.json'),'FINITE_RHS_NOT_EXACT')
assert ev['rows'][0]['actual_hex']==u.hex() and ev['rows'][0]['expected_hex']==float(1).hex() and ev['rows'][0]['row_label']=='101'
assert json.loads((temp/'ulp.json').read_text())==ev
record('smallest_positive_nonzero_not_zero',lambda:rhs(np.array([np.nextafter(0.,1.)]),np.array([0.])),'FINITE_RHS_NOT_EXACT')
for side in ['actual','expected']:
    for value in [np.nan,np.inf,-np.inf]:
        record(side+'_'+str(value)+'_RHS_rejected',lambda side=side,value=value:rhs(np.array([value if side=='actual' else 1.]),np.array([value if side=='expected' else 1.])),'NONFINITE_RHS')
record('shape_rejected_without_broadcast',lambda:rhs(np.zeros((2,1)),np.zeros(2)),'SHAPE_MISMATCH')
record('float32_rejected_before_comparison',lambda:rhs(np.array([1.],dtype='f4'),np.array([1.])),'NOT_BINARY64')
record('wrong_direction_rejected',lambda:rhs(np.array([-0.]),np.array([0.]),sign='>='),'ROW_DIRECTION_MISMATCH')
record('unknown_direction_rejected',lambda:rhs(np.array([0.]),np.array([0.]),sign='>'),'ROW_DIRECTION_MISMATCH')
record('sign_shape_rejected',lambda:rhs(np.zeros(2),np.zeros(2),shape=(1,)),'SIGN_SHAPE_MISMATCH')
record('zero_lower_open_upper_pass',lambda:bound([-0.],[np.inf],[0.],[np.inf]))
record('open_lower_finite_upper_pass',lambda:bound([-np.inf],[1.],[-np.inf],[1.]))
record('signed_zero_equality_bound_pass',lambda:bound([-0.],[-0.],[0.],[0.]))
record('wrong_open_side_rejected',lambda:bound([np.inf],[1.],[-np.inf],[1.]),'OPEN_SIDE_SENTINEL_MISMATCH')
record('finite_endpoint_to_inf_rejected',lambda:bound([-np.inf],[1.],[0.],[1.]),'UNEXPECTED_NONFINITE_BOUND')
record('bound_one_ULP_rejected',lambda:bound([u],[2.],[1.],[2.]),'FINITE_BOUND_NOT_EXACT')
record('swapped_lower_upper_rejected',lambda:bound([2.],[1.],[1.],[2.]),'FINITE_BOUND_NOT_EXACT')
record('nan_bound_rejected',lambda:bound([np.nan],[1.],[0.],[1.]),'NAN_BOUND')
record('invalid_expected_bound_rejected',lambda:bound([0.],[1.],[np.inf],[1.]),'INVALID_EXPECTED_ROW_BOUNDS')
record('both_sides_open_row_rejected',lambda:bound([-np.inf],[np.inf],[-np.inf],[np.inf]),'INVALID_EXPECTED_ROW_BOUNDS')
record('bound_shape_rejected',lambda:bound([0.,0.],[1.],[0.],[1.]),'SHAPE_MISMATCH')
previous=(temp/'ulp.json').read_bytes()
ev=record('failure_file_never_overwritten',lambda:rhs(np.array([2.]),np.array([1.]),report=temp/'ulp.json'),'FINITE_RHS_NOT_EXACT')
assert ev['persistence_error_type']=='FileExistsError' and (temp/'ulp.json').read_bytes()==previous

# Independently execute only the newly wired per-asset validation loops, using
# xarray stand-ins for already-built constraint attributes, never a model.
tree=ast.parse((ROOT/'candidate/c02_model.py').read_text())
export=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='export_model')
storeloop=next(n for n in export.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='asset')
busloop=next(n for n in export.body if isinstance(n,ast.For) and ast.unparse(n.iter)=="led['groups']")
def block(name,ids,rhs,sign,start=1000,dim='Store'):
    data=np.asarray(rhs,dtype='f8').reshape(365,len(ids));coords={'snapshot':np.arange(365),dim:ids}
    return SimpleNamespace(labels=xr.DataArray(np.arange(start,start+data.size).reshape(data.shape),dims=['snapshot',dim],coords=coords),
        rhs=xr.DataArray(data,dims=['snapshot',dim],coords=coords),sign=xr.DataArray(sign))
def run_store_loop(change=None):
    q=1.125; a=np.r_[-q,-np.zeros(364)]
    if change=='value':a[7]=np.nextafter(0.,1.)
    blocks={'Store-energy_balance':block('dynamic',[asset],a,'='),
       'Store-fix-e-lower':block('lo',[asset],-np.zeros(365),'<=' if change=='direction' else '>=',start=2000),
       'Store-fix-e-upper':block('hi',[asset],np.full(365,q),'<=',start=3000)}
    n=SimpleNamespace(stores=pd.DataFrame({'e_initial':[q]},index=[asset]))
    scope={'np':np,'m':SimpleNamespace(constraints=blocks),'n':n,'owner':{asset},'bounds':{},'rhs_exact':rhs_exact,
           'failure_path':temp/(str(change)+'_store.json')}
    exec(compile(ast.Module(body=[storeloop],type_ignores=[]),'<candidate_store_checks>','exec'),scope)
    assert len(scope['bounds'])==731
record('wired_Store_dynamic_lower_upper_signed_zeros_pass',lambda:run_store_loop())
record('wired_Store_lower_wrong_direction_rejected',lambda:run_store_loop('direction'),'ROW_DIRECTION_MISMATCH')
record('wired_Store_nonzero_residual_rejected',lambda:run_store_loop('value'),'FINITE_RHS_NOT_EXACT')
def run_bus_loop(change=False):
    vals=-np.zeros(365)
    if change:vals[5]=1.
    blocks={'Bus-nodal_balance':block('bus',[asset],vals,'=',dim='Bus'),
            'Bus-meshed-nodal_balance':block('mesh',[],np.empty((365,0)),'=',dim='Bus')}
    n=SimpleNamespace(loads=pd.DataFrame({'bus':[asset]},index=['test_load']),
          loads_t=SimpleNamespace(p_set=pd.DataFrame({'test_load':np.zeros(365)})))
    scope={'np':np,'m':SimpleNamespace(constraints=blocks),'n':n,'led':{'groups':[{'load':'test_load'}]},
           'bounds':{},'rhs_exact':rhs_exact,'failure_path':temp/(str(change)+'_bus.json')}
    exec(compile(ast.Module(body=[busloop],type_ignores=[]),'<candidate_bus_checks>','exec'),scope)
    assert len(scope['bounds'])==365
record('wired_final_Bus_signed_zero_pass',lambda:run_bus_loop())
record('wired_final_Bus_changed_RHS_rejected',lambda:run_bus_loop(True),'FINITE_RHS_NOT_EXACT')

bitsnode=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bits')
ns={'np':np};exec(compile(ast.Module(body=[bitsnode],type_ignores=[]),'<unchanged_bits>','exec'),ns)
try:ns['bits'](np.array([0.]),np.array([-0.]))
except ValueError:checks.append({'name':'frozen_identity_bits_still_reject_signed_zero','result':'PASS_REJECTION'})
else:raise AssertionError('bits globally relaxed')
for name in ['c02_model.py','c02_semantics.py']:
    t=ast.parse((ROOT/'candidate'/name).read_text())
    for node in ast.walk(t):
        if isinstance(node,ast.Call):
            fname=node.func.attr if isinstance(node.func,ast.Attribute) else node.func.id if isinstance(node.func,ast.Name) else ''
            assert fname not in {'optimize','presolve','IIS','feasRelax','solve','solve_model','GRBoptimize','GRBstartenv'},fname
assert not any(k.split('.')[0] in {'pypsa','linopy','gurobipy','highspy','mosek'} for k in sys.modules)
checks.append({'name':'no_model_or_solver_module_imported_no_solver_calls_in_candidate','result':'PASS'})
result={'status':'PASS_LOCAL_CHECKER_TESTS_ONLY','checks':checks,'count':len(checks),
  'candidate_SHA256':hashlib.sha256((ROOT/'candidate/c02_model.py').read_bytes()).hexdigest(),
  'helper_SHA256':hashlib.sha256((ROOT/'candidate/c02_semantics.py').read_bytes()).hexdigest(),
  'model_builds':0,'network_builds':0,'solver_calls':0,'cloud_connections':0,'V4_thresholds_changed':False,
  'full_LP_readback':'NOT_TESTED','run_authorized':False,'test_detail_path':str(temp)}
(ROOT/'C02R_LOCAL_UNIT_TESTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'checks':len(checks),'model_builds':0,'solver_calls':0}))
