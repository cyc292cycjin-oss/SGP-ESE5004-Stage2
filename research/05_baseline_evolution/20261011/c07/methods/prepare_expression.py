"""One deterministic budget-matched power-of-two daily expression, alpha=1.
Reads frozen arrays; emits exponents and hashes, no optimizer or model build.
"""
from pathlib import Path
from fractions import Fraction as F
import sys,json,hashlib,math,time,numpy as np,xarray as xr
W=Path(__file__).resolve().parent;ROOT=W.parents[1];B=ROOT/'outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
C6=ROOT/'work/c06_barconvtol_20261012';sys.path.insert(0,str(C6/'release'))
from adapter import open_problem,validate
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def put(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
def ceilpow(v):
 e=math.ceil(math.log2(float(v)))
 assert F(2)**e>=v and F(2)**(e-1)<v
 return e
def main():
 t=time.monotonic();assert read(W/'C07_V4_APPLICABILITY.json')['scientific_decision_required'] is False
 out=W/'expression';out.mkdir(exist_ok=True);assert not list(out.iterdir()),'no overwrite of an expression'
 labels=read(B/'artifacts/mapping/LABELS.json');meta,a=open_problem(B/'bridge/math_problem')
 mm=read(B/'bridge/mapping/MAPPING_MANIFEST.json');scales={}
 for k in ['D','R','vlabels','clabels']:
  p=B/'bridge/mapping'/mm['arrays'][k]['file'];assert sha(p)==mm['arrays'][k]['sha256'];scales[k]=np.load(p,mmap_mode='r')
 D,R,vl,cl=[scales[k] for k in ['D','R','vlabels','clabels']]
 oldd=np.rint(np.log2(D)).astype('<i2');oldr=np.rint(np.log2(R)).astype('<i2')
 assert np.array_equal(np.exp2(oldd.astype(float)),D) and np.array_equal(np.exp2(oldr.astype(float)),R)
 dn=np.minimum(oldd,6);rn=np.maximum(oldr,-6)
 ds=xr.open_dataset(B/'artifacts/daily_365_unsolved.nc');networkmeta=json.loads(ds.attrs['meta'])
 accounts=networkmeta['external_pending_fixed_accounts'];groups=read(B/'artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json')['groups']
 es={};ps={};links={};buses={};plan=[];by={x['FixedAccountID']:x for x in accounts};budgets={}
 for x in accounts:
  k=x['FixedAccountID'];q=float(x['QuantityMWh']);b=min(.001+1e-7*q,1e-6*q);assert b>0
  er=ceilpow(F(8)*F(1e-6)*365/F(b));fr=ceilpow(F(8)*F(1e-6)*8760/F(b))
  es[k]=er;ps[k]=fr;links[x['Meter']]=fr;buses[x['ResourceBus']]=fr;budgets[k]=b
  plan.append({'asset':k,'Q_MWh':q,'B_MWh':b,'R_energy_exponent':er,'R_flow_exponent':fr,'D_e_exponent':-er,'D_p_meter_exponent':-fr,'energy_per_day_budget_scaled':b/365*2.**er,'flow_per_hour_budget_scaled':b/8760*2.**fr})
 for g in groups:
  final=by[g['accounts'][0]]['FinalBuses'];assert len(final)==1
  buses[final[0]]=ceilpow(F(8)*F(1e-6)*8760/F(min(budgets[k] for k in g['accounts'])))
 coverage=[]
 def apply(block,target,active,lookup,negative=False):
  p=B/'artifacts/mapping'/block['labels_file'];assert sha(p)==block['sha256'];lab=np.load(p,mmap_mode='r')
  if lookup is None:return
  if block['name'].startswith('ResearchStoreDirection-'):
   key=block['name'][len('ResearchStoreDirection-'):];assert key in ps;ids=lab.reshape(-1);ex=np.full(ids.shape,ps[key],dtype='<i2');mask=ids>=0
  else:
   dims=block['dims'];axes=[x for x in dims if x!='snapshot'];assert len(axes)==1
   axis=axes[0];names=block['coordinates'][axis];arr=np.array([lookup.get(k,-32768) for k in names],dtype='<i2');shape=[1]*lab.ndim;shape[dims.index(axis)]=len(arr)
   ex=np.broadcast_to(arr.reshape(shape),lab.shape).reshape(-1);ids=lab.reshape(-1);mask=(ids>=0)&(ex!=-32768)
  selected=ids[mask];order=np.argsort(active) if active is cl else np.arange(len(active));pos=np.searchsorted(active[order],selected)
  assert np.all(pos<len(active)),(block['name'],'label absent')
  where=order[pos];assert np.array_equal(active[where],selected),(block['name'],'label not in actual LP',selected[active[where]!=selected][:10])
  target[where]=(-ex[mask] if negative else ex[mask]);coverage.append({'family':block['name'],'assigned':len(selected)})
 for b in labels['variables']:
  name=b['name'];look=es if name=='Store-e' else ps if name=='Store-p' else links if name in ['Link-p','Link-p_nom'] else None
  apply(b,dn,vl,look,True)
  if not b['dims']:
   lab=int(np.load(B/'artifacts/mapping'/b['labels_file']));j=np.searchsorted(vl,lab);assert vl[j]==lab;dn[j]=oldd[j]
 for b in labels['constraints']:
  name=b['name'];look=es if name in ['Store-fix-e-lower','Store-fix-e-upper','Store-energy_balance'] else links if name.startswith(('Link-ext-p-','Link-fix-p-','Link-ext-p_nom-')) else buses if name.startswith('Bus-') else ps if name.startswith('ResearchStoreDirection-') else None
  apply(b,rn,cl,look)
 assert len(es)==807 and len(groups)==385
 np.save(out/'D_exponent.npy',dn.astype('<i2'));np.save(out/'R_exponent.npy',rn.astype('<i2'))
 # Reuse ONLY math/mapping functions, excluding the historical parameter hooks.
 source=ROOT/'work/gate6_numerical_remediation_20261010/numeric_adapter.py'
 code=source.read_text().split('\ndef production_hooks(')[0]
 (out/'c07_expression.py').write_text(code+'\n')
 sys.path.insert(0,str(out));from c07_expression import overlay,checked_ldexp
 newmeta,na,delta=overlay(meta,a,D,R,dn,rn)
 na['cost_scientific']=type(na['cost'])(a['cost_scientific'],lambda key:delta['delta_D_exponent'][key])
 static=validate(newmeta,na);stats={};rawhash={}
 for key,v in na.items():
  h=hashlib.sha256();mn=math.inf;mx=0.;finite=zero=0;maxulp=0.
  for s in range(0,len(v),200000):
   piece=np.ascontiguousarray(v[s:s+200000]);h.update(piece.tobytes());good=np.abs(piece[np.isfinite(piece)]);nonzero=good[good>0]
   finite+=len(good);zero+=int(np.count_nonzero(good==0))
   if len(nonzero):mn=min(mn,float(nonzero.min()));mx=max(mx,float(nonzero.max()))
  rawhash[key]=h.hexdigest();stats[key]={'min_abs_nonzero':mn if math.isfinite(mn) else None,'max_abs':mx,'finite':finite,'zero':zero,'count':len(v),'dtype':v.dtype.str}
 # independent mapping identity with exact dyadic rational arithmetic, no solves
 A=[[F(2),F(-3)],[F(1,2),F(4)]];x=[F(3,8),F(-5,4)];pi=[F(2),F(-1,8)];c=[F(7),F(9)];rc=[c[j]-sum(A[i][j]*pi[i] for i in range(2)) for j in range(2)]
 dt=[F(8),F(1,4)];rt=[F(1,2),F(16)];z=[x[j]/dt[j] for j in range(2)];pn=[pi[i]/rt[i] for i in range(2)];rn0=[rc[j]*dt[j] for j in range(2)]
 An=[[rt[i]*A[i][j]*dt[j] for j in range(2)] for i in range(2)]
 assert all(sum(An[i][j]*z[j] for j in range(2))==rt[i]*sum(A[i][j]*x[j] for j in range(2)) for i in range(2))
 assert all(c[j]*dt[j]-sum(An[i][j]*pn[i] for i in range(2))-rn0[j]==0 for j in range(2))
 assert sum(c[j]*x[j] for j in range(2))==sum(c[j]*dt[j]*z[j] for j in range(2))
 for vals,k in [(np.array([0.,-0.,np.inf,-np.inf]),np.array([2,-2,4,-4])),(np.array([1.,-2.,3.25]),np.array([1,-4,3]))]:assert np.array_equal(checked_ldexp(checked_ldexp(vals,k),-k).view('u8'),vals.view('u8'))
 tests={'status':'PASS','rational_primal_dual_cost_mapping':True,'positive_negative_zero_and_declared_infinity_reversible':True,'whole_arrays_binary64_reverse_exact':True,'native_runtime_test':'PENDING','no_solver_calls':True}
 spec={'expression_id':'C07_DAILY_RESOURCE_BUDGET_POW2_V1','alpha':1,'status':'FROZEN_FOR_C07A_AND_CONDITIONAL_C07B','num_row':meta['num_row'],'num_col':meta['num_col'],'nnz':meta['nnz'],'offset':meta['offset'],'scientific_offset':meta['scientific_offset'],'source_math_manifest_sha256':sha(B/'bridge/math_problem/MATH_PROBLEM.json'),'source_mapping_manifest_sha256':sha(B/'bridge/mapping/MAPPING_MANIFEST.json'),'source_daily_V4_sha256':sha(B/'artifacts/DAILY_V4_BINDING.json'),'parent_V4_sha256':sha(C6/'release/V4_APPROVED.json'),'source_cost_sha256':meta['arrays']['cost']['sha256'],'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in out.iterdir() if p.is_file()},'transformed_array_payload_sha256':rawhash,'array_stats':stats,'changed_D':int(np.count_nonzero(dn!=oldd)),'changed_R':int(np.count_nonzero(rn!=oldr)),'D_exponent_range':[int(dn.min()),int(dn.max())],'R_exponent_range':[int(rn.min()),int(rn.max())],'rules':{'ordinary_D':'min(oldD,64), fixed objective-only variables unchanged','ordinary_R':'max(oldR,1/64)','tau_design':1e-6,'safety':8,'N':365,'H':8760,'resource_R_energy':'2^ceil(log2(8*tau*N/Bi))','resource_R_flow':'2^ceil(log2(8*tau*H/Bi))','resource_D_e':'1/R_energy','resource_D_p_meter_p_capacity':'1/R_flow','group_bus_R':'2^ceil(log2(8*tau*H/min_Bi_in_group))','ordinary_row_reference_lower_bound':'.001; R>=1/64 makes at least1.5625e-5 in input units','limitation':'Absolute feasibility tau is a design reference, not a guarantee on Barrier relative stopping or cumulative residuals. Full original V4 unchanged.'},'input_arrays_materialized':False,'source_arrays_changed':False,'native_readback_required':True,'mapping':'z_old=2^(dn-do)z_new; pi_old=2^(rn-ro)pi_new; rc_old=2^(do-dn)rc_new','tests':tests,'elapsed_seconds':time.monotonic()-t}
 put(out/'C07_EXPRESSION_BINDING.json',spec);put(W/'C07_RESOURCE_SCALE_PLAN.json',{'accounts':plan,'groups':groups,'coverage':coverage});put(W/'C07_EXPRESSION_STATIC_CHECK.json',{'status':'PASS','binding_sha256':sha(out/'C07_EXPRESSION_BINDING.json'),'validation':static,'tests':tests,'stats':stats,'elapsed_seconds':time.monotonic()-t})
 print(json.dumps({k:spec[k] for k in ['expression_id','changed_D','changed_R','D_exponent_range','R_exponent_range','elapsed_seconds']}));print('BINDING',sha(out/'C07_EXPRESSION_BINDING.json'))
if __name__=='__main__':main()
