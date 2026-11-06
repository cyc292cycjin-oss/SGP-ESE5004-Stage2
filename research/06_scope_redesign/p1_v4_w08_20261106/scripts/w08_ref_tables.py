"""W08 section 1: reference tables from the three reference runs (w08_ref_run.py; scratch /home/jin/v4w08/ref_{main,iid,i2chk}/results).

    /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/w08_ref_tables.py

Writes (delivery folder): REFERENCE_V4_MAIN.csv (decision 211: anchors IIa = RAS refit on the v4 seed, residue anchor alignment in RAS,
ID paper-row fuelwood as residue (a)), REFERENCE_V4_IID.csv (same with anchors IId), tables/W08_REF_C3_DEVIATION.csv (ASEAN10 sector
totals vs C.3 x k per step), tables/W08_REF_VS_I2.csv (country differences main / iid / I2 at S7 with the split into the two changes),
evidence/W08_ref.json (copy check: i2chk = I2 results, iid S1 = I2 S1, exact).
Columns of the reference tables: step, country, T_v2 (12 columns of v3_industry.CARRIERS, biomass before overflow), other, share, T and
'other' by carrier (the I2_STEPS_LONG names), biomass before overflow, overflow, s3_0 cap (potential x share), anchors, multipliers, sectors.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[1]
I2R = Path("/home/jin/v4i2/results")
SCR = {k: Path(f"/home/jin/v4w08/ref_{k}/results") for k in ("main", "iid", "i2chk")}
STEPS = ["S0", "S1", "S2", "S3", "S4", "S5a", "S5b", "S5c", "S5d", "S5e", "S5f", "S5g", "S6a", "S6b", "S6c", "S7"]
CC = ["ID", "VN", "TH", "MY", "PH", "SG", "MM", "KH", "LA", "BN", "TL"]
A10 = [c for c in CC if c != "TL"]
SEC = ["Industry", "Transport", "Residential", "Commercial", "AgricultureOthers"]
COLMAP = {"electricity": "elec", "heat": "heat_lt150", "heat_medium_a": "heat_150_200", "heat_medium_b": "heat_200_400", "heat_high": "heat_gt400",
          "oil": "oil", "gas": "gas", "coal": "coal", "biomass": "biomass", "hydrogen": "H2", "ammonia": "ammonia", "methanol": "methanol"}


def load(d: Path, s: str) -> dict:
    return json.loads((d / f"step_{s}.json").read_text())


def rows_of(run: str, d: Path, steps) -> list[dict]:
    out = []
    for s in steps:
        x = load(d, s)
        for c in CC:
            k = x["countries"][c]; a = x["ats_sectors"][c]
            r = dict(run=run, step=s, label=x["label"].split(" ", 1)[1] if " " in x["label"] else x["label"], country=c, T_v2_2050_TWh=k["T"] / 1e6,
                     other_2050_TWh=k["other"] / 1e6, other_share=k["share"], industry_2019_TWh=k["ind19_true"] / 1e6, industry_anchor_2050_TWh=k["ind_anchor"] / 1e6,
                     industry_multiplier=k["ind_mult"], tfec_anchor_2050_TWh=k["tfec_anchor"] / 1e6, ats_industry_2050_TWh=k["ind50_ats"] / 1e6,
                     products_2050_TWh=k["prod50"] / 1e6, implied_industry_fe_2050_TWh=(k["ind50_ats"] + k["prod50"]) / 1e6,
                     transport_2050_TWh=a["sec2050"]["Transport"] / 1e6, residential_2050_TWh=a["sec2050"]["Residential"] / 1e6,
                     commercial_2050_TWh=a["sec2050"]["Commercial"] / 1e6, agriculture_2050_TWh=a["sec2050"]["AgricultureOthers"] / 1e6,
                     neu_2050_TWh=a["sec2050"]["NonEnergyUse"] / 1e6, land_fuel_2050_TWh=a["land"] / 1e6, ev_electricity_2050_TWh=a["ev"] / 1e6,
                     rail_parent_2050_TWh=a["rail_parent"] / 1e6, biomass_before_overflow_TWh=k["bio_before"] / 1e6, biomass_overflow_TWh=k["overflow"] / 1e6,
                     solid_potential_cap_TWh=k["pot"] / 1e6, s30_not_found_2019_TWh=k["s30_not_found"] / 1e6, methanol_dropped_2050_TWh=k["meoh_dropped"] / 1e6)
            for car, col in COLMAP.items():
                r[f"T_{col}"] = k["T_car"].get(car, 0.0) / 1e6
            for car, col in COLMAP.items():
                r[f"other_{col}"] = k["other_car"].get(car, 0.0) / 1e6
            r["T_v2_2050_MWh"] = repr(float(k["T"])); r["other_2050_MWh"] = repr(float(k["other"]))
            out.append(r)
        tot = {f: sum(r[f] for r in out if r["step"] == s and r["run"] == run and r["country"] in CC) for f in out[-1] if f.endswith("_TWh") or f.startswith(("T_", "other_"))
               and not f.endswith("MWh") and f != "other_share"}
        tot = {k_: v for k_, v in tot.items() if isinstance(v, float)}
        t = dict(run=run, step=s, label="sum of the 11 countries", country="ASEAN11", **tot)
        t["other_share"] = t["other_2050_TWh"] / t["T_v2_2050_TWh"] if t["T_v2_2050_TWh"] else 0.0
        t["industry_multiplier"] = None
        out.append(t)
    return out


def write(rows: list[dict], p: Path):
    df = pd.DataFrame(rows)
    df.to_csv(p, index=False, float_format="%.9f", lineterminator="\n")
    return df


def main():
    (W / "tables").mkdir(exist_ok=True); (W / "evidence").mkdir(exist_ok=True)
    ref = {}
    for run in ("main", "iid"):
        ref[run] = write(rows_of(run, SCR[run], STEPS), W / f"REFERENCE_V4_{run.upper()}.csv")
    i2 = pd.DataFrame(rows_of("i2", I2R, STEPS))
    chk = pd.DataFrame(rows_of("i2chk", SCR["i2chk"], ["S1", "S7"]))
    ev = {}
    # ---- copy checks (EXACT): the reference engine without the two changes = I2; iid S1 = I2 S1 (the changes start at S2 / anchor mode)
    def maxdiff(a, b, steps):
        m = a[a.step.isin(steps) & a.country.isin(CC)].set_index(["step", "country"]).T_v2_2050_TWh
        n = b[b.step.isin(steps) & b.country.isin(CC)].set_index(["step", "country"]).T_v2_2050_TWh
        o = a[a.step.isin(steps) & a.country.isin(CC)].set_index(["step", "country"]).other_2050_TWh
        q = b[b.step.isin(steps) & b.country.isin(CC)].set_index(["step", "country"]).other_2050_TWh
        return float((m - n.reindex(m.index)).abs().max()), float((o - q.reindex(o.index)).abs().max())
    ev["copy_check_i2chk_vs_i2_S1_S7_TWh"] = maxdiff(chk, i2, ["S1", "S7"])
    ev["copy_check_iid_S0_S1_vs_i2_TWh"] = maxdiff(ref["iid"], i2, ["S0", "S1"])
    ev["copy_check_main_S0_vs_i2_TWh"] = maxdiff(ref["main"], i2, ["S0"])
    # ---- C.3 deviation per step (ASEAN10 sector totals of the ATS table; industry also with the explicit products)
    v3a = json.loads(Path("/home/jin/v4w08/ref_main/anchors_v3_ras.json").read_text())
    C3 = {s: sum(v3a["tfa"][c][s] for c in A10) / 1e6 for s in SEC}
    dv = []
    for run in ("main", "iid"):
        R = ref[run]
        for s in STEPS:
            z = R[(R.step == s) & R.country.isin(A10)]
            vals = dict(Industry=float(z.ats_industry_2050_TWh.sum()), Transport=float(z.transport_2050_TWh.sum()), Residential=float(z.residential_2050_TWh.sum()),
                        Commercial=float(z.commercial_2050_TWh.sum()), AgricultureOthers=float(z.agriculture_2050_TWh.sum()))
            for sec in SEC:
                dv.append(dict(run=run, step=s, sector=sec, asean10_2050_TWh=vals[sec], c3_x_k_TWh=C3[sec], dev_TWh=vals[sec] - C3[sec], dev_pct=(vals[sec] / C3[sec] - 1) * 100))
            fe = float(z.implied_industry_fe_2050_TWh.sum())
            dv.append(dict(run=run, step=s, sector="Industry incl. explicit products", asean10_2050_TWh=fe, c3_x_k_TWh=C3["Industry"], dev_TWh=fe - C3["Industry"], dev_pct=(fe / C3["Industry"] - 1) * 100))
    pd.DataFrame(dv).to_csv(W / "tables/W08_REF_C3_DEVIATION.csv", index=False, float_format="%.6f", lineterminator="\n")
    # ---- main vs I2 at S7, split: (1) anchor IIa vs IId with the paper fuelwood change (main - iid); (2) paper fuelwood (iid - I2)
    cmp = []
    for c in CC + ["ASEAN11"]:
        g = lambda D, s=("S7"): float(D[(D.step == s) & (D.country == c)].T_v2_2050_TWh.iloc[0])
        o = lambda D, s=("S7"): float(D[(D.step == s) & (D.country == c)].other_2050_TWh.iloc[0])
        cmp.append(dict(country=c, I2_T_v2=g(i2), iid_T_v2=g(ref["iid"]), main_T_v2=g(ref["main"]), main_minus_I2=g(ref["main"]) - g(i2),
                        of_which_paper_fuelwood=g(ref["iid"]) - g(i2), of_which_anchor_IIa=g(ref["main"]) - g(ref["iid"]),
                        I2_other=o(i2), main_other=o(ref["main"]), main_share=o(ref["main"]) / g(ref["main"]) if g(ref["main"]) else 0.0,
                        I2_mult=(float(i2[(i2.step == "S7") & (i2.country == c)].industry_multiplier.iloc[0]) if c != "ASEAN11" else None),
                        main_mult=(float(ref["main"][(ref["main"].step == "S7") & (ref["main"].country == c)].industry_multiplier.iloc[0]) if c != "ASEAN11" else None),
                        main_S1_minus_I2_S1=g(ref["main"], "S1") - g(i2, "S1")))
    pd.DataFrame(cmp).to_csv(W / "tables/W08_REF_VS_I2.csv", index=False, float_format="%.6f", lineterminator="\n")
    ev["asean_T_v2_S7_TWh"] = dict(main=float(ref["main"][(ref["main"].step == "S7") & (ref["main"].country == "ASEAN11")].T_v2_2050_TWh.iloc[0]),
                                   iid=float(ref["iid"][(ref["iid"].step == "S7") & (ref["iid"].country == "ASEAN11")].T_v2_2050_TWh.iloc[0]),
                                   i2=float(i2[(i2.step == "S7") & (i2.country == "ASEAN11")].T_v2_2050_TWh.iloc[0]))
    ev["meta"] = {k: json.loads((SCR[k] / "meta.json").read_text())["inputs"]["fw"] for k in ("main", "iid")}
    ev["runs"] = {k: json.loads((SCR[k] / "RUNS.json").read_text()) for k in SCR}
    (W / "evidence/W08_ref.json").write_text(json.dumps(ev, indent=1, default=float) + "\n")
    pd.set_option("display.width", 250)
    print(json.dumps({k: ev[k] for k in ev if k.startswith(("copy", "asean"))}, indent=1))
    print(pd.DataFrame(cmp).round(2).to_string())
    for run in ("main", "iid"):
        R = ref[run]
        print(run, R[R.country == "ASEAN11"][["step", "T_v2_2050_TWh", "other_2050_TWh", "other_share"]].round(3).to_string())


if __name__ == "__main__":
    main()
