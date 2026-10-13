import numpy as np
def scatter_active(labels,active_labels,values,missing=0.):
    labels=np.asarray(labels);ok=labels>=0;flat=labels[ok]
    positions=np.searchsorted(active_labels,flat)
    if np.any(positions>=len(active_labels)) or not np.array_equal(active_labels[positions],flat):raise ValueError('active label mismatch')
    out=np.full(labels.shape,missing,dtype=np.float64);out[ok]=values[positions]
    if not np.isfinite(out).all():raise ValueError('nonfinite mapped result')
    return out
