"""W08: checks of the network-facing tables against I2 (read only; chain in a scratch folder).
  (1) node rule at S0 (v3 only) reproduces INDUSTRY_CARRIER_NODE_SHARES_V3.csv (I2 gate);
  (2) I2 original case (IId, paper fuelwood purchased): curve weights = I2 tables/I2_CURVE_WEIGHTS.csv; node electricity shares = I2_NODE_SHARES_BY_STEP S7;
  (3) the written out_ras / out_iid tables: summary carrier totals = snapshot T_v2; node shares sum to 1; weights energy = T_v2 elec / heat.
Writes tables/W08_OUTPUT_CHECKS.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "/home/jin/wt_v4_w08/scripts_project")
import v4_industry as V   # noqa: E402
import v4_outputs as O    # noqa: E402
import v4_profiles as PR  # noqa: E402
from v4_common import V4_DIR, V4_MAIN, IND_V3   # noqa: E402

W = Path(__file__).resolve().parents[1]
I2T = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w07_20261106/I2/tables")


def main():
    out = {}
    ch = V.Chain(Path("/home/jin/v4w08/work_check"))
    I = V.Inputs(); N = O.Nodes()
    # (1)
    r0 = ch.run({})
    ref = pd.read_csv(IND_V3 / "INDUSTRY_CARRIER_NODE_SHARES_V3.csv"); ref = ref[ref.case == "main"]
    dev = 0.0
    for c, s in r0["snap"].items():
        if not s["L"]["parts"]:
            continue
        al, _ = N.allocate(c, s["L"]["parts"], v3_only=True)
        for car, dd in al.items():
            sh = O.norm(dd); rr = ref[(ref.country == c) & (ref.carrier == car)].set_index("node").share
            for n in set(sh) | set(rr.index):
                dev = max(dev, abs(sh.get(n, 0.0) - float(rr.get(n, 0.0))))
    out["node_rule_S0_vs_v3_max_abs"] = dev
    # (2)
    s = dict(V4_MAIN, anchor_mode="iid", id_paper_fuelwood="purchased")
    res = ch.run(V.final_case(I, s))
    parts = {c: v["L"]["parts"] for c, v in res["snap"].items() if v["L"]["T"] > 0}
    Wt = PR.composition(parts, PR.dispersed_rows(res["pz"]), N)
    Wi = pd.read_csv(I2T / "I2_CURVE_WEIGHTS.csv")
    m = Wt.merge(Wi, on=["country", "zone", "key", "etype"], how="outer", suffixes=("_w08", "_i2")).fillna(0.0)
    m = m[(m.mwh_w08 > 0.0005) | (m.mwh_i2 > 0.0005)]
    out["curve_weights_vs_I2"] = dict(rows=len(m), max_abs_mwh=float((m.mwh_w08 - m.mwh_i2).abs().max()),
                                      max_rel=float(((m.mwh_w08 - m.mwh_i2).abs() / m.mwh_i2.clip(lower=1.0)).max()))
    ns = pd.read_csv(I2T / "I2_NODE_SHARES_BY_STEP.csv"); ns = ns[ns.step == "S7"]
    dmax = 0.0
    for c, p in parts.items():
        al, _ = N.allocate(c, p); el = O.norm(al.get("electricity", {}))
        z = ns[ns.country == c].set_index("node").share_electricity
        for n in set(el) | set(z.index):
            dmax = max(dmax, abs(el.get(n, 0.0) - float(z.get(n, 0.0))))
    out["node_electricity_shares_vs_I2_S7_max_abs"] = dmax
    # (3)
    for mode in ("ras", "iid"):
        od = V4_DIR / f"out_{mode}"
        S = pd.read_csv(od / "INDUSTRY_2050_SUMMARY_V4.csv").set_index("country")
        snap = json.loads((od / "SNAPSHOT.json").read_text())
        import v3_industry as v3
        dT = max(abs(float(sum(S.at[c, v3.col(k)] for k in v3.CARRIERS)) - x["T"]) for c, x in snap["countries"].items() if c in S.index)
        cs = pd.read_csv(od / "INDUSTRY_CARRIER_NODE_SHARES_V4.csv"); sums = cs.groupby(["country", "carrier"]).share.sum()
        Wm = pd.read_csv(od / "INDUSTRY_CURVE_WEIGHTS_V4.csv")
        el = {c: sum(v["T_car"].get("electricity", 0.0) for _ in [0]) for c, v in snap["countries"].items()}
        dW = max(abs(float(Wm[(Wm.country == c) & (Wm.etype == "elec")].mwh.sum()) - el[c]) for c in el)
        out[f"out_{mode}"] = dict(summary_vs_snapshot_max_abs_mwh=dT, node_share_sum_dev=float((sums - 1.0).abs().max()), weights_elec_vs_T_max_abs_mwh=dW,
                                   asean_T_v2_TWh=sum(v["T"] for v in snap["countries"].values()) / 1e6)
    (W / "tables/W08_OUTPUT_CHECKS.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
