"""S3B R4 (decision 69): LP scaling applied to the linopy model between model creation and solve; the network is never changed.

(a) objective constants out of the LP: the fixed-at-a-value columns that only carry constants (PyPSA `objective_constant` = capital cost of the
    existing part of extendable capacity, coefficient -1; `Research_existing_FOM_constant` and `Research_existing_cross_border_FOM_constant`,
    fixed at 1 with the audited annual FOM as coefficient) are removed with linopy `remove_variables`; their contribution is recorded and added
    back to the reported objective, so the total-cost definition is unchanged (n.objective = LP objective + constants).
(b) energy units of large-capacity Stores (biomass pools MWh -> GWh, CO2 sequestration and capture buffers t -> kt; factor k = 1000):
    column scaling x = k x' of Store-e and Store-e_nom of the selected stores (constraint and objective coefficients x k), then row scaling (/k)
    of every row that belongs to those stores (energy balance, e and e_nom bounds) and of the single-store research rows (CO2 storage caps).
    Net effect: Store-p coefficients in the stores' energy balances become w/k, right-hand sides /k, e_nom cost coefficients x k.
    After the solve, solutions of scaled columns are multiplied by k, duals of scaled rows divided by k, reduced costs of scaled columns
    divided by k, so every reported value is in the original units (MWh, t).
(c) S4C-5 (decision 69 c, implemented under decision 84): Kirchhoff-Voltage-Law row normalisation. PyPSA builds every cycle row as
    1e5 x reactance-weighted flows with one uniform factor (pypsa 0.30.3 optimization/constraints.py line 652 `C = 1e5 * sparse.diags(
    weightings.values) * sub.C`; current PyPSA master: `flow @ C_branch * 1e5`, docstring "The impedances are scaled by 1e5 to improve
    numerical conditioning"); neither PyPSA nor linopy nor PyPSA-Eur rescales rows individually. normalise_kvl_rows divides each KVL row by
    its largest |coefficient| (row infinity norm -> 1); the right-hand side is 0, so the feasible set and the primal solution are unchanged.
    Applied like (b) after the LP export (the exported LP stays in original units); after the solve unscale_kvl_duals restores the KVL
    duals in original units (pi = pi_normalised / row_max); reduced costs are unaffected by row scaling.
"""
from __future__ import annotations

import numpy as np
import xarray as xr

CONSTANT_COLUMNS = ("objective_constant", "Research_existing_FOM_constant", "Research_existing_cross_border_FOM_constant")
STORE_ROW_GROUPS = ("Store-energy_balance", "Store-fix-e-lower", "Store-fix-e-upper", "Store-ext-e-lower", "Store-ext-e-upper", "Store-ext-e_nom-lower", "Store-ext-e_nom-upper")
SINGLE_STORE_ROW_PREFIXES = ("research_co2_storage_cap-",)


def _assign(con, **kw):
    from linopy.common import assign_multiindex_safe
    con._data = assign_multiindex_safe(con.data, **kw)


def remove_objective_constants(m):
    """Remove the constant-only columns from the LP; return their objective contribution (EUR) and evidence."""
    obj = m.objective.expression
    ov, oc = np.asarray(obj.vars).ravel(), np.asarray(obj.coeffs).ravel()
    led = dict(columns={}, total_eur=0.0)
    for name in CONSTANT_COLUMNS:
        if name not in m.variables:
            continue
        v = m.variables[name]; lab = np.asarray(v.labels).ravel()
        lo, up = np.asarray(v.lower).ravel(), np.asarray(v.upper).ravel()
        if not np.allclose(lo, up):
            raise ValueError(f"{name} is not fixed; cannot move it out of the LP")
        refs = [k for k in m.constraints if np.isin(np.asarray(m.constraints[k].vars), lab).any()]
        if refs:
            raise ValueError(f"{name} appears in constraints {refs[:3]}; removal would change the model")
        coef = float(oc[np.isin(ov, lab)].sum()); contrib = float(coef * lo[0])
        m.remove_variables(name)
        led["columns"][name] = dict(value=float(lo[0]), objective_coefficient=coef, contribution_eur=contrib)
        led["total_eur"] += contrib
    return led


def select_stores(n, groups):
    st = n.stores; role = st.research_role if "research_role" in st else None
    sel = {}
    if "biomass_pools" in groups and role is not None:
        sel["biomass_pools"] = sorted(st.index[role == "FINITE_RESOURCE"])
    if "sequestration" in groups:
        sel["sequestration"] = sorted(st.index[st.index.str.startswith("co2 sequestered")])
    if "capture_buffers" in groups and role is not None:
        sel["capture_buffers"] = sorted(st.index[role == "CO2_BUFFER"])
    return sel


def _store_dim(con_or_var):
    dims = [d for d in con_or_var.labels.dims if d.startswith("Store")]
    return dims[0] if dims else None


