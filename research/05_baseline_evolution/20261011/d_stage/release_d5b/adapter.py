"""Review candidate. No environment creation, optimization, presolve or launch entry point.

Only bind an already-authorized native environment in a future interface review.
Source arrays are read-only. No PyPSA model reconstruction is used.
"""
from pathlib import Path
import ctypes as C
import hashlib
import json
import math
import numpy as np

CHUNK = 200_000
INT_MAX = 2_000_000_000
INF = 1e100  # GRB_INFINITY; finite values >=1e20 are rejected, not rounded away.


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def ranges(n, chunk=None):
    if chunk is None:
        chunk = CHUNK
    if chunk <= 0:
        raise ValueError('nonpositive chunk')
    for s in range(0, n, chunk):
        yield s, min(n, s + chunk)


def i32(a):
    if a.size and (a.min() < 0 or a.max() >= INT_MAX):
        raise ValueError('C API integer range exceeded')
    return np.asarray(a, dtype=np.int32)


def native_bounds(a):
    a = np.asarray(a, dtype=np.float64)
    if np.isnan(a).any() or np.any(np.isfinite(a) & (np.abs(a) >= 1e20)):
        raise ValueError('NaN or finite bound in Gurobi infinity range')
    return np.where(np.isposinf(a), INF, np.where(np.isneginf(a), -INF, a))


def row_encoding(lo, hi):
    lf, uf = np.isfinite(lo), np.isfinite(hi)
    eq = lf & uf & (lo == hi)
    lower = lf & np.isposinf(hi)
    upper = np.isneginf(lo) & uf
    if not np.all(eq | lower | upper):
        raise ValueError('Unsupported ranged/free/conflicting/NaN row; no implicit slack variables')
    rhs = np.where(upper, hi, lo)
    if np.any(np.abs(rhs) >= 1e20):
        raise ValueError('finite RHS would change semantics in Gurobi')
    sense = np.where(eq, b'=', np.where(lower, b'>', b'<')).astype('S1')
    return sense, rhs


def open_problem(folder, verify=True):
    folder = Path(folder)
    meta = json.loads((folder / 'MATH_PROBLEM.json').read_text(encoding='utf-8-sig'))
    if meta['sense'] != 1 or not math.isfinite(meta['offset']):
        raise ValueError('only finite-offset minimization supported')
    a = {}
    for key, item in meta['arrays'].items():
        path = folder / item['file']
        if verify and sha256(path) != item['sha256']:
            raise ValueError('SHA mismatch: ' + key)
        x = np.load(path, mmap_mode='r', allow_pickle=False)
        if x.ndim != 1 or x.size != item['count'] or x.dtype.str != item['dtype']:
            raise ValueError('array metadata mismatch: ' + key)
        a[key] = x
    return meta, a


def validate(meta, a):
    n, m = meta['num_col'], meta['num_row']
    nnz = len(a['value'])
    if max(n, m, nnz) >= INT_MAX or len(a['index']) != nnz:
        raise ValueError('dimensions unsupported')
    expected = {'cost': n, 'col_lower': n, 'col_upper': n,
                'row_lower': m, 'row_upper': m, 'start': n + 1}
    if any(len(a[k]) != v for k, v in expected.items()):
        raise ValueError('shape mismatch')
    if a['start'][0] != 0 or a['start'][-1] != nnz:
        raise ValueError('CSC endpoints')
    counts = {'=': 0, '>': 0, '<': 0, 'free_columns': 0}
    for s, e in ranges(n):
        if np.any(np.diff(a['start'][s:e+1]) < 0):
            raise ValueError('nonmonotone CSC')
        if not np.isfinite(a['cost'][s:e]).all():
            raise ValueError('nonfinite cost')
        lo, hi = a['col_lower'][s:e], a['col_upper'][s:e]
        native_bounds(lo); native_bounds(hi)
        if np.any(lo > hi) or np.isposinf(lo).any() or np.isneginf(hi).any():
            raise ValueError('invalid column bounds')
        counts['free_columns'] += int(np.sum(np.isneginf(lo) & np.isposinf(hi)))
    for s, e in ranges(m):
        sense, rhs = row_encoding(a['row_lower'][s:e], a['row_upper'][s:e])
        for k in ('=', '>', '<'):
            counts[k] += int(np.sum(sense == k.encode()))
    for s, e in ranges(nnz):
        ids, vals = a['index'][s:e], a['value'][s:e]
        if np.any(ids < 0) or np.any(ids >= m) or not np.isfinite(vals).all():
            raise ValueError('bad CSC values/row indices')
        if np.any(np.abs(vals) < 1e-13):
            raise ValueError('coefficient risks being discarded by target solver')
    return dict(num_col=n, num_row=m, nnz=nnz, row_senses=counts,
                source_array_bytes=sum(x.nbytes for x in a.values()))


