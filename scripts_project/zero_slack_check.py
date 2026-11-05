"""V3.1 (decision 195, V3_FIX_INSTRUCTION.md section 4): static zero-slack check of the constraint hooks - a build-package gate. No solver is called.

Why: the 2920x3h presolve failure (work/p1_v3_diag_20261105/V3_DIAG_REPORT.md) came from a single row 'final-snapshot level of the bunker account <= 0'
on an account with emission ports only: that row forces every port flow to 0 in every snapshot through the whole Store chain with zero slack, and
Gurobi's default presolve declared such windows INF_OR_UNBD. The same structure can hide in any hook of the two forms

    (F) final-snapshot Store level <= cap        e.g. research_country_co2_limit-<c>, research_co2_storage_cap-<c>, research_asean_co2_limit,
                                                 research_bunker_co2_limit before V3.1
    (A) annual weighted sum <= cap               e.g. ResearchImportAnnual-<generator> (sum_t w_t p_t <= cap)

Rule: a row of form (F) or (A) whose cap is <= 1e-9 (for (F): cap minus the coefficient-weighted e_initial of the stores) and whose ports are all
one-way inflows (no removal port, no two-way port) is a ZERO-SLACK FORCING ROW. It is refused unless the hook writes the forcing explicitly per
variable (every forced variable == 0 in its own row; V3.1 bunker: research_bunker_co2_limit = metering Link-p == 0 per snapshot and link).

How (two parts, both without a solver):
  * the hook rows: the network is built exactly as the solve builds it (l23_violation_analysis.build_model = create_model + every required hook +
    objective constants out; the s2_solve.py path up to the LP export) on its first --truncate snapshots (default 3; the form of a hook does not
    depend on the number of snapshots, its caps are not scaled by truncation); every row of every research hook ('research_*' / 'Research*') is
    classified by its terms: (F), (A), per-variable zero, per-variable bound, other.
  * the ports: from the FULL network (static and time-varying p_min_pu / efficiency over all snapshots): every component port on the bus of a
    constrained Store, or the constrained generator's own output, as inflow / removal / two-way / zero. The bunker account premises of
    s4c_layers.bunker_account_premises are measured on the full network as well.

    python scripts_project/zero_slack_check.py --repo . --out ZERO_SLACK_CHECK.json \
        --network F1=integrated:<nc> --network F2=no_new_xb:<nc> [...] [--truncate 3]
Exit code 0 = every network passed, 3 = a zero-slack forcing row (or a bunker hook not covering every metering flow), 2 = usage / input error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

SCRIPT = "scripts_project/zero_slack_check.py"
TOL = 1e-9
FORMS = ("final_store_level", "annual_weighted_sum", "per_variable_zero", "per_variable_bound", "other")
OPERATIONAL = {"Generator-p": "Generator", "Link-p": "Link", "Store-p": "Store", "StorageUnit-p_dispatch": "StorageUnit", "StorageUnit-p_store": "StorageUnit",
               "Line-s": "Line"}
RULE = ("zero-slack forcing row = a row 'final-snapshot Store level <= cap' or 'annual weighted sum <= cap' with cap <= 1e-9 (final level: cap minus the "
        "weighted e_initial) whose ports are all one-way inflows (no removal port, no two-way port); refused unless written explicitly per variable")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ----------------------------------------------------------------------------------------------------------------------------- ports
def _tv(n, comp: str, attr: str, name: str):
    """time-varying values of one component attribute over the network's snapshots (None when static only)."""
    df = n.pnl(comp).get(attr)
    if df is None or name not in getattr(df, "columns", []):
        return None
    return df[name].to_numpy(dtype=float)


def _range(n, comp: str, attr: str, name: str):
    v = float(n.df(comp).at[name, attr]); s = _tv(n, comp, attr, name)
    return (min(v, float(s.min())), max(v, float(s.max()))) if s is not None and len(s) else (v, v)


def _fixed_zero(n, comp: str, name: str, nom: str) -> bool:
    d = n.df(comp)
    return (not bool(d.at[name, nom + "_extendable"])) and float(d.at[name, nom]) == 0.0


