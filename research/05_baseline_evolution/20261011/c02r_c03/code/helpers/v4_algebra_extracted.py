from pathlib import Path
import math,types
import numpy as np
from fixed_resource_acceptance import RULE_ID
CHUNK = 200_000  # frozen adapter.py:13

def ranges(n, chunk=None):
    if chunk is None:
        chunk = CHUNK
    if chunk <= 0:
        raise ValueError('nonpositive chunk')
    for s in range(0, n, chunk):
        yield s, min(n, s + chunk)

def mapped_primal_dual(z, pi, rc, D, R):
    return z * D, pi * R, rc / D

def endpoint_metrics(v, lo, hi, multiplier):
    """Minimization sign convention. No inf*0 arithmetic; equality/fixed supported."""
    lf, uf = np.isfinite(lo), np.isfinite(hi)
    pos, neg = np.maximum(multiplier, 0), np.minimum(multiplier, 0)
    violation = np.zeros(len(v)); comp = np.zeros(len(v)); dual = np.zeros(len(v))
    violation[lf] = np.maximum(lo[lf] - v[lf], 0)
    violation[uf] = np.maximum(violation[uf], v[uf] - hi[uf])
    sign_error = np.where(~lf, pos, 0) + np.where(~uf, -neg, 0)
    dual[lf] += pos[lf] * lo[lf]
    dual[uf] += neg[uf] * hi[uf]
    comp[lf] += np.abs(pos[lf] * (v[lf] - lo[lf]))
    comp[uf] += np.abs(neg[uf] * (hi[uf] - v[uf]))
    return violation, sign_error, comp, dual

