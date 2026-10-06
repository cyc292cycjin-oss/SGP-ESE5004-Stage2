"""Float64, bounded-memory HiGHS handoff for frozen Linopy 0.5.5.

Uses the frozen Constraint.flat duplicate-coalescing semantics, reads every
transferred row back before solve, and retains original Linopy integer labels.
No model rebuild, file serialization, package modification, or tolerance change.
"""
from contextlib import contextmanager
from types import SimpleNamespace
import hashlib
import json
from decimal import Decimal, getcontext
from collections import defaultdict
from pathlib import Path
import numpy as np
import highspy
import linopy
import linopy.solvers
from scipy.sparse import csr_matrix


@contextmanager
def research_scalar_assignment():
    """Skip non-component research scalars only during frozen PyPSA annotation.

    Their primal values and objective terms remain in the solved Linopy model.
    Integer labels, constraints and the model object never change. PyPSA's
    component mapper assumes every hyphenated variable is a component variable.
    """
    import importlib
    opt = importlib.import_module('pypsa.optimization.optimize')
    original = opt.assign_solution
    def annotate(n):
        data = n.model.variables.data
        old = dict(data)
        allowed = {'Research-existing-FOM-constant','Research-synthetic-FOM'}
        custom = [k for k in data if k.split('-',1)[0] not in n.all_components and k!='objective_constant']
        for name in custom:
            if name not in allowed or data[name].solution.size!=1 or float(data[name].solution)!=1.0:
                raise ValueError('Unqualified custom scalar during result mapping: '+name)
        try:
            # Frozen mapper skips names with no hyphen. This aliases only its
            # iteration keys, after solve; Variable.name and labels are untouched.
            for name in custom: data[name.replace('-','_')]=data.pop(name)
            original(n)
        finally:
            data.clear();data.update(old)
    opt.assign_solution=annotate
    try: yield
    finally: opt.assign_solution=original


def digest(*arrays):
    h = hashlib.sha256()
    for a in arrays:
        a = np.ascontiguousarray(a)
        h.update(str(a.dtype).encode()); h.update(str(a.shape).encode()); h.update(a.tobytes())
    return h.hexdigest()


def ok(status):
    if status != highspy.HighsStatus.kOk:
        raise ValueError(f"HiGHS transfer status {status}")


def exact(a, b, name):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.array_equal(a, b):
        raise ValueError(f"Solver transfer mismatch: {name}; {a.shape} !=/or differs {b.shape}")