def classify_port(n, comp: str, name: str, port: str) -> dict:
    """direction of the injection of one component port into its bus: inflow (>= 0 always), removal (<= 0 always), two_way, zero."""
    if comp == "Link":
        if _fixed_zero(n, "Link", name, "p_nom"):
            return dict(direction="zero", reason="fixed p_nom = 0")
        pmin, _ = _range(n, "Link", "p_min_pu", name)
        two_way = pmin < 0
        if port == "bus0":   # injection = -p
            return dict(direction="two_way" if two_way else "removal", p_min_pu_min=pmin)
        col = "efficiency" if port == "bus1" else "efficiency" + port[3:]
        lo, hi = _range(n, "Link", col, name)
        if two_way and (lo != 0 or hi != 0):
            return dict(direction="two_way", p_min_pu_min=pmin, coefficient_min=lo, coefficient_max=hi)
        if lo > 0:
            return dict(direction="inflow", p_min_pu_min=pmin, coefficient_min=lo, coefficient_max=hi)
        if hi < 0:
            return dict(direction="removal", p_min_pu_min=pmin, coefficient_min=lo, coefficient_max=hi)
        if lo == 0 and hi == 0:
            return dict(direction="zero", reason="coefficient 0")
        return dict(direction="two_way", reason="coefficient changes sign", coefficient_min=lo, coefficient_max=hi)
    if comp == "Generator":
        if _fixed_zero(n, "Generator", name, "p_nom"):
            return dict(direction="zero", reason="fixed p_nom = 0")
        pmin, _ = _range(n, "Generator", "p_min_pu", name); sign = float(n.generators.at[name, "sign"])
        if pmin < 0:
            return dict(direction="two_way", p_min_pu_min=pmin, sign=sign)
        return dict(direction="inflow" if sign > 0 else "removal", p_min_pu_min=pmin, sign=sign)
    if comp == "Load":
        ps = _tv(n, "Load", "p_set", name)
        ps = ps if ps is not None else np.array([float(n.loads.at[name, "p_set"])])
        inj = float(n.loads.at[name, "sign"]) * ps
        if np.all(inj == 0):
            return dict(direction="zero", reason="p_set 0")
        if np.all(inj >= 0):
            return dict(direction="inflow", fixed=True)
        if np.all(inj <= 0):
            return dict(direction="removal", fixed=True)
        return dict(direction="two_way", fixed=True)
    if comp == "Store":
        return dict(direction="zero", reason="fixed e_nom = 0") if _fixed_zero(n, "Store", name, "e_nom") else dict(direction="two_way")
    if comp == "StorageUnit":
        return dict(direction="zero", reason="fixed p_nom = 0") if _fixed_zero(n, "StorageUnit", name, "p_nom") else dict(direction="two_way")
    return dict(direction="two_way", reason=f"{comp} (branch)")


def bus_ports(n, bus: str, exclude_store: set) -> list:
    out = []
    for comp in ("Generator", "Load", "Store", "StorageUnit"):
        d = n.df(comp)
        for x in d.index[d.bus == bus]:
            if comp == "Store" and x in exclude_store:
                continue
            out.append(dict(component=comp, name=str(x), port="bus", **classify_port(n, comp, x, "bus")))
    for col in [c for c in n.links.columns if c.startswith("bus") and c[3:].isdigit()]:
        for x in n.links.index[n.links[col] == bus]:
            out.append(dict(component="Link", name=str(x), port=col, **classify_port(n, "Link", x, col)))
    for comp in ("Line", "Transformer"):
        d = n.df(comp)
        if len(d):
            for x in d.index[(d.bus0 == bus) | (d.bus1 == bus)]:
                out.append(dict(component=comp, name=str(x), port="bus0/bus1", direction="two_way", reason="branch"))
    return out


def port_summary(ports: list) -> dict:
    k = pd.Series([p["direction"] for p in ports], dtype=object).value_counts().to_dict() if ports else {}
    removal_like = [p for p in ports if p["direction"] in ("removal", "two_way")]
    return dict(ports=int(sum(v for d, v in k.items() if d != "zero")), inflow_ports=int(k.get("inflow", 0)), removal_ports=int(k.get("removal", 0)),
                two_way_ports=int(k.get("two_way", 0)), zero_ports=int(k.get("zero", 0)), removal_or_two_way_ports=len(removal_like),
                removal_examples=[f"{p['component']} {p['name']} {p['port']} ({p['direction']})" for p in removal_like[:5]])


