"""S4K-1 data and checks (decision 108): AC lines - linear loss proxy instead of the PyPSA piecewise tangents.

  * source checks: the PyPSA 0.30.3 loss structure the proxy keeps (variables.py define_loss_variables; constraints.py nodal balance -0.5 x loss
    at each end, line capacity rows with the loss, Kirchhoff rows with the flow only, define_loss_constraints; optimize.py create_model order and
    assign_solution p0 / p1 += loss / 2), asserted line by line.
  * LAMBDA_S4K1.csv: every AC line - type, v_nom, model length and great-circle distance (length factor), one-circuit R, i_nom, lambda at
    alpha 0.5 and 1.0, and the S4J tangent parameters (r_pu_eff, first tangent point, zero-loss limit).
  * TANGENT_VS_PROXY_S4K1.csv: loss share of the flow at 0.5-14 GW for every line - S4J tangents, the proxy (alpha 0.5 / 1.0) and r_pu_eff x flow
    (quadratic loss with the circuits fixed at the line's num_parallel).
  * model-build check (no solve), first 56 snapshots: model O = create_model(transmission_losses = 0) + research hooks without the proxy, model P =
    the same with the proxy hook; P's nodal balance, line capacity and Kirchhoff rows minus the loss terms equal O's row by row (EXACT), the loss
    terms are -0.5 at bus0 and bus1 and -/+1 in the capacity rows; counts and coefficient ranges of the proxy rows.
  * AC_LOSS_PROXY_S4K1.json (summary), registry fragment s4k_1.

    python scripts_project/s4k_1_data.py --network <S4K-1 integrated build (ac_losses = linear_proxy)> --tangent <S4J-state build (pypsa_tangent)>
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4k_layers import LAMBDA_COL, PROXY_HOOK, PYPSA_TANGENTS, REFERENCE_TYPE, line_lambda, reference_check

SCRIPT = "scripts_project/s4k_1_data.py"
INSTRUCTION_SHA = "a803f1653736640f1358659b156e6d9dbf7c72be61b9455863f793dea75825d5"
LOC = "work/p1_step4k_20261018/S4K_CLAUDE_CODE_INSTRUCTION.md"
OUT = ROOT / "research_inputs/corridors"
FLOWS = [500, 1000, 2000, 3500, 5000, 7000, 10000, 14000]


def _line(path: Path, no: int, text: str) -> dict:
    got = path.read_text().splitlines()[no - 1]
    if text not in got:
        raise ValueError(f"STOP (S4K-1 point 1): {path.name} line {no} differs from the assumed loss structure: {got.strip()}")
    return dict(file=path.name, line=no, text=got.strip())


def source_checks() -> dict:
    import pypsa
    P = Path(pypsa.__file__).parent / "optimization"
    c, o, v = P / "constraints.py", P / "optimize.py", P / "variables.py"
    return dict(pypsa=pypsa.__version__, lines=[
        _line(v, 146, "def define_loss_variables(n: Network, sns: Sequence, c: str) -> None:"), _line(v, 155, 'n.model.add_variables(0, coords=coords, name=f"{c}-loss", mask=active)'),
        _line(c, 72, "if c in n.passive_branch_components and transmission_losses:"), _line(c, 74, "dispatch_lower = (1, dispatch_lower), (-1, loss)"),
        _line(c, 75, "dispatch_upper = (1, dispatch_upper), (1, loss)"), _line(c, 117, "if c in n.passive_branch_components and transmission_losses:"),
        _line(c, 119, "lhs_lower += ((-1, loss),)"), _line(c, 120, "lhs_upper += ((1, loss),)"),
        _line(c, 556, "if transmission_losses:"), _line(c, 559, '["Line", "loss", "bus0", -0.5],'), _line(c, 560, '["Line", "loss", "bus1", -0.5],'),
        _line(c, 619, "def define_kirchhoff_voltage_constraints(n: Network, sns: pd.Index) -> None:"), _line(c, 632, 's = pd.concat({c: m[f"{c}-s"].to_pandas() for c in comps}, axis=1, names=names)'),
        _line(c, 932, "def define_loss_constraints("), _line(c, 961, 'n.model.add_constraints(loss <= upper_limit, name=f"{c}-loss_upper", mask=active)'),
        _line(c, 964, "p_k = k / tangents * s_max_pu * s_nom_max"),
        _line(o, 258, "if transmission_losses:"), _line(o, 260, "define_loss_variables(n, sns, c)"), _line(o, 279, "meshed_buses = get_strongly_meshed_buses(n)"),
        _line(o, 303, "if transmission_losses:"), _line(o, 305, "define_loss_constraints(n, sns, c, transmission_losses)"),
        _line(o, 456, 'if "Line-loss" in n.model.variables:'), _line(o, 458, "n.lines_t.p0 += losses / 2"), _line(o, 459, "n.lines_t.p1 += losses / 2")])


def haversine_km(x0, y0, x1, y1) -> np.ndarray:
    p0, p1 = np.radians(y0), np.radians(y1); dphi, dl = p1 - p0, np.radians(x1 - x0)
    a = np.sin(dphi / 2) ** 2 + np.cos(p0) * np.cos(p1) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def lambda_table(n) -> pd.DataFrame:
    n.calculate_dependent_values()
    T05, T10 = line_lambda(n, 0.5), line_lambda(n, 1.0)
    if LAMBDA_COL in n.lines and not np.allclose(n.lines[LAMBDA_COL].to_numpy(), T05.ac_loss_lambda.to_numpy(), rtol=0, atol=1e-15):
        raise ValueError("network lambda column differs from the formula at alpha 0.5")
    L, B = n.lines, n.buses
    gc = haversine_km(L.bus0.map(B.x).to_numpy(), L.bus0.map(B.y).to_numpy(), L.bus1.map(B.x).to_numpy(), L.bus1.map(B.y).to_numpy())
    c0, c1 = L.bus0.map(B.country).astype(str), L.bus1.map(B.country).astype(str)
    smax = L.s_nom_max.where(L.s_nom_extendable, L.s_nom).astype(float)
    p1 = T05.s_max_pu * smax / PYPSA_TANGENTS
    return pd.DataFrame(dict(line=L.index, bus0=L.bus0, bus1=L.bus1, country0=c0, country1=c1, pair=["-".join(sorted((a, b))) for a, b in zip(c0, c1)],
                             border_class=T05.border_class, type=T05.type, v_nom_kv=T05.v_nom_kv, length_km=T05.length_km, great_circle_km=gc,
                             length_ratio=T05.length_km / gc, R_one_circuit_ohm=T05.R_one_circuit_ohm, i_nom_ka=T05.i_nom_ka, s_max_pu=T05.s_max_pu,
                             lambda_alpha_0_5=T05.ac_loss_lambda, lambda_alpha_1_0=T10.ac_loss_lambda, num_parallel=L.num_parallel.astype(float), s_nom=L.s_nom.astype(float),
                             s_nom_max=smax, candidate=(L.s_nom == 0) & L.s_nom_extendable, r_pu_eff=L.r_pu_eff.astype(float), tangent_point_1_mw=p1,
                             zero_loss_limit_mw=p1 / 2)).reset_index(drop=True)


def tangent_vs_proxy(T: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, z in T.iterrows():
        pts = [k / PYPSA_TANGENTS * z.s_max_pu * z.s_nom_max for k in range(1, PYPSA_TANGENTS + 1)]
        for f in FLOWS:
            if f > z.s_max_pu * z.s_nom_max:
                continue
            tang = max(0.0, max(2 * z.r_pu_eff * p * f - z.r_pu_eff * p * p for p in pts))
            rows.append(dict(line=z.line, pair=z.pair, border_class=z.border_class, candidate=bool(z.candidate), length_km=z.length_km, flow_mw=f,
                             s4j_tangent_share=tang / f, proxy_share_alpha_0_5=z.lambda_alpha_0_5, proxy_share_alpha_1_0=z.lambda_alpha_1_0,
                             fixed_circuit_quadratic_share=z.r_pu_eff * f))
    return pd.DataFrame(rows)


def _rows(con, drop_labels=None) -> pd.DataFrame:
    """Row-wise term table of a linopy constraint: (row coordinates..., var, coeff) for the valid terms, optionally without some variables."""
    d = con.data; dims = [x for x in d.vars.dims if x != "_term"]
    V = d.vars.transpose(*dims, "_term").values; C = d.coeffs.transpose(*dims, "_term").values
    idx = np.indices(V.shape[:-1]).reshape(len(dims), -1).T
    V = V.reshape(len(idx), -1); C = C.reshape(len(idx), -1)
    keep = V >= 0
    if drop_labels is not None:
        keep &= ~np.isin(V, drop_labels)
    r, t = np.nonzero(keep)
    out = pd.DataFrame({**{f"d{i}": idx[r, i] for i in range(len(dims))}, "var": V[r, t], "coeff": C[r, t]})
    return out.sort_values(list(out.columns)).reset_index(drop=True)


def model_check(network: Path) -> dict:
    import pypsa
    from assembly_components import install_research_constraint_hooks

    def build(proxy: bool):
        n = pypsa.Network(str(network)); n.set_snapshots(n.snapshots[:56])
        n.meta.update(solver_allowed=True, artifact_role="S4K1_MODEL_CHECK_UNSOLVED", s2_solve_label="S4K1_MODEL_CHECK")
        if not proxy:
            n.meta["required_constraint_hooks"] = [h for h in n.meta["required_constraint_hooks"] if h != PROXY_HOOK]
        tl = int(n.meta["research_transmission_losses"]["ac_transmission_losses"])
        m = n.optimize.create_model(transmission_losses=tl); base = list(m.variables); install_research_constraint_hooks(n)
        return n, m, tl, base
    t0 = time.time()
    nO, O, tlO, baseO = build(False); nP, P, tlP, baseP = build(True)
    if baseO != baseP:
        raise ValueError("create_model variables differ between O and P")
    if tlO or tlP:
        raise ValueError("the proxy build must give the solver transmission_losses = 0")
    loss = P["Line-loss"]; LL = np.asarray(loss.labels.values).ravel()
    out = dict(network=str(network), snapshots=56, solver_transmission_losses=tlP, loss_variables=int((LL >= 0).sum()), lines=int(len(nP.lines)),
               num_col=dict(O=int(O.nvars), P=int(P.nvars)), num_row=dict(O=int(O.ncons), P=int(P.ncons)), compare={})
    # the create_model variables keep their labels (the proxy variable is created after create_model; hook variables come later and may shift,
    # but the nodal balance, line and Kirchhoff rows reference create_model variables only)
    for name in baseO:
        if not np.array_equal(np.asarray(O[name].labels.values), np.asarray(P[name].labels.values)):
            raise ValueError(f"variable labels differ between O and P: {name}")
    for name in [k for k in O.constraints if k.endswith("nodal_balance") or k.startswith("Line-") or k == "Kirchhoff-Voltage-Law"]:
        co, cp = O.constraints[name].data.coords, P.constraints[name].data.coords
        if set(co.dims) != set(cp.dims) or any(not np.array_equal(co[d].values, cp[d].values) for d in co.dims if d != "_term"):
            raise ValueError(f"{name}: row coordinates differ between O and P")
        a = _rows(O.constraints[name]); b = _rows(P.constraints[name], drop_labels=LL)
        same = a.equals(b) and np.array_equal(np.asarray(O.constraints[name].rhs.values), np.asarray(P.constraints[name].rhs.values), equal_nan=True)
        lt = _rows(P.constraints[name]); lt = lt[np.isin(lt["var"].to_numpy(), LL)]
        out["compare"][name] = dict(rows=int(np.asarray(O.constraints[name].labels.values).ravel().__ge__(0).sum()), minus_loss_terms_equal=bool(same),
                                    loss_terms=int(len(lt)), loss_coefficients=sorted({float(x) for x in lt.coeff.unique()}))
        if not same:
            raise ValueError(f"{name}: P minus the loss terms differs from O")
    nb = sum(v["loss_terms"] for k, v in out["compare"].items() if k.endswith("nodal_balance"))
    if nb != 2 * out["loss_variables"]:
        raise ValueError(f"nodal balance carries {nb} loss terms, expected 2 x {out['loss_variables']}")
    prox = {}
    for k in [x for x in P.constraints if x.startswith("Line-loss") or x.endswith("loss_upper")]:
        c = P.constraints[k]; v = np.asarray(c.coeffs.values).ravel(); v = v[np.isfinite(v) & (v != 0)]
        prox[k] = dict(rows=int(np.asarray(c.labels.values).ravel().__ge__(0).sum()), coeff_abs_min=float(np.abs(v).min()), coeff_abs_max=float(np.abs(v).max()))
    out.update(proxy_rows=prox, seconds=time.time() - t0, hook=nP.meta.get("research_ac_loss_proxy_model"))
    return out


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); ap.add_argument("--tangent", type=Path, required=True); a = ap.parse_args()
    src = source_checks()
    n = pypsa.Network(str(a.network))
    if n.meta["research_ac_losses"]["mode"] != "linear_proxy" or PROXY_HOOK not in n.meta["required_constraint_hooks"]:
        raise ValueError("--network is not an ac_losses = linear_proxy build")
    nt = pypsa.Network(str(a.tangent))
    if int(nt.meta["research_transmission_losses"]["ac_transmission_losses"]) != PYPSA_TANGENTS:
        raise ValueError("--tangent is not a pypsa_tangent build")
    ref = reference_check(n)
    T = lambda_table(n); write_csv(T.to_dict("records"), OUT / "LAMBDA_S4K1.csv", list(T.columns))
    C = tangent_vs_proxy(T); write_csv(C.to_dict("records"), OUT / "TANGENT_VS_PROXY_S4K1.csv", list(C.columns))
    mc = model_check(a.network)
    q = lambda s: dict(lines=int(len(s)), min=float(s.min()), median=float(s.median()), max=float(s.max()))
    cmp = {}
    for (cand, f), g in C.groupby(["candidate", "flow_mw"]):
        cmp.setdefault("candidates" if cand else "stock", {})[int(f)] = dict(lines=int(len(g)), s4j_tangent_median=float(g.s4j_tangent_share.median()),
                                                                              s4j_tangent_zero_lines=int((g.s4j_tangent_share == 0).sum()), proxy_alpha_0_5_median=float(g.proxy_share_alpha_0_5.median()),
                                                                              proxy_alpha_1_0_median=float(g.proxy_share_alpha_1_0.median()),
                                                                              fixed_circuit_quadratic_median=float(g.fixed_circuit_quadratic_share.median()))
    summ = dict(network=str(a.network), tangent_network=str(a.tangent), sources=src, meta=n.meta["research_ac_losses"], reference_check=ref,
                lambda_alpha_0_5=dict(all=q(T.lambda_alpha_0_5), by_border={k: q(g.lambda_alpha_0_5) for k, g in T.groupby("border_class")},
                                      by_pair={k: q(g.lambda_alpha_0_5) for k, g in T[T.border_class == "cross_border"].groupby("pair")},
                                      by_country_domestic={k: q(g.lambda_alpha_0_5) for k, g in T[T.border_class == "domestic"].groupby("country0")}),
                lambda_alpha_1_0=q(T.lambda_alpha_1_0), length_ratio=dict(all=q(T.length_ratio), stock=q(T[~T.candidate].length_ratio), candidates=q(T[T.candidate].length_ratio)),
                tangent_vs_proxy=cmp, model_check=mc)
    (OUT / "AC_LOSS_PROXY_S4K1.json").write_text(json.dumps(summ, indent=1, default=str))
    reg = Registry(SCRIPT)
    D = "Decision 108 (S4K-1)"
    reg.add("s4k1_ac_losses_switch", f"{D}: research.network.ac_losses = linear_proxy (main) | pypsa_tangent (S4J state: PyPSA transmission_losses = 2; default when absent) | none "
            "(AC lossless, DC / pipeline losses kept); with research.network.transmission_losses = none the AC lines are lossless as well",
            "linear_proxy|pypsa_tangent|none", "flag", "B", "S4K instruction S4K-1 point 4", LOC, INSTRUCTION_SHA, decision_ref="108", status="REFERENCE_ONLY")
    reg.add("s4k1_reference_loading", f"{D}: alpha = reference current as a share of the allowed loading of one circuit (I_ref = alpha x s_max_pu x i_nom); main 0.5, "
            "sensitivity 1.0 (upper bound of the proxy)", 0.5, "share", "B", "S4K instruction S4K-1 points 3-4", LOC, INSTRUCTION_SHA, decision_ref="108", status="REFERENCE_ONLY")
    reg.add("s4k1_lambda", f"{D}: lambda per AC line by line type, one circuit: R = r_per_length x length (model length incl. the 1.25 length factor), lambda = sqrt(3) x I_ref x R / v_nom "
            f"(kA, Ohm, kV); all 148 lines are '{REFERENCE_TYPE}' (r 0.03 Ohm/km, i_nom 2.58 kA, 380 kV, s_max_pu 0.7): lambda = "
            f"{100 * T.lambda_alpha_0_5.min():.2f}-{100 * T.lambda_alpha_0_5.max():.2f} % (median {100 * T.lambda_alpha_0_5.median():.2f} %); check at 100 km "
            f"{100 * ref['0.5']['lambda_100km']:.3f} % (expected about 1.2 %) and {100 * ref['1.0']['lambda_100km']:.3f} % (about 2.5 %), within 20 %",
            "table", "flag", "B", "derived (scripts_project/s4k_1_data.py, PyPSA line_types)", "research_inputs/corridors/LAMBDA_S4K1.csv", sha256(OUT / "LAMBDA_S4K1.csv"),
            decision_ref="108", status="REFERENCE_ONLY")
    reg.add("s4k1_deviation_from_pypsa_eur", f"{D}, registered deviation from PyPSA-Eur (solving.options.transmission_losses = 2): the candidate lines are extended from one "
            "circuit by up to +20 GW, far beyond the usual PyPSA-Eur case, and with the resistance fixed the tangent approximation (tangent points on s_nom_max) is distorted "
            "(zero loss below 3.5-13 GW, 16 lines built exactly to the zero-loss limit in the S4J smoke); when the circuits grow with the flow the loading per circuit stays "
            "about constant and the loss is about proportional to the flow, as the DC efficiency per length; the iterative impedance update (skip_iterations: false) is not "
            "used because it needs several solves per run, not feasible for the coalition study", "linear_proxy", "flag", "B", "S4K instruction S4K-1 point 6; S4J report 8.6",
            LOC, INSTRUCTION_SHA, decision_ref="108", status="REFERENCE_ONLY")
    reg.add("s4k1_loss_structure", f"{D}: the PyPSA {src['pypsa']} loss structure is kept - 'Line-loss' >= 0 per line and snapshot (variables.py 146-155), -0.5 x loss in "
            "the nodal balance at bus0 and bus1 (constraints.py 556-560), the loss in the line capacity rows (72-75, 117-120), Kirchhoff rows with the flow only (619 ff.), "
            "p0 / p1 += loss / 2 after the solve (optimize.py 456-459); the tangents and the r (s_max_pu s_nom_max)^2 upper bound (932-975) are replaced by loss >= lambda s, "
            "loss >= -lambda s, loss <= lambda s_max_pu s_nom (variable s_nom for extendable lines); solver transmission_losses = 0; hook research_ac_loss_proxy rebuilds the "
            "nodal balance and capacity rows with PyPSA's own functions; model check: rows minus the loss terms equal the lossless model row by row",
            "pypsa_structure_tangents_replaced", "flag", "B", "PyPSA 0.30.3 optimization/{variables,constraints,optimize}.py", "research_inputs/corridors/AC_LOSS_PROXY_S4K1.json",
            sha256(OUT / "AC_LOSS_PROXY_S4K1.json"), decision_ref="108", status="REFERENCE_ONLY")
    reg.add("s4k1_ledger", f"{D}: the line loss is withdrawn half at each end and settled at the nodal price of that end (p0 = s + loss/2, p1 = -s + loss/2); the corridor of a "
            "cross-border line pays p0 x price0 + p1 x price1, its rent R = (-p1) price1 - p0 price0 (loss included) is split 50/50 with the infrastructure cost; settlements "
            "cancel between entities, so sum(countries) + bunker = objective - pool surplus (gate B16)", "formula", "flag", "B", "S4K instruction S4K-1 point 5", LOC,
            INSTRUCTION_SHA, decision_ref="108", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4k_1.csv")
    print(json.dumps(dict(reference_check=ref, lambda_alpha_0_5=summ["lambda_alpha_0_5"]["all"], by_border=summ["lambda_alpha_0_5"]["by_border"], length_ratio=summ["length_ratio"]), indent=1))
    print(json.dumps({k: v for k, v in mc.items() if k not in ("compare", "proxy_rows")}, indent=1, default=str))
    print(json.dumps(mc["compare"], indent=1)); print(json.dumps(mc["proxy_rows"], indent=1))
    print(json.dumps(cmp, indent=1))


if __name__ == "__main__":
    main()