def diagnose(meta, a, z, pi, rc, D, R, scratch, row_tolerance, col_tolerance,
             stationarity_atol, stationarity_rtol):
    """O(nnz), chunk vectors, two row scratch memmaps. No dense matrix or solve.

    Reports floating point numerical KKT evidence, NOT a rigorous rational bound.
    A free variable with nonzero stationarity error prevents claiming an exact bound.
    """
    n, m = meta['num_col'], meta['num_row']
    if row_tolerance is None or col_tolerance is None:
        raise ValueError('reviewed original-unit tolerances required')
    for tol,length in [(row_tolerance,m),(col_tolerance,n)]:
        if np.isscalar(tol):
            if not math.isfinite(tol) or tol<0:raise ValueError('invalid physical tolerance')
        else:
            if len(tol)!=length:raise ValueError('tolerance coverage incomplete')
            for s,e in ranges(length):
                if not np.all(np.isfinite(tol[s:e]) & (tol[s:e]>=0)):raise ValueError('invalid physical tolerance')
    if not all(math.isfinite(v) and v>=0 for v in (stationarity_atol,stationarity_rtol)):
        raise ValueError('invalid stationarity tolerance')
    if meta['sense'] != 1:
        raise ValueError('minimization only')
    for vec, length in [(z,n),(rc,n),(D,n),(pi,m),(R,m)]:
        if len(vec) != length:
            raise ValueError('incomplete vector')
        for s,e in ranges(length):
            if not np.isfinite(vec[s:e]).all():
                raise ValueError('nonfinite vector')
    for vec in [D,R]:
        for s,e in ranges(len(vec)):
            if np.any(vec[s:e] <= 0):
                raise ValueError('nonpositive scale')
    scratch=Path(scratch); scratch.mkdir(parents=True, exist_ok=False)
    activity=np.lib.format.open_memmap(scratch/'activity_solver.npy',mode='w+',dtype='<f8',shape=(m,))
    magnitude=np.lib.format.open_memmap(scratch/'activity_abs_solver.npy',mode='w+',dtype='<f8',shape=(m,))
    activity[:]=0; magnitude[:]=0
    metrics={'row_violation_max':0.,'column_violation_max':0.,'stationarity_max_original':0.,
             'stationarity_normalized_max':0.,'dual_sign_error_max_original':0.,
             'complementarity_max':0.,'row_fail_count':0,'column_fail_count':0,
             'stationarity_fail_count':0,'source':'original units via frozen D/R'}
    objective_parts=[]; dual_parts=[]; complement_parts=[]; stationarity_parts=[]
    for s,e in ranges(n,20_000):
        p,q=int(a['start'][s]),int(a['start'][e]); counts=np.diff(a['start'][s:e+1])
        if q-p > 5_000_000:
            raise ValueError('batch scratch cap; review smaller batching before execution')
        rows=a['index'][p:q]; coeff=a['value'][p:q]
        terms=coeff*np.repeat(z[s:e],counts)
        np.add.at(activity,rows,terms);np.add.at(magnitude,rows,np.abs(terms))
        # bincount handles empty columns without reduceat's empty-segment ambiguity.
        col=np.repeat(np.arange(e-s),counts)
        aty=np.bincount(col,weights=coeff*pi[rows],minlength=e-s)
        absaty=np.bincount(col,weights=np.abs(coeff*pi[rows]),minlength=e-s)
        cost=a['cost'][s:e]/D[s:e]; x=z[s:e]*D[s:e]; r=rc[s:e]/D[s:e]
        residual=(a['cost'][s:e]-aty-rc[s:e])/D[s:e]
        scale=np.maximum(1., np.abs(cost)+absaty/D[s:e]+np.abs(r))
        lim=stationarity_atol+stationarity_rtol*scale
        metrics['stationarity_max_original']=max(metrics['stationarity_max_original'],float(np.max(np.abs(residual),initial=0)))
        metrics['stationarity_normalized_max']=max(metrics['stationarity_normalized_max'],float(np.max(np.abs(residual)/scale,initial=0)))
        metrics['stationarity_fail_count']+=int(np.sum(np.abs(residual)>lim))
        stationarity_parts.append(float(np.sum(np.abs(x*residual))))
        lo=a['col_lower'][s:e]*D[s:e];hi=a['col_upper'][s:e]*D[s:e]
        viol,sign,comp,dual=endpoint_metrics(x,lo,hi,r)
        tol=col_tolerance if np.isscalar(col_tolerance) else col_tolerance[s:e]
        metrics['column_fail_count']+=int(np.sum(viol>tol))
        metrics['column_violation_max']=max(metrics['column_violation_max'],float(viol.max(initial=0)))
        metrics['dual_sign_error_max_original']=max(metrics['dual_sign_error_max_original'],float(sign.max(initial=0)))
        metrics['complementarity_max']=max(metrics['complementarity_max'],float(comp.max(initial=0)))
        objective_parts.append(float(np.sum(cost*x)));dual_parts.append(float(np.sum(dual)));complement_parts.append(float(np.sum(comp)))
    for s,e in ranges(m):
        value=activity[s:e]/R[s:e];y=pi[s:e]*R[s:e]
        lo=a['row_lower'][s:e]/R[s:e];hi=a['row_upper'][s:e]/R[s:e]
        viol,sign,comp,dual=endpoint_metrics(value,lo,hi,y)
        tol=row_tolerance if np.isscalar(row_tolerance) else row_tolerance[s:e]
        metrics['row_fail_count']+=int(np.sum(viol>tol))
        metrics['row_violation_max']=max(metrics['row_violation_max'],float(viol.max(initial=0)))
        metrics['dual_sign_error_max_original']=max(metrics['dual_sign_error_max_original'],float(sign.max(initial=0)))
        metrics['complementarity_max']=max(metrics['complementarity_max'],float(comp.max(initial=0)))
        dual_parts.append(float(np.sum(dual)));complement_parts.append(float(np.sum(comp)))
    activity.flush();magnitude.flush()
    p=meta['offset']+math.fsum(objective_parts);d=meta['offset']+math.fsum(dual_parts)
    metrics.update(primal_objective=p,dual_objective_numeric=d,absolute_gap=abs(p-d),
                   relative_gap=abs(p-d)/max(1.,abs(p),abs(d)),
                   complementarity_l1=math.fsum(complement_parts),
                   stationarity_weighted_l1=math.fsum(stationarity_parts),
                   formal_exact_lower_bound=False,qualification='DIAGNOSTIC_ONLY_PENDING_SEMANTIC_AND_EXPORT_GATES')
    if not all(math.isfinite(v) for v in metrics.values() if isinstance(v,float)):
        raise ValueError('overflow in derived checks')
    return metrics

def mathematical_gap_decision(metrics):
    """Proposed 1 ppm numerical certificate, separate from physical gates and approval."""
    scale=max(1.,abs(metrics['primal_objective']),abs(metrics['dual_objective_numeric']))
    keys=['relative_gap','stationarity_normalized_max','complementarity_l1','stationarity_weighted_l1']
    valid=all(math.isfinite(metrics[k]) and metrics[k]>=0 for k in keys) and all(math.isfinite(metrics[k]) for k in ['primal_objective','dual_objective_numeric'])
    good=valid and metrics['relative_gap']<=1e-6 and metrics['stationarity_normalized_max']<=1e-6 and metrics['complementarity_l1']/scale<=1e-6 and metrics['stationarity_weighted_l1']/scale<=1e-6
    return {'numeric_draft_pass':bool(good),'full_acceptance':False,'dual_sign_physical_semantic_export_gates':'REQUIRED_SEPARATELY','original_objective_optimality':'NOT_PROVEN'}

