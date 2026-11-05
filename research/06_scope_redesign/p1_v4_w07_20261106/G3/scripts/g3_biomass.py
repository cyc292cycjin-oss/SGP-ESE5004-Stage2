"""G3 biomass definitions (decision 206 items 1 and 3; S2 method template step 7) for TH, PH, SG.

    PYTHONHASHSEED=0 python scripts/g3_biomass.py          (WSL pypsa-earth python)

Per country: every UNSD biomass commodity (fuelwood 5110, bagasse 5120, black liquor 5140, other vegetal material 5150, charcoal 5160, biogas,
animal waste, liquid biofuels) by flow in 2019 (UNdata export used by the model; SDMX 2015-2022 of g3_sdmx.py for the newer vintage and for 5150,
which the export does not carry), footnote 'Estimate', 2005-2022 series with the 2017->2018 and 2021->2022 changes of industry against households,
and FAOSTAT cross-checks (wood fuel, sugar cane x residue factor, chemical pulp x 22 GJ/t black liquor). Closed-loop rule (206 item 3): self-produced
residues and their heat stay outside T_v2; whether UNSD reports 5140 / 5150 and where.
Outputs <CC>_BIOMASS_CHECK.csv, tables/<CC>_BIOMASS_SERIES.csv, tables/_biomass_evidence.json. Read only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import g3_common as cm   # noqa: E402

COMS = ["Fuelwood", "Bagasse", "Black Liquor", "Charcoal", "Biogases", "Animal waste", "Biodiesel", "Biogasoline", "Other vegetal material and residues"]
IND = "Manufacturing,const.,mining"


def main():
    ev = cm.Ev("biomass"); out = cm.G3 / "tables"
    X = cm.unsd_export(); X["commodity"] = X.commodity.replace({"Black liquor": "Black Liquor"})
    X = X[X.commodity.isin(COMS)].copy()
    sd = pd.read_csv(out / "SDMX_OBS_TH_PH_SG.csv", dtype=str, keep_default_na=False)
    for c_ in ("year", "value", "conversion_factor"):
        sd[c_] = pd.to_numeric(sd[c_].replace("", None), errors="coerce")
    FO, QCL = cm.fao("FO"), cm.fao("QCL")
    conv = cm.upstream_conv()
    for cc in cm.CC3:
        z = X[X.country == cc]
        z = z.assign(tr=z.transaction.str.lower()).drop_duplicates(["commodity", "tr", "year", "q"])
        ser = z[z.year.between(2005, 2022)].pivot_table(index=["commodity", "transaction"], columns="year", values="q", aggfunc="first")
        s5 = sd[(sd.cc == cc) & sd.commodity_code.isin(["5110", "5120", "5140", "5150", "5160"])].pivot_table(index=["commodity", "transaction"], columns="year", values="value", aggfunc="first")
        s5.index = pd.MultiIndex.from_tuples([(f"SDMX {a}", b) for a, b in s5.index])
        pd.concat([ser, s5]).to_csv(out / f"{cc}_BIOMASS_SERIES.csv", float_format="%.3f")
        z19 = z[z.year == 2019]
        rows = []

        def get(com, flow_pred):
            w = z19[(z19.commodity == com) & z19.transaction.str.lower().str.contains(flow_pred)]
            return (float(w.q.max()), ";".join(sorted(set(w["Quantity Footnotes"].astype(str)) - {""}))) if len(w) else (np.nan, "")

        def series_note(com, flow_pred):
            w = z[(z.commodity == com) & z.transaction.str.lower().str.contains(flow_pred)].groupby("year").q.max()
            d = []
            for a, b in ((2017, 2018), (2021, 2022)):
                if a in w.index and b in w.index and w[a] != 0:
                    d.append(f"{a}->{b} {w[a]:,.0f}->{w[b]:,.0f} ({(w[b] / w[a] - 1) * 100:+.0f} %)")
            return "; ".join(d) if d else "no 2017-18 / 2021-22 pair in the export"

        def sdmx(code, tr):
            w = sd[(sd.cc == cc) & (sd.commodity_code == code) & (sd.transaction_code == tr) & (sd.year == 2019)]
            return float(w.value.iloc[0]) if len(w) else np.nan

        if cc == "TH":
            cane = cm.series(QCL, "Thailand", "Sugar cane").set_index("year").value
            bag_p = z[(z.commodity == "Bagasse") & (z.transaction.str.lower() == "production")].groupby("year").q.max()
            sb = sd[(sd.cc == "TH") & (sd.commodity_code == "5120") & (sd.transaction_code == "01")].set_index("year").value
            ratio = {y: (bag_p.get(y, np.nan) * 1e3 / cane[y], sb.get(y, np.nan) * 1e3 / cane[y]) for y in range(2015, 2023) if y in cane.index}
            ind_b, fn_b = get("Bagasse", "manufacturing")
            fw_ind, fn_fw = get("Fuelwood", "manufacturing"); fw_hh, _ = get("Fuelwood", "households"); fw_p, _ = get("Fuelwood", "^production")
            fao_fw = float(cm.series(FO, "Thailand", "Wood fuel, non-coniferous").set_index("year").value[2019])
            pulp = sum(float(cm.series(FO, "Thailand", it).set_index("year").value.get(2019, 0.0)) for it in ("Chemical wood pulp", "Dissolving wood pulp"))
            bl_tj = sdmx("5140", "08812")
            v5150 = {k: sdmx("5150", t) for k, t in (("industry", "121"), ("food", "1214F"), ("paper", "1214G"), ("nmm", "1214B"), ("chemical", "1213"), ("wood", "1214H"),
                                                           ("textile", "1214J"), ("power", "08811"), ("households", "1231"))}
            bg_ind, _ = get("Biogases", "manufacturing")
            rows += [
                dict(commodity="Bagasse (5120)", flow="industry: food and tobacco (+ chemical 30 kt)", value_2019=f"{ind_b:,.1f} kt = {ind_b * conv['Bagasse']:.2f} TWh (export); SDMX {sdmx('5120', '1214F'):,.0f} kt",
                     series_note=series_note("Bagasse", "manufacturing") + f"; SDMX industry 2017->2018 14,517->23,943 kt with cane 93.1->135.1 Mt",
                     faostat_compare="bagasse production / FAOSTAT cane (export; SDMX): " + "; ".join(f"{y} {a:.3f}/{b:.3f}" for y, (a, b) in ratio.items()) + " (IRENA 2017 factor 0.2; wet basis 0.28-0.30 typical, INFERENCE)",
                     proposed_main="closed loop: sugar-mill bagasse and its heat demand leave T_v2 (step 8)", proposed_sensitivity="keep in T_v2 (v3)"),
                dict(commodity="Bagasse (5120)", flow="transformation: main-activity electricity plants", value_2019="24,344 kt (export); SDMX 26,835 kt", series_note="power use, outside T_v2",
                     faostat_compare="-", proposed_main="no change (outside T_v2)", proposed_sensitivity="-"),
                dict(commodity="Biogases", flow="industry (food 19,940, chemical 5,500, paper 120, NMM 40 TJ)", value_2019=f"{bg_ind:,.0f} TJ = {bg_ind / 3600:.2f} TWh", series_note=series_note("Biogases", "manufacturing"),
                     faostat_compare="cassava 31.1 Mt, oil palm fruit 16.4 Mt (FAOSTAT 2019): wastewater biogas of starch and palm mills (INFERENCE)",
                     proposed_main="keep (not named in rule 206 item 3)", proposed_sensitivity="closed loop: out of T_v2 with bagasse"),
                dict(commodity="Fuelwood (5110)", flow="industry (food 737, NMM 106, n.e.s. 36, paper 33, wood 33, chemical 17, textile 14 thousand m3)",
                     value_2019=f"{fw_ind:,.1f} thousand m3 = {fw_ind * conv['Fuelwood']:.2f} TWh; households {fw_hh:,.0f}",
                     series_note=series_note("Fuelwood", "manufacturing") + "; whole series revised down 2016-2018 (households 25,816 -> 8,549 in 2016, production 55,256 -> 18,251 by 2018): "
                                 "a level revision of all flows, not a household / industry reallocation (tables/TH_BIOMASS_SERIES.csv)",
                     faostat_compare=f"UNSD production {fw_p:,.0f} vs FAOSTAT wood fuel (E) {fao_fw / 1e3:,.0f} thousand m3: ratio {fw_p * 1e3 / fao_fw:.2f}",
                     proposed_main="keep (consistent with FAOSTAT; traded fuel)", proposed_sensitivity="-"),
                dict(commodity="Black liquor (5140)", flow="transformation: electricity plants (export: main activity; SDMX: autoproducers)", value_2019=f"{bl_tj:,.0f} TJ (footnote 'Estimate')",
                     series_note="SDMX 2015-2022: 9,947 / 9,291 / 12,581 / 21,121 / 19,843 / 17,229 / 19,329 / 15,072 TJ",
                     faostat_compare=f"FAOSTAT chemical + dissolving pulp 2019 {pulp / 1e3:,.0f} kt x 22 GJ/t = {pulp * 22 / 1e6:,.1f} PJ; UNSD / that = {bl_tj / (pulp * 22 / 1e3):.2f}",
                     proposed_main="reported, but only as power-plant input: outside T_v2 already (consistent with rule 206 item 3)", proposed_sensitivity="-"),
                dict(commodity="Other vegetal material and residues (5150)", flow="industry (SDMX only; not in the UNdata export used by the model)",
                     value_2019=f"{v5150['industry']:,.0f} TJ = {v5150['industry'] / 3600:.2f} TWh: food {v5150['food']:,.0f}, paper {v5150['paper']:,.0f}, NMM {v5150['nmm']:,.0f}, chemical {v5150['chemical']:,.0f}, wood {v5150['wood']:,.0f}, textile {v5150['textile']:,.0f} TJ",
                     series_note="SDMX 2015-2022 industry 75,465 / 159,400 / 139,111 / 111,102 / 121,044 / 108,194 / 81,332 / 95,611 TJ; from 2020 almost all moved to n.e.s. (reclassification)",
                     faostat_compare="rice 31.2 Mt paddy, oil palm fruit 16.4 Mt, cassava 31.1 Mt, sugar cane 131 Mt (FAOSTAT 2019): husk, fibre, shell residues (INFERENCE)",
                     proposed_main="not in v3 T_v2; food / wood / paper parts are self-produced residues (closed loop, stay out); no change",
                     proposed_sensitivity=f"coverage gap: purchased residues in NMM + chemical ({(v5150['nmm'] + v5150['chemical']) / 3600:.2f} TWh) could enter T_v2 (W12 / W08)"),
                dict(commodity="Other vegetal material and residues (5150)", flow="power and households (SDMX)", value_2019=f"power {v5150['power']:,.0f} TJ; households {v5150['households']:,.0f} TJ",
                     series_note="-", faostat_compare="-", proposed_main="outside T_v2", proposed_sensitivity="-"),
                dict(commodity="Charcoal (5160)", flow="households only", value_2019="1,380 kt", series_note="-", faostat_compare="-", proposed_main="no industrial use", proposed_sensitivity="-")]
            for y, (a, b) in ratio.items():
                ev.put(f"TH.bagasse_per_cane.{y}.export", a, "t/t", "UNSD bagasse production (export) / FAOSTAT sugar cane", "INFERENCE", "B")
            ev.put("TH.bagasse_industry_kt", ind_b, "kt", "UNSD 2019 export", "VERIFIED", "B")
            ev.put("TH.black_liquor_tj", bl_tj, "TJ", "SDMX 2019 5140 08812", "VERIFIED", "B")
            ev.put("TH.black_liquor_vs_pulp", bl_tj / (pulp * 22 / 1e3), "-", "UNSD BL / (FAOSTAT chemical + dissolving pulp x 22 GJ/t)", "INFERENCE", "C")
            ev.put("TH.5150_industry_tj", v5150["industry"], "TJ", "SDMX 2019 5150 121", "VERIFIED", "B")
            ev.put("TH.fuelwood_unsd_over_fao", fw_p * 1e3 / fao_fw, "-", "UNSD fuelwood production / FAOSTAT wood fuel 2019", "INFERENCE", "C")
        elif cc == "PH":
            cane = cm.series(QCL, "Philippines", "Sugar cane").set_index("year").value
            sb = sd[(sd.cc == "PH") & (sd.commodity_code == "5120") & (sd.transaction_code == "01")].set_index("year").value
            ratio = {y: sb.get(y, np.nan) * 1e3 / cane[y] for y in range(2015, 2023) if y in cane.index}
            ind_b, fn_b = get("Bagasse", "manufacturing"); fw_ind, _ = get("Fuelwood", "manufacturing"); fw_hh, _ = get("Fuelwood", "households")
            fw_p, _ = get("Fuelwood", "^production")
            fao_fw = float(cm.series(FO, "Philippines", "Wood fuel, non-coniferous").set_index("year").value[2019])
            v5150 = {k: sdmx("5150", t) for k, t in (("industry", "121"), ("food", "1214F"), ("households", "1231"))}
            aw, _ = get("Animal waste", "manufacturing")
            rows += [
                dict(commodity="Bagasse (5120)", flow="industry: food and tobacco", value_2019=f"{ind_b:,.1f} kt = {ind_b * conv['Bagasse']:.2f} TWh", series_note=series_note("Bagasse", "manufacturing"),
                     faostat_compare="SDMX bagasse production / FAOSTAT cane: " + "; ".join(f"{y} {a:.3f}" for y, a in ratio.items()) + " (IRENA 0.2 - consistent)",
                     proposed_main="closed loop: out of T_v2 (step 8)", proposed_sensitivity="keep (v3)"),
                dict(commodity="Bagasse (5120)", flow="transformation: autoproducer electricity plants", value_2019="1,831.6 kt (footnote 'Estimate' on the autoproducer row)", series_note="outside T_v2",
                     faostat_compare="-", proposed_main="no change", proposed_sensitivity="-"),
                dict(commodity="Fuelwood (5110)", flow="industry: food and tobacco", value_2019=f"{fw_ind:,.1f} thousand m3 = {fw_ind * conv['Fuelwood']:.2f} TWh; households {fw_hh:,.0f}",
                     series_note=series_note("Fuelwood", "manufacturing"), faostat_compare=f"UNSD production {fw_p:,.0f} vs FAOSTAT wood fuel (E) {fao_fw / 1e3:,.0f} thousand m3: ratio {fw_p * 1e3 / fao_fw:.2f}",
                     proposed_main="keep", proposed_sensitivity="-"),
                dict(commodity="Animal waste", flow="industry", value_2019=f"{aw:,.1f} TJ", series_note="-", faostat_compare="-", proposed_main="keep (small)", proposed_sensitivity="-"),
                dict(commodity="Black liquor (5140)", flow="-", value_2019="not reported", series_note="-", faostat_compare="FAOSTAT PH chemical pulp 0 (non-wood pulp 25 kt)", proposed_main="nothing to do", proposed_sensitivity="-"),
                dict(commodity="Other vegetal material and residues (5150)", flow="industry: food (SDMX only)", value_2019=f"{v5150['food']:,.0f} TJ = {v5150['food'] / 3600:.2f} TWh; households {v5150['households']:,.0f} TJ",
                     series_note="SDMX 2015-2022 industry 17,430 -> 18,264 (2019) -> 13,698 (2020)", faostat_compare="coconuts 14.8 Mt, rice 18.8 Mt (FAOSTAT 2019): shells, husks (INFERENCE)",
                     proposed_main="not in v3 T_v2; self-produced food-processing residues (closed loop): no change", proposed_sensitivity="-")]
            ev.put("PH.bagasse_industry_kt", ind_b, "kt", "UNSD 2019 export", "VERIFIED", "B")
            ev.put("PH.5150_food_tj", v5150["food"], "TJ", "SDMX 2019 5150 1214F", "VERIFIED", "B")
        else:
            rows += [dict(commodity="Bagasse (5120)", flow="imports -> main-activity electricity plants", value_2019="403.4 kt (SDMX; export 403.39)", series_note="2015-2022 344-454 kt imports",
                          faostat_compare="SG has no sugar cane: imported solid biomass labelled bagasse (wood chips / kernel shells co-fired in the Jurong Island multi-utility plant, INFERENCE)",
                          proposed_main="outside T_v2 (power); no industrial biomass in UNSD SG", proposed_sensitivity="-"),
                     dict(commodity="Fuelwood (5110), charcoal (5160)", flow="charcoal plants / other consumers", value_2019="small", series_note="-", faostat_compare="FAOSTAT wood fuel 28,271 m3 (E)",
                          proposed_main="no industrial use", proposed_sensitivity="-"),
                     dict(commodity="Black liquor (5140), other vegetal (5150)", flow="-", value_2019="not reported", series_note="-", faostat_compare="-", proposed_main="nothing to do", proposed_sensitivity="-")]
        pd.DataFrame(rows).to_csv(cm.G3 / f"{cc}_BIOMASS_CHECK.csv", index=False)
    ev.write(out / "_biomass_evidence.json")
    for cc in cm.CC3:
        print("=====", cc); print(pd.read_csv(cm.G3 / f"{cc}_BIOMASS_CHECK.csv")[["commodity", "flow", "value_2019", "series_note", "faostat_compare"]].to_string()[:3500])


if __name__ == "__main__":
    main()