def scale_store_energy(m, stores, k=1000.0):
    """Column-scale Store-e / Store-e_nom of `stores` by k and row-scale their rows by 1/k. Returns the ledger needed to unscale."""
    stores = list(stores); k = float(k)
    e = m.variables["Store-e"]; enom = m.variables["Store-e_nom"]
    e_dim = _store_dim(e); n_dim = _store_dim(enom)
    ext = [s for s in stores if s in set(enom.labels.coords[n_dim].values)]
    lab_e = np.asarray(e.labels.sel({e_dim: stores})).ravel()
    lab_n = np.asarray(enom.labels.sel({n_dim: ext})).ravel() if ext else np.array([], dtype=np.int64)
    scaled = np.concatenate([lab_e, lab_n]); scaled = scaled[scaled >= 0]
    led = dict(factor=k, stores=stores, extendable=ext, scaled_columns=int(len(scaled)), row_groups={}, unscaled_rows_with_scaled_columns={})
    sset = set(stores)
    for cname in list(m.constraints):
        con = m.constraints[cname]
        vars_ = con.vars
        hit = vars_.isin(scaled)
        if not bool(hit.any()):
            continue
        coeffs = con.coeffs.where(~hit, con.coeffs * k)   # column scaling
        dim = _store_dim(con)
        if cname in STORE_ROW_GROUPS and dim is not None:
            rowmask = xr.DataArray(np.isin(con.labels.coords[dim].values, list(sset)), coords={dim: con.labels.coords[dim].values}, dims=[dim])
            rowmask = rowmask.broadcast_like(con.labels)
        elif cname.startswith(SINGLE_STORE_ROW_PREFIXES):
            rowmask = xr.ones_like(con.labels, dtype=bool)
        else:
            rowmask = None
        if rowmask is not None:
            coeffs = coeffs.where(~rowmask, coeffs / k)
            rhs = con.rhs.where(~rowmask, con.rhs / k)
            _assign(con, coeffs=coeffs, rhs=rhs)
            led["row_groups"][cname] = dict(rows=int(rowmask.sum()), dim=dim)
        else:
            _assign(con, coeffs=coeffs)
            led["unscaled_rows_with_scaled_columns"][cname] = int(hit.any(dim=con.term_dim).sum()) if hasattr(con, "term_dim") else int(hit.sum())
    # objective coefficients of scaled columns x k
    from linopy.expressions import LinearExpression
    obj = m.objective.expression; d = obj.data
    mask = d.vars.isin(scaled)
    led["objective_terms_scaled"] = int(mask.sum())
    if bool(mask.any()):
        m.objective = LinearExpression(d.assign(coeffs=d.coeffs.where(~mask, d.coeffs * k)), m)
    led["_labels"] = scaled  # not serialised
    led["_e_dim"], led["_n_dim"] = e_dim, n_dim
    m.matrices.clean_cached_properties()
    return led


def unscale_solution(m, led):
    """Back to original units: scaled columns x k, duals of scaled rows / k."""
    k = led["factor"]; stores = led["stores"]; ext = led["extendable"]
    for vname, dim, names in [("Store-e", led["_e_dim"], stores), ("Store-e_nom", led["_n_dim"], ext)]:
        if not names:
            continue
        v = m.variables[vname]; sol = v.solution
        mask = xr.DataArray(np.isin(sol.coords[dim].values, names), coords={dim: sol.coords[dim].values}, dims=[dim]).broadcast_like(sol)
        v.solution = sol.where(~mask, sol * k)
    for cname, info in led["row_groups"].items():
        con = m.constraints[cname]
        if "dual" not in con.data:
            continue
        dual = con.dual; dim = info["dim"]
        if cname.startswith(SINGLE_STORE_ROW_PREFIXES) or dim is None:
            con.dual = dual / k
        else:
            mask = xr.DataArray(np.isin(dual.coords[dim].values, stores), coords={dim: dual.coords[dim].values}, dims=[dim]).broadcast_like(dual)
            con.dual = dual.where(~mask, dual / k)
    m.matrices.clean_cached_properties()


def unscale_reduced_costs(rc_map, led):
    k = led["factor"]
    for lab in led["_labels"]:
        if int(lab) in rc_map:
            rc_map[int(lab)] = rc_map[int(lab)] / k
    return rc_map


KVL_ROW = "Kirchhoff-Voltage-Law"


def _abs_stats(a):
    a = np.asarray(a, dtype=float); a = a[np.isfinite(a) & (a > 0)]
    return dict(min=float(a.min()), max=float(a.max()), ratio=float(a.max() / a.min())) if a.size else dict(min=None, max=None, ratio=None)


def normalise_kvl_rows(m):
    """(c) Divide every Kirchhoff-Voltage-Law row by its largest |coefficient|. Returns the ledger (row maxima kept privately for unscaling)."""
    if KVL_ROW not in m.constraints:
        return dict(applied=False, reason="no Kirchhoff-Voltage-Law rows")
    con = m.constraints[KVL_ROW]
    c = con.coeffs; valid = (con.vars != -1) & c.notnull() & (c != 0)
    a = abs(c).where(valid)
    rowmax = a.max("_term"); rowmin = a.min("_term")
    ok = (rowmax > 0) & (con.labels != -1)
    scale = xr.where(ok, rowmax, 1.0)
    _assign(con, coeffs=c / scale)
    after = abs(con.coeffs).where(valid)
    rr = (rowmax / rowmin).where(ok)
    led = dict(applied=True, constraint=KVL_ROW, rows=int(ok.sum()), method="row infinity norm: each KVL row divided by its largest |coefficient|; rhs 0 unchanged",
               coefficients_before=_abs_stats(a.values), coefficients_after=_abs_stats(after.values),
               row_max_before=_abs_stats(rowmax.where(ok).values), within_row_ratio_max=float(rr.max()), within_row_ratio_median=float(rr.median()),
               duals="restored after the solve: pi = pi_normalised / row_max (unscale_kvl_duals)")
    led["_rowmax"] = scale
    m.matrices.clean_cached_properties()
    return led


def unscale_kvl_duals(m, led):
    """(c) After the solve: KVL duals back to the original row scale (pi = pi_normalised / row_max)."""
    if not led.get("applied"):
        return
    con = m.constraints[KVL_ROW]
    if "dual" in con.data:
        con.dual = con.dual / led["_rowmax"]
    m.matrices.clean_cached_properties()


def public(led):
    return {kk: vv for kk, vv in led.items() if not kk.startswith("_")}
