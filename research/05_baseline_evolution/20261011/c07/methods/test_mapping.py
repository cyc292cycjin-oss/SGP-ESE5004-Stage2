"""Small no-solver independent interface positive/negative tests."""
from pathlib import Path
import sys,json,numpy as np
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W.parent/'c06_barconvtol_20261012/release'));sys.path.insert(0,str(W/'expression'))
from adapter import row_encoding,native_bounds,exact_readback
from c07_expression import overlay,checked_ldexp
tests=[]
def test(name,fn):fn();tests.append({'test':name,'status':'PASS','solver_calls':0})
def rejected(fn):
 try:fn()
 except (ValueError,AssertionError,TypeError):return
 raise AssertionError('negative case accepted')
class Fake:
 def __init__(self,a,mut=None):self.a=a;self.mut=mut
 def scalar(self,k,t):return {'NumVars':2,'NumConstrs':2,'ModelSense':1,'ObjCon':-3}[k]
 def array(self,k,s,n,dtype=None):
  if k=='VType':return np.full(n,b'C',dtype='S1')
  if k in ('Sense','RHS'):v=row_encoding(self.a['row_lower'],self.a['row_upper'])[0 if k=='Sense' else 1][s:s+n].copy()
  else:v=self.a[{'Obj':'cost','LB':'col_lower','UB':'col_upper'}[k]][s:s+n].copy()
  if k in ('LB','UB'):v=native_bounds(v)
  if self.mut and k==self.mut[0]:v[0]=self.mut[1]
  return v
 def matrix_columns(self,s,n):
  p,q=self.a['start'][s],self.a['start'][s+n];return self.a['start'][s:s+n]-p,self.a['index'][p:q],self.a['value'][p:q]
a={'start':np.array([0,2,4],dtype='i4'),'index':np.array([0,1,0,1],dtype='i4'),'value':np.array([1.,2.,-1.,1.]),'cost':np.array([3.,4.]),'row_lower':np.array([0.,-np.inf]),'row_upper':np.array([0.,5.]),'col_lower':np.array([-np.inf,0.]),'col_upper':np.array([np.inf,10.])}
m={'num_col':2,'num_row':2,'nnz':4,'sense':1,'offset':-3.}
test('positive_negative_zero_semantic_native_readback',lambda:exact_readback(Fake(a,('RHS',-0.)),m,a))
test('nonzero_one_ULP_native_readback_rejected',lambda:rejected(lambda:exact_readback(Fake(a,('Obj',np.nextafter(3.,4.))),m,a)))
test('NaN_RHS_rejected',lambda:rejected(lambda:row_encoding(np.array([np.nan]),np.array([np.nan]))))
test('undeclared_free_row_rejected',lambda:rejected(lambda:row_encoding(np.array([-np.inf]),np.array([np.inf]))))
test('free_column_endpoints_preserved',lambda:exact_readback(Fake(a),m,a))
test('mapping_shape_rejected',lambda:rejected(lambda:overlay(m,a,np.ones(2),np.ones(2),np.zeros(3,dtype='i2'),np.zeros(2,dtype='i2'))))
_,identity,_=overlay(m,a,np.ones(2),np.ones(2),np.zeros(2,dtype='i2'),np.zeros(2,dtype='i2'))
test('identity_expression_native_readback',lambda:exact_readback(Fake(a),m,identity))
_,new,delta=overlay(m,a,np.ones(2),np.ones(2),np.array([2,-1],dtype='i2'),np.array([1,-2],dtype='i2'))
def points():
 for x,feasible in [(np.array([1.,1.]),True),(np.array([4.,0.]),False)]:
  old=np.array([[1.,-1.],[2.,1.]])@x;z=checked_ldexp(x,-delta['delta_D_exponent']);act=np.zeros(2)
  for j in range(2):
   p,q=a['start'][j:j+2];np.add.at(act,a['index'][p:q],new['value'][p:q]*z[j])
  assert np.array_equal(checked_ldexp(act,-delta['delta_R_exponent']),old)
  assert bool(old[0]==0 and old[1]<=5)==feasible
test('known_feasible_and_violating_point_same_original_residual',points)
test('overflow_rejected',lambda:rejected(lambda:checked_ldexp(np.array([1e300]),np.array([1000]))))
test('underflow_nonreversible_rejected',lambda:rejected(lambda:checked_ldexp(np.array([1e-300]),np.array([-1000]))))
result={'status':'PASS','tests':tests,'native_API_calls':0,'solver_calls':0,'full_arrays':'separate C07_EXPRESSION_STATIC_CHECK.json'}
(W/'C07_MAPPING_INTERFACE_TESTS.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(tests))