def load_candidate(backend, meta, a):
    """Native load only. Tests use a fake backend; no native API is run here today."""
    validate(meta, a)
    backend.create(meta['offset'])
    for s, e in ranges(meta['num_row']):
        sense, rhs = row_encoding(a['row_lower'][s:e], a['row_upper'][s:e])
        backend.rows(sense, rhs)
    backend.update()  # row identities must exist before CSC columns reference them
    for s, e in ranges(meta['num_col']):
        p, q = int(a['start'][s]), int(a['start'][e])
        backend.columns(i32(a['start'][s:e] - p), i32(a['index'][p:q]),
                        a['value'][p:q], a['cost'][s:e],
                        native_bounds(a['col_lower'][s:e]), native_bounds(a['col_upper'][s:e]))
    backend.update()


def exact_readback(backend, meta, a):
    """No optimization. Check all coefficients, senses, bounds, objective and types."""
    n, m = meta['num_col'], meta['num_row']
    if backend.scalar('NumVars', int) != n or backend.scalar('NumConstrs', int) != m:
        raise ValueError('readback dimensions')
    if backend.scalar('ModelSense', int) != 1 or backend.scalar('ObjCon', float) != meta['offset']:
        raise ValueError('readback objective metadata')
    for s, e in ranges(n):
        for attr, key in [('Obj', 'cost'), ('LB', 'col_lower'), ('UB', 'col_upper')]:
            got = backend.array(attr, s, e-s)
            expected = a[key][s:e]
            if attr in ('LB', 'UB'):
                # Normalize only source-declared infinities. All finite values compare exactly.
                infmask = np.isinf(expected)
                if not np.all(np.sign(got[infmask]) == np.sign(expected[infmask])) or not np.all(np.abs(got[infmask]) >= 1e20):
                    raise ValueError('infinity readback')
                got = got.copy(); got[infmask] = expected[infmask]
            if not np.array_equal(got, expected):
                raise ValueError('readback ' + attr)
        if not np.all(backend.array('VType', s, e-s, 'S1') == b'C'):
            raise ValueError('noncontinuous variable')
        starts, ids, vals = backend.matrix_columns(s, e-s)
        p, q = int(a['start'][s]), int(a['start'][e])
        if not (np.array_equal(starts, a['start'][s:e]-p) and
                np.array_equal(ids, a['index'][p:q]) and np.array_equal(vals, a['value'][p:q])):
            raise ValueError('CSC exact readback failed (including ordering)')
    for s, e in ranges(m):
        sense, rhs = row_encoding(a['row_lower'][s:e], a['row_upper'][s:e])
        if not np.array_equal(backend.array('Sense', s, e-s, 'S1'), sense) or not np.array_equal(backend.array('RHS', s, e-s), rhs):
            raise ValueError('row readback')
    return {'status': 'EXACT_READBACK_PASS', 'basis_required': False}


