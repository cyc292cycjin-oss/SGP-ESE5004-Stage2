"""V4 S2 section 5: captive-power screening for the 11 ASEAN countries (read only, for the W07 extension).

    PYTHONHASHSEED=0 python scripts/v4s2_captive_screen.py          (WSL pypsa-earth python)

The S1 section 1.2 inequality per country, UNSD 2019: autoproducer electricity from combustible fuels against the fuel recorded in the
autoproducer transformation rows, converted with the pypsa-asean factors (gas and biogas in TJ / 3,600) and turned into the most electricity
it could give at technology-data v0.15.0 2050 efficiencies (upper bounds for 2019 plants: coal 0.356, lignite 0.33, gas CCGT 0.60, oil 0.35,
solid biomass 0.468, biogas at OCGT 0.43) and at 100 % (EXACT bound). Output above the bound = fuel recorded elsewhere, most likely in industry
final consumption (INFERENCE). Context: UNSD 2019 industry coal of the D1 base and the v3 'other' bucket coal, GEM GIPT 2026-09 captive coal
capacity at the end of 2019 ('Captive Industry Type' field; S1 operating rule). Screening only: nothing is estimated or changed.
Outputs s2/ASEAN11_AUTOPRODUCER_FUEL_2019.csv, s2/ASEAN11_CAPTIVE_SCREEN.csv, s2/_captive_screen_evidence.json.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402
import v4s1_common as c1   # noqa: E402

ISO = {"Brunei Darussalam": "BN", "Cambodia": "KH", "Indonesia": "ID", "Lao People's Dem. Rep.": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH",
       "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Viet Nam": "VN"}
GROUP = {"Hard coal": ("coal", "Hard coal"), "Hrad coal": ("coal", "Hard coal"), "Brown coal": ("lignite", "Brown coal"), "Lignite": ("lignite", "Brown coal"),
         "Natural Gas (including LNG)": ("gas", "TJ"), "Natural gas (including LNG)": ("gas", "TJ"), "Natural gas": ("gas", "TJ"), "Gas Oil/ Diesel Oil": ("oil", "Gas Oil/ Diesel Oil"),
         "Fuel oil": ("oil", "Fuel oil"), "Refinery Gas": ("oil", "Refinery Gas"), "Refinery gas": ("oil", "Refinery Gas"), "Bagasse": ("solid biomass", "Bagasse"),
         "Fuelwood": ("solid biomass", "Fuelwood"), "Biogases": ("biogas", "TJ")}
ETA_TECH = {"coal": "coal", "lignite": "lignite", "gas": "CCGT", "oil": "oil", "solid biomass": "biomass", "biogas": "OCGT"}


def main():
    W = cm.WORK; out = W / "s2"; ev = cm.Ev("5")
    cf = c1.conv_factors()
    td = pd.read_csv(cm.REPO / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020.csv")
    eta = {k: float(td[(td.technology == t) & (td.parameter == "efficiency")].value.iloc[0]) for k, t in ETA_TECH.items()}
    for k, v in eta.items():
        ev.put(f"eta.{k}", v, "-", f"technology-data v0.15.0 2050 efficiency of '{ETA_TECH[k]}' (upper bound for 2019 plants)", "VERIFIED", "B")
    d = pd.concat((pd.read_csv(f, sep=";", dtype=str, on_bad_lines="skip") for f in sorted(glob.glob(str(c1.UNSD_DIR / "*.txt")))), ignore_index=True)
    d = d[d.Year.eq("2019") & d["Country or Area"].isin(ISO)].copy()
    sp = d["Commodity - Transaction"].str.split(" - ", n=1, expand=True); d["commodity"], d["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    d["q"] = pd.to_numeric(d.Quantity, errors="coerce"); d["iso"] = d["Country or Area"].map(ISO)
    fin = d[d.transaction.str.lower().str.contains("autoproducer") & d.transaction.str.lower().str.contains("transformation") & d.commodity.isin(GROUP)].copy()
    fin["fuel"] = fin.commodity.map(lambda c: GROUP[c][0]); fin["key"] = fin.commodity.map(lambda c: GROUP[c][1])
    fin["twh"] = [r.q / 3600.0 if r.key == "TJ" else r.q * cf[r.key] for r in fin.itertuples()]   # cf: TWh per thousand t (or thousand m3)
    fin = fin.sort_values(["iso", "fuel", "commodity"])
    # duplicated commodity names for the same quantity (e.g. BN 'Brown coal' and 'Lignite' 341.064 kt): keep one per (iso, key, quantity)
    fin["dup"] = fin.duplicated(subset=["iso", "key", "q"], keep="first")
    fin[["iso", "commodity", "transaction", "Unit", "q", "fuel", "twh", "dup"]].to_csv(out / "ASEAN11_AUTOPRODUCER_FUEL_2019.csv", index=False, float_format="%.6g")
    fu = fin[~fin.dup]
    g = pd.read_csv(cm.REPO / "research_inputs/registry_v5/sources/GEM_GIPT_2026-09_ASEAN11.csv", low_memory=False)
    g["sy"] = pd.to_numeric(g["Start year"], errors="coerce"); g["ry"] = pd.to_numeric(g["Retired year"], errors="coerce")
    g["op19"] = g.Status.isin(["operating", "retired", "mothballed"]) & (g.sy <= 2019) & ~(g.ry <= 2019)
    capt = g[g["Captive Industry Type"].notna()]
    cache = json.loads((cm.REPO / cm.CACHE_REL).read_text())
    ob = pd.read_csv(cm.REPO / "research_inputs/demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[ob["mode"] == "aeo8_ats_anchor"].set_index("country")
    d1 = pd.read_csv(cm.REPO / cm.D1_REL, keep_default_na=False); d1 = d1[d1.sector == "Industry"]
    rows = []
    for name, iso in ISO.items():
        z = d[d.iso == iso]
        val = lambda com, tr: float(z[(z.commodity == com) & (z.transaction == tr)].q.sum()) if len(z[(z.commodity == com) & (z.transaction == tr)]) else np.nan
        prod_all = val("Electricity", "total production, autoproducer")
        prod_comb = float(z[z.commodity.eq("From combustible fuels – Autoproducer")].q.sum()) if z.commodity.eq("From combustible fuels – Autoproducer").any() else np.nan
        cap = val("Electricity", "total net installed capacity of electric power plants, autoproducer")
        f = fu[fu.iso == iso]
        fuel_twh = float(f.twh.sum()); bound_eta = float(sum(r.twh * eta[r.fuel] for r in f.itertuples())) * 1e3   # GWh
        bound_100 = fuel_twh * 1e3
        rec = [r for r in cache["records"] if r["country"] == iso and r["carrier"] == "coal"]
        ind_coal = sum(float(v) for k, v in rec[0].items() if k not in ("country", "carrier")) / 1e6 if rec else 0.0
        oth_coal = float(ob.at[iso, "other_2019_coal_mwh"]) / 1e6 if iso in ob.index else 0.0
        e19 = float(d1[d1.country == iso].base_2019_mwh.astype(float).sum()) / 1e6
        gc = capt[(capt.iso == iso) & capt.Type.eq("coal")]; ga = capt[capt.iso == iso]
        c19 = float(gc[gc.op19]["Capacity (MW)"].sum()); a19 = float(ga[ga.op19]["Capacity (MW)"].sum())
        types = "; ".join(f"{t} {v:,.0f}" for t, v in gc[gc.op19].groupby("Captive Industry Type")["Capacity (MW)"].sum().sort_values(ascending=False).items())
        resid = prod_comb - bound_eta if pd.notna(prod_comb) else np.nan
        if pd.isna(prod_comb):
            verdict = "no autoproducer rows in UNSD 2019: inequality not testable"
        elif prod_comb > bound_100:
            verdict = "output > fuel at 100 % (EXACT): fuel recorded elsewhere"
        elif prod_comb > bound_eta:
            verdict = "output > fuel at technology-data efficiency (INFERENCE): part of the fuel recorded elsewhere"
        else:
            verdict = "inequality not violated"
        rows.append(dict(iso=iso, autoproducer_production_gwh=prod_all, autoproducer_combustible_gwh=prod_comb, autoproducer_capacity_mw=cap,
                         fuel_in_transformation_twh=fuel_twh, fuels=";".join(f"{r.commodity} {r.q:,.1f} {r.Unit.split(',')[0]}" for r in f.itertuples()),
                         max_gen_at_tech_eff_gwh=bound_eta, max_gen_at_100pct_gwh=bound_100, implied_efficiency=(prod_comb / bound_100 if bound_100 > 0 and pd.notna(prod_comb) else np.nan),
                         unexplained_gen_gwh=resid, verdict=verdict, industry_coal_2019_twh=ind_coal, other_bucket_coal_2019_twh=oth_coal, industry_2019_twh=e19,
                         gipt_captive_coal_2019_mw=c19, gipt_captive_coal_types_2019=types, gipt_captive_all_2019_mw=a19,
                         gipt_captive_coal_2026_operating_mw=float(gc[gc.Status.eq("operating")]["Capacity (MW)"].sum()),
                         hours_if_unexplained_were_captive_coal=(resid / c19 * 1e3 if c19 > 0 and pd.notna(resid) and 0 < resid / c19 * 1e3 <= 8760 else np.nan),
                         hours_note=("> 8,760 h: the unexplained output cannot be captive coal alone (gas / biomass autoproducers, INFERENCE)" if c19 > 0 and pd.notna(resid) and resid / c19 * 1e3 > 8760 else "")))
    S = pd.DataFrame(rows)

    def advice(r):
        if r.iso == "ID":
            return "done in S1 (option b quantified, decision 204 item 1)"
        if r.verdict.startswith("output > fuel at 100") or (r.verdict.startswith("output > fuel at technology") and r.gipt_captive_coal_2019_mw > 0):
            return "extend in W07: estimate the captive fuel left in industry (S1 method)"
        if r.gipt_captive_coal_2019_mw > 100:
            return "check in W07: GIPT captive coal exists although the inequality holds or is not testable"
        if r.verdict.startswith("output > fuel at technology"):
            return "check in W07: small gap, likely gas / oil efficiency"
        return "no action from this screen"
    S["advice_w07"] = S.apply(advice, axis=1)
    S.to_csv(out / "ASEAN11_CAPTIVE_SCREEN.csv", index=False, float_format="%.6g")
    for r in S.itertuples():
        for k in ("autoproducer_production_gwh", "autoproducer_combustible_gwh", "autoproducer_capacity_mw", "fuel_in_transformation_twh", "max_gen_at_tech_eff_gwh", "max_gen_at_100pct_gwh",
                  "implied_efficiency", "unexplained_gen_gwh", "industry_coal_2019_twh", "other_bucket_coal_2019_twh", "gipt_captive_coal_2019_mw", "gipt_captive_all_2019_mw",
                  "gipt_captive_coal_2026_operating_mw", "hours_if_unexplained_were_captive_coal"):
            v = getattr(r, k)
            if pd.notna(v):
                ev.put(f"{r.iso}.{k}", v, k.split("_")[-1], "UNdata export 2025-05-02 / GEM GIPT 2026-09 / repository D1 tables",
                       "VERIFIED" if k in ("autoproducer_production_gwh", "autoproducer_combustible_gwh", "autoproducer_capacity_mw", "gipt_captive_coal_2019_mw", "gipt_captive_all_2019_mw",
                                           "gipt_captive_coal_2026_operating_mw", "industry_coal_2019_twh", "other_bucket_coal_2019_twh") else ("EXACT" if k in ("max_gen_at_100pct_gwh", "fuel_in_transformation_twh") else "INFERENCE"),
                       "B" if k.startswith(("autoproducer", "gipt", "fuel", "industry", "other")) else "C")
        ev.put(f"{r.iso}.verdict", r.verdict, "-", "s2/ASEAN11_CAPTIVE_SCREEN.csv", "EXACT" if "EXACT" in r.verdict else "INFERENCE", "B")
        ev.put(f"{r.iso}.advice_w07", r.advice_w07, "-", "s2/ASEAN11_CAPTIVE_SCREEN.csv", "PROPOSED", "-")
    ev.write(out / "_captive_screen_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 60)
    print(S.drop(columns=["fuels"]).round(2).T.to_string())


if __name__ == "__main__":
    main()
