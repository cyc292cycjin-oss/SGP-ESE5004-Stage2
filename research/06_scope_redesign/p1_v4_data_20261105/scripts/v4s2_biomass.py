"""V4 S2 section 3 (decision 204 item 4): the Indonesian 'fuelwood - n.e.s. industry' row of UNSD 2019 (65,253 thousand m3, 165.74 TWh before the
cement deduction, 148.54 TWh in the v2 'other' bucket) checked against FAO, HEESI and a bottom-up estimate.

    PYTHONHASHSEED=0 python scripts/v4s2_biomass.py          (WSL pypsa-earth python; scratch chain for the effect on T_v2, repository read only)

1. Definitions: UNSD commodity codes of the export (5110 fuelwood ... 5160 charcoal; SIEC 511 'fuelwood, wood residues and by-products' by code
   alignment), FAO forestry items (wood fuel is reported apart from wood residues, chips, pellets, charcoal). Every UNSD 2019 ID biomass commodity and
   transaction (households included), the upstream m3 / t -> TWh factors (pypsa-asean get_conv_factors, UNSD 2014 balance methodology) and the
   UNSD footnotes ('1' = Estimate). UNSD 2005-2022 fuelwood series against FAO wood fuel (production and trade).
2. Bottom-up 2019: pulp mills (black liquor, ETSAP 22 GJ/t; PyPSA-Eur pulp / paper biomass part), palm-oil mills (fibre and shell, section 2),
   sugar (bagasse), wood processing residues (FAOSTAT sawnwood / plywood x FAO 2001 Indonesian recovery rates x UNSD fuelwood factor; FAOSTAT
   'wood residues' production).
3. Comparison table UNSD industry biomass rows x bottom-up x HEESI x FAO.
4. Candidate values for the row (PROPOSED, not implemented) and their effect on T_v2 / 'other' 2050 on top of the combined case of section 1.
Outputs s2/ID_BIOMASS_UNSD_2019.csv, s2/ID_FUELWOOD_SERIES.csv, s2/ID_BIOMASS_COMPARISON.csv, s2/ID_FUELWOOD_OPTIONS.csv, s2/_biomass_evidence.json.
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s2_common as cm   # noqa: E402
import v4s1_common as c1   # noqa: E402

UNSD_DIR = "/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data"
FAO2001 = "research_inputs/biomass_v5/sources/FAO2001_X6966E02_mill_residues_text.txt"


def unsd_all() -> pd.DataFrame:
    rows, notes = [], {}
    for f in sorted(glob.glob(UNSD_DIR + "/*.txt")):
        txt = open(f, encoding="utf-8").read()
        body, _, foot = txt.partition('"fnSeqID";"Footnote"')
        for line in foot.strip().splitlines():
            m = re.match(r'^"(\d+)";"(.*)"$', line.strip())
            if m:
                notes[m.group(1)] = m.group(2)
        d = pd.read_csv(f, sep=";", dtype=str, nrows=None, on_bad_lines="skip")
        rows.append(d)
    d = pd.concat(rows, ignore_index=True)
    d = d[d["Country or Area"].eq("Indonesia")].copy()
    sp = d["Commodity - Transaction"].str.split(" - ", n=1, expand=True); d["commodity"], d["transaction"] = sp[0].str.strip(), sp[1].fillna("").str.strip()
    d["q"] = pd.to_numeric(d.Quantity, errors="coerce"); d["y"] = pd.to_numeric(d.Year, errors="coerce")
    d["footnote"] = d["Quantity Footnotes"].fillna("").map(lambda s: "; ".join(notes.get(x.strip(), x) for x in str(s).split(",") if x.strip()))
    return d.dropna(subset=["y"]).assign(y=lambda z: z.y.astype(int)), notes


def main():
    W = cm.WORK; out = W / "s2"; ev = cm.Ev("3")
    U, notes = unsd_all()
    ev.extra["unsd_footnote_legend"] = notes
    cf = c1.conv_factors()
    fac = {"Fuelwood": cf["Fuelwood"], "Bagasse": cf["Bagasse"], "Charcoal": cf["Charcoal"], "Biodiesel": cf["Biodiesel"], "Biogasoline": cf["Biogasoline"]}
    for k, v in fac.items():
        ev.put(f"factor.{k}", v, "TWh per thousand unit", "pypsa-asean scripts/_helpers.py get_conv_factors (comment: UNSD energy balance methodology 2014, 05.pdf; not on disk)", "VERIFIED", "B")
    ev.put("factor.Fuelwood_GJ_per_m3", cf["Fuelwood"] * 3.6e6 / 1e3, "GJ/m3", "derived from the factor", "EXACT", "B")
    bio_coms = ["Fuelwood", "Bagasse", "Black liquor", "Black Liquor", "Other vegetal material and residues", "Other Vegetal Material and Residues", "Charcoal", "Biodiesel", "Biogasoline", "Biogases", "Animal waste", "Municipal wastes", "Industrial Waste"]
    b19 = U[U.commodity.isin(bio_coms) & U.y.eq(2019)].copy()
    b19["twh"] = [r.q * fac.get(r.commodity, np.nan) / 1e3 if r.commodity in fac else (r.q / 3600.0 if r.Unit == "Terajoules" else np.nan) for r in b19.itertuples()]
    b19[["commodity", "transaction", "Unit", "q", "twh", "footnote"]].to_csv(out / "ID_BIOMASS_UNSD_2019.csv", index=False, float_format="%.6g")
    present = sorted(b19.commodity.unique())
    ev.put("unsd2019.commodities_present", ";".join(present), "-", "UNdata export 2025-05-02, Indonesia 2019", "VERIFIED", "B")
    ev.put("unsd2019.black_liquor_reported", int(b19.commodity.str.lower().eq("black liquor").any()), "0/1", "UNdata export", "VERIFIED", "B")
    ev.put("unsd2019.other_vegetal_reported", int(b19.commodity.str.lower().str.startswith("other vegetal").any()), "0/1", "UNdata export", "VERIFIED", "B")
    for r in b19.itertuples():
        ev.put(f"unsd2019.{r.commodity}.{r.transaction}", r.q, r.Unit, f"UNdata export 2025-05-02{' (footnote: ' + r.footnote + ')' if r.footnote else ''}", "VERIFIED", "C" if r.footnote else "B")
    # ---- fuelwood series and FAO
    FO = cm.fao("FO")
    fw = U[U.commodity.eq("Fuelwood") & U.y.between(2005, 2022)].pivot_table(index="y", columns="transaction", values="q", aggfunc="first")
    fwn = U[U.commodity.eq("Fuelwood") & U.y.between(2005, 2022)].pivot_table(index="y", columns="transaction", values="footnote", aggfunc="first")
    S = pd.DataFrame(index=fw.index)
    for k, t in (("production", "Production"), ("imports", "Imports"), ("exports", "Exports"), ("charcoal_plants", "Transformation in charcoal plants"),
                 ("final_consumption", "Final energy consumption"), ("industry_nes", "Consumption not elsewhere specified (industry)"), ("households", "Consumption by households")):
        S[f"unsd_{k}_km3"] = fw.get(t)
    S["unsd_industry_nes_footnote"] = fwn.get("Consumption not elsewhere specified (industry)")
    wf = cm.series(FO, "Indonesia", "Wood fuel, non-coniferous").set_index("year")
    wfi = cm.series(FO, "Indonesia", "Wood fuel, non-coniferous", "Import quantity").set_index("year"); wfe = cm.series(FO, "Indonesia", "Wood fuel, non-coniferous", "Export quantity").set_index("year")
    S["fao_wood_fuel_km3"] = [float(wf.at[y, "value"]) / 1e3 if y in wf.index else np.nan for y in S.index]
    S["fao_wood_fuel_flag"] = [wf.at[y, "flag"] if y in wf.index else "" for y in S.index]
    S["fao_wood_fuel_imports_km3"] = [float(wfi.at[y, "value"]) / 1e3 if y in wfi.index else np.nan for y in S.index]
    S["fao_wood_fuel_exports_km3"] = [float(wfe.at[y, "value"]) / 1e3 if y in wfe.index else np.nan for y in S.index]
    S["unsd_production_over_fao"] = S.unsd_production_km3 / S.fao_wood_fuel_km3
    S["unsd_industry_share_of_final"] = S.unsd_industry_nes_km3 / S.unsd_final_consumption_km3
    S.index.name = "year"; S.reset_index().to_csv(out / "ID_FUELWOOD_SERIES.csv", index=False, float_format="%.6g")
    pre = S.loc[2010:2017, "unsd_industry_nes_km3"].mean(); post = S.loc[2020:2021, "unsd_industry_nes_km3"].mean()
    for y in (2017, 2018, 2019, 2020, 2021, 2022):
        for k in ("unsd_industry_nes_km3", "unsd_households_km3", "unsd_final_consumption_km3", "unsd_production_km3", "unsd_imports_km3", "unsd_exports_km3", "fao_wood_fuel_km3"):
            v = S.at[y, k]
            if pd.notna(v):
                ev.put(f"series.{y}.{k}", float(v), "thousand m3", "UNdata export / FAOSTAT FO", "VERIFIED", "C" if "unsd" in k else "C")
    ev.put("series.industry_mean_2010_2017_km3", pre, "thousand m3", "UNSD ID fuelwood n.e.s. industry, mean 2010-2017 (before the 2018 break)", "EXACT", "C")
    ev.put("series.industry_mean_2020_2021_km3", post, "thousand m3", "UNSD, mean 2020-2021", "EXACT", "C")
    d_ind = S.at[2018, "unsd_industry_nes_km3"] - S.at[2017, "unsd_industry_nes_km3"]; d_hh = S.at[2018, "unsd_households_km3"] - S.at[2017, "unsd_households_km3"]
    ev.put("series.2017_2018.delta_industry_km3", d_ind, "thousand m3", "UNSD", "EXACT", "C")
    ev.put("series.2017_2018.delta_households_km3", d_hh, "thousand m3", "UNSD", "EXACT", "C")
    ev.put("series.2017_2018.delta_final_km3", S.at[2018, "unsd_final_consumption_km3"] - S.at[2017, "unsd_final_consumption_km3"], "thousand m3", "UNSD", "EXACT", "C")
    ev.put("series.2019.unsd_production_over_fao", S.at[2019, "unsd_production_over_fao"], "-", "UNSD fuelwood production / FAO wood fuel production", "EXACT", "C")
    # FAO other wood-energy items 2019
    for it in ("Wood residues", "Wood chips and particles", "Wood pellets", "Wood charcoal", "Wood briquettes and other agglomerates"):
        for el in ("Production", "Import quantity", "Export quantity"):
            v, f = cm.value(FO, "Indonesia", it, 2019, el)
            ev.put(f"fao2019.{it}.{el}", v, cm.series(FO, "Indonesia", it, el).Unit.iloc[0], f"FAOSTAT FO flag {f}", "VERIFIED", cm.FLAG_GRADE.get(f, "C"))
    # ---- HEESI 2019
    r33 = c1.heesi_year_rows(W, 46, "2019")[0]
    heesi = dict(traditional_biomass_kboe=r33[0], industrial_biomass_kboe=r33[1])
    H = c1.heesi_values(W); boe = c1.boe_gj(H)
    txt = (W / c1.HEESI_DIR / "p170.txt").read_text(encoding="utf-8")
    fw_boe = float(re.search(r"^\s*Firewood\s+Ton\s+([\d.]+)", txt, re.M).group(1))
    ev.put("heesi.firewood_boe_per_t", fw_boe, "BOE/t", "HEESI 2025 Annex 03 (PDF p.170)", "VERIFIED", "B")
    ev.put("heesi.boe_gj", boe, "GJ/BOE", "S1: Annex 03 electric power 0.6130 BOE/MWh", "INFERENCE", "B")
    for k, v in heesi.items():
        ev.put(f"heesi.2019.{k}", v, "thousand BOE", "HEESI 2025 table 3.3 (PDF p.46)", "VERIFIED", "B")
        ev.put(f"heesi.2019.{k}_twh", v * boe / 3600.0, "TWh", "thousand BOE x 5.873 GJ/BOE", "INFERENCE", "B")
    # ---- bottom-up 2019
    P = json.loads((W / "s2/_products_evidence.json").read_text())
    pv = {r["key"]: r["value"] for r in P["numbers"]}
    fao_txt = (cm.REPO / FAO2001).read_text(encoding="utf-8")
    rec = {}
    for mill in ("Sawmill", "Plywood mill"):
        m = re.search(rf"^\s*{mill}\s*\|\s*(\d+)\s*\|\s*Indonesia\s*\|\s*IUFRO, 1992", fao_txt, re.M)
        rec[mill] = float(m.group(1)) / 100.0
    sawn, fs = cm.value(FO, "Indonesia", "Sawnwood, non-coniferous", 2019); ply, fp = cm.value(FO, "Indonesia", "Plywood and LVL", 2019)
    res_m3 = sawn * (1 / rec["Sawmill"] - 1) + ply * (1 / rec["Plywood mill"] - 1)
    wr_m3 = cm.value(FO, "Indonesia", "Wood residues", 2019)[0]
    f_fw = cf["Fuelwood"] / 1e3   # TWh per m3
    BU = [dict(block="pulp mills", item="black liquor of chemical + dissolving pulp (ETSAP 22 GJ/t pulp)", low_twh=pv["2.pp.2019.black_liquor_etsap"], high_twh=pv["2.pp.2019.black_liquor_etsap"],
               source="s2/ID_PULP_PAPER_ENERGY.csv; V4_PRODUCT_ROUTE_MAP.csv note", grade="C", in_unsd_2019="no item (no black liquor for ID)"),
          dict(block="pulp mills", item="PyPSA-Eur pulp/paper biomass part on FAOSTAT 2019 (EU27 structure; use, not generation)", low_twh=pv["2.pp.2019.biomass_part"], high_twh=pv["2.pp.2019.biomass_part"],
               source="s2/ID_PULP_PAPER_ENERGY.csv", grade="C", in_unsd_2019="unknown (would be fuelwood or black liquor)"),
          dict(block="palm-oil mills", item="mesocarp fibre (low) + palm kernel shell (high), 15 GJ/t", low_twh=pv["2.palm.2019.mill_fuel_low_twh"], high_twh=pv["2.palm.2019.mill_fuel_high_twh"],
               source="s2/ID_SUGAR_PALM_CHECK.csv (FFB x IRENA 2022 Box 4)", grade="C", in_unsd_2019="no item (no 'other vegetal material' for ID)"),
          dict(block="sugar mills", item="bagasse (UNSD reported) / FAOSTAT cane x 0.2 x 7.72 GJ/t", low_twh=pv["2.sugar.2019.irena_bagasse_t"] / 1e3 * cf["Bagasse"], high_twh=pv["2.sugar.2019.unsd_bagasse_twh"],
               source="UNSD / IRENA 2017 Table R3", grade="B", in_unsd_2019="yes (bagasse 6,964.7 kt)"),
          dict(block="wood industries", item="FAOSTAT 'wood residues' production (low) / sawnwood + plywood residues at FAO 2001 Indonesian recovery rates (high), 9.144 GJ/m3",
               low_twh=wr_m3 * f_fw, high_twh=res_m3 * f_fw, source=f"FAOSTAT FO 2019 (sawnwood {sawn:.0f} m3 {fs}, plywood {ply:.0f} m3 {fp}); FAO 2001 Table 9 (IUFRO 1992: sawmill {rec['Sawmill']:.2f}, plywood {rec['Plywood mill']:.2f})",
               grade="C/D", in_unsd_2019="possibly in fuelwood (SIEC 511 includes wood residues)")]
    B = pd.DataFrame(BU)
    ev.put("bottomup.wood_residues_m3", res_m3, "m3", "sawnwood x (1/0.46 - 1) + plywood x (1/0.50 - 1)", "INFERENCE", "C")
    for r in B.itertuples():
        ev.put(f"bottomup.{r.block}.{r.item[:40]}.low", r.low_twh, "TWh", r.source, "INFERENCE", r.grade)
        ev.put(f"bottomup.{r.block}.{r.item[:40]}.high", r.high_twh, "TWh", r.source, "INFERENCE", r.grade)
    # ---- comparison table
    g = lambda c, t: float(b19[(b19.commodity == c) & (b19.transaction == t)].q.iloc[0])
    fw_ind = g("Fuelwood", "Consumption not elsewhere specified (industry)")
    C = [dict(source="UNSD 2019", item="fuelwood, n.e.s. industry (footnote: Estimate)", quantity=fw_ind, unit="thousand m3", twh=fw_ind * f_fw * 1e3, scope="industry",
              comment="2005-2017 flat ~29-30 thousand m3 x 10^3; 2018-2019 doubled while households halved; 2020-2021 ~35"),
         dict(source="UNSD 2019", item="fuelwood, chemical industry", quantity=g("Fuelwood", "Consumption by chemical and petrochemical"), unit="thousand m3",
              twh=g("Fuelwood", "Consumption by chemical and petrochemical") * f_fw * 1e3, scope="industry", comment="UNSD chemicals row"),
         dict(source="UNSD 2019", item="bagasse, n.e.s. industry", quantity=g("Bagasse", "Consumption not elsewhere specified (industry)"), unit="thousand t",
              twh=g("Bagasse", "Consumption not elsewhere specified (industry)") * cf["Bagasse"], scope="industry", comment="matches cane x 0.19-0.31 t/t (section 2)"),
         dict(source="UNSD 2019", item="charcoal, n.e.s. industry", quantity=g("Charcoal", "Consumption not elsewhere specified (industry)"), unit="thousand t",
              twh=g("Charcoal", "Consumption not elsewhere specified (industry)") * cf["Charcoal"], scope="industry", comment=""),
         dict(source="UNSD 2019", item="biodiesel, n.e.s. industry", quantity=g("Biodiesel", "Consumption not elsewhere specified (industry)"), unit="thousand t",
              twh=g("Biodiesel", "Consumption not elsewhere specified (industry)") * cf["Biodiesel"], scope="industry", comment=""),
         dict(source="UNSD 2019", item="fuelwood, households", quantity=g("Fuelwood", "Consumption by households"), unit="thousand m3", twh=g("Fuelwood", "Consumption by households") * f_fw * 1e3,
              scope="households", comment="75 (2017) -> 35.6 (2018) thousand m3 x 10^3"),
         dict(source="UNSD 2019", item="fuelwood, total final consumption", quantity=g("Fuelwood", "Final energy consumption"), unit="thousand m3", twh=g("Fuelwood", "Final energy consumption") * f_fw * 1e3,
              scope="all", comment="+ 10,764 to charcoal plants"),
         dict(source="UNSD 2019", item="fuelwood, imports / exports", quantity=g("Fuelwood", "Imports"), unit="thousand m3", twh=g("Fuelwood", "Imports") * f_fw * 1e3, scope="trade",
              comment=f"exports {g('Fuelwood', 'Exports'):.0f}; only 2018-2019 reported; FAO wood fuel trade 2019 < 1 thousand m3"),
         dict(source="FAOSTAT FO 2019", item="wood fuel, non-coniferous, production (E)", quantity=float(S.at[2019, "fao_wood_fuel_km3"]), unit="thousand m3",
              twh=float(S.at[2019, "fao_wood_fuel_km3"]) * f_fw * 1e3, scope="all (roundwood used as fuel)", comment="FAO lists wood residues, chips, pellets, charcoal as separate items"),
         dict(source="FAOSTAT FO 2019", item="wood residues, production (I)", quantity=wr_m3 / 1e3, unit="thousand m3", twh=wr_m3 * f_fw, scope="supply", comment=""),
         dict(source="HEESI 2025", item="industrial biomass 2019 (table 3.3)", quantity=heesi["industrial_biomass_kboe"], unit="thousand BOE", twh=heesi["industrial_biomass_kboe"] * boe / 3600.0,
              scope="industry (traded biomass)", comment="2023 20,452 / 2024 53,147 thousand BOE"),
         dict(source="HEESI 2025", item="traditional biomass 2019 (table 3.3, estimate)", quantity=heesi["traditional_biomass_kboe"], unit="thousand BOE", twh=heesi["traditional_biomass_kboe"] * boe / 3600.0,
              scope="households", comment=""),
         ] + [dict(source="bottom-up 2019", item=f"{r.block}: {r.item}", quantity=np.nan, unit="", twh=r.low_twh, twh_high=r.high_twh, scope="industry (self-generated residues)", comment=r.in_unsd_2019)
              for r in B.itertuples()]
    CO = pd.DataFrame(C); CO.to_csv(out / "ID_BIOMASS_COMPARISON.csv", index=False, float_format="%.6g")
    for r in CO.itertuples():
        ev.put(f"compare.{r.source}.{r.item[:60]}", r.twh, "TWh", "s2/ID_BIOMASS_COMPARISON.csv", "VERIFIED" if r.source != "bottom-up 2019" else "INFERENCE", "B" if r.source == "HEESI 2025" else "C")
    # ---- candidate values and their effect on T_v2 / other (scratch chain, on top of the combined case)
    import v4s2_chain as chn
    R = chn.Runner(); R.reproduce()
    base_all = R.scenario("all (1-5)", b="central", ni="nf2023", cem=True, steel=True, prod=True)
    cand = [("UNSD 2019 (status quo)", fw_ind), ("UNSD mean 2020-2021", post), ("UNSD mean 2010-2017 (before the 2018 break)", pre),
            ("HEESI industrial biomass 2019 (traded only), firewood 2.2979 BOE/t", None)]
    O = []
    for lab, km3 in cand:
        if km3 is None:
            new_twh = heesi["industrial_biomass_kboe"] * boe / 3600.0
        else:
            new_twh = km3 * f_fw * 1e3
        d = fw_ind * f_fw * 1e3 - new_twh
        r = R.scenario(f"all + fuelwood: {lab}", b="central", ni="nf2023", cem=True, steel=True, prod=True, extra_moves=[("other", "biomass", d * 1e6)]) if d > 0 else base_all
        r0 = R.scenario(f"v3 + fuelwood: {lab}", extra_moves=[("other", "biomass", d * 1e6)]) if d > 0 else R.scenario("v3")
        O.append(dict(candidate=lab, row_km3=(km3 if km3 is not None else np.nan), row_twh_2019=new_twh, delta_2019_twh=-d,
                      all_T_2050_twh=r["T_2050_twh"], all_other_2050_twh=r["other_2050_twh"], all_other_share=r["other_share"],
                      v3_T_2050_twh=r0["T_2050_twh"], v3_other_2050_twh=r0["other_2050_twh"], v3_other_share=r0["other_share"]))
    R.ch.restore(); R.ch.unpatch()
    OP = pd.DataFrame(O); OP.to_csv(out / "ID_FUELWOOD_OPTIONS.csv", index=False, float_format="%.6f")
    for r in OP.itertuples():
        for k in ("row_twh_2019", "delta_2019_twh", "all_T_2050_twh", "all_other_2050_twh", "all_other_share", "v3_other_2050_twh", "v3_other_share"):
            ev.put(f"option.{r.candidate}.{k}", getattr(r, k), "-" if k.endswith("share") else "TWh", "s2/ID_FUELWOOD_OPTIONS.csv (scratch chain)", "PROPOSED (quantified)", "C")
    ev.write(out / "_biomass_evidence.json")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30); pd.set_option("display.max_colwidth", 70)
    print(b19[["commodity", "transaction", "q", "twh", "footnote"]].to_string())
    print(S.round(2).to_string())
    print(B.round(2).to_string()); print(CO[["source", "item", "quantity", "unit", "twh"]].round(2).to_string()); print(OP.round(3).to_string())
    print("heesi", heesi, "boe", boe, "rec", rec, "pre", pre, "post", post)


if __name__ == "__main__":
    main()
