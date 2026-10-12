"""Bounded independent exact source and V4 applicability arithmetic. No solver."""
from pathlib import Path
from fractions import Fraction as F
import json,hashlib,math,sys,numpy as np,xarray as xr
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
B=ROOT/'outputs/c03_daily_diagnostic/c02r_c03_daily122_20261012T044259Z_25e62c10/cloud_run'
C6=ROOT/'work/c06_barconvtol_20261012'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(n,v):
 with (W/n).open('x') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 accounts=read(C6/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json')['accounts'];by={a['asset']:a for a in accounts}
 groups=read(B/'artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json')['groups']
 ds=xr.open_dataset(B/'artifacts/daily_365_unsolved.nc');meta=json.loads(ds.attrs['meta'])
 # All source Q/demand/weights are checked independently of returned candidates.
 loadnames=list(map(str,ds['loads_t_p_set_i'].values));w=ds['snapshots_stores'].values
 loads=ds['loads_t_p_set'].values
 records=[];under=[]
 for g in groups:
  aa=[by[k] for k in g['accounts']];q=sum((F(a['Q_MWh']) for a in aa),F())
  # fixed terminal biomass loads are static; do not substitute rounded prior total.
  p=loads[:,loadnames.index(g['load'])];assert np.all(p==p[0]);d=sum((F(float(h))*F(float(v)) for h,v in zip(w,p)),F())
  assert d==F(g['D']) and q==F(g['Q']) and q-d==F(g['slack']) and q>=d
  budgets=[min(F(.001)+F(1e-7)*F(a['Q_MWh']),F(1e-6)*F(a['Q_MWh'])) for a in aa]
  s=q-d;assert s<min(budgets)
  record={'load':g['load'],'accounts':g['accounts'],'D_exact':str(d),'Q_exact':str(q),'Sg_exact':str(s),'Sg_MWh':float(s),'min_Bi_exact_formula':str(min(budgets)),'Sg_over_min_Bi':float(s/min(budgets)),'all_exact_feasible_terminal_stocks_within_Bi':True}
  records.append(record)
  for a in aa:
   c=a['C06'];m=c['metrics']
   if not c['checks']['annual'] and m['annual_signed_error_MWh']<0:
    under.append({'asset':a['asset'],'Q':a['Q_MWh'],'underuse_MWh':-m['annual_signed_error_MWh'],'terminal_stock_MWh':m['terminal_stock_MWh'],'budget_MWh':c['budget_MWh'],'source_group_slack_MWh':float(s),'same_group_negative_terminal_MWh':math.fsum(min(by[k]['C06']['metrics']['terminal_stock_MWh'],0) for k in g['accounts']),'group':g['load'],'source_slack_explains_underuse':False})
 assert len(accounts)==807 and len(groups)==385 and len(under)==23
 # Endpoint and stationarity are checked without executing production acceptance.
 sys.path.insert(0,str(C6/'release'));import basis_free as bf
 v=np.array([2.,2.,3.,0.]);lo=np.array([2.,-np.inf,-np.inf,-np.inf]);hi=np.array([2.,2.,np.inf,np.inf]);y=np.array([-4.,-3.,0.,2.])
 viol,sign,comp,dual=bf.endpoint_metrics(v,lo,hi,y)
 assert np.array_equal(viol,[0,0,0,0]) and np.array_equal(sign,[0,0,0,2]) and np.array_equal(comp,[0,0,0,0]) and np.array_equal(dual,[-8,-6,0,0])
 # KKT absolute-unit denominator and global objective constant are unchanged.
 contract=C6/'release/V4_APPROVED.json';assert sha(contract)=='955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f'
 k=read(C6/'analysis_view/postprocess/KKT.json');offset=-12788967.997821666
 summary={'status':'V4_APPLICABLE_WITH_EXPLICIT_NUMERICAL_LIMITS','scientific_decision_required':False,'production_code_changed':False,'groups':385,'accounts':807,'all_Sg_nonnegative_and_below_each_budget':True,'max_Sg_MWh':max(r['Sg_MWh'] for r in records),'max_Sg_over_min_Bi':max(r['Sg_over_min_Bi'] for r in records),'C06_underuse_accounts':23,'C06_underuse_explained_by_scheme_A_roundoff':0,'mathematical_assumptions':['Each fixed-resource Store is noncyclic, initially Q, lossless and nonnegative; discharge-only.','Resource Bus has Store and exclusive meter; meter efficiency=1. Destination Bus has only group meters and fixed approved Load.','Annual weighted sum of exact equalities gives sum(e_T)=sum(Q)-D=Sg; nonnegative stock then 0<=e_iT<=Sg.','For an approximate returned point, positive and negative inventory may cancel. The exact implication cannot excuse negative stocks or distributed numerical leakage.'],'theorem_scope':'Terminal/annual proximity is a consequence in this frozen isolated group; Q remains a cap, not a new general mandatory-use scientific definition. No standalone e_T=0 constraint is invented.','endpoint_tests':'PASS equality/fixed arbitrary-sign multiplier; upper-only negative multiplier; free zero multiplier; free nonzero RC rejection','KKT_scale_with_offset':max(1,abs(k['primal_objective']),abs(k['dual_objective_numeric'])),'KKT_scale_excluding_offset_diagnostic_only':max(1,abs(k['primal_objective']-offset),abs(k['dual_objective_numeric']-offset)),'absolute_EUR_gap':k['absolute_gap'],'formal_V4_sha256':sha(contract),'scope':'No optimizer, no source edit, no threshold change; literature review separate','source_files':{str(p.relative_to(ROOT)):sha(p) for p in [B/'artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json',C6/'C06_ALL_ACCOUNT_AND_GROUP_COMPARISON.json',C6/'release/helpers/fixed_resource_acceptance.py',C6/'release/helpers/v4_algebra_extracted.py',contract]}}
 put('C07_V4_APPLICABILITY.json',dict(summary,groups_detail=records,C06_underuse_detail=under));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
