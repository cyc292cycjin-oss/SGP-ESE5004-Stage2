"""Independent algebra diagnostics, never a solver or an automatic scientific PASS.

No basis is queried. Semantic engineering/export checks remain separate gates.
Supplied tolerances must come from a reviewed contract; there are no physical defaults.
"""
from pathlib import Path
import math
import numpy as np
from adapter import ranges


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


def acceptance_draft(native_status, gates):
    required={'transfer','complete_primal_dual','all_rows_original_units','physical_dynamics',
              'fixed_inventory_original_bounds','all_prefixes_and_annual','objective_fom_once',
              'dual_kkt_gap','export_reload','durable_sha_backup','approved_contract'}
    missing=sorted(k for k in required if gates.get(k) is not True)
    if native_status != 2:
        missing.append('native_OPTIMAL')
    return {'status':'DRAFT_ACCEPTANCE_CHECKS_SATISFIED' if not missing else 'NOT_ACCEPTED',
            'missing':missing,'historical_gate6_pass':False,'basis_required':False}