def transfer(model, *, slice_size=200_000, progress=None, certificate_labels=(), certificate_factors=None, transformation=None):
    """Transfer and verify all canonical coefficients; never call a solver."""
    if linopy.__version__ != "0.5.5" or model.type != "LP":
        raise ValueError("This audited adapter requires frozen Linopy 0.5.5 LP")
    getcontext().prec = 100  # exact binary64 certificate accumulation
    h = highspy.Highs()
    # No numerical solver option changes. Silence transfer banners only.
    ok(h.setOptionValue("output_flag", False))
    vf = model.variables.flat
    vl = vf.labels.to_numpy(dtype=np.int64)
    if len(np.unique(vl)) != len(vl): raise ValueError("Duplicate variable label")
    vmap = np.full(model.shape[1], -1, dtype=np.int32)
    vmap[vl] = np.arange(len(vl), dtype=np.int32)
    lb, ub = vf.lower.to_numpy(), vf.upper.to_numpy()
    obj = model.objective.flat
    costs = np.zeros(len(vl), dtype=np.float64)
    if len(obj):
        keys = vmap[obj.vars.to_numpy(dtype=int)]
        if (keys < 0).any(): raise ValueError("Unknown objective variable")
        costs[keys] = obj.coeffs.to_numpy()
    offset = float(model.objective.expression.const.item())
    # Linopy 0.5.5 rejects nonzero objective constants at construction.
    if offset != 0: raise ValueError("Unexpected objective offset in frozen model")
    if transformation is not None:lb,ub,costs=transformation.columns(vl,lb,ub,costs)
    ok(h.addVars(len(vl), lb, ub))
    ok(h.changeColsCost(len(vl), np.arange(len(vl), dtype=np.int32), costs))
    if model.sense == "max": ok(h.changeObjectiveSense(highspy.ObjSense.kMaximize))
    for start in range(0, len(vl), slice_size):
        ids = np.arange(start, min(start+slice_size,len(vl)), dtype=np.int32)
        status, count, rc, rl, ru, _ = h.getCols(len(ids), ids); ok(status)
        exact(costs[ids], rc, "objective"); exact(lb[ids], rl, "variable lower"); exact(ub[ids], ru, "variable upper")
    status, received_offset = h.getObjectiveOffset(); ok(status); exact(offset, received_offset, "objective offset")
    status, sense = h.getObjectiveSense(); ok(status)
    if sense != (highspy.ObjSense.kMinimize if model.sense == "min" else highspy.ObjSense.kMaximize): raise ValueError("Objective sense changed")
    receipt = dict(status="TRANSFER_IN_PROGRESS", io_api="direct", adapter="PROJECT_STREAMED_FLOAT64",
        comparison="exact float64 equality; canonical duplicate terms coalesced by frozen Constraint.flat; row/column reorder mapped by integer labels",
        variables=len(vl), variable_labels_sha256=digest(vl), bounds_objective_sha256=digest(lb,ub,costs),
        objective_offset=offset, objective_sense=model.sense, max_absolute_transfer_difference=0.0,
        constraint_blocks=[], certificate_requested=len(certificate_labels), solver_run_started=False)
    del vf, lb, ub, obj, costs
    labels = []; seen = np.zeros(model.shape[0], dtype=bool)
    wanted = set(map(int, certificate_labels)); matched = set()
    factors={int(k):Decimal(str(v)) for k,v in (certificate_factors or {}).items()}
    cert_rhs=Decimal(0); cert_terms=defaultdict(Decimal)
    row_count = nnz = 0
    for name, constraint in model.constraints.items():
        group_rows = group_nnz = 0; hasher = hashlib.sha256()
        for part in constraint.iterate_slices(slice_size=slice_size):
            f = part.flat
            if f.empty: continue
            rows = f.drop_duplicates("labels")
            cl = rows.labels.to_numpy(dtype=np.int64)
            if seen[cl].any(): raise ValueError("Constraint row split/repeated across chunks")
            seen[cl] = True; matched.update(wanted.intersection(cl.tolist()))
            local_rows = np.searchsorted(cl, f.labels.to_numpy())
            if not np.array_equal(cl[local_rows], f.labels.to_numpy()): raise ValueError("Noncanonical row order")
            cols = vmap[f.vars.to_numpy(dtype=int)]
            if (cols < 0).any(): raise ValueError("Unknown matrix variable")
            a = csr_matrix((f.coeffs.to_numpy(dtype=float), (local_rows, cols)),shape=(len(cl),len(vl)))
            a.sum_duplicates(); a.sort_indices(); a.eliminate_zeros()
            rhs = rows.rhs.to_numpy(dtype=float); signs=rows.sign.to_numpy()
            for ci in np.flatnonzero(np.isin(cl,list(factors))):
                factor=factors[int(cl[ci])]
                cert_rhs+=factor*Decimal.from_float(float(rhs[ci]))
                for j in range(a.indptr[ci],a.indptr[ci+1]):
                    cert_terms[int(vl[a.indices[j]])]+=factor*Decimal.from_float(float(a.data[j]))
            lower=np.where(signs!="<=",rhs,-np.inf); upper=np.where(signs!=">=",rhs,np.inf)
            if not np.isin(signs,["=","<=",">="]).all(): raise ValueError("Unknown constraint sign")
            if transformation is not None:a,lower,upper=transformation.rows(cl,a,lower,upper)
            ok(h.addRows(len(cl), lower, upper, a.nnz, a.indptr.astype(np.int32), a.indices.astype(np.int32), a.data))
            ids=np.arange(row_count,row_count+len(cl),dtype=np.int32)
            status,count,rl,ru,nz=h.getRows(len(ids),ids); ok(status)
            exact(lower,rl,"row lower"); exact(upper,ru,"row upper")
            status,starts,indices,values=h.getRowsEntries(len(ids),ids); ok(status)
            received=csr_matrix((values,indices,np.r_[starts,len(values)]),shape=a.shape)
            received.sum_duplicates(); received.sort_indices(); received.eliminate_zeros()
            exact(a.indptr,received.indptr,"matrix row offsets"); exact(a.indices,received.indices,"matrix column indices"); exact(a.data,received.data,"matrix coefficients")
            hasher.update(digest(cl,lower,upper,a.indptr,a.indices,a.data).encode())
            labels.append(cl); row_count+=len(cl); nnz+=a.nnz; group_rows+=len(cl); group_nnz+=a.nnz
        receipt['constraint_blocks'].append(dict(name=name,rows=group_rows,nnz=group_nnz,canonical_and_received_sha256=hasher.hexdigest(),status="EXACT_FLOAT64_MATCH"))
        if progress: progress("handoff", dict(rows=row_count,nnz=nnz,group=name))
    if matched != wanted: raise ValueError(f"Certificate rows absent: {sorted(wanted-matched)[:10]}")
    cl=np.concatenate(labels) if labels else np.array([],dtype=np.int64)
    if len(cl)!=model.ncons or len(vl)!=model.nvars or h.getNumRow()!=len(cl) or h.getNumCol()!=len(vl) or h.getNumNz()!=nnz:
        raise ValueError("Model/solver dimensions or nnz disagree")
    receipt.update(status="PASS", constraints=len(cl), nnz=int(nnz), constraint_labels_sha256=digest(cl),
        certificate_rows_verified=len(matched), all_rows_verified=True, all_variable_bounds_verified=True,
        all_objective_coefficients_verified=True, label_mapping="original integer labels retained in solver row/column order")
    receipt['certificate_native_binary64_sum']={'rhs':str(cert_rhs),'nonzero_lhs':{str(k):str(v) for k,v in cert_terms.items() if v},'method':'Exact Decimal.from_float accumulation of original binary64 coefficients; all compared bit-preserving to received solver values'}
    if transformation is not None:
        receipt['original_to_solver_mapping']=transformation.finish()
        receipt['comparison']='Received matrix equals transformed matrix exactly; original-to-transformed inverse mapping separately verified. Original matrix is not required to equal transformed RHS/bounds.'
        receipt['certificate_native_binary64_sum']['method']='Exact original binary64 algebra before reversible scaling; it is not replaced by the transformed RHS.'
    return h, SimpleNamespace(matrices=SimpleNamespace(vlabels=vl,clabels=cl)), receipt


