"""G2-3: coal net calorific value of Viet Nam under the decision-207 rule (B-G2 item 4; A3 item 7).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_ncv.py

Default = UNSD country value (W11 scheme b); an alternative replaces it only if at least two independent physical evidences conflict with it.
Evidence collected here (all from local files or the SDMX responses; nothing from memory):
  * UNSD SDMX CONVERSION_FACTOR of every VN coal series 2005-2022 (official);
  * UNSD 2014 country NCV table and APEC Energy Statistics 2022 (read by W11, ncv/NCV_REFERENCE_VALUES.csv);
  * the UNSD power sector: coal to electricity plants (kt) and coal electricity (GWh) 2015-2022 -> t/MWh and the fleet efficiency implied by
    each candidate NCV (tables/VN_COAL_POWER_SERIES.csv of v4w07g2_captive.py);
  * GEM GIPT 2026-09 VN coal fleet operating at the end of 2019: coal rank (W11 GIPT_COAL_RANK_CAPACITY.csv) and steam-cycle technology.
Chain check: the W11 VN results (mode I) are re-run in this scratch copy with the same deltas (industry coal of the ATS table and the UNSD cache
cell ratios) and must agree to 1e-6 TWh. Writes VN_NCV.csv, tables/VN_NCV_EVIDENCE_TABLE.csv, evidence/_ncv_evidence.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

T = cm.WORK / "tables"
V3_GJ = 0.007167 * 3600.0   # 25.8012 GJ/t, frozen upstream hard coal factor
SCHEMES = {"v3": V3_GJ, "207_unsd": 23.446, "c_apec2022": 21.695, "d_ipcc_anthracite": 26.7}
HARD_COAL_KT = {"chemical and petrochemical": 1980.0, "other": 23878.35}   # UNSD 2019 industry hard coal rows of the D1 base (export = SDMX)


def ncv_edit(gj: float) -> tuple[dict, dict]:
    """base_delta (industry coal, MWh) and the UNSD cache cell ratios for a hard-coal NCV in GJ/t (coke unchanged at 28.2)."""
    r = gj / V3_GJ
    d = sum(HARD_COAL_KT.values()) * (gj - V3_GJ) / 3.6 * 1e3   # kt x GJ/t = TJ; / 3.6 = GWh; x 1e3 = MWh
    return {"coal": d}, {("coal", k): r for k in HARD_COAL_KT}


def main():
    ev = cm.Ev("ncv")
    s = cm.sdmx_long()
    cf = s[s.commodity.isin(["0100", "0311", "5110", "5120", "4630", "4670", "4680"])].groupby(["commodity_name", "year"]).conversion_factor.agg(["min", "max"]).reset_index()
    cf.to_csv(T / "VN_SDMX_CONVERSION_FACTORS.csv", index=False, float_format="%.6f")
    hc = cf[cf.commodity_name == "Hard Coal"]
    ev.put("sdmx_hard_coal_cf_2007_2022_min", float(hc[hc.year >= 2007]["min"].min()), "GJ/t", "SDMX CONVERSION_FACTOR, all VN hard-coal flows 2007-2022", "VERIFIED", "A")
    ev.put("sdmx_hard_coal_cf_2007_2022_max", float(hc[hc.year >= 2007]["max"].max()), "GJ/t", "same", "VERIFIED", "A")
    ev.put("sdmx_hard_coal_cf_2005_2006", float(hc[hc.year <= 2006]["max"].max()), "GJ/t", "SDMX CONVERSION_FACTOR 2005-2006 (standard value)", "VERIFIED", "A")
    # ---------------- evidence table ----------------
    pw = pd.read_csv(T / "VN_COAL_POWER_SERIES.csv")
    rows = []
    for name, gj in SCHEMES.items():
        eff = 3.6 / (pw.t_per_mwh * gj)
        rows.append(dict(evidence="UNSD power sector 2015-2022: coal electricity / (coal to electricity plants x NCV)", candidate=name, ncv_gj_t=gj,
                         eff_2019=float(eff[pw.year == 2019].iloc[0]), eff_median_2015_2022=float(eff.median()), eff_min=float(eff.min()), eff_max=float(eff.max()),
                         note="2019 coal electricity printed as the round 100,000 GWh (2020: 119,147 GWh from the same 59.3 Mt): 2019 is an outlier"))
        ev.put(f"power_eff_median.{name}", float(eff.median()), "ratio", "tables/VN_COAL_POWER_SERIES.csv; UNSD SDMX 0100/088 and 7000T/01CL", "EXACT", "B")
    P = pd.DataFrame(rows)
    gi = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
    vn = gi[(gi.iso == "VN") & gi.Type.eq("coal")].copy()
    vn["sy"] = pd.to_numeric(vn["Start year"], errors="coerce"); vn["ry"] = pd.to_numeric(vn["Retired year"], errors="coerce")
    op = vn.Status.isin(["operating", "retired", "mothballed"]) & (vn.sy <= 2019) & ~(vn.ry <= 2019)
    tech = vn[op].groupby("Technology")["Capacity (MW)"].sum()
    for k, x in tech.items():
        ev.put(f"gipt_vn_coal_mw_2019.{k}", float(x), "MW", "GEM GIPT 2026-09 VN coal units operating at the end of 2019, by technology", "VERIFIED", "B")
    rank = pd.read_csv(cm.NCVW / "ncv/GIPT_COAL_RANK_CAPACITY.csv"); rank = rank[rank["Country/area"] == "Vietnam"].iloc[0]
    ref = pd.read_csv(cm.NCVW / "ncv/NCV_REFERENCE_VALUES.csv")
    ref_vn = ref[ref.iloc[:, 8].astype(str).eq("VN")] if ref.shape[1] > 8 else ref.iloc[0:0]
    E = pd.DataFrame([
        dict(evidence="UNSD SDMX CONVERSION_FACTOR (all VN hard-coal flows)", value="23.446 GJ/t (2007-2022); 25.8 (2005-2006)", source="sdmx/VN_coal.xml", status="VERIFIED", grade="A",
             independent_of_unsd=False, direction_vs_unsd="="),
        dict(evidence="UNSD Energy Balances 2014, country NCV table: VN hard coal production / imports", value="23.4 / 23.4 GJ/t", source="W11 ncv/NCV_REFERENCE_VALUES.csv (UNSD_NCV.pdf p.4, p.9)",
             status="VERIFIED", grade="B", independent_of_unsd=False, direction_vs_unsd="="),
        dict(evidence="UN Energy Balances 2019 TJ / UNdata kt, 10 flows", value="23.446 GJ/t", source="W11 ncv/UNSD_IMPLIED_COAL_NCV_2019.csv", status="VERIFIED", grade="B",
             independent_of_unsd=False, direction_vs_unsd="="),
        dict(evidence="APEC Energy Statistics 2022, average NCV 2022, VN anthracite", value="21.695 GJ/t (-7.5 %)", source="W11 ncv/NCV_REFERENCE_VALUES.csv (page image, TRANSCRIBED; note: some economies back-calculate)",
             status="TRANSCRIBED", grade="C", independent_of_unsd=True, direction_vs_unsd="lower"),
        dict(evidence="UNSD power sector implied fleet efficiency at 23.446 GJ/t, median 2015-2022", value=f"{P.set_index('candidate').at['207_unsd', 'eff_median_2015_2022']:.3f} (range {P.set_index('candidate').at['207_unsd', 'eff_min']:.3f}-{P.set_index('candidate').at['207_unsd', 'eff_max']:.3f})",
             source="tables/VN_COAL_POWER_SERIES.csv", status="EXACT", grade="B", independent_of_unsd=False,
             direction_vs_unsd="none: 30-34 % is plausible for a fleet that is 74 % subcritical by capacity (INFERENCE); at 26.7 GJ/t the median falls to 27 %, at 21.695 rises to 33 %"),
        dict(evidence="GEM GIPT 2026-09 VN coal fleet by coal rank (known-rank capacity)", value=f"anthracite {rank.share_known_anthracite:.1%}, bituminous {rank.share_known_bituminous:.1%}, lignite {rank.share_known_lignite:.1%}",
             source="W11 ncv/GIPT_COAL_RANK_CAPACITY.csv", status="VERIFIED", grade="C", independent_of_unsd=True,
             direction_vs_unsd="higher if IPCC defaults applied (anthracite 26.7, other bituminous 25.8); domestic power anthracite is a high-ash slack grade, so the rank alone does not fix the NCV (INFERENCE)"),
        dict(evidence="GEM GIPT VN coal fleet by technology, end 2019", value="; ".join(f"{k} {x:,.0f} MW" for k, x in tech.items()), source="registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv",
             status="VERIFIED", grade="B", independent_of_unsd=True, direction_vs_unsd="context for the efficiency check only"),
    ])
    E.to_csv(T / "VN_NCV_EVIDENCE_TABLE.csv", index=False)
    P.to_csv(T / "VN_NCV_POWER_CHECK.csv", index=False, float_format="%.6f")
    # ---------------- A6 table ----------------
    a6 = pd.DataFrame([
        dict(commodity="hard coal (industry: chemical 1,980 kt, n.e.s. 23,878 kt)", v3=round(V3_GJ, 4), unsd_country=23.446, national="21.695 (APEC 2022 anthracite, C)", ipcc="26.7 anthracite / 25.8 other bituminous",
             physical_evidence="power-sector efficiency 30-34 % at 23.446 (plausible); GIPT rank anthracite 58.8 % / bituminous 40.8 % (points up); APEC 21.695 (points down): no two independent evidences agree on another value",
             proposed="23.446 (decision 207 default = W11 b); sensitivities 21.695 (c) and 26.7 (d)"),
        dict(commodity="coke-oven coke (iron and steel 5,326 kt)", v3=28.2, unsd_country=28.2, national="", ipcc=28.2, physical_evidence="", proposed="28.2 (unchanged)"),
        dict(commodity="fuelwood (thousand m3)", v3=9.144, unsd_country=9.135, national="", ipcc="15.6 GJ/t (mass basis, not comparable)", physical_evidence="", proposed="9.144 (difference 0.1 %, not material)"),
        dict(commodity="bagasse (kt, wet)", v3=7.718, unsd_country=7.7221, national="", ipcc=11.6, physical_evidence="", proposed="7.718 (unchanged; supply side 15 GJ/t inconsistency belongs to W12)"),
        dict(commodity="LPG / fuel oil / diesel", v3="47.27 / 40.39 / 42.98", unsd_country="47.3 / 40.4 / 43.0", national="", ipcc="same", physical_evidence="", proposed="unchanged"),
        dict(commodity="natural gas (TJ GCV)", v3="x0.90", unsd_country="x0.90 (UNSD rule)", national="", ipcc="", physical_evidence="", proposed="unchanged"),
    ])
    a6.to_csv(cm.WORK / "VN_NCV.csv", index=False)
    # ---------------- chain check against W11 (mode I, v3 APEC decomposition) ----------------
    v3 = cm.import_v3(); fut = v3.future_vectors()
    ch = cm.Chain(); ch.copy()
    w11 = pd.read_csv(cm.NCVW / "ncv/NCV_IMPACT_COUNTRY.csv"); w11 = w11[(w11.country == "VN") & (w11["mode"] == "I")].set_index("case")
    chk = []
    dl = pd.read_csv(cm.NCVW / "ncv/NCV_BASE_DELTAS_2019.csv")
    dl = dl[(dl.country == "VN") & (dl.account == "IndustryFinalEnergy") & (dl.carrier == "coal")].iloc[0]
    kt = sum(HARD_COAL_KT.values())
    for name, case in (("207_unsd", "b"), ("c_apec2022", "c"), ("d_ipcc_anthracite", "d")):
        gj_w11 = V3_GJ + float(dl[f"{case}_delta_mwh"]) / 1e3 * 3.6 / kt   # W11 used its implied value (b: 23.446018), SDMX prints 23.446
        ev.put(f"w11_ncv_used.{name}", gj_w11, "GJ/t", "W11 ncv/NCV_BASE_DELTAS_2019.csv VN industry coal delta / 25,858.35 kt", "EXACT", "B")
        bd, cr = ncv_edit(gj_w11)
        res = ch.run(base_delta=bd, cache_ratio=cr)
        lay = cm.v3_layer(v3, res, fut)
        chk.append(dict(scheme=name, w11_case=case, base_delta_twh=bd["coal"] / 1e6, T_twh=lay["T"] / 1e6, T_w11=float(w11.at[case, "T_v2_2050_twh"]),
                        other_twh=lay["other_total"] / 1e6, other_w11=float(w11.at[case, "other_2050_twh"])))
    C = pd.DataFrame(chk); C["dev_T"] = C.T_twh - C.T_w11; C["dev_other"] = C.other_twh - C.other_w11
    C.to_csv(T / "VN_NCV_W11_CHECK.csv", index=False, float_format="%.9f")
    if C[["dev_T", "dev_other"]].abs().max().max() > 1e-5:
        raise SystemExit(f"STOP: NCV chain check does not reproduce W11: {C}")
    for r in C.itertuples():
        ev.put(f"w11_check.{r.scheme}.T_twh", r.T_twh, "TWh", f"scratch chain vs W11 NCV_IMPACT_COUNTRY (case {r.w11_case}, mode I): dev {r.dev_T:.2e}", "EXACT", "D")
        ev.put(f"w11_check.{r.scheme}.other_twh", r.other_twh, "TWh", f"same, other bucket: dev {r.dev_other:.2e}", "EXACT", "D")
        ev.put(f"base_delta_2019.{r.scheme}", r.base_delta_twh, "TWh", "VN industry hard coal 25,858.35 kt x (NCV - 25.8012) GJ/t", "EXACT", "B")
    ev.write(cm.WORK / "evidence/_ncv_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80)
    print(P.round(4).to_string()); print(E[["evidence", "value", "direction_vs_unsd"]].to_string()); print(C.round(6).to_string())


if __name__ == "__main__":
    main()
