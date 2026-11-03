"""V3 HPC package (instruction V14 section 2): read-only element-wise comparison of two PyPSA netCDF networks, no solver.
Every netCDF variable (data and coordinates) is compared bit by bit; a differing component variable is resolved to the differing components (static: the
<list>_i index; time series: the <list>_t_<attr>_i columns), components present in one file only are listed, global attributes are compared and the
meta JSON is parsed and compared key by key (leaf paths). Output: one JSON with the differences; the caller judges them against a pre-registered list.
usage: python chk_nets.py <old.nc> <new.nc> <out.json> [--carriers]"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
import xarray as xr


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def bits_equal(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return False
    if a.dtype.kind in "fc":
        return bool(np.array_equal(a.view(f"u{a.dtype.itemsize}"), b.view(f"u{b.dtype.itemsize}")))
    return bool(np.array_equal(a, b)) if a.dtype.kind in "iubM" else a.tolist() == b.tolist()


def elem_diff(a, b):
    """indices (along the last axis for 2-D, the only axis for 1-D) where a and b differ bit-wise; NaN == NaN counts as equal"""
    a, b = np.asarray(a), np.asarray(b)
    if a.dtype.kind in "fc" and b.dtype.kind in "fc" and a.dtype == b.dtype:
        ne = a.view(f"u{a.dtype.itemsize}") != b.view(f"u{b.dtype.itemsize}")
    else:
        ne = np.asarray(a.astype(str) != b.astype(str))
    return np.where(ne.any(axis=0) if ne.ndim == 2 else ne)[0]


def meta_diff(a, b, path=()):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            out += [path + (k,)] if (k in a) != (k in b) else meta_diff(a[k], b[k], path + (k,))
        return out
    return [] if json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True) else [path]


def get(d, path):
    for k in path:
        d = d.get(k) if isinstance(d, dict) else None
    return d


def compare(old: Path, new: Path) -> dict:
    o = xr.open_dataset(old, engine="netcdf4", decode_cf=False, mask_and_scale=False); n = xr.open_dataset(new, engine="netcdf4", decode_cf=False, mask_and_scale=False)
    carrier = {}
    for ds in (o, n):
        for v in ds.variables:
            if v.endswith("_carrier") and len(ds[v].dims) == 1 and ds[v].dims[0].endswith("_i") and "_t_" not in v:
                lst = v[: -len("_carrier")]
                if f"{lst}_i" in ds.variables:
                    carrier.setdefault(lst, {}).update(zip([str(x) for x in ds[f"{lst}_i"].values], [str(x) for x in ds[v].values]))
    res = dict(old=str(old), new=str(new), sha256_old=sha(old), sha256_new=sha(new), bytes_old=old.stat().st_size, bytes_new=new.stat().st_size,
               only_in_old=[], only_in_new=[], variables={}, index_changes={}, attributes=[], meta_keys={})
    for v in sorted(set(o.variables) | set(n.variables)):
        if v not in o.variables or v not in n.variables:
            (res["only_in_old"] if v in o.variables else res["only_in_new"]).append(v); continue
        a, b = o[v], n[v]
        if a.dims == b.dims and bits_equal(a.values, b.values) and repr(sorted(a.attrs.items())) == repr(sorted(b.attrs.items())):
            continue
        dim = a.dims[-1] if a.dims else None
        info = dict(dims=list(a.dims), attrs_equal=repr(sorted(a.attrs.items())) == repr(sorted(b.attrs.items())))
        if dim and dim in o.variables and dim in n.variables and dim != v:
            io, inn = [str(x) for x in o[dim].values], [str(x) for x in n[dim].values]
            so, sn = set(io), set(inn)
            common = [x for x in io if x in sn]
            if io != inn:
                res["index_changes"][dim] = dict(removed=[x for x in io if x not in sn], added=[x for x in inn if x not in so], order_same=common == [x for x in inn if x in so])
            if common:
                ao = a.sel({dim: common}).values if io != common else a.values
                bo = b.sel({dim: common}).values if inn != common else b.values
                if ao.shape == bo.shape:
                    idx = elem_diff(ao, bo); names = [common[i] for i in idx]
                    lst = dim[: -len("_i")]; base = lst.split("_t_")[0]
                    info.update(n_elements=len(common), n_differing=len(names), differing=names[:2000], differing_carriers=sorted({carrier.get(base, {}).get(x, "?") for x in names}))
                    if a.ndim == 1 and len(names) <= 20:
                        info["values"] = {x: [ao[i].item() if hasattr(ao[i], "item") else ao[i], bo[i].item() if hasattr(bo[i], "item") else bo[i]] for x, i in zip(names, idx)}
                else:
                    info["shape_mismatch"] = [list(ao.shape), list(bo.shape)]
        res["variables"][v] = info
    res["attributes"] = [k for k in sorted(set(o.attrs) | set(n.attrs)) if k != "meta" and o.attrs.get(k) != n.attrs.get(k)]
    mo, mn = json.loads(o.attrs.get("meta", "{}")), json.loads(n.attrs.get("meta", "{}"))
    for p in meta_diff(mo, mn):
        x, y = get(mo, p), get(mn, p)
        short = lambda z: z if len(json.dumps(z, default=str)) <= 300 else f"<{type(z).__name__} {len(json.dumps(z, default=str))} chars>"
        res["meta_keys"][".".join(map(str, p))] = [short(x), short(y)]
    o.close(); n.close()
    return res


if __name__ == "__main__":
    r = compare(Path(sys.argv[1]), Path(sys.argv[2]))
    Path(sys.argv[3]).write_text(json.dumps(r, indent=1, default=str) + "\n")
    print(json.dumps(dict(sha_old=r["sha256_old"][:8], sha_new=r["sha256_new"][:8], only_old=r["only_in_old"], only_new=r["only_in_new"],
                          variables={k: (v.get("n_differing"), v.get("differing_carriers")) for k, v in r["variables"].items()}, index_changes={k: (len(v["removed"]), len(v["added"])) for k, v in r["index_changes"].items()},
                          attributes=r["attributes"], meta_keys=list(r["meta_keys"])), default=str))