def bounded_columns(a,n,columns=20000,max_nnz=4_000_000):
 s=0
 while s<n:
  e=min(n,s+columns)
  if int(a['start'][e])-int(a['start'][s])>max_nnz:
   e=min(e,int(np.searchsorted(a['start'],int(a['start'][s])+max_nnz,side='right'))-1)
   if e<=s:raise ValueError('single column exceeds scratch budget')
  yield s,e;s=e

def budget_arrays(meta,a,z,D,R,directory,contract):
 require_contract(contract)
 directory=Path(directory);directory.mkdir(exist_ok=False,parents=True)
 n,m=meta['num_col'],meta['num_row']
 magnitude=np.lib.format.open_memmap(directory/'row_magnitude.npy',mode='w+',dtype='<f8',shape=(m,));magnitude[:]=0
 for s,e in bounded_columns(a,n):
  p,q=int(a['start'][s]),int(a['start'][e]);np.add.at(magnitude,a['index'][p:q],np.abs(a['value'][p:q]*np.repeat(z[s:e],np.diff(a['start'][s:e+1]))))
 rt=np.lib.format.open_memmap(directory/'row_tolerance.npy',mode='w+',dtype='<f8',shape=(m,))
 ct=np.lib.format.open_memmap(directory/'col_tolerance.npy',mode='w+',dtype='<f8',shape=(n,))
 for s,e in ranges(m):
  l=a['row_lower'][s:e]/R[s:e];u=a['row_upper'][s:e]/R[s:e]
  reference=np.maximum(np.where(np.isfinite(l),np.abs(l),0),np.where(np.isfinite(u),np.abs(u),0))
  rt[s:e]=1e-3+1e-7*np.maximum(reference,magnitude[s:e]/R[s:e])
 for s,e in ranges(n):
  l=a['col_lower'][s:e]*D[s:e];u=a['col_upper'][s:e]*D[s:e]
  ct[s:e]=1e-3+1e-7*np.maximum(np.abs(z[s:e]*D[s:e]),np.maximum(np.where(np.isfinite(l),np.abs(l),0),np.where(np.isfinite(u),np.abs(u),0)))
 rt.flush();ct.flush();magnitude.flush();return rt,ct

def complete_kkt(meta,a,z,pi,rc,D,R,directory,contract):
 rt,ct=budget_arrays(meta,a,z,D,R,Path(directory)/'budgets',contract)
 def adaptive_ranges(length,chunk=None):
  return bounded_columns(a,length) if length==meta['num_col'] and chunk==20000 else ranges(length,chunk)
 # Preserve the verified formulas; replace only fixed-width batching that can exceed
 # scratch memory for dense capacity columns in the actual frozen CSC.
 bounded_diagnose=types.FunctionType(diagnose.__code__,dict(diagnose.__globals__,ranges=adaptive_ranges))
 out=bounded_diagnose(meta,a,z,pi,rc,D,R,Path(directory)/'algebra',rt,ct,0.,1e-6)
 # Existing algebra reports raw sign error. Add an explicit normalized sign gate,
 # including forbidden multipliers on free columns and nonexistent endpoints.
 maxerr=0.;count=0
 for length,mult,scale,lo,hi in [(meta['num_col'],rc,D,a['col_lower'],a['col_upper']),(meta['num_row'],pi,R,a['row_lower'],a['row_upper'])]:
  iscol=mult is rc
  for s,e in ranges(length):
   v=mult[s:e]/scale[s:e] if iscol else mult[s:e]*scale[s:e]
   error=np.where(~np.isfinite(lo[s:e]),np.maximum(v,0),0)+np.where(~np.isfinite(hi[s:e]),np.maximum(-v,0),0)
   norm=error/np.maximum(1,np.abs(v));maxerr=max(maxerr,float(norm.max(initial=0)));count+=int(np.count_nonzero(norm>1e-6))
 out.update(dual_sign_normalized_max=maxerr,dual_sign_fail_count=count)
 decision=mathematical_gap_decision(out)
 out['independent_kkt_pass']=bool(decision['numeric_draft_pass'] and not count and out['row_fail_count']==out['column_fail_count']==out['stationarity_fail_count']==0)
 return out

def require_contract(c):
 for key in ('approved_by_user','physical_budget_approved','perturbation_scope_approved','basis_free_kkt_approved'):
  if c.get(key) is not True:raise ValueError('Final scientific contract not explicitly approved')
 if c.get('contract_id')!='AUTHOR_SCIENTIFIC_ACCEPTANCE_V4' or c.get('fixed_resource_rule_id')!=RULE_ID:raise ValueError('wrong contract')
 expected={'physical_absolute_floor_in_each_equation_native_unit':1e-3,'physical_relative_budget':1e-7,'kkt_normalized_budget':1e-6}
 if any(c.get(k)!=v for k,v in expected.items()):raise ValueError('unimplemented numerical budget')
