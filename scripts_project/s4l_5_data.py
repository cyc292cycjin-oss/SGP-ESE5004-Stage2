"""S4L-5 (user-authorised additional diagnostic, 2026-10-19, after the S4L report; diagnostic only, not the main run):
  table   per country solid biomass: national potential (finite pools), fixed final demand in the network, ratio, the decision-36 / R1.6
          overflow already moved to methane (registry industry_biomass_overflow_to_gas_<c>), the demand before the rule; countries with
          ratio >= 0.999 flagged (the rule binds: demand capped at the potential);
  compare the 98 % diagnostic network (research.s2.industry.biomass_overflow_cap_share = 0.98) against the S4K-3 network: loads that changed,
          per-country biomass / gas totals, pool balance; registry fragment s4l_5.

    python scripts_project/s4l_5_data.py table   --s4k results_project/s4k/s4k3/builds --out research_inputs/numerics
    python scripts_project/s4l_5_data.py compare --s4k results_project/s4k/s4k3/builds --diag results_project/s4l/s4l5/builds --out research_inputs/numerics
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, ROOT, Registry, sha256  # noqa: E402
from s4l_layers import pool_balance  # noqa: E402

SCRIPT = "scripts_project/s4l_5_data.py"
INSTRUCTION_SHA = "03508400f675304cd0bdfd40ccbd0c61005644e7b2a122dffbe2048e6a5d529b"
SRC = "User authorisation 2026-10-19 after the S4L report (additional diagnostic within S4L: biomass zero-slack countries, 98 % cap, 2 runs)"
LOC = "work/p1_step4l_20261019/S4L_REPORT.md"
BINDING_RATIO = 0.999
CAP_SHARE = 0.98
SCEN = ("integrated", "disconnected")


def net(p):
    import pypsa
    logging.getLogger("pypsa").setLevel(logging.ERROR)
    return pypsa.Network(str(p))


def biomass_table(n, reg: pd.DataFrame) -> pd.DataFrame:
    """Per country: pools (potential), fixed demand on the biomass final-energy buses, ratio, overflow (registry), demand before the rule."""
    bal = {b["country"]: b for b in pool_balance(n) if b["bus"].startswith("solid biomass ")}
    rows = []
    for c, b in sorted(bal.items()):
        ov = float(reg.at[f"industry_biomass_overflow_to_gas_{c}", "value"]) if f"industry_biomass_overflow_to_gas_{c}" in reg.index else np.nan
        pot, dem = b["pool_total_mwh"], b["fixed_demand_mwh"]
        rows.append(dict(country=c, pools=b["pools"], potential_mwh=pot, fixed_demand_mwh=dem, ratio=(dem / pot if pot else np.nan), binding=bool(pot and dem / pot >= BINDING_RATIO),
                         overflow_to_methane_mwh=ov, demand_before_rule_mwh=(dem + ov if np.isfinite(ov) else np.nan), ratio_before_rule=((dem + ov) / pot if (pot and np.isfinite(ov)) else np.nan),
                         slack_mwh=b["slack_mwh"], cap_98pct_mwh=(CAP_SHARE * pot if (pot and dem / pot >= BINDING_RATIO) else np.nan),
                         moved_to_methane_at_98pct_mwh=((1 - CAP_SHARE) * pot if (pot and dem / pot >= BINDING_RATIO) else 0.0)))
    return pd.DataFrame(rows)


def loads_by_account(n) -> pd.DataFrame:
    w = n.snapshot_weightings.generators
    ann = n.get_switchable_as_dense("Load", "p_set").mul(w, axis=0).sum()
    L = n.loads.copy(); L["annual_mwh"] = ann.reindex(L.index).to_numpy()
    cols = [c for c in ("country", "carrier", "sector", "account") if c in L]
    return L.groupby(cols).annual_mwh.sum().reset_index()


def table(a):
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    reg = pd.read_csv(ROOT / "research_inputs/registry_v5/DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    res = {}
    for sc in SCEN:
        n = net(Path(a.s4k) / sc / f"{sc}_2920_3h_unsolved.nc"); T = biomass_table(n, reg)
        T.to_csv(out / f"BIOMASS_BALANCE_S4L5_{sc}.csv", index=False)
        ov = (n.meta.get("s2_demand_ledger") or {}).get("parameters", {})
        res[sc] = dict(table=T.to_dict("records"), binding=sorted(T.country[T.binding]), rule=dict(config_key="research.s2.industry.biomass_overflow_to_methane", value=True, decision="36 (R1.6 inside the decision-55 R1 carrier structure)",
                       code="scripts_project/s2_layers.py add_demand_layer: overflow = max(0, industry biomass + agriculture biomass - national solid-biomass potential) moved to methane at equal heat, industry first then agriculture"))
        print(sc, T[["country", "potential_mwh", "fixed_demand_mwh", "ratio", "binding", "overflow_to_methane_mwh", "ratio_before_rule"]].round(4).to_string())
    (out / "BIOMASS_BALANCE_S4L5.json").write_text(json.dumps(res, indent=1, default=str))
    reg5 = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"
    reg5.add("s4l5_biomass_zero_slack_origin", "S4L-5 point 1: in BN, SG and VN the fixed solid-biomass final demand equals the national solid-biomass potential (ratio 1.000; "
             "slack 0) because the decision-36 / R1.6 rule (research.s2.industry.biomass_overflow_to_methane = true, inside the decision-55 R1 industrial carrier structure) "
             "caps the fixed biomass demand at the potential and moves the excess to methane at equal heat (BN 470,100 MWh, SG 18,857,051 MWh, VN 233,232,628 MWh moved; demand "
             "before the rule = 5.1 x, 599 x and 2.9 x the potential); every other country has a positive slack (demand / potential 0.89 TH, 0.59 ID, 0.53 PH, 0.52 MY, 0.27 MM, "
             "0.22 KH, 0.19 LA, 0 TL)", "decision_36_cap_at_potential",
             "flag", "B", SRC, LOC, INSTRUCTION_SHA, decision_ref="36,55,113", status="REFERENCE_ONLY")
    reg5.add("s4l5_biomass_overflow_cap_share", "S4L-5 point 2 (diagnostic only, not the main run): research.s2.industry.biomass_overflow_cap_share = 1.0 (main: cap = potential) | 0.98 "
             "(diagnostic network: for the countries where the decision-36 rule binds - fixed biomass demand >= biomass_overflow_binding_ratio 0.999 x potential - the cap is "
             "0.98 x potential and the extra 2 % moves to methane by the same rule, industry first then agriculture); no other change, no dust cleanup", str(CAP_SHARE),
             "share", "B", SRC, cfg, sha256(ROOT / cfg), decision_ref="36,55,113", status="SENSITIVITY")
    reg5.add("s4l5_diagnostic_runs", "S4L-5 point 3: the 98 % diagnostic network solved with profile A, integrated and disconnected STEPS, 56x3h, 30 min stop-loss, no retry; "
             "reported: status, gates, objective, solid-biomass shadow prices, per-country ledger differences against the S4K + A reference under the S4L-2 standard "
             "(s4l2_comparison_standard); results in a separate report section and listed for the user's decision, not merged into the main run", "2_runs", "flag", "B",
             SRC, LOC, INSTRUCTION_SHA, decision_ref="36,55,113", status="REFERENCE_ONLY")
    reg5.write(REG_DIR / "fragments" / "s4l_5.csv")
    print("registry fragment s4l_5 written:", len(reg5.rows), "rows")


def compare(a):
    out = Path(a.out); res = {}
    for sc in SCEN:
        k = net(Path(a.s4k) / sc / f"{sc}_2920_3h_unsolved.nc"); d = net(Path(a.diag) / sc / f"{sc}_2920_3h_unsolved.nc")
        lk, ld = loads_by_account(k), loads_by_account(d)
        key = [c for c in ("country", "carrier", "sector", "account") if c in lk]
        M = lk.merge(ld, on=key, how="outer", suffixes=("_s4k", "_diag")).fillna(0.0)
        M["delta_mwh"] = M.annual_mwh_diag - M.annual_mwh_s4k
        ch = M[M.delta_mwh.abs() > 1e-6].sort_values(["country", "carrier"])
        ch.to_csv(out / f"BIOMASS98_LOAD_CHANGES_S4L5_{sc}.csv", index=False)
        comp = {}
        for c in k.iterate_components():
            t = c.name; dk, dd = k.df(t), d.df(t)
            comp[t] = dict(s4k=int(len(dk)), diag=int(len(dd)), names_equal=bool(dk.index.equals(dd.index)))
        pk = {b["country"]: b for b in pool_balance(k) if b["bus"].startswith("solid")}; pdg = {b["country"]: b for b in pool_balance(d) if b["bus"].startswith("solid")}
        bal = {c: dict(potential_mwh=pk[c]["pool_total_mwh"], demand_s4k_mwh=pk[c]["fixed_demand_mwh"], demand_diag_mwh=pdg[c]["fixed_demand_mwh"],
                       ratio_diag=(pdg[c]["fixed_demand_mwh"] / pk[c]["pool_total_mwh"] if pk[c]["pool_total_mwh"] else None), slack_diag_mwh=pdg[c]["slack_mwh"]) for c in pk}
        ovk = ((k.meta.get("s2_demand_ledger") or {}).get("parameters") or {}); ovd = ((d.meta.get("s2_demand_ledger") or {}).get("parameters") or {})
        res[sc] = dict(components=comp, loads_changed=int(len(ch)), load_changes=ch.to_dict("records"), by_country_carrier_delta_mwh={f"{r.country}|{r.carrier}": float(v) for (r, v) in ((row, row.delta_mwh) for row in ch.itertuples())},
                       pool_balance=bal, overflow_ledger_diag=(d.meta.get("s2_demand_ledger") or {}).get("industry", {}).get("biomass_overflow") if isinstance((d.meta.get("s2_demand_ledger") or {}).get("industry"), dict) else None,
                       research_config_sha256=dict(s4k=k.meta.get("research_config_sha256"), diag=d.meta.get("research_config_sha256")), overrides=(d.meta.get("research_config") or {}).get("config_overrides"))
        print(sc, "loads changed:", len(ch), "components equal names:", all(v["names_equal"] for v in comp.values()))
        print(ch.groupby(["country", "carrier"]).delta_mwh.sum().round(1).to_string())
        print({c: (round(v["ratio_diag"], 4), round(v["slack_diag_mwh"], 1)) for c, v in bal.items() if v["ratio_diag"] and v["ratio_diag"] > 0.9})
    (out / "BIOMASS98_IMPACT_S4L5.json").write_text(json.dumps(res, indent=1, default=str))


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("table"); p1.add_argument("--s4k", type=Path, required=True); p1.add_argument("--out", type=Path, required=True)
    p2 = sub.add_parser("compare"); p2.add_argument("--s4k", type=Path, required=True); p2.add_argument("--diag", type=Path, required=True); p2.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    (table if a.cmd == "table" else compare)(a)


if __name__ == "__main__":
    main()