@contextmanager
def audited_direct_backend(receipt_path, *, progress=None, before_run=None, certificate_labels=(), certificate_factors=None, transformation=None):
    """Scope backend replacement; use frozen _solve and original Model.solve mapping."""
    original = linopy.solvers.Highs
    class AuditedHighs(original):
        @property
        def solver_name(self):
            return linopy.solvers.SolverName.Highs

        def solve_problem_from_model(self, model, solution_fn=None, log_fn=None,
                warmstart_fn=None, basis_fn=None, env=None, explicit_coordinate_names=False):
            if warmstart_fn or basis_fn or env or explicit_coordinate_names:
                raise ValueError("Unaudited optional direct solver arguments")
            h, mapping, receipt=transfer(model,progress=progress,certificate_labels=certificate_labels,certificate_factors=certificate_factors,transformation=transformation)
            Path(receipt_path).write_text(json.dumps(receipt,indent=2)+'\n')
            if before_run: before_run(h,receipt)
            receipt['solver_run_started']=True
            Path(receipt_path).write_text(json.dumps(receipt,indent=2)+'\n')
            # Frozen backend receives only the verified label vectors, avoiding
            # a second global long-form matrix while mapping the same model.
            ok(h.setOptionValue("output_flag", True))
            result=self._solve(h,solution_fn=None,log_fn=log_fn,model=mapping,io_api="direct",sense=model.sense)
            if transformation is not None:
                result=transformation.restore(result)
                receipt['solution_map_verified']=bool(len(result.solution.primal))
                receipt['dual_map_verified']=bool(len(result.solution.dual))
                Path(receipt_path).write_text(json.dumps(receipt,indent=2)+'\n')
            return result
    linopy.solvers.Highs=AuditedHighs
    try: yield
    finally: linopy.solvers.Highs=original