def save_returned(backend, meta, directory, native_returned=False):
    """Capture raw legal attributes after native return; availability != qualification."""
    if not native_returned:
        raise ValueError('Cannot read a running solver')
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=False)
    receipt = {'qualification': 'UNQUALIFIED', 'native_status': backend.scalar('Status', int),
               'vectors': {}, 'basis': 'NOT_REQUESTED', 'native_info': {}}
    def receipt_write():
        (directory/'RAW_RECEIPT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    receipt_write()  # save native status before any possibly unavailable vector
    for attr,kind in [('SolCount',int),('BarIterCount',int),('IterCount',float),('Runtime',float),
                      ('ObjVal',float),('BoundVio',float),('ConstrVio',float),('DualVio',float),
                      ('MaxVio',float),('ComplVio',float)]:
        try:
            value=backend.scalar(attr,kind)
            receipt['native_info'][attr]=value if math.isfinite(value) else {'status':'NONFINITE','value':str(value)}
        except Exception as exc:
            receipt['native_info'][attr]={'status':'NOT_AVAILABLE','error_type':type(exc).__name__}
    receipt_write()
    for attr, n in [('X', meta['num_col']), ('Pi', meta['num_row']), ('RC', meta['num_col'])]:
        path = directory/(attr+'.partial.npy')
        out = None
        try:
            out = np.lib.format.open_memmap(path, mode='w+', dtype='<f8', shape=(n,))
            for s, e in ranges(n):
                v = backend.array(attr, s, e-s)
                if len(v) != e-s or not np.isfinite(v).all():
                    raise ValueError('nonfinite or incomplete returned array')
                out[s:e] = v
            out.flush(); del out; out = None
            final = directory/(attr+'.npy'); path.rename(final)
            receipt['vectors'][attr] = {'status': 'SAVED_UNQUALIFIED', 'sha256': sha256(final), 'count': n}
        except Exception as exc:
            if out is not None:
                out.flush(); del out
            receipt['vectors'][attr] = {'status': 'NOT_AVAILABLE_OR_INCOMPLETE', 'error_type': type(exc).__name__}
        receipt_write()
    return receipt


def save_original_vectors(raw_directory, mapping_folder, output_directory):
    """Post-return label-preserving export, independent of any PyPSA model object."""
    raw_directory, mapping_folder = Path(raw_directory), Path(mapping_folder)
    dest=Path(output_directory); dest.mkdir(parents=True,exist_ok=False)
    receipt=json.loads((raw_directory/'RAW_RECEIPT.json').read_text(encoding='utf-8'))
    manifest=json.loads((mapping_folder/'MAPPING_MANIFEST.json').read_text(encoding='utf-8-sig'))
    scales={}
    for key in ('D','R','vlabels','clabels'):
        item=manifest['arrays'][key]; p=mapping_folder/item['file']
        if sha256(p)!=item['sha256']:raise ValueError('mapping hash mismatch')
        scales[key]=np.load(p,mmap_mode='r',allow_pickle=False)
    exported={}
    for attr,key,divide,labels in [('X','D',False,'vlabels'),('Pi','R',False,'clabels'),('RC','D',True,'vlabels')]:
        info=receipt['vectors'].get(attr,{})
        if info.get('status')!='SAVED_UNQUALIFIED':
            raise ValueError('incomplete raw vector: '+attr)
        raw_path=raw_directory/(attr+'.npy')
        if sha256(raw_path)!=info['sha256']:raise ValueError('raw hash mismatch')
        raw=np.load(raw_path,mmap_mode='r',allow_pickle=False);factor=scales[key]
        if len(raw)!=len(factor) or len(raw)!=len(scales[labels]):raise ValueError('mapping length')
        path=dest/(attr+'_original.partial.npy')
        out=np.lib.format.open_memmap(path,mode='w+',dtype='<f8',shape=raw.shape)
        for s,e in ranges(len(raw)):
            if not np.all(np.isfinite(factor[s:e]) & (factor[s:e]>0)):raise ValueError('invalid scale')
            mapped=raw[s:e]/factor[s:e] if divide else raw[s:e]*factor[s:e]
            inverse=mapped*factor[s:e] if divide else mapped/factor[s:e]
            if not np.isfinite(mapped).all() or not np.array_equal(inverse,raw[s:e]):raise ValueError('inexact original-unit mapping')
            out[s:e]=mapped
        out.flush();del out
        final=dest/(attr+'_original.npy');path.rename(final)
        exported[attr]={'sha256':sha256(final),'label_array_reference':str(mapping_folder/manifest['arrays'][labels]['file']),
                        'labels_sha256':manifest['arrays'][labels]['sha256']}
    result={'qualification':'UNQUALIFIED_PENDING_ACCEPTANCE','native_status':receipt['native_status'],
            'mapping_manifest_sha256':sha256(mapping_folder/'MAPPING_MANIFEST.json'),'vectors':exported,
            'semantic_network_export':'PENDING_COORDINATE_MAP_AND_ENGINEERING_CHECKS'}
    (dest/'ORIGINAL_VECTOR_INDEX.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result


class CBackend:
    """Unexecuted native C API candidate, avoiding millions of Python Var wrappers.

    Caller owns an already-authorized GRBenv*. No license, DLL discovery or solve.
    Must verify ABI against the chosen gurobi_c.h before native integration tests.
    """
    def __init__(self, library, environment):
        self.lib, self.env, self.model = library, environment, C.c_void_p()
        p, i, d, s = C.c_void_p, C.c_int, C.c_double, C.c_char_p
        signatures = {
            'GRBnewmodel': [p,p,s,i,p,p,p,p,p], 'GRBaddconstrs': [p,i,i,p,p,p,p,p,p],
            'GRBaddvars': [p,i,i,p,p,p,p,p,p,p,p], 'GRBupdatemodel': [p],
            'GRBsetdblattr': [p,s,d], 'GRBsetintattr': [p,s,i],
            'GRBgetdblattr': [p,s,p], 'GRBgetintattr': [p,s,p],
            'GRBgetdblattrarray': [p,s,i,i,p], 'GRBgetcharattrarray': [p,s,i,i,p],
            'GRBgetvars': [p,p,p,p,p,i,i],
        }
        for name, args in signatures.items():
            f = getattr(library, name); f.argtypes = args; f.restype = i
        library.GRBfreemodel.argtypes = [p]; library.GRBfreemodel.restype = None

    def call(self, name, *args):
        code = getattr(self.lib, name)(*args)
        if code:
            raise RuntimeError(f'{name}: native error {code}')

    @staticmethod
    def ptr(a):
        if not a.flags.c_contiguous:
            raise ValueError('noncontiguous native buffer')
        return a.ctypes.data_as(C.c_void_p)

    def create(self, offset):
        self.call('GRBnewmodel', self.env, C.byref(self.model), b'FROZEN_FULL_SC_CANDIDATE', 0, None, None, None, None, None)
        self.call('GRBsetintattr', self.model, b'ModelSense', 1)
        self.call('GRBsetdblattr', self.model, b'ObjCon', offset)

    def rows(self, sense, rhs):
        beg = np.zeros(len(rhs), dtype=np.int32)
        self.call('GRBaddconstrs', self.model, len(rhs), 0, self.ptr(beg), None, None, self.ptr(sense), self.ptr(rhs), None)

    def columns(self, beg, ids, vals, obj, lb, ub):
        self.call('GRBaddvars', self.model, len(obj), len(vals), *[self.ptr(x) for x in (beg, ids, vals, obj, lb, ub)], None, None)

    def update(self):
        self.call('GRBupdatemodel', self.model)

    def scalar(self, attr, kind):
        value = C.c_int() if kind is int else C.c_double()
        self.call('GRBgetintattr' if kind is int else 'GRBgetdblattr', self.model, attr.encode(), C.byref(value))
        return value.value

    def array(self, attr, start, count, dtype='<f8'):
        out = np.empty(count, dtype=dtype)
        self.call('GRBgetcharattrarray' if dtype == 'S1' else 'GRBgetdblattrarray', self.model, attr.encode(), start, count, self.ptr(out))
        return out

    def matrix_columns(self, start, count):
        nz = C.c_int()
        self.call('GRBgetvars', self.model, C.byref(nz), None, None, None, start, count)
        beg, ids, val = np.empty(count, np.int32), np.empty(nz.value, np.int32), np.empty(nz.value, np.float64)
        self.call('GRBgetvars', self.model, C.byref(nz), self.ptr(beg), self.ptr(ids), self.ptr(val), start, count)
        return beg, ids, val

    def close(self):
        if self.model.value:
            self.lib.GRBfreemodel(self.model); self.model = C.c_void_p()
