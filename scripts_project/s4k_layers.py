"""S4K model layer (S4K instruction v1, 2026-10-18; decision 108): AC lines - linear loss proxy instead of the PyPSA piecewise tangents.

Switches (configs/research/baseline.yaml):
  research.network.ac_losses: linear_proxy (main) | pypsa_tangent (S4J state, PyPSA transmission_losses = 2; default when absent) | none
  research.network.ac_loss_reference_loading: alpha = 0.5 (main; sensitivity 1.0)
  With research.network.transmission_losses = none (S4J switch) the AC lines are lossless as well (the S4J 'no losses' comparison is unchanged).
  DC links and pipelines keep the S4J-2 losses.

PyPSA 0.30.3 structure that the proxy keeps (pypsa/optimization; S4K report section 2 cites the lines):
  * variables.py 146-155 define_loss_variables: 'Line-loss' >= 0 over (snapshot, Line);
  * constraints.py 556-562 define_nodal_balance_constraints: the loss is withdrawn half at bus0 and half at bus1 (coefficient -0.5 each);
  * constraints.py 72-75 / 117-120: the line capacity rows include the loss (s - loss >= lower, s + loss <= upper; extendable: with the
    s_nom variable);
  * constraints.py 619 ff. define_kirchhoff_voltage_constraints: only the flow 'Line-s' - the loss does not enter the cycle rows;
  * optimize.py 455-459 assign_solution: p0 += loss / 2, p1 += loss / 2 when 'Line-loss' exists (so p0 + p1 = loss after the solve);
  * constraints.py 932-975 define_loss_constraints: loss <= r (s_max_pu s_nom_max)^2 and the tangents - REPLACED here by
      loss >= lambda * s,  loss >= -lambda * s,  loss <= lambda * s_max_pu * s_nom  (s_nom = variable for extendable lines).
  The solver gets transmission_losses = 0 (no PyPSA tangents, no double counting); the hook research_ac_loss_proxy creates 'Line-loss' with
  PyPSA's own define_loss_variables and rebuilds the nodal balance and the line capacity rows with PyPSA's own functions (transmission_losses
  = 1, which only switches the loss terms on), then adds the three proxy rows. It runs first among the research hooks.

lambda per line (by line type; one circuit): R = r_per_length * length (Ohm; length = model length incl. the 1.25 length factor),
  I_ref = alpha * s_max_pu * i_nom (kA), lambda = sqrt(3) * I_ref * R / v_nom (kV). Independent of num_parallel: with the number of circuits
  growing with the flow the loading per circuit stays about constant, so the loss is about proportional to the flow (as the DC efficiency per
  length). Check (stop condition): the 380 kV 4-bundle type at 100 km gives about 1.2 % (alpha 0.5) and 2.5 % (alpha 1.0), within 20 %.
"""
from __future__ import annotations

import math

import pandas as pd

AC_LOSS_MODES = ("linear_proxy", "pypsa_tangent", "none")
PROXY_HOOK = "research_ac_loss_proxy"
LAMBDA_COL = "ac_loss_lambda"
PYPSA_TANGENTS = 2                       # S4J state (PyPSA-Eur v2025.07.0 solving.options.transmission_losses, config line 1001)
REFERENCE_TYPE = "Al/St 240/40 4-bundle 380.0"
REFERENCE_CHECK = {0.5: 0.012, 1.0: 0.025}   # instruction S4K-1 point 3: lambda at 100 km, 380 kV 4-bundle
REFERENCE_TOLERANCE = 0.20


def ac_loss_mode(cfg) -> str:
    v = str((cfg["research"].get("network") or {}).get("ac_losses", "pypsa_tangent")).lower()
    if v not in AC_LOSS_MODES:
        raise ValueError("Unknown research.network.ac_losses " + v)
    return v


def reference_loading(cfg) -> float:
    a = float((cfg["research"].get("network") or {}).get("ac_loss_reference_loading", 0.5))
    if not 0.0 < a <= 1.0:
        raise ValueError(f"research.network.ac_loss_reference_loading must be in (0, 1]: {a}")
    return a