# ----------------------------------------------------------------------------------------------------------------------------- hook rows
class Decoder:
    """linopy variable label -> (variable name, coordinates)."""

    def __init__(self, m):
        self.m = m; names = list(m.variables)
        top = max(int(np.asarray(m.variables[v].labels).max()) for v in names) + 1
        self.vid = np.full(top, -1, dtype=np.int32); self.names = names; self._pos = {}
        for i, v in enumerate(names):
            lab = np.asarray(m.variables[v].labels).ravel(); lab = lab[lab >= 0]; self.vid[lab] = i

    def name(self, label: int) -> str:
        return self.names[int(self.vid[int(label)])]

    def coords(self, vname: str, labels) -> list:
        lab = self.m.variables[vname].labels
        if vname not in self._pos:
            flat = np.asarray(lab.values).ravel(); ok = np.flatnonzero(flat >= 0)
            self._pos[vname] = pd.Series(ok, index=flat[ok])
        idx = np.unravel_index(self._pos[vname].reindex(np.asarray(labels, dtype=np.int64)).to_numpy(dtype=np.int64), lab.shape)
        return [{d: lab.coords[d].values[idx[k][j]] for k, d in enumerate(lab.dims)} for j in range(len(labels))]


def _snap(v) -> str:
    """one key for a snapshot coordinate whatever its type (numpy datetime64 from linopy, pandas Timestamp from the network, int in toy networks)."""
    if isinstance(v, (int, np.integer)):
        return f"int:{int(v)}"
    try:
        return pd.Timestamp(v).isoformat()
    except (TypeError, ValueError):
        return str(v)


def _rows(con):
    lab = con.labels; dims = list(lab.dims); L = np.asarray(lab.values).ravel()
    tdim = "_term"
    V = np.asarray(con.vars.transpose(*dims, tdim).values).reshape(len(L), -1)
    C = np.asarray(con.coeffs.transpose(*dims, tdim).values, dtype=float).reshape(len(L), -1)
    S = np.broadcast_to(np.asarray(con.sign.values), lab.shape).ravel()
    R = np.broadcast_to(np.asarray(con.rhs.values, dtype=float), lab.shape).ravel()
    keep = L >= 0
    return V[keep], C[keep], S[keep], R[keep]


def classify_row(D: Decoder, v, c, sign, rhs, last, nsnap) -> dict:
    ok = (v >= 0) & (c != 0); v, c = v[ok], c[ok]
    if sign == ">=":
        c, rhs, sign = -c, -rhs, "<="
    if len(v) == 0:
        return dict(form="other", reason="no term")
    names = {D.name(x) for x in v}
    if len(v) == 1 and sign == "=" and rhs == 0:
        return dict(form="per_variable_zero", variable=next(iter(names)), labels=[int(v[0])])
    if sign == "<=" and names == {"Store-e"} and np.all(c > 0):   # one or several stores (single-term rows included: the former bunker row)
        co = D.coords("Store-e", v)
        if all(_snap(x["snapshot"]) == _snap(last) for x in co):
            return dict(form="final_store_level", stores=[str(x["Store"]) for x in co], coefficients=[float(x) for x in c], cap=float(rhs))
    if len(v) == 1:
        return dict(form="per_variable_bound", variable=next(iter(names)))
    if sign == "<=" and len(names) == 1 and next(iter(names)) in OPERATIONAL and np.all(c > 0) and len(v) == nsnap:
        vn = next(iter(names)); co = D.coords(vn, v); dim = [d for d in co[0] if d != "snapshot"][0]
        comps = {str(x[dim]) for x in co}
        if len(comps) == 1 and len({_snap(x["snapshot"]) for x in co}) == nsnap:
            return dict(form="annual_weighted_sum", variable=vn, component_type=OPERATIONAL[vn], component=comps.pop(), cap=float(rhs))
    return dict(form="other", variables=sorted(names)[:6], terms=int(len(v)), sign=str(sign))


