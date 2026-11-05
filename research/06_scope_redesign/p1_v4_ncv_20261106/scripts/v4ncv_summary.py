"""V4 W11 section 4 and the report numbers: significance per country and scheme, interaction with S1 (captive coal C in tonnes),
plausibility of the ID coal NCV from PLN's coal rate, cement-deduction gaps, 11-country totals; markdown tables for the report and
V4_NCV_EVIDENCE.json (every number the report quotes, with source file, status and data grade).

    python scripts/v4ncv_summary.py --work <work dir>

Reads only ncv/*.csv of this step and, read-only, the S1 tables committed on this branch (research/06_scope_redesign/p1_v4_data_20261105/s1/).
Outputs ncv/NCV_SIGNIFICANCE.csv, ncv/NCV_S1_INTERPLAY.csv, ncv/NCV_ID_COAL_PLAUSIBILITY.csv, ncv/NCV_REPORT_TABLES.md, V4_NCV_EVIDENCE.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402

S1 = cm.REPO / "research/06_scope_redesign/p1_v4_data_20261105/s1"
THRESH = 2.0
EV = []


def ev(key, value, unit, desc, source, status, grade):
    EV.append(dict(id=key, value=(None if value is None or (isinstance(value, float) and np.isnan(value)) else value), unit=unit, description=desc,
                   source=source, status=status, grade=grade))


def md(df: pd.DataFrame, fmt: dict | None = None) -> str:
    fmt = fmt or {}
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join("---:" if pd.api.types.is_numeric_dtype(df[c]) else "---" for c in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else format(v, fmt.get(c, ",.2f")))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    n = a.work / "ncv"
    C = pd.read_csv(n / "NCV_IMPACT_COUNTRY.csv")
    S = pd.read_csv(n / "NCV_IMPACT_SECTOR.csv")
    X = pd.read_csv(n / "NCV_FACTOR_SCHEMES.csv")
    D = pd.read_csv(n / "NCV_BASE_DELTAS_2019.csv")
    G = pd.read_csv(n / "NCV_IMPACT_S3_GAPS.csv")
    U = pd.read_csv(n / "UNSD_IMPLIED_COAL_NCV_2019.csv")
    R = pd.read_csv(n / "NCV_REFERENCE_VALUES.csv")
    chain = json.loads((n / "_chain_evidence.json").read_text())
    tabs = {}
    # ---- coal factors per country --------------------------------------------------------------------------------------------------
    fx = []
    for cc in cm.ISO:
        for com in ("Hard coal", "Brown coal", "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Anthracite"):
            z = X[(X.country == cc) & (X.commodity == com) & (X.scheme != "a")]
            if not len(z):
                continue
            row = dict(country=cc, commodity=com, v3=float(X[(X.commodity == com) & (X.scheme == "a")].gj_per_unit.iloc[0]))
            for s in ("b", "c", "d"):
                zz = z[z.scheme == s]
                row[s] = float(zz.gj_per_unit.iloc[0]) if len(zz) else np.nan
                row[f"{s}_status"] = zz.status.iloc[0] if len(zz) else ""
            fx.append(row)
    FX = pd.DataFrame(fx)
    tabs["factors"] = md(FX[["country", "commodity", "v3", "b", "b_status", "c", "c_status", "d", "d_status"]], {k: ".3f" for k in ("v3", "b", "c", "d")})
    for r in FX.itertuples():
        for s in ("b", "c", "d"):
            v = getattr(r, s)
            if not np.isnan(v):
                ev(f"factor_{r.country}_{r.commodity}_{s}", round(float(v), 4), "GJ/t", f"{r.country} {r.commodity} scheme ({s})", "ncv/NCV_FACTOR_SCHEMES.csv",
                   getattr(r, f"{s}_status"), "B" if getattr(r, f"{s}_status") == "VERIFIED" else "C")
    for r in U.itertuples():
        ev(f"unsd2019_{r.country}_{r.commodity}_{r.source[:3]}", (None if np.isnan(r.implied_gj_per_t) else round(float(r.implied_gj_per_t), 4)), "GJ/t",
           f"UNSD 2019 implied NCV ({r.source}); flows agreeing {r.flows_agreeing} of {r.flows}", "ncv/UNSD_IMPLIED_COAL_NCV_2019.csv",
           "VERIFIED" if str(r.status).startswith("VERIFIED") else "NOT_DERIVABLE", "B")
    for r in R.itertuples():
        ev(f"ref_{r.source[:20]}_{r.country}_{r.item}".replace(" ", "_"), (r.gj_per_unit if pd.notna(r.gj_per_unit) else r.value), "GJ per unit" if pd.notna(r.gj_per_unit) else str(r.unit),
           f"{r.source} p.{r.pdf_page} ({r.table}) {r.item}", "ncv/NCV_REFERENCE_VALUES.csv", r.status, r.grade)
    # ---- 2019 base deltas by country x sector ---------------------------------------------------------------------------------------
    S19 = S[(S["mode"] == "I") & S.case.isin(["b", "c", "d"])].pivot_table(index=["country", "sector"], columns="case", values="delta_2019_twh").reset_index()
    S19 = S19[(S19[["b", "c", "d"]].abs() > 0.0005).any(axis=1)]
    base19 = S[(S.case == "a")].set_index(["country", "sector"]).base_2019_twh
    S19.insert(2, "v3_2019", [base19.get((c, s), np.nan) for c, s in zip(S19.country, S19.sector)])
    tabs["base2019"] = md(S19, {"v3_2019": ",.2f", "b": "+,.2f", "c": "+,.2f", "d": "+,.2f"})
    for r in S19.itertuples():
        for s in ("b", "c", "d"):
            ev(f"delta2019_{r.country}_{r.sector}_{s}", round(float(getattr(r, s)), 4), "TWh", f"2019 base change {r.country} {r.sector}, scheme ({s})", "ncv/NCV_IMPACT_SECTOR.csv (mode I)", "EXACT", "D")
    # ---- 2050 per country ------------------------------------------------------------------------------------------------------------
    keep = [c for c in cm.ISO if c != "TL"]
    v3 = C[C.case == "a"].set_index("country")
    rows = []
    for cc in keep:
        r = dict(country=cc, T_v3=v3.at[cc, "T_v2_2050_twh"], other_v3=v3.at[cc, "other_2050_twh"], other_share_v3=v3.at[cc, "other_share_pct"])
        for s in ("b", "c", "d"):
            for m in ("I", "II"):
                z = C[(C.case == s) & (C["mode"] == m) & (C.country == cc)].iloc[0]
                r[f"dT_{s}{m}"] = z.delta_T_twh; r[f"dT%_{s}{m}"] = z.delta_T_pct; r[f"dO_{s}{m}"] = z.delta_other_twh
                r[f"dTot%_{s}{m}"] = z.delta_total_pct; r[f"share_{s}{m}"] = z.other_share_pct
                for k, unit in (("delta_T_twh", "TWh"), ("delta_T_pct", "%"), ("delta_other_twh", "TWh"), ("delta_other_pct", "%"), ("delta_total_twh", "TWh"),
                                ("delta_total_pct", "%"), ("T_v2_2050_twh", "TWh"), ("other_2050_twh", "TWh"), ("other_share_pct", "%")):
                    ev(f"{k}_{cc}_{s}_{m}", round(float(z[k]), 4), unit, f"{k} {cc} scheme ({s}) mode {m}", "ncv/NCV_IMPACT_COUNTRY.csv", "EXACT", "D")
        rows.append(r)
    P = pd.DataFrame(rows)
    for cc in keep:
        ev(f"T_v2_v3_{cc}", round(float(v3.at[cc, "T_v2_2050_twh"]), 4), "TWh", f"T_v2 2050 v3 {cc}", "ncv/NCV_IMPACT_COUNTRY.csv (reproduces repository)", "EXACT", "D")
        ev(f"other_v3_{cc}", round(float(v3.at[cc, "other_2050_twh"]), 4), "TWh", f"v3 other bucket 2050 {cc}", "ncv/NCV_IMPACT_COUNTRY.csv", "EXACT", "D")
    tI = P[["country", "T_v3", "dT_bI", "dT%_bI", "dT_cI", "dT%_cI", "dT_dI", "dT%_dI", "other_v3", "dO_bI", "dO_cI", "dO_dI"]]
    tII = P[["country", "dT_bII", "dT%_bII", "dT_cII", "dT%_cII", "dT_dII", "dT%_dII", "dO_bII", "dO_cII", "dO_dII", "dTot%_bII", "dTot%_cII", "dTot%_dII"]]
    pct = {c: "+.2f" for c in tI.columns if "%" in c}
    tabs["impact_I"] = md(tI, {**pct, **{c: "+,.2f" for c in tI.columns if c.startswith(("dT_", "dO_"))}, "T_v3": ",.2f", "other_v3": ",.2f"})
    tabs["impact_II"] = md(tII, {**{c: "+.2f" for c in tII.columns if "%" in c}, **{c: "+,.2f" for c in tII.columns if c.startswith(("dT_", "dO_"))}})
    shares = P[["country", "other_share_v3", "share_bI", "share_cI", "share_dI", "share_bII", "share_cII", "share_dII"]]
    tabs["shares"] = md(shares, {c: ".2f" for c in shares.columns if c != "country"})
    tot = C[C.country.isin(keep)].groupby(["case", "mode"])[["T_v2_2050_twh", "delta_T_twh", "other_2050_twh", "delta_other_twh", "nonindustry_2050_twh",
                                                              "delta_nonindustry_twh", "total_final_2050_twh", "delta_total_twh"]].sum().reset_index()
    tot["delta_T_pct"] = tot.delta_T_twh / (tot.T_v2_2050_twh - tot.delta_T_twh) * 100
    tot["delta_total_pct"] = tot.delta_total_twh / (tot.total_final_2050_twh - tot.delta_total_twh) * 100
    tot["other_share_pct"] = tot.other_2050_twh / tot.T_v2_2050_twh * 100
    tabs["totals"] = md(tot, {"delta_T_pct": "+.2f", "delta_total_pct": "+.2f", "other_share_pct": ".2f", "delta_T_twh": "+,.2f", "delta_other_twh": "+,.2f",
                              "delta_nonindustry_twh": "+,.2f", "delta_total_twh": "+,.2f"})
    for r in tot.itertuples():
        for k in ("T_v2_2050_twh", "delta_T_twh", "delta_T_pct", "other_2050_twh", "delta_other_twh", "total_final_2050_twh", "delta_total_twh", "delta_total_pct", "other_share_pct"):
            ev(f"asean10_{k}_{r.case}_{r.mode}", round(float(getattr(r, k)), 4), "%" if "pct" in k else "TWh", f"10 countries with demand (TL has no industry) {k} case {r.case} mode {r.mode}",
               "ncv/NCV_IMPACT_COUNTRY.csv (sum)", "EXACT", "D")
    # non-industry 2050 by sector (mode I) where changed
    S50 = S[(S["mode"] == "I") & S.case.isin(["b", "c", "d"]) & S.sector.isin(["Residential", "Commercial", "AgricultureOthers", "Transport", "NonEnergyUse"])]
    S50 = S50.pivot_table(index=["country", "sector"], columns="case", values="delta_2050_twh").reset_index()
    S50 = S50[(S50[["b", "c", "d"]].abs() > 0.0005).any(axis=1)]
    tabs["nonind2050"] = md(S50, {"b": "+,.3f", "c": "+,.3f", "d": "+,.3f"})
    for r in S50.itertuples():
        for s in ("b", "c", "d"):
            ev(f"delta2050_{r.country}_{r.sector}_{s}_I", round(float(getattr(r, s)), 4), "TWh", f"2050 change {r.country} {r.sector} scheme ({s}) mode I", "ncv/NCV_IMPACT_SECTOR.csv", "EXACT", "D")
    # ---- significance -----------------------------------------------------------------------------------------------------------------
    sig = []
    for cc in keep:
        for s in ("b", "c", "d"):
            for m in ("I", "II"):
                z = C[(C.case == s) & (C["mode"] == m) & (C.country == cc)].iloc[0]
                big = abs(z.delta_T_pct) > THRESH or abs(z.delta_total_pct) > THRESH
                sig.append(dict(country=cc, scheme=s, mode=m, delta_T_pct=z.delta_T_pct, delta_total_pct=z.delta_total_pct, significant=big))
    SG = pd.DataFrame(sig)
    SG.to_csv(n / "NCV_SIGNIFICANCE.csv", index=False, float_format="%.4f")
    sigI = SG[SG["mode"] == "I"].pivot_table(index="country", columns="scheme", values="significant", aggfunc="first")
    tabs["significance"] = md(sigI.reset_index().replace({True: "> 2 %", False: "—"}))
    # ---- cement-deduction gaps (s3_0 log) for PH / KH / LA -------------------------------------------------------------------------
    g = G[G.country.isin(["PH", "KH", "LA", "MY", "MM"]) & G.item.str.contains("not found in other|exceeds the other bucket")]
    gp = g.groupby(["case", "mode", "country"]).mwh.sum().div(1e6).reset_index()
    gt = gp.pivot_table(index="country", columns=["case", "mode"], values="mwh").reset_index()
    gt.columns = ["_".join(c for c in col if c) if isinstance(col, tuple) else col for col in gt.columns]
    tabs["gaps"] = md(gt, {c: ",.3f" for c in gt.columns if c != "country"})
    for r in gp.itertuples():
        ev(f"cement_gap_{r.country}_{r.case}_{r.mode}", round(float(r.mwh), 4), "TWh", f"s3_0 2019 cement deduction not covered by the industry rows, {r.country}", "ncv/NCV_IMPACT_S3_GAPS.csv", "EXACT", "D")
    # ---- S1 interplay: captive coal in tonnes ----------------------------------------------------------------------------------------
    cap = pd.read_csv(S1 / "ID_CAPTIVE_COAL_2019.csv")
    cap = cap[cap.group == "合计"].set_index("level")
    fID = {s: float(X[(X.country == "ID") & (X.commodity == "Hard coal") & (X.scheme == s)].gj_per_unit.iloc[0]) for s in ("a", "b", "c", "d")}
    rows = []
    for lv in ("low", "central", "mid", "high"):
        kt = float(cap.at[lv, "coal_in_industry_kt"]); e = float(cap.at[lv, "gen_in_industry_gwh"]) / 1e3
        r = dict(level=lv, coal_kt=kt, E_twh=e)
        for s in ("a", "b", "c", "d"):
            c_twh = kt * fID[s] / 3.6 / 1e3
            r[f"C_{s}_twh"] = c_twh; r[f"eta_{s}"] = e / c_twh
            ev(f"captive_C_{lv}_{s}", round(c_twh, 4), "TWh", f"S1 captive coal C ({lv}) at the ID hard-coal NCV of scheme ({s})", "ncv/NCV_S1_INTERPLAY.csv (S1 ID_CAPTIVE_COAL_2019.csv kt)", "EXACT", "C")
            ev(f"captive_eta_{lv}_{s}", round(e / c_twh, 4), "-", f"implied efficiency E/C ({lv}) scheme ({s})", "ncv/NCV_S1_INTERPLAY.csv", "INFERENCE", "C")
        rows.append(r)
    SI = pd.DataFrame(rows)
    SI.to_csv(n / "NCV_S1_INTERPLAY.csv", index=False, float_format="%.6f")
    tabs["s1"] = md(SI, {**{c: ",.2f" for c in SI.columns if c.startswith("C_") or c in ("coal_kt", "E_twh")}, **{c: ".3f" for c in SI.columns if c.startswith("eta")}})
    SC = pd.read_csv(n / "NCV_S1_COMBINED.csv")
    sce = json.loads((n / "_s1_combined_evidence.json").read_text())
    tabs["s1_combined"] = md(SC[["level", "scheme", "ncv_gj_t", "C_twh", "E_twh", "dT_captive_only", "dT_ncv_only", "dT_combined", "interaction", "dO_combined",
                                 "other_share_combined_pct"]], {"ncv_gj_t": ".3f", "C_twh": ",.2f", "E_twh": ",.2f", "dT_captive_only": "+,.2f", "dT_ncv_only": "+,.2f",
                                                               "dT_combined": "+,.2f", "interaction": "+,.2f", "dO_combined": "+,.2f", "other_share_combined_pct": ".2f"})
    for r in SC.itertuples():
        for k in ("C_twh", "dT_captive_only", "dT_ncv_only", "dT_combined", "interaction", "dO_combined", "other_share_combined_pct"):
            ev(f"s1comb_{k}_{r.level}_{r.scheme}", round(float(getattr(r, k)), 4), "%" if "pct" in k else "TWh", f"ID, S1 option (b) {r.level} combined with NCV scheme ({r.scheme}), mode I: {k}",
               "ncv/NCV_S1_COMBINED.csv", "EXACT", "D")
    for lv, v in sce["s1_reproduction"].items():
        ev(f"s1_reproduction_dev_{lv}", v["dev"], "TWh", f"captive-only run here minus S1 ID_CAPTIVE_OPTIONS.csv T_2050 ({lv}); S1 table printed to 1e-6 TWh",
           "ncv/_s1_combined_evidence.json", "VERIFIED", "A")
    # PLN plausibility: coal t per MWh (HEESI 2025 6.4.7 / 6.4.2, S1 table) -> efficiency at each NCV
    H = pd.read_csv(S1 / "HEESI_2025_VALUES_USED.csv")
    H["year"] = pd.to_numeric(H.year, errors="coerce")
    t = float(H[(H.table.str.startswith("6.4.7")) & (H.column == "Coal") & (H.year == 2019)].value.iloc[0])
    gwh = float(H[(H.table.str.startswith("6.4.2")) & (H.column == "Steam PP Coal") & (H.year == 2019)].value.iloc[0])
    rate = t / (gwh * 1e3)
    pl = [dict(ncv_label=lbl, gj_per_t=v, pln_eta=3.6 / (rate * v)) for lbl, v in
          (("v3 25.80", fID["a"]), ("UNSD 2019 24.48", fID["b"]), ("HEESI 2019 24.67", fID["c"]), ("HEESI average coal 20.29 (2023+)", 3.4554 * 3.6 / 0.6130),
           ("APEC 2022 ID 20.10", 20.096), ("IPCC sub-bituminous 18.9", fID["d"]))]
    PL = pd.DataFrame(pl)
    PL.to_csv(n / "NCV_ID_COAL_PLAUSIBILITY.csv", index=False, float_format="%.6f")
    tabs["pln"] = md(PL, {"gj_per_t": ".3f", "pln_eta": ".3f"})
    ev("pln_coal_t_2019", t, "t", "PLN coal consumption 2019 (HEESI 2025 table 6.4.7)", "S1 s1/HEESI_2025_VALUES_USED.csv", "VERIFIED", "B")
    ev("pln_coal_gwh_2019", gwh, "GWh", "PLN steam coal generation 2019 (HEESI 2025 table 6.4.2)", "S1 s1/HEESI_2025_VALUES_USED.csv", "VERIFIED", "B")
    ev("pln_t_per_mwh_2019", round(rate, 6), "t/MWh", "PLN coal rate 2019", "derived", "EXACT", "B")
    for r in PL.itertuples():
        ev(f"pln_eta_{r.ncv_label}".replace(" ", "_"), round(float(r.pln_eta), 4), "-", f"PLN coal fleet efficiency implied at NCV {r.ncv_label}", "ncv/NCV_ID_COAL_PLAUSIBILITY.csv", "INFERENCE", "C")
    # ---- reproduction ----------------------------------------------------------------------------------------------------------------
    ev("reproduction_I_byte_identical", all(chain["reproduction"]["I"]["byte_identical"].values()), "-", "unmodified copy: s3_0 outputs byte-identical", "ncv/_chain_evidence.json", "VERIFIED", "A")
    ev("reproduction_I_v3_other_max_dev_mwh", chain["reproduction"]["I"]["max_abs_dev_v3_other_mwh"], "MWh", "max |v3 other recomputed - repository| over countries and carriers",
       "ncv/_chain_evidence.json", "VERIFIED", "A")
    ev("reproduction_II_byte_identical", all(chain["reproduction"]["II"]["byte_identical"].values()), "-", "unmodified copy: m08b + s3_0 outputs byte-identical", "ncv/_chain_evidence.json", "VERIFIED", "A")
    ev("compute_seconds_chain", round(chain["timing_s"]["total"], 1), "s", "scratch-copy runs total", "ncv/_chain_evidence.json", "VERIFIED", "A")
    # ---- write -----------------------------------------------------------------------------------------------------------------------
    (n / "NCV_REPORT_TABLES.md").write_text("\n\n".join(f"### {k}\n\n{v}" for k, v in tabs.items()) + "\n", encoding="utf-8")
    meta = dict(step="V4 W11 NCV audit", instruction_sha256="30a83f0cca9111ea9c25e01c9a84a932b2a8a3affc82ab186fa7f2459d31b19a",
                status_legend="EXACT / VERIFIED / INFERENCE / PROPOSED / NOT_DERIVABLE / TRANSCRIBED", grade_legend="A actual statistics or receipt, B official / national statistics, C derived or proxy, D model estimate, E missing",
                n=len(EV))
    (a.work / "V4_NCV_EVIDENCE.json").write_text(json.dumps(dict(meta=meta, items=EV), indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(len(EV), "evidence items")
    print((n / "NCV_REPORT_TABLES.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