def type_lambda_per_km(n, line_type: str, alpha: float, s_max_pu: float, v_nom: float) -> float:
    t = n.line_types.loc[line_type]
    return math.sqrt(3.0) * alpha * s_max_pu * float(t.i_nom) * float(t.r_per_length) / v_nom


def line_lambda(n, alpha: float) -> pd.DataFrame:
    """Per-line table: type, v_nom, length, one-circuit R, i_nom, I_ref and lambda (fraction of the flow)."""
    L = n.lines
    if (L.type.astype(str) == "").any():
        raise ValueError("AC lines without a line type: lambda by type undefined " + str(list(L.index[L.type.astype(str) == ""])[:5]))
    v0, v1 = L.bus0.map(n.buses.v_nom).astype(float), L.bus1.map(n.buses.v_nom).astype(float)
    if (v0 != v1).any():
        raise ValueError("AC lines between different voltage levels")
    lt = n.line_types.reindex(L.type)
    smax = n.get_switchable_as_dense("Line", "s_max_pu").max()   # static 0.7 in this model; the maximum if a series were set
    R = lt.r_per_length.to_numpy() * L.length.astype(float).to_numpy()
    I_ref = alpha * smax.reindex(L.index).to_numpy() * lt.i_nom.to_numpy()
    lam = math.sqrt(3.0) * I_ref * R / v0.to_numpy()
    return pd.DataFrame(dict(type=L.type.astype(str), v_nom_kv=v0, length_km=L.length.astype(float), r_ohm_per_km=lt.r_per_length.to_numpy(),
                             R_one_circuit_ohm=R, i_nom_ka=lt.i_nom.to_numpy(), s_max_pu=smax.reindex(L.index).to_numpy(), I_ref_ka=I_ref, ac_loss_lambda=lam,
                             border_class=(L.border_class.astype(str) if "border_class" in L else "")), index=L.index)


def reference_check(n) -> dict:
    """Instruction S4K-1 point 3 (stop condition): the 380 kV 4-bundle type at 100 km against 1.2 % (alpha 0.5) and 2.5 % (alpha 1.0)."""
    out = {}
    for a, exp in REFERENCE_CHECK.items():
        lam = 100.0 * type_lambda_per_km(n, REFERENCE_TYPE, a, 0.7, 380.0)
        out[str(a)] = dict(lambda_100km=lam, expected=exp, relative_difference=lam / exp - 1.0, within=abs(lam / exp - 1.0) <= REFERENCE_TOLERANCE)
    if not all(v["within"] for v in out.values()):
        raise ValueError("STOP (S4K-1 point 3): lambda reference check off by more than 20 %: " + str(out))
    return out


def apply_ac_losses(n, cfg, losses: dict) -> dict:
    """S4K-1 (decision 108). Call after s4j_layers.apply_transmission_losses (its meta dict 'losses' gets the AC tangent count the solver reads)."""
    tl_mode = losses.get("mode", "none")
    mode = ac_loss_mode(cfg) if tl_mode != "none" else "none"   # transmission_losses = none -> AC lossless too
    alpha = reference_loading(cfg)
    losses["ac_losses"] = mode
    losses["ac_transmission_losses"] = PYPSA_TANGENTS if mode == "pypsa_tangent" else 0
    n.meta["research_transmission_losses"] = losses
    led = dict(mode=mode, configured=ac_loss_mode(cfg), transmission_losses=tl_mode, solver_transmission_losses=losses["ac_transmission_losses"])
    if mode == "linear_proxy":
        tab = line_lambda(n, alpha)
        n.lines[LAMBDA_COL] = tab.ac_loss_lambda.astype(float)
        n.meta["required_constraint_hooks"] = sorted(set(n.meta.get("required_constraint_hooks", [])) | {PROXY_HOOK})
        lam = tab.ac_loss_lambda
        led.update(alpha=alpha, hook=PROXY_HOOK, lines=int(len(tab)), reference_check=reference_check(n),
                   lambda_min=float(lam.min()), lambda_median=float(lam.median()), lambda_max=float(lam.max()),
                   by_border={k: dict(lines=int(len(g)), min=float(g.min()), median=float(g.median()), max=float(g.max())) for k, g in lam.groupby(tab.border_class)},
                   formula="lambda = sqrt(3) * alpha * s_max_pu * i_nom * r_per_length * length / v_nom (one circuit, by line type)")
    n.meta["research_ac_losses"] = led
    return led


