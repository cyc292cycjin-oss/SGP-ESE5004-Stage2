"""V4 W11 section 4.3: NCV schemes combined with S1 option (b) (captive coal C removed from ID industry coal, eta*C added as electricity,
ATS multiplier unchanged), ID, mode I, in the scratch copy.

    PYTHONHASHSEED=0 python scripts/v4ncv_s1_combined.py --work <work dir> --repo /home/jin/wt_v4_ncv --chain /home/jin/v4ncv/chain

C is physical in S1 (kt = capacity x hours x t/MWh); in energy it must use the same NCV as the industry coal row: C_s = kt x NCV_s.
E (generation) does not depend on the NCV. Cases per level (central, low, mid): captive only at the v3 NCV (must reproduce S1 s1/ID_CAPTIVE_OPTIONS.csv
T_2050 to 1e-6 TWh), NCV only (b, c, d), NCV + captive. The S1 edit is replicated: ID 'other' cache cell coal - C, electricity + E;
ATS Industry coal base - C, electricity base + E, value_2050 = base x multiplier.
Output ncv/NCV_S1_COMBINED.csv, ncv/_s1_combined_evidence.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402
import v4ncv_chain as ch   # noqa: E402

S1 = cm.REPO / "research/06_scope_redesign/p1_v4_data_20261105/s1"


def captive_edit(chain: Path, c_mwh: float, e_mwh: float) -> None:
    cp = chain / ch.CACHE
    cache = json.loads(cp.read_text())
    for r in cache["records"]:
        if r["country"] == "ID" and r["carrier"] == "coal":
            r["other"] = repr(float(r["other"]) - c_mwh)
        if r["country"] == "ID" and r["carrier"] == "electricity":
            r["other"] = repr(float(r["other"]) + e_mwh)
    cp.write_text(json.dumps(cache))
    dp = chain / ch.ATS
    d = pd.read_csv(dp, keep_default_na=False, dtype=str)
    for car, dv in (("coal", -c_mwh), ("electricity", e_mwh)):
        m = (d.country == "ID") & (d.sector == "Industry") & (d.carrier == car)
        if m.sum() != 1:
            raise ValueError(f"ID Industry {car}: {m.sum()} rows")
        b = float(d.loc[m, "base_2019_mwh"].iloc[0]) + dv
        d.loc[m, "base_2019_mwh"] = repr(b)
        d.loc[m, "value_2050_mwh"] = repr(b * float(d.loc[m, "multiplier_total"].iloc[0]))
    d.to_csv(dp, index=False)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO)
    ap.add_argument("--chain", type=Path, default=Path("/home/jin/v4ncv/chain")); a = ap.parse_args()
    sys.path.insert(0, str(a.repo / "scripts_project"))
    import v3_industry as v3   # noqa: E402
    fut = v3.future_vectors(); ne = v3.nickel_unit_energy(); nf = v3.nonferrous(fut, "main", ne)[0]
    deltas = pd.read_csv(a.work / "ncv/NCV_BASE_DELTAS_2019.csv")
    ratios = pd.read_csv(a.work / "ncv/NCV_CACHE_RATIOS_2019.csv")
    X = pd.read_csv(a.work / "ncv/NCV_FACTOR_SCHEMES.csv")
    f = {s: float(X[(X.country == "ID") & (X.commodity == "Hard coal") & (X.scheme == s)].gj_per_unit.iloc[0]) for s in ("a", "b", "c", "d")}
    cap = pd.read_csv(S1 / "ID_CAPTIVE_COAL_2019.csv"); cap = cap[cap.group == "合计"].set_index("level")
    s1opt = pd.read_csv(S1 / "ID_CAPTIVE_OPTIONS.csv"); s1opt = s1opt[s1opt.option == "b"].set_index("level")
    if not (a.chain / ch.CACHE).exists():
        ch.copy_chain(a.repo, a.chain)
    orig = {rel: (a.repo / rel).read_bytes() for rel in (ch.CACHE, ch.ATS, ch.D1)}
    rows, ev = [], dict(s1_reproduction={})

    def run_case(scheme, level):
        ch.restore(a.chain, orig)
        if scheme != "a":
            ch.apply_table(a.chain / ch.ATS, deltas, scheme, rescale_2050=True)
            ch.apply_cache(a.chain / ch.CACHE, ratios, scheme)
        C = E = 0.0
        if level:
            # S1 options used coal_in_industry_twh_model (= kt x 7.167 MWh/t) from this table; the same tonnes at the scheme NCV:
            C = float(cap.at[level, "coal_in_industry_twh_model"]) * 1e6 * (f[scheme] / f["a"])
            E = float(cap.at[level, "gen_in_industry_gwh"]) * 1e3
            captive_edit(a.chain, C, E)
        ch.run(a.chain, "s3_0_industry.py")
        res = ch.collect(a.chain, v3, fut, nf); res.pop("_gaps")
        return res["ID"]["T"] / 1e6, sum(res["ID"]["other"].values()) / 1e6, C / 1e6, E / 1e6

    T0, O0, _, _ = run_case("a", None)
    for lv in ("central", "low", "mid"):
        Tc, Oc, Cc, Ec = run_case("a", lv)
        ev["s1_reproduction"][lv] = dict(T_here=Tc, T_s1=float(s1opt.at[lv, "T_2050_twh"]), dev=Tc - float(s1opt.at[lv, "T_2050_twh"]))
        for s in ("b", "c", "d"):
            Tn, On, _, _ = run_case(s, None)
            Tb, Ob, Cb, Eb = run_case(s, lv)
            rows.append(dict(level=lv, scheme=s, ncv_gj_t=f[s], C_twh=Cb, E_twh=Eb, T_v3=T0, dT_captive_only=Tc - T0, dT_ncv_only=Tn - T0, dT_combined=Tb - T0,
                             interaction=(Tb - T0) - (Tc - T0) - (Tn - T0), other_v3=O0, dO_captive_only=Oc - O0, dO_ncv_only=On - O0, dO_combined=Ob - O0,
                             other_share_combined_pct=Ob / Tb * 100))
    ch.restore(a.chain, orig)
    R = pd.DataFrame(rows)
    R.to_csv(a.work / "ncv/NCV_S1_COMBINED.csv", index=False, float_format="%.6f")
    (a.work / "ncv/_s1_combined_evidence.json").write_text(json.dumps(ev, indent=1) + "\n")
    print(json.dumps(ev, indent=0))
    pd.set_option("display.width", 250)
    print(R.round(3).to_string())
    bad = [k for k, v in ev["s1_reproduction"].items() if abs(v["dev"]) > 1e-6]
    if bad:
        raise SystemExit(f"S1 option (b) not reproduced for {bad}")


if __name__ == "__main__":
    main()