def scan_hooks(n_model, m, n_full) -> list:
    """every research hook row of the model classified; (F) / (A) rows judged with the ports of the FULL network."""
    D = Decoder(m); last = n_model.snapshots[-1]; nsnap = len(n_model.snapshots)
    out = []
    for name in m.constraints:
        if not (name.startswith("research_") or name.startswith("Research")):
            continue
        V, C, S, R = _rows(m.constraints[name])
        rows = [classify_row(D, V[i], C[i], S[i], R[i], last, nsnap) for i in range(len(V))]
        forms = sorted({r["form"] for r in rows})
        rec = dict(name=name, rows=len(rows), form=forms[0] if len(forms) == 1 else "mixed:" + "+".join(forms))
        if rec["form"] == "final_store_level":
            caps, ports, stores, verdicts = [], [], set(), []
            for r in rows:
                st = r["stores"]; stores |= set(st)
                e0 = float(sum(k * float(n_full.stores.at[s, "e_initial"]) for s, k in zip(st, r["coefficients"])))
                p = []
                for s in st:
                    p += bus_ports(n_full, str(n_full.stores.at[s, "bus"]), set(st))
                ps = port_summary(p); eff = r["cap"] - e0
                caps.append(r["cap"]); ports.append(ps)
                if ps["ports"] == 0:
                    verdicts.append("no_ports")
                elif ps["removal_or_two_way_ports"] > 0:
                    verdicts.append("removal_ports_present")
                elif eff > TOL:
                    verdicts.append("positive_cap")
                else:
                    verdicts.append("zero_slack_forcing_row")
            rec.update(stores=sorted(stores), cap_min=min(caps), cap_max=max(caps), e_initial=[float(n_full.stores.at[s, "e_initial"]) for s in sorted(stores)],
                       e_cyclic=[bool(n_full.stores.at[s, "e_cyclic"]) for s in sorted(stores)])
            rec.update(ports[0] if len(ports) == 1 else dict(port_summaries=ports))
            rec["verdict"] = "zero_slack_forcing_row" if "zero_slack_forcing_row" in verdicts else sorted(set(verdicts))[0]
        elif rec["form"] == "annual_weighted_sum":
            r = rows[0]
            if len(rows) != 1:
                rec.update(verdict="other_form", note="several annual rows under one name")
            else:
                p = [dict(component=r["component_type"], name=r["component"], port="own output", **classify_port(n_full, r["component_type"], r["component"], "bus" if r["component_type"] != "Link" else "bus1"))]
                ps = port_summary(p)
                one_way = ps["removal_or_two_way_ports"] == 0
                rec.update(component=f'{r["component_type"]} {r["component"]}', cap_min=r["cap"], cap_max=r["cap"], **ps,
                           verdict=("zero_slack_forcing_row" if (one_way and r["cap"] <= TOL) else ("positive_cap" if r["cap"] > TOL else "removal_ports_present")))
        elif rec["form"] == "per_variable_zero":
            rec.update(variables=sorted({r["variable"] for r in rows}), verdict="explicit_per_variable_zero")
        elif rec["form"] == "per_variable_bound":
            rec.update(variables=sorted({r["variable"] for r in rows}), verdict="other_form", note="explicit per-variable bound rows (not forms F / A)")
        else:
            ex = next((r for r in rows if r["form"] == "other"), rows[0] if rows else {})
            rec.update(verdict="other_form", example={k: v for k, v in ex.items() if k != "labels"})
        out.append(rec)
    return out


def bunker_check(n_model, m, n_full) -> dict:
    """V3.1: the bunker hook must be the explicit per-variable form covering every metering link x every snapshot of the model."""
    from s4c_layers import BUNKER_CO2_BUS, BUNKER_HOOK, BUNKER_ROW, bunker_account_premises, bunker_metering_links, validate_bunker_account
    hooks = set(n_full.meta.get("required_constraint_hooks", []))
    if BUNKER_HOOK not in hooks:
        return dict(present=False, passed=True)
    res = dict(present=True, hook=BUNKER_HOOK, row=BUNKER_ROW)
    try:
        acc = validate_bunker_account(n_full)
        res["premises_full_network"] = bunker_account_premises(n_full, acc["store"], acc["ports"])
    except ValueError as e:
        res.update(passed=False, error="validate_bunker_account (full network): " + str(e)[:400]); return res
    meters = bunker_metering_links(acc)
    want = {(str(x), _snap(t)) for x in meters for t in n_model.snapshots}
    if BUNKER_ROW not in m.constraints:
        res.update(passed=False, error=f"hook {BUNKER_HOOK} required but row {BUNKER_ROW} not in the model"); return res
    D = Decoder(m); V, C, S, R = _rows(m.constraints[BUNKER_ROW])
    single = bool(np.all(((V >= 0) & (C != 0)).sum(axis=1) == 1)); eq = bool(np.all(S == "=")); zero = bool(np.all(R == 0))
    lab = V[(V >= 0) & (C != 0)]
    names = {D.name(x) for x in lab}
    got = {(str(c["Link"]), _snap(c["snapshot"])) for c in D.coords("Link-p", lab)} if names == {"Link-p"} else set()
    res.update(account=BUNKER_CO2_BUS, metering_links=len(meters), snapshots_in_model=int(len(n_model.snapshots)), rows=int(len(V)), expected_rows=len(want),
               single_term_rows=single, equality_rows=eq, zero_rhs=zero, variables=sorted(names), covers_every_metering_flow=(got == want),
               missing=len(want - got), extra=len(got - want))
    res["passed"] = bool(single and eq and zero and names == {"Link-p"} and got == want and res["premises_full_network"]["passed"])
    return res


