"""R4 exploration (no solve): objective constant columns, candidate Stores for unit scaling and the constraint groups that reference them."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main(net, truncate=56):
    import pypsa, logging, inspect
    import linopy
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    from s2_solve import set_representative_weights
    from assembly_components import install_research_constraint_hooks
    print("linopy Model.matrices:", [l.strip() for l in inspect.getsource(linopy.Model).splitlines() if "matrices" in l][:6])
    print("solve clean cache:", [l.strip() for l in inspect.getsource(linopy.Model.solve).splitlines() if "clean_cached" in l or "matrices" in l][:6])
    n = pypsa.Network(net)
    n.set_snapshots(n.snapshots[:truncate]); set_representative_weights(n); n.meta["solver_allowed"] = True
    m = n.optimize.create_model(); install_research_constraint_hooks(n)
    obj = m.objective.expression
    ov, oc = np.asarray(obj.vars).ravel(), np.asarray(obj.coeffs).ravel()
    out = {}
    for name in ["objective_constant", "Research_existing_FOM_constant", "Research_existing_cross_border_FOM_constant"]:
        if name not in m.variables:
            out[name] = "absent"; continue
        v = m.variables[name]; lab = np.asarray(v.labels).ravel()
        lo, up = float(np.asarray(v.lower).ravel()[0]), float(np.asarray(v.upper).ravel()[0])
        coef = float(oc[np.isin(ov, lab)].sum())
        in_cons = [k for k in m.constraints if np.isin(np.asarray(m.constraints[k].vars), lab).any()]
        out[name] = dict(lower=lo, upper=up, objective_coeff=coef, contribution=coef * lo, in_constraints=in_cons)
    print(json.dumps(out, indent=1))
    st = n.stores
    role = st.research_role if "research_role" in st else None
    sel = {"biomass_pools": list(st.index[role == "FINITE_RESOURCE"]), "sequestration": list(st.index[st.index.str.startswith("co2 sequestered")]),
           "capture_buffers": list(st.index[role == "CO2_BUFFER"]), "atmosphere": list(st.index[st.carrier == "co2 atmosphere"])}
    print({k: len(v) for k, v in sel.items()})
    e = m.variables["Store-e"]; enom = m.variables["Store-e_nom"]
    print("Store-e dims", e.dims, "Store-e_nom dims", enom.dims, "ext coord", enom.dims)
    for k, names in sel.items():
        labs = np.asarray(e.labels.sel(Store=names)).ravel()
        ext = [s for s in names if s in set(enom.labels.coords[enom.dims[0]].values)]
        labn = np.asarray(enom.labels.sel({enom.dims[0]: ext})).ravel() if ext else np.array([], dtype=int)
        lo = np.asarray(e.lower.sel(Store=names)); up = np.asarray(e.upper.sel(Store=names))
        groups = {}
        for cname in m.constraints:
            v = np.asarray(m.constraints[cname].vars)
            hit = np.isin(v, labs) | (np.isin(v, labn) if len(labn) else False)
            if hit.any():
                rows = hit.reshape(-1, v.shape[-1]).any(axis=1).sum() if v.ndim > 1 else int(hit.any())
                groups[cname] = int(rows)
        objhit = int(np.isin(ov, np.concatenate([labs, labn])).sum())
        print(f"== {k}: stores {len(names)}, extendable {len(ext)}, e bounds lo [{np.nanmin(lo):.3g},{np.nanmax(lo):.3g}] up [{np.nanmin(up):.3g},{np.nanmax(up):.3g}], objective terms {objhit}")
        print("   constraint groups (rows):", groups)
        if ext:
            print("   e_nom bounds:", float(np.nanmin(np.asarray(enom.lower.sel({enom.dims[0]: ext})))), float(np.nanmax(np.asarray(enom.upper.sel({enom.dims[0]: ext})))))
    # rhs of the store constraint groups for the selection
    for cname in ["Store-energy_balance", "Store-fix-e-upper", "Store-fix-e-lower", "Store-ext-e-upper", "Store-ext-e-lower", "Store-ext-e_nom-upper", "research_co2_storage_cap"]:
        if cname in m.constraints:
            c = m.constraints[cname]; r = np.asarray(c.rhs); print(cname, "dims", c.dims, "rhs max", float(np.nanmax(np.abs(r))) if r.size else None, "coeff max", float(np.nanmax(np.abs(np.asarray(c.coeffs)))))
    print("research constraint names:", [k for k in m.constraints if k.lower().startswith("research")][:40])


if __name__ == "__main__":
    main(sys.argv[1])