def install_ac_loss_proxy(n) -> dict:
    """research_ac_loss_proxy hook (see the module docstring). Must run right after create_model(transmission_losses=0), before other hooks."""
    import xarray as xr
    from pypsa.optimization.common import reindex
    from pypsa.optimization.constraints import (define_nodal_balance_constraints, define_operational_constraints_for_extendables,
                                                define_operational_constraints_for_non_extendables)
    from pypsa.optimization.variables import define_loss_variables
    m = n.model
    if getattr(n, "_research_ac_proxy_model", None) is m:
        raise ValueError("AC loss proxy hook already installed")
    if "Line-loss" in m.variables:
        raise ValueError("PyPSA transmission_losses active together with the AC loss proxy (double counting)")
    if LAMBDA_COL not in n.lines:
        raise ValueError("AC loss proxy hook without the per-line lambda column")
    sns = n.snapshots
    if not pd.Index(m["Line-s"].coords["snapshot"].values).equals(pd.Index(sns)):
        raise ValueError("model snapshots differ from the network snapshots")
    define_loss_variables(n, sns, "Line")                                   # 'Line-loss' >= 0 (PyPSA)
    rebuilt = []
    for name, dim, suffix in (("Bus-nodal_balance", "Bus", ""), ("Bus-meshed-nodal_balance", "Bus-meshed", "-meshed")):
        if name in m.constraints:   # same bus split as create_model; PyPSA adds -0.5 loss at bus0 and bus1
            buses = pd.Index(m.constraints[name].coords[dim].values, name="Bus")
            m.remove_constraints(name)
            define_nodal_balance_constraints(n, sns, transmission_losses=1, buses=buses, suffix=suffix)
            rebuilt.append(name)
    for name in ("Line-fix-s-lower", "Line-fix-s-upper", "Line-ext-s-lower", "Line-ext-s-upper"):
        if name in m.constraints:
            m.remove_constraints(name); rebuilt.append(name)
    define_operational_constraints_for_non_extendables(n, sns, "Line", "s", 1)   # s - loss >= lower, s + loss <= upper (PyPSA)
    define_operational_constraints_for_extendables(n, sns, "Line", "s", 1)
    lam = xr.DataArray(n.lines[LAMBDA_COL].astype(float).to_numpy(), coords={"Line": n.lines.index.rename("Line")}, dims="Line")
    loss, s = m["Line-loss"], m["Line-s"]
    m.add_constraints(loss - lam * s >= 0, name="Line-loss_proxy-pos")      # loss >= lambda * s
    m.add_constraints(loss + lam * s >= 0, name="Line-loss_proxy-neg")      # loss >= -lambda * s
    smax = n.get_switchable_as_dense("Line", "s_max_pu", sns)
    added = ["Line-loss_proxy-pos", "Line-loss_proxy-neg"]
    fix_i, ext_i = n.get_non_extendable_i("Line"), n.get_extendable_i("Line")
    if len(fix_i):
        ub = smax[fix_i].mul(n.lines.s_nom.reindex(fix_i) * n.lines[LAMBDA_COL].reindex(fix_i), axis=1)
        m.add_constraints(reindex(loss, "Line", fix_i) <= xr.DataArray(ub.rename_axis(columns=fix_i.name)), name="Line-fix-loss_upper"); added.append("Line-fix-loss_upper")
    if len(ext_i):
        coef = smax[ext_i].mul(n.lines[LAMBDA_COL].reindex(ext_i), axis=1)
        m.add_constraints(reindex(loss, "Line", ext_i) - xr.DataArray(coef.rename_axis(columns=ext_i.name)) * m["Line-s_nom"] <= 0, name="Line-ext-loss_upper")
        added.append("Line-ext-loss_upper")
    n._research_ac_proxy_model = m
    led = dict(hook=PROXY_HOOK, loss_variables=int(m["Line-loss"].size), rebuilt=rebuilt, added=added)
    n.meta["research_ac_loss_proxy_model"] = led
    return led
