"""Detached, lossless Gate5 ownership primitives. This module never runs a solver.

The caller must retain the native problem and externally authorize any future
solve. Frozen input, coefficients, tolerances and scientific hooks are unchanged.
"""
import gc
import ctypes
import json
import weakref
from contextlib import contextmanager
from pathlib import Path
import numpy as np
import xarray as xr
from precision_handoff import digest, exact, scalar_value_diagnostic
from gate5_resources import sha

CHUNK = 200_000


@contextmanager
def explicit_empty_dask_chunks():
    """Avoid frozen Dask auto-chunk division by zero for empty term axes only.

    An empty array has no coefficient values. The shape/dtype are unchanged;
    supplying explicit unit chunks only bypasses its undefined size heuristic.
    Never patch installed packages, and always restore the function afterward.
    """
    import dask.array.core as core
    from unittest.mock import patch
    original = core.from_array
    def from_array(a, chunks='auto', *args, **kwargs):
        if isinstance(chunks, str) and chunks == 'auto' and isinstance(a, np.ndarray) and a.size == 0:
            chunks = tuple(max(1, int(s)) for s in a.shape)
        return original(a, chunks, *args, **kwargs)
    with patch.object(core, 'from_array', from_array):
        yield


@contextmanager
def bounded_build_allocator():
    """Return completed construction temporaries at existing block boundaries.

    The frozen methods, arguments, order, stored datasets and labels are used
    verbatim. This only collects unreachable objects and trims free libc pages.
    """
    import linopy
    from unittest.mock import patch
    count = [0]
    def wrap(original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            count[0] += 1
            if count[0] % 16 == 0:
                gc.collect()
            try:
                ctypes.CDLL(None).malloc_trim(0)
            except (AttributeError, OSError):
                pass
            return result
        return call
    with patch.object(linopy.Model, 'add_variables', wrap(linopy.Model.add_variables)), \
         patch.object(linopy.Model, 'add_constraints', wrap(linopy.Model.add_constraints)):
        yield


def checked_int32(values):
    a = np.asarray(values)
    if a.dtype.kind not in 'iu':
        raise TypeError('Only integer metadata may be compressed')
    if a.size and (int(a.min()) < -(2**31) or int(a.max()) >= 2**31):
        raise OverflowError('Integer metadata does not fit int32')
    return a.astype(np.int32, copy=False)


def trim():
    gc.collect()
    # Optional allocator release, not an equivalence or memory-success claim.
    try:
        return int(ctypes.CDLL(None).malloc_trim(0))
    except (AttributeError, OSError):
        return None


def write_array(path, values, dtype, chunk=CHUNK):
    """At most one binding-returned list and one bounded conversion coexist."""
    path = Path(path)
    out = np.lib.format.open_memmap(path, mode='w+', dtype=dtype, shape=(len(values),))
    for start in range(0, len(values), chunk):
        end = min(start + chunk, len(values))
        out[start:end] = values[start:end]
    out.flush()
    del out
    return dict(file=path.name, sha256=sha(path), count=len(values), dtype=np.dtype(dtype).str)


def save_mapping(folder, n, mapping, transformation, input_path, input_sha):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    record = dict(schema=1, input_path=str(input_path), input_sha256=input_sha,
                  variables=[], constraints=[], arrays={}, scientific_float_dtype='float64')
    for key, values, dtype in [('vlabels', mapping.matrices.vlabels, np.int32),
                                ('clabels', mapping.matrices.clabels, np.int32),
                                ('D', transformation.d, np.float64), ('R', transformation.r, np.float64)]:
        if dtype == np.int32:
            values = checked_int32(values)
        elif np.asarray(values).dtype != np.dtype('float64'):
            raise TypeError('Scientific arrays must already be float64')
        record['arrays'][key] = write_array(folder / (key + '.npy'), values, dtype)
    for kind, items in [('variables', n.model.variables), ('constraints', n.model.constraints)]:
        for name, block in items.items():
            a = block.labels
            # Coordinate identity is revalidated on the byte-identical network
            # rebuild, and labels are validated per named block before mapping.
            record[kind].append(dict(name=name, shape=list(a.shape), dims=list(a.dims),
                                     labels_sha256=digest(a.values),
                                     coordinate_sha256={d: sha_index(a.get_index(d)) for d in a.dims}))
    record['research_scalars'] = [dict(name=name, labels=[int(x) for x in v.labels.values.reshape(-1)])
                                   for name, v in n.model.variables.items() if name.startswith('Research-')]
    record['model_shape'] = list(n.model.shape)
    (folder / 'MAPPING_MANIFEST.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


def sha_index(index):
    # Hash exact pandas index representation, including name, dtype and order.
    import pickle, hashlib
    return hashlib.sha256(pickle.dumps(index, protocol=5)).hexdigest()


def load_arrays(folder, record):
    folder = Path(folder)
    arrays = {}
    for key, entry in record['arrays'].items():
        path = folder / entry['file']
        if sha(path) != entry['sha256']:
            raise ValueError('Mapping payload hash mismatch: ' + key)
        a = np.load(path, mmap_mode='r', allow_pickle=False)
        if a.dtype.str != entry['dtype'] or a.shape != (entry['count'],):
            raise ValueError('Mapping dtype/shape mismatch: ' + key)
        arrays[key] = a
    return arrays


def inverse_labels(labels, size):
    checked_int32(labels)
    if len(labels) >= 2**31 or (len(labels) and (int(labels.min()) < 0 or int(labels.max()) >= size)):
        raise ValueError('Label domain invalid')
    if len(np.unique(labels)) != len(labels):
        raise ValueError('Duplicate labels')
    lookup = np.full(size, -1, dtype=np.int32)
    lookup[labels] = np.arange(len(labels), dtype=np.int32)
    return lookup


def qualify_and_store(h, folder, mapping_folder, record):
    """Call getSolution exactly once. No Series, no second qualification fetch.

    Captures all four native vectors, flags and status, even for a rejected
    candidate. Only qualified primal/FOM states can subsequently be mapped.
    Native row activities and reduced costs stay in native scale for diagnosis.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=False)
    arrays = load_arrays(mapping_folder, record)
    native = h.getSolution()
    info = h.getInfo()
    state = h.getModelStatus()
    objective = float(h.getObjectiveValue())
    from linopy.constants import Status, SolverStatus
    condition = termination_condition(int(state))
    status = Status.from_termination_condition(condition)
    status_allowed = status.is_ok or status.status == SolverStatus.unknown
    q = dict(model_status=h.modelStatusToString(state), model_status_code=int(state),
             native_value_valid=bool(native.value_valid), native_dual_valid=bool(native.dual_valid),
             info_valid=bool(info.valid), primal_solution_status=int(info.primal_solution_status),
             dual_solution_status=int(info.dual_solution_status), objective=objective if np.isfinite(objective) else None,
             objective_finite=bool(np.isfinite(objective)), native_getSolution_calls=1, arrays={})
    q['linopy_termination_condition'] = condition
    q['linopy_status_allows_candidate'] = status_allowed
    for key, length in [('col_value', len(arrays['vlabels'])), ('col_dual', len(arrays['vlabels'])),
                         ('row_value', len(arrays['clabels'])), ('row_dual', len(arrays['clabels']))]:
        values = getattr(native, key)  # pybind property is read once per vector
        q['arrays'][key] = write_array(folder / (key + '.npy'), values, np.float64)
        q['arrays'][key]['expected_count'] = length
        del values
    del native
    primal = np.load(folder / 'col_value.npy', mmap_mode='r')
    dual = np.load(folder / 'row_dual.npy', mmap_mode='r')
    q['nonfinite_primal_count'] = count_nonfinite(primal)
    q['nonfinite_dual_count'] = count_nonfinite(dual)
    lengths_ok = all(v['count'] == v['expected_count'] for v in q['arrays'].values())
    q['native_feasible_primal'] = bool(q['native_value_valid'] and q['info_valid'] and
        q['primal_solution_status'] == 2 and lengths_ok and len(primal) and
        q['nonfinite_primal_count'] == 0 and q['objective_finite'])
    q['custom_scalar_diagnostics_before_mapping'] = []
    q['custom_scalar_diagnostics_original_scale'] = []
    if lengths_ok:
        lookup = inverse_labels(arrays['vlabels'], record['model_shape'][1])
        for scalar in record['research_scalars']:
            pos = lookup[scalar['labels']]
            if (pos < 0).any():
                raise ValueError('Unmapped research scalar')
            raw = primal[pos]
            mapped = raw * arrays['D'][pos]
            for field, values in [('custom_scalar_diagnostics_before_mapping', raw),
                                  ('custom_scalar_diagnostics_original_scale', mapped)]:
                q[field].append(scalar_value_diagnostic(scalar['name'], values, scalar['labels']))
    q['network_writeback_qualified'] = bool(status_allowed and q['native_feasible_primal'] and
        all(x['qualified'] for field in ['custom_scalar_diagnostics_before_mapping',
                                       'custom_scalar_diagnostics_original_scale'] for x in q[field]))
    q['original_unit_validation'] = 'NOT_RUN'
    (folder / 'NATIVE_QUALIFICATION.json').write_text(json.dumps(q, indent=2, allow_nan=False) + '\n')
    return q


def count_nonfinite(a):
    return sum(int((~np.isfinite(a[i:i+CHUNK])).sum()) for i in range(0, len(a), CHUNK))


def map_values(labels, lookup, values, scales):
    """Same label lookup, -1 -> NaN, and x=D*z / pi=R*y as frozen mapping."""
    flat = np.asarray(labels).reshape(-1)
    out = np.empty(len(flat), dtype=np.float64)
    for start in range(0, len(flat), CHUNK):
        lab = flat[start:start+CHUNK]
        if (lab < -1).any() or (lab >= len(lookup)).any():
            raise ValueError('Invalid mapping label')
        valid = lab >= 0
        pos = lookup[lab[valid]]
        if (pos < 0).any():
            raise ValueError('Missing active label')
        raw = values[pos]
        factor = scales[pos]
        mapped = raw * factor
        exact(mapped / factor, raw, 'result inverse scale')
        target = out[start:start+len(lab)]
        target[:] = np.nan
        target[valid] = mapped
    return out.reshape(np.shape(labels))


def apply_stored_solution(n, mapping_folder, result_folder, record, q):
    """Rebuild only after native solver destruction; verify labels before writeback.

    Deliberately retains the frozen PyPSA mapper and dynamic validation. The
    source-model rebuild's measured build envelope must be budgeted postsolve.
    """
    if not q['network_writeback_qualified']:
        raise ValueError('Unqualified native result')
    arrays = load_arrays(mapping_folder, record)
    for key, entry in q['arrays'].items():
        if sha(Path(result_folder) / entry['file']) != entry['sha256']:
            raise ValueError('Native solution changed: ' + key)
    for kind, label_key, scale_key, value_key, size in [
            ('variables', 'vlabels', 'D', 'col_value', record['model_shape'][1]),
            ('constraints', 'clabels', 'R', 'row_dual', record['model_shape'][0])]:
        lookup = inverse_labels(arrays[label_key], size)
        values = np.load(Path(result_folder) / (value_key + '.npy'), mmap_mode='r')
        blocks = getattr(n.model, kind)
        if list(blocks) != [b['name'] for b in record[kind]]:
            raise ValueError('Rebuilt block order changed')
        for expected, (name, block) in zip(record[kind], blocks.items()):
            a = block.labels
            if digest(a.values) != expected['labels_sha256'] or list(a.shape) != expected['shape'] or list(a.dims) != expected['dims']:
                raise ValueError('Rebuilt label identity changed: ' + name)
            if any(sha_index(a.get_index(d)) != expected['coordinate_sha256'][d] for d in a.dims):
                raise ValueError('Rebuilt coordinate identity changed: ' + name)
            data = xr.DataArray(map_values(a.values, lookup, values, arrays[scale_key]), coords=a.coords, dims=a.dims)
            if kind == 'variables':
                block.solution = data
            else:
                block.dual = data
        del lookup, values
    n.model.objective._value = q['objective']
    n.model.status = 'ok'
    n.model.termination_condition = 'optimal' if q['model_status_code'] == 7 else 'unknown'
    n.model.solver_name = 'highs'
    # Use frozen termination translation for all nonoptimal candidates too.
    n.model.termination_condition = termination_condition(q['model_status_code'])
    from precision_handoff import research_scalar_assignment
    import importlib
    opt = importlib.import_module('pypsa.optimization.optimize')
    with research_scalar_assignment(Path(result_folder) / 'FOM_SCALAR_ASSIGNMENT_DIAGNOSTIC.json'):
        opt.assign_solution(n)
    opt.assign_duals(n)
    opt.post_processing(n)
    return n


def termination_condition(code):
    import highspy
    # Mirrors frozen Linopy 0.5.5 condition table, without invoking its _solve.
    groups = {'unknown': ['kNotset','kModelEmpty','kUnknown'],
              'internal_solver_error': ['kLoadError','kModelError','kPresolveError','kSolveError','kPostsolveError'],
              'resource_interrupt': ['kMemoryLimit'], 'optimal': ['kOptimal'],
              'infeasible': ['kInfeasible'], 'infeasible_or_unbounded': ['kUnboundedOrInfeasible'],
              'unbounded': ['kUnbounded'], 'terminated_by_limit': ['kObjectiveBound','kObjectiveTarget','kSolutionLimit'],
              'time_limit': ['kTimeLimit'], 'iteration_limit': ['kIterationLimit'], 'user_interrupt': ['kInterrupt']}
    return next((condition for condition, names in groups.items()
                 if any(code == int(getattr(highspy.HighsModelStatus, name)) for name in names)), 'unknown')


def release_native(owner):
    """Owner is a one-element list so the last external reference is cleared."""
    owner[0].clear()
    owner[0] = None
    trim()


def reload_map_validate(source, input_sha, mapping_folder, result_folder, record, q, identity):
    """Future postsolve path; never solves and never declares Gate5 PASS."""
    import pypsa
    from assembly_components import install_research_constraint_hooks
    from fixed_inventory_scaling import physical_checks
    from validation_dynamics import dynamic_checks
    if sha(source) != input_sha:
        raise ValueError('Frozen input changed before result reload')
    n = pypsa.Network(source)
    n.optimize.create_model()
    install_research_constraint_hooks(n)
    apply_stored_solution(n, mapping_folder, result_folder, record, q)
    checks, detail = dynamic_checks(n)
    checks += physical_checks(n, identity)
    # Caller must preserve the original metadata/export/roundtrip contract.
    return n, checks, detail