def configured_caps_without_row(n_full, m) -> dict:
    """caps configured in the network metadata whose constraint is not in the model (e.g. CO2 storage caps of countries without a storage account)."""
    out = {}
    cs = n_full.meta.get("research_co2_storage") or {}
    for c, cap in (cs.get("caps_t_per_year") or {}).items():
        sb = f"co2 sequestered {c}"
        if f"research_co2_storage_cap-{c}" not in m.constraints:
            out[f"research_co2_storage_cap-{c}"] = dict(cap_t_per_year=float(cap), store=sb, store_present=bool(sb in n_full.stores.index),
                                                        reason="no row: the country has no co2 sequestered store (s2_layers.install_co2_storage_cap skips it)")
    return out


def check_network(repo: Path, label: str, scenario: str, network: Path, truncate: int) -> dict:
    import pypsa
    from l23_violation_analysis import build_model
    t0 = time.time()
    n_full = pypsa.Network(str(network))
    n, m, _ = build_model(repo, network, scenario, truncate, "ZERO_SLACK_CHECK")
    rows = scan_hooks(n, m, n_full)
    bunker = bunker_check(n, m, n_full)
    forcing = [r["name"] for r in rows if r.get("verdict") == "zero_slack_forcing_row"]
    res = dict(label=label, scenario=scenario, network=str(network), network_sha256=sha(network), network_bytes=network.stat().st_size,
               snapshots_full=int(len(n_full.snapshots)), truncate_for_hook_rows=int(truncate), required_constraint_hooks=sorted(n_full.meta.get("required_constraint_hooks", [])),
               constraints=rows, forms=pd.Series([r["form"] for r in rows], dtype=object).value_counts().to_dict(),
               verdicts=pd.Series([r.get("verdict") for r in rows], dtype=object).value_counts().to_dict(),
               configured_caps_without_row=configured_caps_without_row(n_full, m), bunker=bunker,
               zero_slack_forcing_rows=forcing, passed=bool(not forcing and bunker.get("passed", True)), seconds=round(time.time() - t0, 1))
    del n, m, n_full
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--network", action="append", required=True, help="LABEL=SCENARIO:PATH (e.g. F1=integrated:networks/integrated_2920_3h_unsolved.nc)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--truncate", type=int, default=3)
    a = ap.parse_args(argv)
    logging.disable(logging.WARNING)
    if a.truncate < 2:
        print("--truncate must be >= 2 (an annual sum needs two snapshots to be told from a per-variable bound)"); return 2
    specs = []
    for s in a.network:
        try:
            lab, rest = s.split("=", 1); sc, p = rest.split(":", 1)
        except ValueError:
            print("bad --network " + s); return 2
        if not Path(p).is_file():
            print("network not found: " + p); return 2
        specs.append((lab, sc, Path(p)))
    nets = [check_network(a.repo, lab, sc, p, a.truncate) for lab, sc, p in specs]
    res = dict(script=SCRIPT, decision="195 (V3.1)", instruction="V3_FIX_INSTRUCTION.md section 4", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               rule=RULE, tolerance=TOL, solver_called=False, networks=nets, passed=bool(all(x["passed"] for x in nets)))
    a.out.write_text(json.dumps(res, indent=1, default=str) + "\n")
    for x in nets:
        print(f"ZERO_SLACK_CHECK {x['label']} {x['scenario']}: passed={x['passed']} forcing={x['zero_slack_forcing_rows']} bunker={x['bunker'].get('passed')} "
              f"constraints={len(x['constraints'])} verdicts={x['verdicts']} ({x['seconds']} s)")
    print("ZERO_SLACK_CHECK_RESULT:" + ("PASS" if res["passed"] else "REFUSED"))
    return 0 if res["passed"] else 3


if __name__ == "__main__":
    sys.exit(main())
