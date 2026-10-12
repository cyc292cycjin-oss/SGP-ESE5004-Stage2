"""Exact LP row semantics only; never use for frozen input/file identity.

Finite binary64 equality has zero tolerance and identifies the two signed zeros.
Infinity is forbidden in a finite RHS; only explicitly expected open-side bound
sentinels (-inf lower, +inf upper) are permitted by bounds_exact.
"""
from pathlib import Path
import json
import os
import numpy as np


class SemanticCheckError(ValueError):
    def __init__(self, evidence):
        self.evidence = evidence
        super().__init__(json.dumps(evidence, ensure_ascii=False, allow_nan=False))


def _hex(value):
    try:
        return float(value).hex()
    except (ValueError, TypeError, OverflowError):
        return 'INVALID:' + repr(value)


def _fail(reason, *, asset_id, family, row_labels, report_path, arrays):
    labels = np.asarray(row_labels)
    converted = {k: np.asarray(v) for k, v in arrays.items()}
    length = max([labels.size] + [a.size for a in converted.values()])
    rows = []
    for i in range(length):
        row = {'flat_index': i, 'row_label': str(labels.flat[i]) if i < labels.size else None}
        for k, a in converted.items():
            row[k + ('_hex' if a.dtype.kind in 'fiu' else '_value')] = (
                _hex(a.flat[i]) if a.dtype.kind in 'fiu' else str(a.flat[i])
            ) if i < a.size else None
        rows.append(row)
    evidence = {'schema': 'C02R_EXACT_ROW_FAILURE_V1', 'reason': reason,
                'asset_id': str(asset_id), 'constraint_family': str(family),
                'row_labels_shape': list(labels.shape),
                'arrays': {k: {'shape': list(a.shape), 'dtype': str(a.dtype)} for k, a in converted.items()},
                'rows': rows, 'rtol': 0, 'atol': 0, 'scientific_values_modified': False}
    if report_path is not None:
        try:
            # One failure record per new run, never replace the earlier evidence.
            with Path(report_path).open('x', encoding='utf-8') as f:
                json.dump(evidence, f, ensure_ascii=False, indent=2, allow_nan=False)
                f.write('\n'); f.flush(); os.fsync(f.fileno())
        except OSError as exc:
            evidence['persistence_error_type'] = type(exc).__name__
            evidence['evidence_retained_in_exception'] = True
    raise SemanticCheckError(evidence)


def _context(asset_id, family, row_labels, report_path):
    return dict(asset_id=asset_id, family=family, row_labels=row_labels, report_path=report_path)


def _structure(values, context):
    arrays = {k: np.asarray(v) for k, v in values.items()}
    labels = np.asarray(context['row_labels'])
    if labels.dtype.kind not in 'iu' or np.any(labels < 0):
        _fail('INVALID_ROW_LABELS', arrays=arrays, **context)
    if any(a.shape != labels.shape for a in arrays.values()):
        _fail('SHAPE_MISMATCH', arrays=arrays, **context)
    if any(a.dtype.kind != 'f' or a.dtype.itemsize != 8 for a in arrays.values()):
        _fail('NOT_BINARY64', arrays=arrays, **context)
    return arrays


def rhs_exact(actual, expected, *, actual_signs, expected_sign,
              asset_id, family, row_labels, report_path=None):
    context = _context(asset_id, family, row_labels, report_path)
    arrays = _structure({'actual': actual, 'expected': expected}, context)
    a, e = arrays['actual'], arrays['expected']
    signs = np.asarray(actual_signs)
    diagnostic = {**arrays, 'actual_signs': signs,
                  'expected_signs': np.full(e.shape, expected_sign)}
    if signs.shape != e.shape:
        _fail('SIGN_SHAPE_MISMATCH', arrays=diagnostic, **context)
    if expected_sign not in ('=', '<=', '>=') or not np.all(signs == expected_sign):
        _fail('ROW_DIRECTION_MISMATCH', arrays=diagnostic, **context)
    if not all(np.isfinite(x).all() for x in (a, e)):
        _fail('NONFINITE_RHS', arrays=diagnostic, **context)
    if not np.array_equal(a, e):
        _fail('FINITE_RHS_NOT_EXACT', arrays=diagnostic, **context)
    return {'status': 'EXACT_SEMANTIC_PASS', 'signed_zero_pairs': int(
        np.count_nonzero((a == 0) & (e == 0) & (np.signbit(a) != np.signbit(e))))}


def bounds_exact(actual_lower, actual_upper, expected_lower, expected_upper, *,
                 asset_id, family, row_labels, report_path=None):
    context = _context(asset_id, family, row_labels, report_path)
    arrays = _structure(dict(actual_lower=actual_lower, actual_upper=actual_upper,
                             expected_lower=expected_lower, expected_upper=expected_upper), context)
    lo, hi, elo, ehi = (arrays[k] for k in ('actual_lower', 'actual_upper', 'expected_lower', 'expected_upper'))
    if any(np.isnan(x).any() for x in arrays.values()):
        _fail('NAN_BOUND', arrays=arrays, **context)
    if np.isposinf(elo).any() or np.isneginf(ehi).any() or np.any(elo > ehi) or np.any(np.isneginf(elo) & np.isposinf(ehi)):
        _fail('INVALID_EXPECTED_ROW_BOUNDS', arrays=arrays, **context)
    # Finite expected endpoints cannot turn into Inf; unbounded sentinels must
    # retain the exact correct side and sign. This is not general Inf acceptance.
    for actual, expected in ((lo, elo), (hi, ehi)):
        finite = np.isfinite(expected)
        if not np.isfinite(actual[finite]).all():
            _fail('UNEXPECTED_NONFINITE_BOUND', arrays=arrays, **context)
        if not np.array_equal(actual[~finite], expected[~finite]):
            _fail('OPEN_SIDE_SENTINEL_MISMATCH', arrays=arrays, **context)
        if not np.array_equal(actual[finite], expected[finite]):
            _fail('FINITE_BOUND_NOT_EXACT', arrays=arrays, **context)
    return {'status': 'EXACT_SEMANTIC_PASS', 'signed_zero_pairs': sum(int(np.count_nonzero(
        (a == 0) & (e == 0) & (np.signbit(a) != np.signbit(e)))) for a, e in ((lo, elo), (hi, ehi)))}
